"""Unit tests for conversation title generation."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base, User, Conversation, Message
from app.services.conversation_service import ConversationService
from app.config import settings


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    # Clear any existing metadata to avoid SQLite index conflicts
    for table in Base.metadata.sorted_tables:
        table.indexes.clear()
    
    # Use StaticPool and connect events to handle SQLite concurrency
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create tables with if_not_exists to avoid conflicts
    with engine.begin() as conn:
        Base.metadata.create_all(conn, checkfirst=True)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    yield db

    db.close()
    engine.dispose()


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
def mock_llm_service():
    """Create a mock LLM service."""
    service = AsyncMock()
    return service


class TestTitleGeneration:
    """Test conversation title generation."""

    @pytest.mark.asyncio
    async def test_generate_title_success(self, conversation_service, mock_llm_service):
        """Test generating a valid title."""
        mock_llm_service.generate.return_value = "Test Conversation Topic"

        title = await conversation_service.generate_conversation_title(
            "This is a test message about a specific topic",
            mock_llm_service,
        )

        assert title == "Test Conversation Topic"
        assert len(title) <= settings.TITLE_MAX_LENGTH
        mock_llm_service.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_title_with_quotes(self, conversation_service, mock_llm_service):
        """Test title generation with quotes is stripped."""
        mock_llm_service.generate.return_value = '"Test Conversation Topic"'

        title = await conversation_service.generate_conversation_title(
            "This is a test message",
            mock_llm_service,
        )

        assert title == "Test Conversation Topic"
        assert '"' not in title

    @pytest.mark.asyncio
    async def test_generate_title_truncates_long_message(
        self, conversation_service, mock_llm_service
    ):
        """Test that long messages are truncated to first 50 words."""
        long_message = " ".join(["word"] * 100)
        mock_llm_service.generate.return_value = "Summary"

        title = await conversation_service.generate_conversation_title(
            long_message,
            mock_llm_service,
        )

        # Verify generate was called with truncated content
        call_args = mock_llm_service.generate.call_args
        prompt = call_args.kwargs["prompt"]
        
        # Should only contain ~50 words worth of content
        word_count = len(prompt.split())
        assert word_count <= settings.TITLE_INPUT_WORDS + 5  # +5 for "User message: " prefix

    @pytest.mark.asyncio
    async def test_generate_title_empty_message(
        self, conversation_service, mock_llm_service
    ):
        """Test title generation with empty message falls back."""
        title = await conversation_service.generate_conversation_title(
            "",
            mock_llm_service,
        )

        assert title == "New Conversation"
        mock_llm_service.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_title_whitespace_only(
        self, conversation_service, mock_llm_service
    ):
        """Test title generation with whitespace-only message falls back."""
        title = await conversation_service.generate_conversation_title(
            "   \n\t  ",
            mock_llm_service,
        )

        assert title == "New Conversation"

    @pytest.mark.asyncio
    async def test_generate_title_too_long_regenerates(
        self, conversation_service, mock_llm_service
    ):
        """Test that titles > 30 chars trigger regeneration."""
        # First attempt: too long
        # Second attempt: acceptable
        mock_llm_service.generate.side_effect = [
            "This is a very long title that exceeds the maximum allowed characters",
            "Short Title",
        ]

        title = await conversation_service.generate_conversation_title(
            "Test message",
            mock_llm_service,
        )

        assert title == "Short Title"
        assert len(title) <= settings.TITLE_MAX_LENGTH
        assert mock_llm_service.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_title_still_too_long_after_regenerate(
        self, conversation_service, mock_llm_service
    ):
        """Test that titles still > 30 chars after regenerate are truncated."""
        mock_llm_service.generate.side_effect = [
            "This is still a very long title that exceeds maximum",
            "This is also a very long title that exceeds maximum",
        ]

        title = await conversation_service.generate_conversation_title(
            "Test message",
            mock_llm_service,
        )

        assert len(title) <= settings.TITLE_MAX_LENGTH
        assert mock_llm_service.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_title_too_short_falls_back(
        self, conversation_service, mock_llm_service
    ):
        """Test that generated titles < 3 chars fall back to message prefix."""
        mock_llm_service.generate.return_value = "XY"  # Too short

        title = await conversation_service.generate_conversation_title(
            "My test message for conversation",
            mock_llm_service,
        )

        # Should fallback to first 30 chars of message
        assert len(title) <= settings.TITLE_MAX_LENGTH
        assert title.startswith("My test message")

    @pytest.mark.asyncio
    async def test_generate_title_llm_exception(
        self, conversation_service, mock_llm_service
    ):
        """Test title generation falls back on LLM exception."""
        mock_llm_service.generate.side_effect = Exception("LLM Error")

        title = await conversation_service.generate_conversation_title(
            "Test message for fallback",
            mock_llm_service,
        )

        assert title == "Test message for fallback"
        assert len(title) <= settings.TITLE_MAX_LENGTH

    @pytest.mark.asyncio
    async def test_generate_title_with_special_characters(
        self, conversation_service, mock_llm_service
    ):
        """Test title generation with special characters."""
        mock_llm_service.generate.return_value = "Python 3.11 & Async/Await"

        title = await conversation_service.generate_conversation_title(
            "How to use Python 3.11 with async/await",
            mock_llm_service,
        )

        assert "Python" in title
        assert "&" in title or "and" in title.lower()

    @pytest.mark.asyncio
    async def test_generate_title_temperature_is_low(
        self, conversation_service, mock_llm_service
    ):
        """Test that title generation uses low temperature for consistency."""
        mock_llm_service.generate.return_value = "Title"

        await conversation_service.generate_conversation_title(
            "Test message",
            mock_llm_service,
        )

        call_kwargs = mock_llm_service.generate.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3  # Low temp for factual titles

    @pytest.mark.asyncio
    async def test_generate_title_uses_correct_model(
        self, conversation_service, mock_llm_service
    ):
        """Test that title generation uses the configured fast model."""
        mock_llm_service.generate.return_value = "Title"

        await conversation_service.generate_conversation_title(
            "Test message",
            mock_llm_service,
        )

        call_kwargs = mock_llm_service.generate.call_args.kwargs
        assert call_kwargs["model"] == settings.TITLE_GENERATION_MODEL


class TestUpdateTitleInternal:
    """Test internal title update method."""

    def test_update_title_success(self, conversation_service, test_user, test_db):
        """Test successful title update."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id,
            title="Original Title",
            db=test_db,
        )

        success = conversation_service._update_conversation_title_internal(
            conversation.id,
            "New Title",
            test_db,
        )

        assert success is True

        # Verify title was updated in DB
        updated = test_db.query(Conversation).filter(
            Conversation.id == conversation.id
        ).first()
        assert updated.title == "New Title"

    def test_update_title_not_found(self, conversation_service, test_db):
        """Test update fails gracefully when conversation not found."""
        success = conversation_service._update_conversation_title_internal(
            "nonexistent-id",
            "New Title",
            test_db,
        )

        assert success is False

    def test_update_title_respects_db_constraint(
        self, conversation_service, test_user, test_db
    ):
        """Test that title is truncated to 255 chars (DB constraint)."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id,
            title="Original",
            db=test_db,
        )

        long_title = "X" * 300

        success = conversation_service._update_conversation_title_internal(
            conversation.id,
            long_title,
            test_db,
        )

        assert success is True

        # Verify title was truncated
        updated = test_db.query(Conversation).filter(
            Conversation.id == conversation.id
        ).first()
        assert len(updated.title) == 255

    def test_update_title_updates_timestamp(
        self, conversation_service, test_user, test_db
    ):
        """Test that updated_at timestamp is refreshed."""
        conversation = conversation_service.create_conversation(
            user_id=test_user.id,
            title="Original",
            db=test_db,
        )

        original_updated_at = conversation.updated_at

        # Give time for timestamp to differ
        import time
        time.sleep(0.01)

        conversation_service._update_conversation_title_internal(
            conversation.id,
            "New Title",
            test_db,
        )

        # Verify timestamp was updated
        updated = test_db.query(Conversation).filter(
            Conversation.id == conversation.id
        ).first()
        assert updated.updated_at > original_updated_at

    def test_update_title_db_rollback_on_error(
        self, conversation_service, test_db
    ):
        """Test that DB session is rolled back on error."""
        # Use a closed session to trigger error
        closed_db = test_db
        closed_db.close()

        success = conversation_service._update_conversation_title_internal(
            "any-id",
            "New Title",
            closed_db,
        )

        assert success is False
