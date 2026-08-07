"""Transcription API router for voice-to-text conversion."""

import logging
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import tempfile
import os

from app.config import settings
from app.db import get_db
from app.auth import verify_api_key
from app.db.models import User
from app.services.transcription_service import TranscriptionService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["transcription"])
transcription_service = TranscriptionService()


async def verify_transcription_api_key(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
) -> User:
    """Verify API key for transcription endpoint."""
    user = verify_api_key(db, x_api_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )
    return user


@router.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    user: User = Depends(verify_transcription_api_key),
) -> JSONResponse:
    """
    Transcribe audio file using Ollama Whisper model.

    Args:
        file: Audio file (WAV, MP3, M4A, WebM)
        user: Authenticated user (via X-API-Key header)

    Returns:
        JSON with transcribed text and metadata

    Raises:
        400: Invalid file format or missing file
        403: Invalid or missing API key
        413: File too large
        503: Transcription service unavailable
        500: Transcription failed
    """
    try:
        # Validate transcription is enabled
        if not settings.TRANSCRIPTION_ENABLED:
            logger.warning("Transcription endpoint accessed but feature disabled")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Transcription service disabled"
            )

        # Validate file present
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file required"
            )

        # Validate MIME type
        if file.content_type not in settings.ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio format: {file.content_type}. Supported: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
            )

        # Read file content
        file_content = await file.read()

        # Validate file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.TRANSCRIPTION_MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Audio file too large: {file_size_mb:.1f}MB (max: {settings.TRANSCRIPTION_MAX_FILE_SIZE_MB}MB)"
            )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(file_content)
            temp_path = tmp.name

        try:
            # Transcribe
            logger.info(f"Starting transcription for file: {file.filename}")
            result = await transcription_service.transcribe(temp_path)

            # Check for errors
            if result.error:
                logger.error(f"Transcription error: {result.error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Transcription failed: {result.error}"
                )

            logger.info(f"Transcription successful: {len(result.text)} chars")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "text": result.text,
                    "language": result.language,
                    "duration_seconds": result.duration_seconds,
                    "model": result.model,
                }
            )
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in transcribe endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription service error"
        )
