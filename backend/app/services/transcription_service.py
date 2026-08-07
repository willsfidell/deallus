"""Transcription service for voice-to-text conversion via Ollama Whisper."""

import logging
import os
from dataclasses import dataclass
from typing import Optional
import asyncio
import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result of transcription operation."""
    text: str  # Transcribed text
    language: str  # Detected language (e.g., "en")
    duration_seconds: float  # Audio duration
    model: str  # Model used
    error: Optional[str] = None  # Error message if transcription failed


class TranscriptionService:
    """Service for transcribing audio files via Ollama Whisper."""

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.TRANSCRIPTION_MODEL):
        """
        Initialize transcription service.

        Args:
            base_url: Ollama base URL (e.g., http://localhost:11434)
            model: Model name (e.g., "whisper")
        """
        self.base_url = base_url
        self.model = model
        self.timeout = settings.TRANSCRIPTION_TIMEOUT_SECONDS
        logger.info(f"TranscriptionService initialized with base_url={base_url}, model={model}")

    async def transcribe(self, file_path: str, language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio file using Ollama Whisper.

        Args:
            file_path: Path to audio file
            language: Optional language code (e.g., "en"). If None, auto-detect.

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            FileNotFoundError: If audio file not found
            asyncio.TimeoutError: If transcription exceeds timeout
        """
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return TranscriptionResult(
                text="",
                language="",
                duration_seconds=0,
                model=self.model,
                error="Audio file not found"
            )

        try:
            logger.debug(f"Starting transcription for {file_path}")
            
            # Read audio file
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            logger.debug(f"Audio file read: {len(audio_data)} bytes")
            
            # Call Ollama transcription via aiohttp
            async with aiohttp.ClientSession() as session:
                # Prepare multipart form data
                form = aiohttp.FormData()
                form.add_field('audio', audio_data, filename='audio.wav')
                if language:
                    form.add_field('language', language)
                
                transcribe_url = f"{self.base_url}/api/transcribe"
                logger.debug(f"Calling Ollama transcribe endpoint: {transcribe_url}")
                
                async with session.post(
                    transcribe_url,
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Ollama error: {resp.status} - {error_text}")
                        return TranscriptionResult(
                            text="",
                            language="",
                            duration_seconds=0,
                            model=self.model,
                            error=f"Transcription service returned {resp.status}"
                        )
                    
                    result = await resp.json()
                    logger.debug(f"Transcription successful: {len(result.get('text', ''))} chars")
                    
                    return TranscriptionResult(
                        text=result.get('text', ''),
                        language=result.get('language', ''),
                        duration_seconds=result.get('duration_seconds', 0.0),
                        model=self.model,
                        error=None
                    )
        
        except asyncio.TimeoutError:
            logger.error(f"Transcription timeout after {self.timeout}s")
            return TranscriptionResult(
                text="",
                language="",
                duration_seconds=0,
                model=self.model,
                error="Transcription timeout"
            )
        except Exception as e:
            logger.exception(f"Transcription error: {e}")
            return TranscriptionResult(
                text="",
                language="",
                duration_seconds=0,
                model=self.model,
                error=str(e)
            )
