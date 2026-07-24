"""
Context Manager for multi-turn conversations.

Manages conversation context windows, message loading, token counting, and truncation.
Uses Redis cache with PostgreSQL fallback for persistence.
"""

import logging
from typing import Optional, Dict, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.db.models import Conversation, Message
from app.services.redis_service import (
    RedisService,
    get_conversation_cache_key,
    get_conversation_messages_key,
)

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages conversation context, message loading, and token management."""

    def __init__(self, redis_service: Optional[RedisService] = None):
        """
        Initialize context manager.

        Args:
            redis_service: Optional Redis service for caching
        """
        self.redis = redis_service
        self.max_messages = settings.CONTEXT_MAX_MESSAGES
        self.max_tokens = settings.CONTEXT_MAX_TOKENS
        self.token_multiplier = settings.TOKEN_ESTIMATE_MULTIPLIER

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.

        Simple heuristic: ~4 characters per token (LLM average).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return max(1, int(len(text) * settings.TOKEN_ESTIMATE_MULTIPLIER))

    async def get_conversation_context(
        self,
        conversation_id: str,
        db: Session,
        include_system_message: bool = True,
    ) -> Dict[str, Any]:
        """
        Load conversation context for a new message.

        Context includes:
        - Previous messages (up to max_messages, max_tokens)
        - Last model used (for continuity bonus)
        - Total token count

        Args:
            conversation_id: ID of conversation
            db: Database session
            include_system_message: Whether to include a system message in context

        Returns:
            Dict with keys:
                - messages: List of message dicts in conversation order
                - last_model_used: Model used in last assistant message (or None)
                - total_tokens: Total tokens in context
                - message_count: Number of messages loaded
        """
        # Try Redis cache first
        cache_key = get_conversation_cache_key(conversation_id)
        if self.redis:
            cached_context = await self.redis.get(cache_key)
            if cached_context:
                logger.info(
                    f"🔗 Context loaded from Redis cache: {conversation_id} "
                    f"({len(cached_context.get('messages', []))} messages)"
                )
                return cached_context

        # Fall back to database
        logger.info(f"🔍 Loading context from database: {conversation_id}")

        try:
            # Load conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return {
                    "messages": [],
                    "last_model_used": None,
                    "total_tokens": 0,
                    "message_count": 0,
                }

            # Load messages in descending order (latest first)
            db_messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(desc(Message.created_at)).limit(self.max_messages).all()

            # Reverse to chronological order
            db_messages = list(reversed(db_messages))

            # Build context with token tracking
            messages = []
            total_tokens = 0

            # Add system message if requested
            if include_system_message:
                system_message = {
                    "role": "system",
                    "content": (
                        "You are a helpful AI assistant. "
                        "Respond concisely and accurately."
                    ),
                }
                system_tokens = self.estimate_tokens(system_message["content"])
                messages.append(system_message)
                total_tokens += system_tokens

            # Add user/assistant messages, respecting token limit
            last_model_used = None

            for msg in db_messages:
                msg_tokens = msg.token_count or self.estimate_tokens(msg.content)

                # Check if adding this message would exceed token limit
                if total_tokens + msg_tokens > self.max_tokens:
                    logger.debug(
                        f"⚠️  Context window limit reached: "
                        f"{total_tokens + msg_tokens} > {self.max_tokens}"
                    )
                    break

                message_dict = {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                }

                if msg.role == "assistant":
                    message_dict["model_used"] = msg.model_used
                    last_model_used = msg.model_used

                messages.append(message_dict)
                total_tokens += msg_tokens

            # Build context result
            context = {
                "messages": messages,
                "last_model_used": last_model_used,
                "total_tokens": total_tokens,
                "message_count": len([m for m in messages if m["role"] != "system"]),
            }

            logger.info(
                f"✅ Context loaded: {conversation_id} "
                f"({len(context['messages'])} messages, "
                f"{total_tokens} tokens, "
                f"last_model: {last_model_used})"
            )

            # Cache context in Redis
            if self.redis:
                cache_ttl = 3600  # 1 hour
                await self.redis.set(cache_key, context, ttl=cache_ttl)
                logger.debug(f"💾 Context cached in Redis (TTL: {cache_ttl}s)")

            return context

        except Exception as e:
            logger.error(f"Error loading conversation context: {e}", exc_info=True)
            return {
                "messages": [],
                "last_model_used": None,
                "total_tokens": 0,
                "message_count": 0,
            }

    async def add_message_to_context(
        self,
        conversation_id: str,
        message_id: str,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        token_count: Optional[int] = None,
    ) -> None:
        """
        Add a message to conversation context and update caches.

        Args:
            conversation_id: Conversation ID
            message_id: Message ID
            role: Message role ("user", "assistant", "system")
            content: Message content
            model_used: Model used (if role is "assistant")
            token_count: Token count (calculated if not provided)
        """
        if token_count is None:
            token_count = self.estimate_tokens(content)

        # Invalidate Redis cache for this conversation
        if self.redis:
            cache_key = get_conversation_cache_key(conversation_id)
            await self.redis.delete(cache_key)
            logger.debug(f"♻️  Invalidated context cache: {conversation_id}")

    async def truncate_context(
        self,
        conversation_id: str,
        db: Session,
    ) -> None:
        """
        Truncate old messages from conversation if token limit exceeded.

        This is a simple truncation strategy (oldest messages dropped first).
        Future enhancement: Use LLM to summarize old messages instead.

        Args:
            conversation_id: Conversation ID
            db: Database session
        """
        logger.info(f"🔄 Truncating context for conversation: {conversation_id}")

        try:
            # Get all messages in chronological order
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()

            if len(messages) <= self.max_messages:
                logger.debug("No truncation needed, message count within limit")
                return

            # Calculate which messages to keep (keep last max_messages)
            messages_to_drop = len(messages) - self.max_messages
            messages_to_drop_ids = [msg.id for msg in messages[:messages_to_drop]]

            # Delete old messages
            db.query(Message).filter(
                Message.id.in_(messages_to_drop_ids)
            ).delete(synchronize_session=False)

            db.commit()

            logger.info(
                f"✅ Truncated {messages_to_drop} old messages "
                f"from conversation: {conversation_id}"
            )

            # Invalidate cache
            if self.redis:
                cache_key = get_conversation_cache_key(conversation_id)
                await self.redis.delete(cache_key)

        except Exception as e:
            logger.error(f"Error truncating context: {e}", exc_info=True)
            db.rollback()

    def format_messages_for_api(self, messages: List[Dict]) -> str:
        """
        Format messages for display/API response.

        Args:
            messages: List of message dicts

        Returns:
            Formatted string representation
        """
        formatted = []
        for msg in messages:
            if msg["role"] == "system":
                formatted.append(f"[SYSTEM] {msg['content'][:100]}...")
            else:
                content_preview = msg["content"][:50] + (
                    "..." if len(msg["content"]) > 50 else ""
                )
                formatted.append(f"[{msg['role'].upper()}] {content_preview}")

        return "\n".join(formatted)
