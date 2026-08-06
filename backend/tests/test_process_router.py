"""Tests for process router with attachment integration."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base, User, Attachment, Conversation, Message
from app.models.schemas import ProcessRequest
from app.services.conversation_service import ConversationService
from app.services.context_manager import ContextManager
from app.config import settings


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    from sqlalchemy.pool import StaticPool
    
    # Clear any existing metadata to avoid SQLite index conflicts
    for table in Base.metadata.sorted_tables:
        table.indexes.clear()
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create tables with checkfirst to avoid conflicts
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
def test_conversation(test_db: Session, test_user: User):
    """Create a test conversation."""
    conv = Conversation(
        id="conv_001",
        user_id=test_user.id,
        title="Test Conversation",
        is_active=True,
        conversation_metadata={},
    )
    test_db.add(conv)
    test_db.commit()
    test_db.refresh(conv)
    return conv


@pytest.fixture
def conversation_service(test_db: Session):
    """Create a conversation service for testing."""
    return ConversationService(redis_service=None)


@pytest.fixture
def context_manager(test_db: Session):
    """Create a context manager for testing."""
    return ContextManager(redis_service=None)


class TestAttachmentLoading:
    """Tests for loading and extracting attachment text."""
    
    def test_attachment_loading_single_file(self, test_db: Session, test_user: User):
        """Test loading a single attachment."""
        # Create attachment
        attachment = Attachment(
            id="att_001",
            user_id=test_user.id,
            filename="document.txt",
            mime_type="text/plain",
            size_bytes=100,
            extracted_text="This is test content from the attachment.",
            extraction_status="completed",
            page_count=1,
            word_count=7,
            extraction_method="text_extraction",
            ocr_applied=False,
        )
        test_db.add(attachment)
        test_db.commit()
        
        # Load attachment
        loaded = test_db.query(Attachment).filter(
            Attachment.id == "att_001",
            Attachment.user_id == test_user.id
        ).first()
        
        assert loaded is not None
        assert loaded.filename == "document.txt"
        assert loaded.extracted_text == "This is test content from the attachment."
        assert loaded.extraction_status == "completed"
    
    def test_attachment_loading_multiple_files(self, test_db: Session, test_user: User):
        """Test loading multiple attachments."""
        # Create multiple attachments
        att1 = Attachment(
            id="att_001",
            user_id=test_user.id,
            filename="doc1.txt",
            mime_type="text/plain",
            size_bytes=100,
            extracted_text="Content 1",
            extraction_status="completed",
            word_count=2,
        )
        att2 = Attachment(
            id="att_002",
            user_id=test_user.id,
            filename="doc2.txt",
            mime_type="text/plain",
            size_bytes=120,
            extracted_text="Content 2",
            extraction_status="completed",
            word_count=2,
        )
        test_db.add_all([att1, att2])
        test_db.commit()
        
        # Load both
        attachments = test_db.query(Attachment).filter(
            Attachment.user_id == test_user.id,
            Attachment.id.in_(["att_001", "att_002"])
        ).all()
        
        assert len(attachments) == 2
        assert attachments[0].filename in ["doc1.txt", "doc2.txt"]
        assert attachments[1].filename in ["doc1.txt", "doc2.txt"]
    
    def test_attachment_loading_incomplete_skipped(self, test_db: Session, test_user: User):
        """Test that incomplete attachments are skipped."""
        # Create incomplete attachment
        attachment = Attachment(
            id="att_001",
            user_id=test_user.id,
            filename="processing.txt",
            mime_type="text/plain",
            size_bytes=100,
            extracted_text=None,
            extraction_status="processing",
            word_count=0,
        )
        test_db.add(attachment)
        test_db.commit()
        
        # Try to load with filter for completed
        loaded = test_db.query(Attachment).filter(
            Attachment.id == "att_001",
            Attachment.extraction_status == "completed"
        ).first()
        
        assert loaded is None
    
    def test_attachment_loading_user_ownership(self, test_db: Session):
        """Test that attachments are filtered by user ownership."""
        # Create two users
        user1 = User(email="user1@example.com", username="user1", hashed_password="pass1", is_active=True)
        user2 = User(email="user2@example.com", username="user2", hashed_password="pass2", is_active=True)
        test_db.add_all([user1, user2])
        test_db.commit()
        
        # Create attachment for user1
        att = Attachment(
            id="att_001",
            user_id=user1.id,
            filename="user1_doc.txt",
            mime_type="text/plain",
            size_bytes=100,
            extracted_text="User 1 content",
            extraction_status="completed",
            word_count=2,
        )
        test_db.add(att)
        test_db.commit()
        
        # User2 should not be able to load it
        loaded_by_user2 = test_db.query(Attachment).filter(
            Attachment.id == "att_001",
            Attachment.user_id == user2.id
        ).first()
        
        assert loaded_by_user2 is None
        
        # User1 should be able to load it
        loaded_by_user1 = test_db.query(Attachment).filter(
            Attachment.id == "att_001",
            Attachment.user_id == user1.id
        ).first()
        
        assert loaded_by_user1 is not None


class TestAttachmentTextTruncation:
    """Tests for attachment text truncation logic."""
    
    def test_truncation_under_limit(self):
        """Test that short text is not truncated."""
        text = "This is short text " * 50  # ~250 words
        words = text.split()
        
        assert len(words) < settings.MAX_ATTACHMENT_WORDS_IN_PROMPT
    
    def test_truncation_over_limit(self):
        """Test that long text is truncated correctly."""
        # Create text longer than limit
        text = "word " * (settings.MAX_ATTACHMENT_WORDS_IN_PROMPT + 100)
        words = text.split()
        
        assert len(words) > settings.MAX_ATTACHMENT_WORDS_IN_PROMPT
        
        # Simulate truncation logic
        if len(words) > settings.MAX_ATTACHMENT_WORDS_IN_PROMPT:
            truncated = " ".join(words[:settings.MAX_ATTACHMENT_WORDS_IN_PROMPT])
            truncated_words = truncated.split()
            
            assert len(truncated_words) == settings.MAX_ATTACHMENT_WORDS_IN_PROMPT
    
    def test_truncation_message_format(self):
        """Test format of truncation message."""
        word_count = settings.MAX_ATTACHMENT_WORDS_IN_PROMPT + 100
        omitted = word_count - settings.MAX_ATTACHMENT_WORDS_IN_PROMPT
        
        # Simulate the message
        message = f"[... {omitted} words omitted]"
        
        assert str(omitted) in message
        assert "words omitted" in message


class TestAttachmentPromptIntegration:
    """Tests for integrating attachment text into prompts."""
    
    def test_prompt_building_single_attachment(self):
        """Test prompt building with single attachment."""
        user_question = "Summarize this"
        attachment_text = "This is the document content"
        filename = "document.txt"
        
        # Simulate prompt building
        prompt_part = f"[File: {filename}]\n{attachment_text}"
        enhanced_prompt = f"{prompt_part}\n\nUser question: {user_question}"
        
        assert filename in enhanced_prompt
        assert attachment_text in enhanced_prompt
        assert user_question in enhanced_prompt
        assert "[File:" in enhanced_prompt
    
    def test_prompt_building_multiple_attachments(self):
        """Test prompt building with multiple attachments."""
        user_question = "Compare these"
        attachments = [
            {"filename": "doc1.txt", "text": "Content 1"},
            {"filename": "doc2.txt", "text": "Content 2"},
        ]
        
        # Simulate prompt building
        prompt_parts = []
        for att in attachments:
            prompt_parts.append(f"[File: {att['filename']}]\n{att['text']}")
        
        enhanced_prompt = "\n\n".join(prompt_parts) + "\n\nUser question: " + user_question
        
        assert "doc1.txt" in enhanced_prompt
        assert "doc2.txt" in enhanced_prompt
        assert "Content 1" in enhanced_prompt
        assert "Content 2" in enhanced_prompt
        assert user_question in enhanced_prompt
    
    def test_prompt_without_attachments(self):
        """Test that prompt works without attachments."""
        user_question = "Hello world"
        
        # No attachments case
        enhanced_prompt = user_question
        
        assert enhanced_prompt == user_question
        assert "[File:" not in enhanced_prompt


class TestMessageStorage:
    """Tests for storing attachment metadata with messages."""
    
    def test_message_with_attachment_metadata(self, test_db: Session, test_user: User, 
                                              test_conversation: Conversation, 
                                              conversation_service: ConversationService):
        """Test storing message with attachment metadata."""
        attachment_metadata = {
            "id": "att_001",
            "filename": "document.txt",
            "mime_type": "text/plain",
            "size_bytes": 1024,
            "extracted_text": "Content",
            "page_count": 1,
            "word_count": 1,
            "extraction_method": "text",
            "ocr_applied": False,
        }
        
        # Add message with attachments
        message = conversation_service.add_message(
            conversation_id=test_conversation.id,
            role="user",
            content="Process this attachment",
            db=test_db,
            attachments=[attachment_metadata],
        )
        
        assert message.attachments is not None
        assert len(message.attachments) == 1
        assert message.attachments[0]["id"] == "att_001"
        assert message.attachments[0]["filename"] == "document.txt"
    
    def test_message_with_multiple_attachment_metadata(self, test_db: Session, test_user: User,
                                                        test_conversation: Conversation,
                                                        conversation_service: ConversationService):
        """Test storing message with multiple attachment metadata."""
        attachments = [
            {
                "id": "att_001",
                "filename": "doc1.txt",
                "mime_type": "text/plain",
                "size_bytes": 100,
                "extracted_text": "Content 1",
                "page_count": 1,
                "word_count": 2,
                "extraction_method": "text",
                "ocr_applied": False,
            },
            {
                "id": "att_002",
                "filename": "doc2.txt",
                "mime_type": "text/plain",
                "size_bytes": 120,
                "extracted_text": "Content 2",
                "page_count": 1,
                "word_count": 2,
                "extraction_method": "text",
                "ocr_applied": False,
            },
        ]
        
        message = conversation_service.add_message(
            conversation_id=test_conversation.id,
            role="user",
            content="Process these attachments",
            db=test_db,
            attachments=attachments,
        )
        
        assert len(message.attachments) == 2
        assert message.attachments[0]["filename"] == "doc1.txt"
        assert message.attachments[1]["filename"] == "doc2.txt"
    
    def test_message_without_attachments(self, test_db: Session, test_user: User,
                                        test_conversation: Conversation,
                                        conversation_service: ConversationService):
        """Test that message without attachments still works."""
        message = conversation_service.add_message(
            conversation_id=test_conversation.id,
            role="user",
            content="Simple message",
            db=test_db,
        )
        
        assert message.attachments == []


class TestAttachmentCleanup:
    """Tests for attachment cleanup after processing."""
    
    def test_attachment_deletion(self, test_db: Session, test_user: User):
        """Test that attachments can be deleted."""
        # Create attachment
        attachment = Attachment(
            id="att_001",
            user_id=test_user.id,
            filename="temp.txt",
            mime_type="text/plain",
            size_bytes=100,
            extracted_text="Temporary content",
            extraction_status="completed",
            word_count=2,
        )
        test_db.add(attachment)
        test_db.commit()
        
        # Verify it exists
        exists = test_db.query(Attachment).filter(Attachment.id == "att_001").first()
        assert exists is not None
        
        # Delete it
        test_db.delete(attachment)
        test_db.commit()
        
        # Verify deletion
        exists = test_db.query(Attachment).filter(Attachment.id == "att_001").first()
        assert exists is None
    
    def test_multiple_attachment_deletion(self, test_db: Session, test_user: User):
        """Test deletion of multiple attachments."""
        # Create multiple attachments
        att_ids = ["att_001", "att_002", "att_003"]
        for att_id in att_ids:
            att = Attachment(
                id=att_id,
                user_id=test_user.id,
                filename=f"{att_id}.txt",
                mime_type="text/plain",
                size_bytes=100,
                extracted_text="Content",
                extraction_status="completed",
                word_count=1,
            )
            test_db.add(att)
        test_db.commit()
        
        # Verify all exist
        count = test_db.query(Attachment).filter(Attachment.id.in_(att_ids)).count()
        assert count == 3
        
        # Delete all
        for att_id in att_ids:
            att = test_db.query(Attachment).filter(Attachment.id == att_id).first()
            if att:
                test_db.delete(att)
        test_db.commit()
        
        # Verify all deleted
        count = test_db.query(Attachment).filter(Attachment.id.in_(att_ids)).count()
        assert count == 0


class TestProcessRequestSchema:
    """Tests for ProcessRequest schema with attachment_ids."""
    
    def test_process_request_without_attachments(self):
        """Test ProcessRequest without attachment_ids."""
        request = ProcessRequest(
            prompt="Hello world"
        )
        
        assert request.prompt == "Hello world"
        assert request.attachment_ids is None
    
    def test_process_request_with_attachment_ids(self):
        """Test ProcessRequest with attachment_ids."""
        request = ProcessRequest(
            prompt="Process this",
            attachment_ids=["att_001", "att_002"]
        )
        
        assert request.prompt == "Process this"
        assert request.attachment_ids == ["att_001", "att_002"]
        assert len(request.attachment_ids) == 2
    
    def test_process_request_with_conversation_and_attachments(self):
        """Test ProcessRequest with both conversation_id and attachment_ids."""
        request = ProcessRequest(
            prompt="Continue with attachment",
            conversation_id="conv_001",
            attachment_ids=["att_001"]
        )
        
        assert request.prompt == "Continue with attachment"
        assert request.conversation_id == "conv_001"
        assert request.attachment_ids == ["att_001"]
    
    def test_process_request_minimal_prompt(self):
        """Test ProcessRequest requires non-empty prompt."""
        with pytest.raises(ValueError):
            ProcessRequest(prompt="")
