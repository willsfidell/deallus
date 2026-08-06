"""
Conversation Service for multi-turn conversation management.

Handles CRUD operations, message storage, and business logic for conversations.
"""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.db.models import Conversation, Message
from app.services.redis_service import RedisService, get_conversation_cache_key
from app.config import settings

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages."""

    def __init__(self, redis_service: Optional[RedisService] = None):
        """
        Initialize conversation service.

        Args:
            redis_service: Optional Redis service for caching
        """
        self.redis = redis_service

    def create_conversation(
        self,
        user_id: int,
        title: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User ID
            title: Optional conversation title (auto-generated if not provided)
            db: Database session

        Returns:
            Created Conversation object
        """
        if db is None:
            raise ValueError("Database session is required")

        conversation_id = str(uuid.uuid4())

        # Auto-generate title if not provided
        if not title:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            title = f"Conversation {timestamp}"

        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            title=title,
            is_active=True,
            conversation_metadata={},
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(f"✅ Created conversation: {conversation_id} (user: {user_id})")

        return conversation

    def get_conversation(
        self,
        conversation_id: str,
        user_id: int,
        db: Session,
    ) -> Optional[Conversation]:
        """
        Get conversation by ID, verifying user ownership.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            db: Database session

        Returns:
            Conversation object or None if not found/not owned
        """
        conversation = db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        ).first()

        if not conversation:
            logger.warning(
                f"Conversation not found or not owned: "
                f"{conversation_id} (user: {user_id})"
            )
            return None

        return conversation

    def list_conversations(
        self,
        user_id: int,
        db: Session,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Conversation]:
        """
        List conversations for a user.

        Args:
            user_id: User ID
            db: Database session
            active_only: Only return active conversations
            limit: Maximum number to return
            offset: Pagination offset

        Returns:
            List of Conversation objects
        """
        query = db.query(Conversation).filter(Conversation.user_id == user_id)

        if active_only:
            query = query.filter(Conversation.is_active == True)

        conversations = query.order_by(
            desc(Conversation.updated_at)
        ).limit(limit).offset(offset).all()

        logger.info(
            f"📋 Listed {len(conversations)} conversations for user {user_id}"
        )

        return conversations

    def update_conversation(
        self,
        conversation_id: str,
        user_id: int,
        db: Session,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[Conversation]:
        """
        Update conversation details.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            db: Database session
            title: New title (if provided)
            metadata: New metadata (merged with existing)

        Returns:
            Updated Conversation object or None if not found/not owned
        """
        conversation = self.get_conversation(conversation_id, user_id, db)

        if not conversation:
            return None

        if title:
            conversation.title = title

        if metadata:
            # Merge with existing metadata
            conversation.conversation_metadata = {
                **conversation.conversation_metadata,
                **metadata,
            }

        conversation.updated_at = datetime.utcnow()

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(f"✏️  Updated conversation: {conversation_id}")

        # Invalidate Redis cache
        if self.redis:
            cache_key = get_conversation_cache_key(conversation_id)
            import asyncio
            try:
                asyncio.create_task(self.redis.delete(cache_key))
            except:
                pass

        return conversation

    def archive_conversation(
        self,
        conversation_id: str,
        user_id: int,
        db: Session,
    ) -> Optional[Conversation]:
        """
        Archive (soft delete) a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            db: Database session

        Returns:
            Archived Conversation object or None if not found/not owned
        """
        conversation = self.get_conversation(conversation_id, user_id, db)

        if not conversation:
            return None

        conversation.is_active = False
        conversation.updated_at = datetime.utcnow()

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(f"🗑️  Archived conversation: {conversation_id}")

        # Invalidate Redis cache
        if self.redis:
            cache_key = get_conversation_cache_key(conversation_id)
            import asyncio
            try:
                asyncio.create_task(self.redis.delete(cache_key))
            except:
                pass

        return conversation

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        db: Session,
        model_used: Optional[str] = None,
        token_count: int = 0,
        tool_executions: Optional[list] = None,
        attachments: Optional[list] = None,
    ) -> Message:
        """
        Add a message to conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role ("user", "assistant", "system")
            content: Message content
            db: Database session
            model_used: Model used (if role is "assistant")
            token_count: Estimated token count
            tool_executions: List of tool execution details
            attachments: Optional list of attachment metadata dicts

        Returns:
            Created Message object
        """
        message_id = str(uuid.uuid4())

        message = Message(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_used=model_used,
            token_count=token_count,
            tool_executions=tool_executions or [],
            attachments=attachments or [],
        )

        db.add(message)

        # Update conversation updated_at
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if conversation:
            conversation.updated_at = datetime.utcnow()
            db.add(conversation)

        db.commit()
        db.refresh(message)

        logger.info(
            f"✉️  Added {role} message to conversation {conversation_id}: "
            f"{message_id}"
        )

        # Invalidate Redis cache
        if self.redis:
            cache_key = get_conversation_cache_key(conversation_id)
            import asyncio
            try:
                asyncio.create_task(self.redis.delete(cache_key))
            except:
                pass

        return message

    def get_conversation_messages(
        self,
        conversation_id: str,
        db: Session,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Message]:
        """
        Get all messages in a conversation.

        Args:
            conversation_id: Conversation ID
            db: Database session
            limit: Maximum number of messages to return
            offset: Pagination offset

        Returns:
            List of Message objects in chronological order
        """
        query = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)

        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        messages = query.all()

        logger.debug(
            f"📧 Retrieved {len(messages)} messages from conversation {conversation_id}"
        )

        return messages

    def get_conversation_message_count(
        self,
        conversation_id: str,
        db: Session,
    ) -> int:
        """
        Get total message count for a conversation.

        Args:
            conversation_id: Conversation ID
            db: Database session

        Returns:
            Message count
        """
        count = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).count()

        return count

    def delete_message(
        self,
        message_id: str,
        conversation_id: str,
        db: Session,
    ) -> bool:
        """
        Delete a message from conversation.

        Args:
            message_id: Message ID
            conversation_id: Conversation ID (for verification)
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        message = db.query(Message).filter(
            and_(
                Message.id == message_id,
                Message.conversation_id == conversation_id,
            )
        ).first()

        if not message:
            logger.warning(f"Message not found: {message_id}")
            return False

        db.delete(message)
        db.commit()

        logger.info(f"🗑️  Deleted message: {message_id}")

        # Invalidate Redis cache
        if self.redis:
            cache_key = get_conversation_cache_key(conversation_id)
            import asyncio
            try:
                asyncio.create_task(self.redis.delete(cache_key))
            except:
                pass

        return True

    def clear_conversation(
        self,
        conversation_id: str,
        user_id: int,
        db: Session,
    ) -> Optional[Conversation]:
        """
        Clear all messages from a conversation (soft reset).

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership verification)
            db: Database session

        Returns:
            Conversation object or None if not found/not owned
        """
        conversation = self.get_conversation(conversation_id, user_id, db)

        if not conversation:
            return None

        # Delete all messages
        db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()

        conversation.updated_at = datetime.utcnow()

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(f"🧹 Cleared all messages from conversation: {conversation_id}")

        # Invalidate Redis cache
        if self.redis:
            cache_key = get_conversation_cache_key(conversation_id)
            import asyncio
            try:
                asyncio.create_task(self.redis.delete(cache_key))
            except:
                pass

        return conversation

    async def generate_conversation_title(
        self,
        message_content: str,
        llm_service,
    ) -> str:
        """
        Generate a concise conversation title from first message.

        Args:
            message_content: First user message content
            llm_service: LLM service instance

        Returns:
            Generated title (max TITLE_MAX_LENGTH chars)
        """
        try:
            # Truncate to first N words
            words = message_content.strip().split()[:settings.TITLE_INPUT_WORDS]
            truncated_content = " ".join(words)

            if not truncated_content:
                return "New Conversation"

            # Build system prompt
            system_prompt = (
                f"Generate a brief, descriptive title (maximum {settings.TITLE_MAX_LENGTH} characters) "
                f"for this conversation based on the user's message. The title should capture "
                f"the main topic or intent. Respond with ONLY the title text, no quotes or extra punctuation."
            )

            # Try to generate title with regeneration logic for titles > 30 chars
            attempts = 0
            max_attempts = 2

            while attempts < max_attempts:
                generated_title = await llm_service.generate(
                    prompt=f"User message: {truncated_content}",
                    model=settings.TITLE_GENERATION_MODEL,
                    max_tokens=20,
                    temperature=0.3,
                    system_prompt=system_prompt,
                )

                # Clean title (remove quotes, strip whitespace)
                title = generated_title.strip().strip('"\'')

                # Check if title is acceptable length
                if len(title) <= settings.TITLE_MAX_LENGTH:
                    # Title is good!
                    if len(title) >= 3:
                        logger.info(f"Generated title: '{title}' ({len(title)} chars)")
                        return title
                    else:
                        # Too short, use fallback
                        logger.warning(f"Generated title too short: '{title}'")
                        break

                # Title too long, try to regenerate if attempts left
                attempts += 1
                if attempts < max_attempts:
                    logger.info(
                        f"Title too long ({len(title)} chars), regenerating with stricter instructions..."
                    )
                    system_prompt = (
                        f"Generate a VERY brief title (MAXIMUM {settings.TITLE_MAX_LENGTH} characters, "
                        f"no more!). Be extremely concise. Respond with ONLY the title, no quotes."
                    )

            # If we got here, either regeneration failed or title was still too long
            # Fallback: first TITLE_MAX_LENGTH chars of message
            logger.warning(f"Title generation failed after {attempts} attempts. Using fallback.")
            fallback = message_content.strip()[:settings.TITLE_MAX_LENGTH]
            return fallback if fallback else "New Conversation"

        except Exception as e:
            # Fallback: First TITLE_MAX_LENGTH chars of message
            logger.warning(f"Title generation exception: {e}. Using fallback.")
            fallback = message_content.strip()[:settings.TITLE_MAX_LENGTH]
            return fallback if fallback else "New Conversation"

    def _update_conversation_title_internal(
        self,
        conversation_id: str,
        title: str,
        db: Session,
    ) -> bool:
        """
        Update conversation title (internal use, no ownership check).

        Used by async background tasks where ownership already verified.

        Args:
            conversation_id: Conversation ID
            title: New title
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if not conversation:
                logger.warning(
                    f"Conversation {conversation_id} not found for title update"
                )
                return False

            # Update title (respect DB constraint: max 255 chars)
            conversation.title = title[:255]
            conversation.updated_at = datetime.utcnow()

            db.add(conversation)
            db.commit()

            logger.info(
                f"✏️  Updated title for conversation {conversation_id}: '{title}'"
            )

            # Invalidate Redis cache
            if self.redis:
                cache_key = get_conversation_cache_key(conversation_id)
                try:
                    asyncio.create_task(self.redis.delete(cache_key))
                except:
                    pass

            return True

        except Exception as e:
            logger.error(f"Failed to update conversation title: {e}")
            db.rollback()
            return False
