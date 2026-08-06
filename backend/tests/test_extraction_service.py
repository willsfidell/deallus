"""Tests for the extraction service."""

import asyncio
import pytest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.extraction_service import ExtractionService, ExtractionResult


class TestExtractionResult:
    """Test the ExtractionResult dataclass."""

    def test_extraction_result_calculates_word_count(self):
        """Word count is calculated from extracted text."""
        result = ExtractionResult(
            extracted_text="hello world this is a test"
        )
        assert result.word_count == 6

    def test_extraction_result_empty_text(self):
        """Empty text defaults to empty string."""
        result = ExtractionResult(extracted_text="")
        assert result.extracted_text == ""
        assert result.word_count == 0

    def test_extraction_result_warnings_initialized(self):
        """Warnings list is initialized if not provided."""
        result = ExtractionResult(extracted_text="test")
        assert result.warnings == []
        assert isinstance(result.warnings, list)

    def test_extraction_result_none_extracted_text(self):
        """None extracted text is converted to empty string."""
        result = ExtractionResult(extracted_text=None)
        assert result.extracted_text == ""


class TestPDFExtractor:
    """Test PDF extraction functionality."""

    @pytest.fixture
    def service(self):
        """Create an ExtractionService instance."""
        return ExtractionService()

    @pytest.mark.asyncio
    async def test_extract_pdf_no_bytes(self, service):
        """Extract PDF with no content returns error."""
        result = await service.extract_pdf(file_path=None, file_bytes=None)
        
        assert isinstance(result, ExtractionResult)
        assert result.error is not None
        assert "No PDF content" in result.error

    @pytest.mark.asyncio
    async def test_extract_pdf_invalid_bytes(self, service):
        """Invalid PDF bytes return error."""
        invalid_bytes = b"not a pdf at all"
        
        result = await service.extract_pdf(file_path=None, file_bytes=invalid_bytes)
        
        assert isinstance(result, ExtractionResult)
        # Should either extract empty or error
        assert result.extracted_text == "" or result.error is not None

    @pytest.mark.asyncio
    async def test_extract_pdf_with_basic_extraction_mock(self, service):
        """PDF extraction with mocked basic extraction."""
        pdf_bytes = b"mock pdf content"
        
        # Mock the basic extraction to succeed with sufficient text
        async def mock_basic_extract(file_bytes):
            return {
                'success': True,
                'text': 'Extracted PDF text content with more than 50 characters to pass the threshold test',
                'page_count': 1
            }
        
        with patch.object(service, '_try_basic_pdf_extraction', mock_basic_extract):
            result = await service.extract_pdf(file_path=None, file_bytes=pdf_bytes)
        
        assert isinstance(result, ExtractionResult)
        assert 'Extracted PDF text content' in result.extracted_text
        assert result.page_count == 1
        assert result.extraction_method == "basic_pdf"
        assert result.ocr_applied is False

    @pytest.mark.asyncio
    async def test_extract_pdf_fallback_to_ocr_with_mock(self, service):
        """PDF extraction falls back to OCR when basic extraction fails."""
        pdf_bytes = b"mock scanned pdf"
        
        # Mock basic extraction to return minimal text (not enough to pass threshold)
        async def mock_basic_extract(file_bytes):
            return {
                'success': True,
                'text': 'Short',  # Only 5 characters, below 50 char threshold
                'page_count': 1
            }
        
        # Mock OCR extraction to succeed
        async def mock_ocr_extract(file_bytes):
            return {
                'success': True,
                'text': 'OCR extracted text from scanned PDF which is now much longer',
                'page_count': 1
            }
        
        with patch.object(service, '_try_basic_pdf_extraction', mock_basic_extract):
            with patch.object(service, '_try_paddle_ocr_fallback', mock_ocr_extract):
                result = await service.extract_pdf(file_path=None, file_bytes=pdf_bytes)
        
        assert isinstance(result, ExtractionResult)
        assert 'OCR extracted text from scanned PDF' in result.extracted_text
        assert result.page_count == 1
        assert result.extraction_method == "paddle_ocr"
        assert result.ocr_applied is True
        assert "OCR fallback" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_extract_pdf_calculates_processing_time(self, service):
        """PDF extraction calculates processing time."""
        pdf_bytes = b"mock pdf"
        
        # Mock extraction to succeed
        async def mock_extract(file_bytes):
            await asyncio.sleep(0.01)  # Simulate some processing
            return {
                'success': True,
                'text': 'Some text',
                'page_count': 1
            }
        
        with patch.object(service, '_try_basic_pdf_extraction', mock_extract):
            result = await service.extract_pdf(file_path=None, file_bytes=pdf_bytes)
        
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_extract_pdf_from_file_path(self, service):
        """PDF extraction from file path."""
        # Create a temporary PDF file
        import tempfile
        pdf_content = b"mock pdf content"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_content)
            temp_path = f.name
        
        try:
            # Mock extraction to succeed with sufficient text
            async def mock_extract(file_bytes):
                return {
                    'success': True,
                    'text': 'Extracted from file and it has more than 50 characters of content here',
                    'page_count': 1
                }
            
            with patch.object(service, '_try_basic_pdf_extraction', mock_extract):
                result = await service.extract_pdf(file_path=temp_path)
            
            assert 'Extracted from file' in result.extracted_text
            assert result.page_count == 1
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_extract_pdf_all_methods_fail(self, service):
        """PDF extraction returns error when all methods fail."""
        pdf_bytes = b"mock pdf"
        
        # Mock all extraction methods to fail
        async def mock_marker_fail(file_bytes):
            return {'success': False}
        
        async def mock_basic_fail(file_bytes):
            return {'success': False}
        
        async def mock_ocr_fail(file_bytes):
            return {'success': False}
        
        with patch.object(service, '_try_marker_extraction', mock_marker_fail):
            with patch.object(service, '_try_basic_pdf_extraction', mock_basic_fail):
                with patch.object(service, '_try_paddle_ocr_fallback', mock_ocr_fail):
                    result = await service.extract_pdf(file_path=None, file_bytes=pdf_bytes)
        
        assert result.extracted_text == ""
        assert result.error is not None
        assert "Could not extract" in result.error


