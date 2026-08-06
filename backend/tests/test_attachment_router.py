"""Tests for the attachment router."""

import pytest
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from io import BytesIO

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.api.attachment_router import AttachmentResponse
from app.services.extraction_service import ExtractionResult


class TestAttachmentResponse:
    """Tests for AttachmentResponse model."""
    
    def test_attachment_response_initialization(self):
        """AttachmentResponse should initialize with attachment data."""
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.filename = "test.txt"
        mock_attachment.mime_type = "text/plain"
        mock_attachment.size_bytes = 1024
        mock_attachment.extraction_status = "completed"
        mock_attachment.extraction_method = "pdf_text"
        mock_attachment.ocr_applied = False
        mock_attachment.processing_time_ms = 100.5
        mock_attachment.page_count = 1
        mock_attachment.word_count = 50
        mock_attachment.extracted_text = "This is the extracted text content"
        
        response = AttachmentResponse(mock_attachment)
        
        assert response.id == "test-123"
        assert response.filename == "test.txt"
        assert response.mime_type == "text/plain"
        assert response.size_bytes == 1024
        assert response.status == "completed"
        assert response.word_count == 50
        assert response.extracted_text_preview is not None
    
    def test_attachment_response_preview_truncation(self):
        """AttachmentResponse should truncate long extracted text."""
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.filename = "test.txt"
        mock_attachment.mime_type = "text/plain"
        mock_attachment.size_bytes = 1024
        mock_attachment.extraction_status = "completed"
        mock_attachment.extraction_method = "pdf_text"
        mock_attachment.ocr_applied = False
        mock_attachment.processing_time_ms = 100.5
        mock_attachment.page_count = 1
        mock_attachment.word_count = 500
        # Long text
        mock_attachment.extracted_text = "A" * 300
        
        response = AttachmentResponse(mock_attachment, preview_length=200)
        
        # Preview should be truncated to 200 chars
        assert len(response.extracted_text_preview) <= 200
        assert response.extracted_text_preview is not None
    
    def test_attachment_response_no_text(self):
        """AttachmentResponse should handle missing extracted text."""
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.filename = "test.txt"
        mock_attachment.mime_type = "text/plain"
        mock_attachment.size_bytes = 1024
        mock_attachment.extraction_status = "failed"
        mock_attachment.extraction_method = None
        mock_attachment.ocr_applied = False
        mock_attachment.processing_time_ms = 100.5
        mock_attachment.page_count = None
        mock_attachment.word_count = 0
        mock_attachment.extracted_text = None
        
        response = AttachmentResponse(mock_attachment)
        
        assert response.extracted_text_preview is None
        assert response.status == "failed"
    
    def test_attachment_response_dict(self):
        """AttachmentResponse.dict() should return proper dictionary."""
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.filename = "test.txt"
        mock_attachment.mime_type = "text/plain"
        mock_attachment.size_bytes = 1024
        mock_attachment.extraction_status = "completed"
        mock_attachment.extraction_method = "pdf_text"
        mock_attachment.ocr_applied = False
        mock_attachment.processing_time_ms = 100.5
        mock_attachment.page_count = 1
        mock_attachment.word_count = 50
        mock_attachment.extracted_text = "Test content"
        
        response = AttachmentResponse(mock_attachment)
        result_dict = response.dict()
        
        # Verify required fields
        assert "id" in result_dict
        assert "filename" in result_dict
        assert "mime_type" in result_dict
        assert "size_bytes" in result_dict
        assert "status" in result_dict
        assert "extraction_method" in result_dict
        assert "ocr_applied" in result_dict
        assert "processing_time_ms" in result_dict
        assert "page_count" in result_dict
        assert "word_count" in result_dict
        assert "extracted_text_preview" in result_dict
        
        # Verify values
        assert result_dict["id"] == "test-123"
        assert result_dict["filename"] == "test.txt"
        assert result_dict["status"] == "completed"


class TestUploadEndpointValidation:
    """Tests for upload endpoint validation logic."""
    
    def test_allowed_mime_types(self):
        """Test that allowed MIME types are correctly configured."""
        from app.config import settings
        
        assert "application/pdf" in settings.ALLOWED_MIME_TYPES
        assert "text/plain" in settings.ALLOWED_MIME_TYPES
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in settings.ALLOWED_MIME_TYPES
    
    def test_file_size_limit_configured(self):
        """Test that file size limits are configured."""
        from app.config import settings
        
        assert settings.MAX_FILE_SIZE_MB == 5
        assert settings.MAX_FILES_PER_MESSAGE == 5
        assert settings.MAX_TOTAL_SIZE_MB == 10
        assert settings.EXTRACTION_TIMEOUT_SECONDS == 30
    
    def test_attachment_expiry_configured(self):
        """Test that attachment expiry is configured."""
        from app.config import settings
        
        assert settings.ATTACHMENT_EXPIRY_HOURS == 24
        assert settings.ATTACHMENT_CACHE_TTL_SECONDS == 3600


class TestExtractionResultIntegration:
    """Tests for extraction service integration."""
    
    @pytest.mark.asyncio
    async def test_extraction_result_fields(self):
        """ExtractionResult should have all required fields."""
        result = ExtractionResult(
            extracted_text="Sample extracted text",
            page_count=1,
            extraction_method="pdf_text",
            ocr_applied=False,
            processing_time_ms=50.0,
            warnings=[]
        )
        
        assert result.extracted_text == "Sample extracted text"
        assert result.page_count == 1
        assert result.word_count == 3  # "Sample extracted text"
        assert result.extraction_method == "pdf_text"
        assert result.ocr_applied is False
        assert result.processing_time_ms == 50.0
        assert result.warnings == []
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_extraction_result_with_error(self):
        """ExtractionResult should handle errors."""
        result = ExtractionResult(
            extracted_text="",
            error="File parsing failed"
        )
        
        assert result.extracted_text == ""
        assert result.error == "File parsing failed"
        assert result.word_count == 0


class TestAttachmentRouterSetup:
    """Tests for attachment router configuration."""
    
    def test_router_prefix(self):
        """Router should have correct prefix."""
        from app.api.attachment_router import router
        
        assert router.prefix == "/api/attachments"
        assert router.tags == ["attachments"]
    
    def test_upload_endpoint_exists(self):
        """Upload endpoint should exist in router."""
        from app.api.attachment_router import router
        
        routes = [route for route in router.routes if "upload" in route.path]
        assert len(routes) > 0
        
        # Check for POST method
        upload_routes = [r for r in routes if "POST" in r.methods]
        assert len(upload_routes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
