"""Router for file attachment upload and management."""

import logging
import uuid
import os
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db, Attachment
from app.auth import verify_api_key
from app.db.models import User
from app.services.extraction_service import ExtractionService
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/attachments", tags=["attachments"])

# Temp file storage
TEMP_DIR = "/tmp/attachments"
os.makedirs(TEMP_DIR, exist_ok=True)


async def verify_api_key_header(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
) -> User:
    """Dependency to verify API key."""
    user = verify_api_key(db=db, api_key=x_api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return user


class AttachmentResponse:
    """Response model for attachment."""
    def __init__(self, attachment, preview_length=200):
        self.id = attachment.id
        self.filename = attachment.filename
        self.mime_type = attachment.mime_type
        self.size_bytes = attachment.size_bytes
        self.status = attachment.extraction_status
        self.extraction_method = attachment.extraction_method
        self.ocr_applied = attachment.ocr_applied
        self.processing_time_ms = attachment.processing_time_ms
        self.page_count = attachment.page_count
        self.word_count = attachment.word_count
        
        # Preview (first N chars)
        if attachment.extracted_text:
            self.extracted_text_preview = attachment.extracted_text[:preview_length]
        else:
            self.extracted_text_preview = None
        
        self.error = None
        self.warnings = None
    
    def dict(self):
        result = {
            "id": self.id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "extraction_method": self.extraction_method,
            "ocr_applied": self.ocr_applied,
            "processing_time_ms": self.processing_time_ms,
            "page_count": self.page_count,
            "word_count": self.word_count,
            "extracted_text_preview": self.extracted_text_preview,
        }
        if self.error:
            result["error"] = self.error
        if self.warnings:
            result["warnings"] = self.warnings
        return result


@router.post("/upload")
async def upload_attachment(
    file: UploadFile = File(...),
    user: User = Depends(verify_api_key_header),
    db: Session = Depends(get_db),
):
    """Upload and extract text from file."""
    try:
        # Validate MIME type
        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file.content_type}' not supported. Please upload PDF, TXT, or DOCX files."
            )
        
        # Read file
        contents = await file.read()
        file_size = len(contents)
        
        # Validate size
        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
            )
        
        # Save temp file
        attachment_id = str(uuid.uuid4())[:8]  # Use shorter ID
        temp_file_path = os.path.join(TEMP_DIR, f"{attachment_id}_{file.filename}")
        
        with open(temp_file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"Saved temp file: {temp_file_path}")
        
        # Create DB record
        expires_at = datetime.utcnow() + timedelta(hours=settings.ATTACHMENT_EXPIRY_HOURS)
        
        attachment = Attachment(
            id=attachment_id,
            user_id=user.id,
            filename=file.filename,
            mime_type=file.content_type,
            size_bytes=file_size,
            extraction_status="processing",
            expires_at=expires_at,
        )
        
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        logger.info(f"Created attachment record: {attachment_id}")
        
        # Extract text
        extraction_service = ExtractionService()
        result = await extraction_service.extract_from_file(
            temp_file_path,
            file.content_type,
            settings.EXTRACTION_TIMEOUT_SECONDS
        )
        
        # Update DB with extraction results
        attachment.extracted_text = result.extracted_text
        attachment.extraction_status = "failed" if result.error else "completed"
        attachment.extraction_error = result.error
        attachment.extraction_method = result.extraction_method
        attachment.page_count = result.page_count
        attachment.word_count = result.word_count
        attachment.ocr_applied = result.ocr_applied
        attachment.processing_time_ms = result.processing_time_ms
        
        db.commit()
        db.refresh(attachment)
        
        # Cache in Redis
        redis = await RedisService.get_instance()
        if redis and result.extracted_text:
            await redis.set(
                f"attachment:{attachment_id}",
                {
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "extracted_text": result.extracted_text,
                    "status": attachment.extraction_status,
                },
                ttl=settings.ATTACHMENT_CACHE_TTL_SECONDS
            )
        
        # Cleanup temp file
        os.remove(temp_file_path)
        logger.info(f"Cleaned up temp file: {temp_file_path}")
        
        # Return response
        response = AttachmentResponse(attachment)
        if result.error:
            response.error = result.error
        if result.warnings:
            response.warnings = result.warnings
        
        logger.info(f"Upload complete: {attachment_id}")
        return response.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )
