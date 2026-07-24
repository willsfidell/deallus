"""Integration tests for multi-turn conversation flow."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base, User, APIKey, Conversation, Message
from app.services.context_manager import ContextManager
from app.services.conversation_service import ConversationService
from app.services.redis_service import RedisService
from app.config import settings


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    yield db

    db.close()


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password_here",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def conversation_service(test_db: Session):
    """Create a conversation service for testing."""
    return ConversationService(redis_service=None)  # No Redis for tests


@pytest.fixture
def context_manager(test_db: Session):
    """Create a context manager for testing."""
    return ContextManager(redis_service=None)  # No Redis for tests


class TestConversationCreation:
    """Test conversation creation and management."""

    def test_create_conversation(self, conversation_service, test_user, test_db):
        """Test creating a new conversation."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, title="Test Conversation", db=test_db
        )

        assert conversation.id is not None
        assert conversation.user_id == test_user.id
        assert conversation.title == "Test Conversation"
        assert conversation.is_active == True

    def test_create_conversation_auto_title(
        self, conversation_service, test_user, test_db
    ):
        """Test that conversation gets auto-generated title if not provided."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        assert conversation.title is not None
        assert "Conversation" in conversation.title

    def test_get_conversation_ownership(
        self, conversation_service, test_user, test_db
    ):
        """Test that conversations can only be retrieved by owner."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, title="Private", db=test_db
        )

        # Owner can retrieve
        retrieved = conversation_service.get_conversation(
            conversation.id, test_user.id, test_db
        )
        assert retrieved is not None

        # Different user cannot retrieve
        different_user_id = test_user.id + 999
        retrieved = conversation_service.get_conversation(
            conversation.id, different_user_id, test_db
        )
        assert retrieved is None

    def test_list_conversations(self, conversation_service, test_user, test_db):
        """Test listing conversations for a user."""
        # Create 3 conversations
        for i in range(3):
            conversation_service.create_conversation(
                user_id=test_user.id, title=f"Conversation {i}", db=test_db
            )

        conversations = conversation_service.list_conversations(
            user_id=test_user.id, db=test_db
        )

        assert len(conversations) == 3

    def test_archive_conversation(self, conversation_service, test_user, test_db):
        """Test archiving (soft delete) a conversation."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, title="To Archive", db=test_db
        )

        archived = conversation_service.archive_conversation(
            conversation.id, test_user.id, test_db
        )

        assert archived.is_active == False

        # Archived conversation not in active list
        active = conversation_service.list_conversations(
            user_id=test_user.id, db=test_db, active_only=True
        )
        assert len(active) == 0


class TestConversationMessages:
    """Test message storage in conversations."""

    def test_add_user_message(self, conversation_service, test_user, test_db):
        """Test adding a user message to conversation."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        message = conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Hello, how are you?",
            db=test_db,
        )

        assert message.id is not None
        assert message.role == "user"
        assert message.content == "Hello, how are you?"

    def test_add_assistant_message_with_model(
        self, conversation_service, test_user, test_db
    ):
        """Test adding an assistant message with model used."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        message = conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content="I'm doing well, thank you for asking!",
            db=test_db,
            model_used="ollama/llama2",
            token_count=15,
        )

        assert message.model_used == "ollama/llama2"
        assert message.token_count == 15

    def test_get_conversation_messages(self, conversation_service, test_user, test_db):
        """Test retrieving messages from a conversation."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Add 3 messages
        for i in range(3):
            conversation_service.add_message(
                conversation_id=conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                db=test_db,
                model_used="ollama/llama2" if i % 2 == 1 else None,
            )

        messages = conversation_service.get_conversation_messages(
            conversation.id, test_db
        )

        assert len(messages) == 3
        # Messages should be in chronological order
        for i, msg in enumerate(messages):
            assert msg.content == f"Message {i}"

    def test_message_count(self, conversation_service, test_user, test_db):
        """Test getting message count."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Add messages
        for i in range(5):
            conversation_service.add_message(
                conversation_id=conversation.id,
                role="user",
                content=f"Message {i}",
                db=test_db,
            )

        count = conversation_service.get_conversation_message_count(
            conversation.id, test_db
        )

        assert count == 5

    def test_delete_message(self, conversation_service, test_user, test_db):
        """Test deleting a message from conversation."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        message = conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Delete me",
            db=test_db,
        )

        # Delete the message
        success = conversation_service.delete_message(
            message.id, conversation.id, test_db
        )

        assert success == True

        # Message should be gone
        messages = conversation_service.get_conversation_messages(
            conversation.id, test_db
        )
        assert len(messages) == 0

    def test_clear_conversation(self, conversation_service, test_user, test_db):
        """Test clearing all messages from conversation."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Add 5 messages
        for i in range(5):
            conversation_service.add_message(
                conversation_id=conversation.id,
                role="user",
                content=f"Message {i}",
                db=test_db,
            )

        # Clear conversation
        cleared = conversation_service.clear_conversation(
            conversation.id, test_user.id, test_db
        )

        assert cleared is not None

        # No messages should remain
        messages = conversation_service.get_conversation_messages(
            conversation.id, test_db
        )
        assert len(messages) == 0


class TestContextManagement:
    """Test context loading and management."""

    def test_estimate_tokens(self, context_manager):
        """Test token estimation."""
        text = "This is a test message"
        tokens = context_manager.estimate_tokens(text)

        # Should be approximately len(text) * 0.25
        assert tokens > 0
        assert tokens == len(text) // 4 or tokens == (len(text) // 4) + 1

    @pytest.mark.asyncio
    async def test_load_conversation_context(
        self, context_manager, conversation_service, test_user, test_db
    ):
        """Test loading conversation context."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Add messages
        conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Hello",
            db=test_db,
        )

        conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content="Hi there! How can I help?",
            db=test_db,
            model_used="ollama/llama2",
        )

        # Load context
        context = await context_manager.get_conversation_context(
            conversation.id, test_db, include_system_message=False
        )

        assert context["message_count"] == 2
        assert context["last_model_used"] == "ollama/llama2"
        assert context["total_tokens"] > 0
        assert len(context["messages"]) == 2

    @pytest.mark.asyncio
    async def test_context_respects_message_limit(
        self, context_manager, conversation_service, test_user, test_db
    ):
        """Test that context respects max messages limit."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Add more messages than max_messages
        max_messages = context_manager.max_messages
        for i in range(max_messages + 5):
            conversation_service.add_message(
                conversation_id=conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                db=test_db,
            )

        # Load context
        context = await context_manager.get_conversation_context(
            conversation.id, test_db, include_system_message=False
        )

        # Should not exceed max_messages
        assert context["message_count"] <= max_messages

    @pytest.mark.asyncio
    async def test_context_preserves_message_order(
        self, context_manager, conversation_service, test_user, test_db
    ):
        """Test that context preserves chronological message order."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Add messages with specific content
        for i in range(5):
            conversation_service.add_message(
                conversation_id=conversation.id,
                role="user",
                content=f"Message {i}",
                db=test_db,
            )

        # Load context
        context = await context_manager.get_conversation_context(
            conversation.id, test_db, include_system_message=False
        )

        # Messages should be in order (after system message if included)
        non_system_messages = [m for m in context["messages"] if m["role"] != "system"]
        for i, msg in enumerate(non_system_messages):
            assert msg["content"] == f"Message {i}"


