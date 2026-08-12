"""Transcription service for voice-to-text conversion via faster-whisper."""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


@dataclass
class TranscriptionResult:
    """Result of transcription operation."""

    text: str  # Transcribed text
    language: str  # Detected language (e.g., "en")
    duration_seconds: float  # Audio duration
    model: str  # Model used
    error: Optional[str] = None  # Error message if transcription failed


class TranscriptionService:
    """Service for transcribing audio files via faster-whisper (local)."""

    def __init__(self, model: str = settings.TRANSCRIPTION_MODEL):
        """
        Initialize transcription service.

        Args:
            model: faster-whisper model name (e.g., "base", "small", "medium")

        Raises:
            RuntimeError: If faster-whisper is not installed
        """
        if WhisperModel is None:
            raise RuntimeError(
                "faster-whisper package not installed. Install with: pip install faster-whisper"
            )

        self.model_name = model
        self.model = None
        self.device = "cpu"  # No GPU support for now
        self.compute_type = "int8"  # Optimized for CPU inference
        logger.info(
            f"TranscriptionService initialized with model={model}, "
            f"device={self.device}, compute_type={self.compute_type}"
        )

    async def _load_model(self):
        """Load Whisper model (lazy loading on first use)."""
        if self.model is None:
            logger.info(f"Loading faster-whisper model: {self.model_name} on {self.device}")
            try:
                self.model = WhisperModel(
                    self.model_name, device=self.device, compute_type=self.compute_type
                )
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load faster-whisper model: {e}")
                raise

    async def transcribe(
        self, file_path: str, language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file using faster-whisper.

        Args:
            file_path: Path to audio file
            language: Optional language code (e.g., "en"). If None, auto-detect.

        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return TranscriptionResult(
                text="",
                language="",
                duration_seconds=0,
                model=self.model_name,
                error="Audio file not found",
            )

        try:
            logger.debug(f"Starting transcription for {file_path}")

            # Verify file size
            file_size = os.path.getsize(file_path)
            logger.debug(f"Audio file size: {file_size} bytes")

            # Load model if not already loaded
            await self._load_model()

            # Transcribe in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()

            def _transcribe():
                logger.debug(f"Calling faster-whisper transcribe on {file_path}")
                segments, info = self.model.transcribe(
                    file_path, language=language, 
                )
                # Convert generator to list and extract text
                segments_list = list(segments)
                text = " ".join([segment.text for segment in segments_list])
                return text, info

            try:
                text, info = await asyncio.wait_for(
                    loop.run_in_executor(None, _transcribe),
                    timeout=settings.TRANSCRIPTION_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Transcription timeout after {settings.TRANSCRIPTION_TIMEOUT_SECONDS}s"
                )
                return TranscriptionResult(
                    text="",
                    language="",
                    duration_seconds=0,
                    model=self.model_name,
                    error="Transcription timeout",
                )

            logger.debug(f"Transcription successful: {len(text)} chars")

            return TranscriptionResult(
                text=text.strip(),
                language=info.language or "",
                duration_seconds=info.duration or 0.0,
                model=self.model_name,
                error=None,
            )

        except Exception as e:
            logger.exception(f"Transcription error: {e}")
            return TranscriptionResult(
                text="",
                language="",
                duration_seconds=0,
                model=self.model_name,
                error=str(e),
            )