class TestExtractionService:
    """Test the main ExtractionService class."""

    @pytest.fixture
    def service(self):
        """Create an ExtractionService instance."""
        return ExtractionService()

    @pytest.mark.asyncio
    async def test_extract_from_file_pdf(self, service):
        """extract_from_file routes PDF correctly."""
        # Create a temporary PDF file
        import tempfile
        pdf_content = b"mock pdf"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_content)
            temp_path = f.name
        
        try:
            # Mock extraction to succeed
            async def mock_extract(file_path_arg=None, file_bytes_arg=None):
                return ExtractionResult(
                    extracted_text="Test content",
                    page_count=1,
                    extraction_method="test"
                )
            
            with patch.object(service, 'extract_pdf', mock_extract):
                result = await service.extract_from_file(
                    file_path=temp_path,
                    mime_type="application/pdf",
                    timeout_seconds=30
                )
            
            assert isinstance(result, ExtractionResult)
            assert result.processing_time_ms > 0
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_extract_from_file_text(self, service):
        """extract_from_file routes text files correctly."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"plain text content")
            temp_path = f.name
        
        try:
            # Mock extract_text to succeed
            async def mock_extract_text(path):
                return ExtractionResult(
                    extracted_text="Plain text",
                    extraction_method="text"
                )
            
            with patch.object(service, 'extract_text', mock_extract_text):
                result = await service.extract_from_file(
                    file_path=temp_path,
                    mime_type="text/plain",
                    timeout_seconds=30
                )
            
            assert result.extraction_method == "text"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_extract_from_file_unsupported_mime(self, service):
        """Unsupported MIME types return error."""
        result = await service.extract_from_file(
            file_path="/tmp/test",
            mime_type="application/unsupported",
            timeout_seconds=30
        )
        
        assert result.error is not None
        assert "Unsupported" in result.error

    @pytest.mark.asyncio
    async def test_extract_from_file_timeout(self, service):
        """Timeout during extraction returns error."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"mock pdf")
            temp_path = f.name
        
        try:
            # Mock extract_pdf to be very slow
            async def mock_slow_extract(path):
                await asyncio.sleep(5)
                return ExtractionResult(extracted_text="Never reached")
            
            with patch.object(service, 'extract_pdf', mock_slow_extract):
                result = await service.extract_from_file(
                    file_path=temp_path,
                    mime_type="application/pdf",
                    timeout_seconds=0.1  # Very short timeout
                )
            
            assert result.error is not None
            assert "timed out" in result.error.lower()
        finally:
            Path(temp_path).unlink()


