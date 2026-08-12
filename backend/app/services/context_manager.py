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

    async def summarize_old_messages(
        self,
        conversation_id: str,
        db: Session,
    ) -> Optional[str]:
        """
        Summarize old messages in conversation when approaching token limit.

        Strategy:
        1. Load all messages chronologically
        2. Calculate cumulative tokens and determine which messages to summarize
        3. Ask LLM to create factual, bullet-point summary
        4. Replace old messages with single summary message (with system role)
        5. Return summary text (or None if no summarization occurred)

        Args:
            conversation_id: Conversation ID
            db: Database session

        Returns:
            Summary text if summarization occurred, None otherwise
        """
        try:
            # Load all messages chronologically
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()

            if len(messages) < settings.SUMMARIZATION_MIN_MESSAGES:
                logger.debug(
                    f"Too few messages ({len(messages)}) to summarize. "
                    f"Minimum: {settings.SUMMARIZATION_MIN_MESSAGES}"
                )
                return None

            # Calculate total tokens
            total_tokens = sum(msg.token_count or self.estimate_tokens(msg.content) for msg in messages)
            threshold = settings.CONTEXT_MAX_TOKENS * settings.SUMMARIZATION_THRESHOLD

            if total_tokens <= threshold:
                logger.debug(
                    f"Token limit not exceeded: {total_tokens} <= {threshold}"
                )
                return None

            # Calculate target token count
            target_tokens = settings.CONTEXT_MAX_TOKENS * settings.SUMMARIZATION_TARGET_RATIO

            # Determine which messages to summarize (oldest first, until we reach target)
            messages_to_summarize = []
            cumulative_tokens = 0

            for msg in messages:
                msg_tokens = msg.token_count or self.estimate_tokens(msg.content)
                if cumulative_tokens < (total_tokens - target_tokens):
                    messages_to_summarize.append(msg)
                    cumulative_tokens += msg_tokens

            if len(messages_to_summarize) < 2:
                logger.debug("Not enough messages to summarize meaningfully")
                return None

            logger.info(
                f"📝 Summarizing {len(messages_to_summarize)} old messages "
                f"({cumulative_tokens} tokens) for conversation: {conversation_id}"
            )

            # Format messages for summarization
            formatted_messages = []
            for msg in messages_to_summarize:
                if msg.role == "user":
                    formatted_messages.append(f"**User:** {msg.content}")
                elif msg.role == "assistant":
                    formatted_messages.append(f"**Assistant:** {msg.content}")

            messages_text = "\n\n".join(formatted_messages)

            # Create summarization prompt (technical, factual, bullet points)
            summary_prompt = f"""Summarize the following conversation concisely as bullet points, preserving key information and context:

---
{messages_text}
---

Provide a summary in 3-5 bullet points covering:
- Main topics discussed
- Important facts or conclusions
- Any decisions made
- Relevant context for future messages

Be factual and technical. Format as bullet points."""

            # Call LLM for summary
            from app.services import get_llm_service
            llm_service = get_llm_service()

            summary = await llm_service.generate(
                prompt=summary_prompt,
                model=settings.SUMMARIZATION_MODEL,
                max_tokens=500,
                temperature=0.3,  # Lower temperature for factual summary
            )

            # Estimate summary token count
            summary_tokens = self.estimate_tokens(summary)

            logger.info(
                f"✅ Summarization complete: {len(messages_to_summarize)} messages "
                f"({cumulative_tokens} tokens) → 1 summary ({summary_tokens} tokens). "
                f"Saved: {cumulative_tokens - summary_tokens} tokens"
            )

            # Create summary message
            import uuid
            summary_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="system",
                content=f"[Previous Conversation Summary]\n{summary}",
                model_used=settings.SUMMARIZATION_MODEL,
                token_count=summary_tokens,
                tool_executions=[],
            )

            # Delete old messages
            message_ids_to_delete = [msg.id for msg in messages_to_summarize]
            db.query(Message).filter(
                Message.id.in_(message_ids_to_delete)
            ).delete(synchronize_session=False)

            # Add summary message
            db.add(summary_message)
            db.commit()

            logger.info(
                f"🔄 Replaced {len(messages_to_summarize)} messages with summary "
                f"in conversation {conversation_id}"
            )

            # Invalidate Redis cache
            if self.redis:
                cache_key = get_conversation_cache_key(conversation_id)
                await self.redis.delete(cache_key)
                logger.debug("♻️  Invalidated context cache after summarization")

            return summary

        except Exception as e:
            logger.error(
                f"Error during summarization: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            # Fall back gracefully - don't block message processing
            return None

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
