"""Tests for transcription service."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, AsyncMock, MagicMock
from aiohttp import ClientSession

from app.services.transcription_service import TranscriptionService, TranscriptionResult


@pytest.fixture
def transcription_service():
    """Create transcription service for testing."""
    return TranscriptionService(base_url="http://localhost:11434", model="whisper")


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
    mock_response = {
        'text': 'Hello world this is a test',
        'language': 'en',
        'duration_seconds': 3.5
    }
    
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        
        # Mock context manager
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await transcription_service.transcribe(temp_audio_file)
        
        assert result.text == 'Hello world this is a test'
        assert result.language == 'en'
        assert result.duration_seconds == 3.5
        assert result.model == 'whisper'
        assert result.error is None


@pytest.mark.asyncio
async def test_transcribe_api_error(transcription_service, temp_audio_file):
    """Test transcription with API error."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 500
        mock_response_obj.text = AsyncMock(return_value="Internal server error")
        
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await transcription_service.transcribe(temp_audio_file)
        
        assert result.text == ""
        assert "500" in result.error


@pytest.mark.asyncio
async def test_transcribe_with_language_param(transcription_service, temp_audio_file):
    """Test transcription with explicit language parameter."""
    mock_response = {
        'text': 'Bonjour le monde',
        'language': 'fr',
        'duration_seconds': 2.0
    }
    
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await transcription_service.transcribe(temp_audio_file, language='fr')
        
        assert result.text == 'Bonjour le monde'
        assert result.language == 'fr'
        assert result.error is None


@pytest.mark.asyncio
async def test_transcribe_timeout(transcription_service, temp_audio_file):
    """Test transcription timeout."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        
        # Raise TimeoutError when awaiting the context manager
        mock_response_obj.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_response_obj.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock()
        mock_session.post.return_value = mock_response_obj
        
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
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