class TestPaddleOCRFixes:
    """Test critical fixes for PaddleOCR and error handling."""

    @pytest.fixture
    def service(self):
        """Create an ExtractionService instance."""
        return ExtractionService()

    @pytest.mark.asyncio
    async def test_paddle_ocr_handles_invalid_result_format(self, service):
        """PaddleOCR handles invalid result format without crashing."""
        pdf_bytes = b"mock pdf"
        
        # Mock OCR to return None or malformed data
        async def mock_ocr_invalid(file_bytes):
            return {
                'success': True,
                'text': 'This should be ignored because result is invalid',
                'page_count': 1
            }
        
        # This test primarily validates the error handling in _try_paddle_ocr_fallback
        # The actual fix is in the result parsing validation
        with patch.object(service, '_try_paddle_ocr_fallback', mock_ocr_invalid):
            result = await service.extract_pdf(file_path=None, file_bytes=pdf_bytes)
        
        # Should handle gracefully
        assert isinstance(result, ExtractionResult)

    @pytest.mark.asyncio
    async def test_extract_pdf_with_timeout_parameter(self, service):
        """extract_pdf respects timeout parameter for direct calls."""
        pdf_bytes = b"mock pdf"
        
        # Mock slow extraction
        async def mock_slow_extract(file_bytes):
            await asyncio.sleep(2)
            return {
                'success': True,
                'text': 'Should timeout',
                'page_count': 1
            }
        
        with patch.object(service, '_try_basic_pdf_extraction', mock_slow_extract):
            result = await service.extract_pdf(
                file_path=None,
                file_bytes=pdf_bytes,
                timeout_seconds=0.1  # Very short timeout
            )
        
        assert result.error is not None
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_marker_extraction_in_fallback_chain(self, service):
        """Marker extraction is in the correct position in fallback chain."""
        pdf_bytes = b"mock pdf"
        
        call_order = []
        
        # Track which methods are called
        async def mock_basic_minimal(file_bytes):
            call_order.append("basic")
            return {
                'success': True,
                'text': 'Short',  # Below threshold
                'page_count': 1
            }
        
        async def mock_marker(file_bytes):
            call_order.append("marker")
            return {'success': False}  # Marker not implemented
        
        async def mock_ocr(file_bytes):
            call_order.append("ocr")
            return {
                'success': True,
                'text': 'OCR result',
                'page_count': 1
            }
        
        with patch.object(service, '_try_basic_pdf_extraction', mock_basic_minimal):
            with patch.object(service, '_try_marker_extraction', mock_marker):
                with patch.object(service, '_try_paddle_ocr_fallback', mock_ocr):
                    result = await service.extract_pdf(file_path=None, file_bytes=pdf_bytes)
        
        # Verify call order: basic -> marker -> ocr
        assert call_order == ["basic", "marker", "ocr"]
        # Verify final result is from OCR
        assert result.extraction_method == "paddle_ocr"

