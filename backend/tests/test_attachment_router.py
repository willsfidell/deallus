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
from fastapi import HTTPException


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
    
    def test_get_endpoint_exists(self):
        """GET endpoint should exist in router."""
        from app.api.attachment_router import router
        
        # Check for GET endpoint with {attachment_id} path
        routes = [route for route in router.routes if "{attachment_id}" in route.path]
        assert len(routes) > 0
        
        # Check for GET method
        get_routes = [r for r in routes if "GET" in r.methods]
        assert len(get_routes) > 0
    
    def test_delete_endpoint_exists(self):
        """DELETE endpoint should exist in router."""
        from app.api.attachment_router import router
        
        # Check for DELETE endpoint with {attachment_id} path
        routes = [route for route in router.routes if "{attachment_id}" in route.path]
        assert len(routes) > 0
        
        # Check for DELETE method
        delete_routes = [r for r in routes if "DELETE" in r.methods]
        assert len(delete_routes) > 0


class TestGetAttachmentEndpoint:
    """Tests for GET /api/attachments/{attachment_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_attachment_success(self):
        """GET endpoint should return attachment status and preview."""
        from app.api.attachment_router import get_attachment
        
        # Mock attachment
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.user_id = 1
        mock_attachment.filename = "test.txt"
        mock_attachment.mime_type = "text/plain"
        mock_attachment.size_bytes = 1024
        mock_attachment.extraction_status = "completed"
        mock_attachment.extracted_text = "This is extracted text"
        mock_attachment.extraction_error = None
        mock_attachment.extraction_method = "text_extraction"
        mock_attachment.ocr_applied = False
        mock_attachment.processing_time_ms = 100.0
        mock_attachment.page_count = 1
        mock_attachment.word_count = 4
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_attachment
        
        # Mock Redis
        with patch("app.api.attachment_router.RedisService.get_instance") as mock_redis_instance:
            mock_redis_instance.return_value = None  # No Redis cache
            
            result = await get_attachment("test-123", mock_user, mock_db)
            
            # Verify response structure
            assert result["id"] == "test-123"
            assert result["filename"] == "test.txt"
            assert result["status"] == "completed"
            assert result["extracted_text"] == "This is extracted text"
    
    @pytest.mark.asyncio
    async def test_get_attachment_not_found(self):
        """GET endpoint should return 404 if attachment not found."""
        from app.api.attachment_router import get_attachment
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database - no attachment found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_attachment("nonexistent", mock_user, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_attachment_unauthorized_user(self):
        """GET endpoint should return 404 if attachment belongs to different user."""
        from app.api.attachment_router import get_attachment
        
        # Mock attachment belonging to different user
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.user_id = 2  # Different user
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None  # Filter excludes other user's attachments
        
        with pytest.raises(HTTPException) as exc_info:
            await get_attachment("test-123", mock_user, mock_db)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_attachment_with_preview(self):
        """GET endpoint should return preview for processing status."""
        from app.api.attachment_router import get_attachment
        
        # Mock attachment still processing
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.user_id = 1
        mock_attachment.filename = "test.pdf"
        mock_attachment.mime_type = "application/pdf"
        mock_attachment.size_bytes = 2048
        mock_attachment.extraction_status = "processing"
        mock_attachment.extracted_text = None
        mock_attachment.extraction_error = None
        mock_attachment.extraction_method = None
        mock_attachment.ocr_applied = False
        mock_attachment.processing_time_ms = None
        mock_attachment.page_count = None
        mock_attachment.word_count = 0
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_attachment
        
        with patch("app.api.attachment_router.RedisService.get_instance") as mock_redis_instance:
            mock_redis_instance.return_value = None
            
            result = await get_attachment("test-123", mock_user, mock_db)
            
            assert result["status"] == "processing"
            assert "extracted_text" not in result or result.get("extracted_text") is None


class TestDeleteAttachmentEndpoint:
    """Tests for DELETE /api/attachments/{attachment_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_attachment_success(self):
        """DELETE endpoint should delete attachment and return success."""
        from app.api.attachment_router import delete_attachment
        
        # Mock attachment
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.user_id = 1
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_attachment
        
        # Mock Redis
        with patch("app.api.attachment_router.RedisService.get_instance") as mock_redis_instance:
            mock_redis_instance.return_value = None
            
            result = await delete_attachment("test-123", mock_user, mock_db)
            
            # Verify deletion was called
            mock_db.delete.assert_called_once_with(mock_attachment)
            mock_db.commit.assert_called()
            
            # Verify response
            assert result["message"] == "Attachment deleted successfully"
    
    @pytest.mark.asyncio
    async def test_delete_attachment_not_found(self):
        """DELETE endpoint should return 404 if attachment not found."""
        from app.api.attachment_router import delete_attachment
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database - no attachment found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_attachment("nonexistent", mock_user, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_delete_attachment_clears_cache(self):
        """DELETE endpoint should clear Redis cache."""
        from app.api.attachment_router import delete_attachment
        
        # Mock attachment
        mock_attachment = Mock()
        mock_attachment.id = "test-123"
        mock_attachment.user_id = 1
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_attachment
        
        # Mock Redis with delete method
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()
        
        with patch("app.api.attachment_router.RedisService.get_instance") as mock_redis_instance:
            mock_redis_instance.return_value = mock_redis
            
            result = await delete_attachment("test-123", mock_user, mock_db)
            
            # Verify Redis delete was called
            mock_redis.delete.assert_called_once_with("attachment:test-123")
            
            assert result["message"] == "Attachment deleted successfully"
    
    @pytest.mark.asyncio
    async def test_delete_attachment_unauthorized_user(self):
        """DELETE endpoint should return 404 if attachment belongs to different user."""
        from app.api.attachment_router import delete_attachment
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock database - no attachment found for this user
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_attachment("test-123", mock_user, mock_db)
        
        assert exc_info.value.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
