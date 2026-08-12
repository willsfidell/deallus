"""Tests for transcription service."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.transcription_service import TranscriptionService, TranscriptionResult


@pytest.fixture
def transcription_service():
    """Create transcription service for testing."""
    return TranscriptionService(model="base")


@pytest.fixture
def temp_audio_file():
    """Create temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Write dummy WAV file (at least has some content)
        f.write(b'RIFF' + b'\x00' * 100)  # Minimal WAV header
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.mark.asyncio
async def test_transcribe_file_not_found(transcription_service):
    """Test transcription with non-existent file."""
    result = await transcription_service.transcribe('/nonexistent/path/audio.wav')
    
    assert result.text == ""
    assert result.error == "Audio file not found"
    assert result.error is not None


@pytest.mark.asyncio
async def test_transcribe_success(transcription_service, temp_audio_file):
    """Test successful transcription."""
    # Create mock segment
    mock_segment = MagicMock()
    mock_segment.text = "Hello world this is a test"
    
    # Create mock info
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.duration = 3.5
    
    with patch('app.services.transcription_service.WhisperModel') as mock_model_class:
        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(return_value=([mock_segment], mock_info))
        mock_model_class.return_value = mock_model
        
        result = await transcription_service.transcribe(temp_audio_file)
        
        assert result.text == "Hello world this is a test"
        assert result.language == "en"
        assert result.duration_seconds == 3.5
        assert result.model == "base"
        assert result.error is None


@pytest.mark.asyncio
async def test_transcribe_api_error(transcription_service, temp_audio_file):
    """Test transcription with API error."""
    with patch('app.services.transcription_service.WhisperModel') as mock_model_class:
        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(side_effect=Exception("Model error"))
        mock_model_class.return_value = mock_model
        
        result = await transcription_service.transcribe(temp_audio_file)
        
        assert result.text == ""
        assert "Model error" in result.error


@pytest.mark.asyncio
async def test_transcribe_with_language_param(transcription_service, temp_audio_file):
    """Test transcription with explicit language parameter."""
    mock_segment = MagicMock()
    mock_segment.text = "Bonjour le monde"
    
    mock_info = MagicMock()
    mock_info.language = "fr"
    mock_info.duration = 2.0
    
    with patch('app.services.transcription_service.WhisperModel') as mock_model_class:
        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(return_value=([mock_segment], mock_info))
        mock_model_class.return_value = mock_model
        
        result = await transcription_service.transcribe(temp_audio_file, language='fr')
        
        assert result.text == "Bonjour le monde"
        assert result.language == "fr"
        assert result.error is None


@pytest.mark.asyncio
async def test_transcribe_timeout(transcription_service, temp_audio_file):
    """Test transcription timeout."""
    with patch('app.services.transcription_service.WhisperModel') as mock_model_class:
        mock_model = MagicMock()
        
        # Make transcribe raise TimeoutError when called
        async def async_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()
        
        # We need to mock the executor behavior instead
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            mock_model.transcribe = MagicMock(side_effect=Exception("Timeout"))
            mock_model_class.return_value = mock_model
            
            result = await transcription_service.transcribe(temp_audio_file)
            
            assert result.text == ""
            assert "timeout" in result.error.lower()


@pytest.mark.asyncio 
async def test_transcribe_generic_exception(transcription_service, temp_audio_file):
    """Test transcription with generic exception."""
    with patch('builtins.open', side_effect=IOError("Disk read error")):
        result = await transcription_service.transcribe(temp_audio_file)
        
        assert result.text == ""
        assert result.error is not None