class TestMultiTurnConversation:
    """Test complete multi-turn conversation scenarios."""

    @pytest.mark.asyncio
    async def test_image_task_continuity(
        self,
        context_manager,
        conversation_service,
        test_user,
        test_db,
    ):
        """Test task continuity across multiple turns."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Turn 1: Image generation
        conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Draw an image of a ball",
            db=test_db,
        )

        conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content="[Generated image of a ball]",
            db=test_db,
            model_used="ollama/stable-diffusion",
        )

        # Turn 2: Follow-up for same image
        conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Make it blue",
            db=test_db,
        )

        # Load context - should have previous model
        context = await context_manager.get_conversation_context(
            conversation.id, test_db, include_system_message=False
        )

        assert context["last_model_used"] == "ollama/stable-diffusion"
        assert context["message_count"] == 3

    @pytest.mark.asyncio
    async def test_topic_switch_detection(
        self,
        context_manager,
        conversation_service,
        test_user,
        test_db,
    ):
        """Test detecting topic switches in conversation."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id, db=test_db
        )

        # Turn 1: Image generation
        conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Draw an image",
            db=test_db,
        )

        conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content="[Generated image]",
            db=test_db,
            model_used="ollama/stable-diffusion",
        )

        # Turn 2: Different topic
        conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Classify this sentiment: Great product!",
            db=test_db,
        )

        # Load context - should still have image model as previous
        context = await context_manager.get_conversation_context(
            conversation.id, test_db, include_system_message=False
        )

        # Even though topic switched, context should record previous model
        # (The routing decision would use this context to apply bonus)
        assert context["last_model_used"] == "ollama/stable-diffusion"
