"""Text extraction service for various file types."""

import logging
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable
from pathlib import Path
from io import BytesIO

logger = logging.getLogger(__name__)

# Type for extraction function
ExtractionFunc = Callable[[bytes], Dict[str, any]]


@dataclass
class ExtractionResult:
    """Result of text extraction."""
    extracted_text: str
    page_count: Optional[int] = None
    word_count: int = 0
    extraction_method: str = "unknown"
    ocr_applied: bool = False
    processing_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.extracted_text:
            self.extracted_text = ""
        self.word_count = len(self.extracted_text.split()) if self.extracted_text else 0


class ExtractionService:
    """Service for extracting text from various file types."""
    
    async def extract_from_file(
        self,
        file_path: str,
        mime_type: str,
        timeout_seconds: int = 30
    ) -> ExtractionResult:
        """Main entry point - routes to appropriate extractor."""
        start_time = time.time()
        
        try:
            if mime_type == "application/pdf":
                result = await asyncio.wait_for(
                    self.extract_pdf(file_path),
                    timeout=timeout_seconds
                )
            elif mime_type.startswith("text/"):
                result = await self.extract_text(file_path)
            elif "word" in mime_type or "document" in mime_type:
                result = await self.extract_docx(file_path)
            else:
                return ExtractionResult(
                    extracted_text="",
                    error=f"Unsupported MIME type: {mime_type}"
                )
            
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Extraction timed out for {file_path}")
            return ExtractionResult(
                extracted_text="",
                error=f"Extraction timed out after {timeout_seconds} seconds",
                processing_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractionResult(
                extracted_text="",
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def extract_pdf(self, file_path: str = None, file_bytes: bytes = None) -> ExtractionResult:
        """Extract text from PDF using Marker, fallback to PaddleOCR."""
        start_time = time.time()
        
        try:
            # Read file if path provided
            if file_path and not file_bytes:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
            
            if not file_bytes:
                return ExtractionResult(
                    extracted_text="",
                    error="No PDF content provided"
                )
            
            # Try Marker first
            marker_result = await self._try_marker_extraction(file_bytes)
            
            if marker_result and marker_result.get('success'):
                # Marker successfully extracted text
                return ExtractionResult(
                    extracted_text=marker_result.get('text', ''),
                    page_count=marker_result.get('page_count'),
                    extraction_method="marker",
                    ocr_applied=False,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Try basic PDF text extraction (no OCR yet)
            basic_result = await self._try_basic_pdf_extraction(file_bytes)
            if basic_result and basic_result.get('success'):
                text = basic_result.get('text', '')
                if len(text.strip()) > 50:  # If we got meaningful text
                    return ExtractionResult(
                        extracted_text=text,
                        page_count=basic_result.get('page_count'),
                        extraction_method="basic_pdf",
                        ocr_applied=False,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
            
            # Fall back to PaddleOCR for scanned PDFs
            logger.info("Basic extraction got minimal text, attempting PaddleOCR fallback")
            ocr_result = await self._try_paddle_ocr_fallback(file_bytes)
            
            if ocr_result and ocr_result.get('success'):
                return ExtractionResult(
                    extracted_text=ocr_result.get('text', ''),
                    page_count=ocr_result.get('page_count'),
                    extraction_method="paddle_ocr",
                    ocr_applied=True,
                    warnings=["Used OCR fallback for scanned PDF"],
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            return ExtractionResult(
                extracted_text="",
                error="Could not extract text from PDF with any available method",
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                extracted_text="",
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _try_marker_extraction(self, file_bytes: bytes) -> Optional[Dict]:
        """Try to extract text from PDF using Marker library."""
        try:
            # marker-pdf library is complex and requires GPU/ML setup
            # For now, we'll skip it in favor of simpler extraction methods
            # This can be implemented when marker is properly installed
            logger.debug("Marker extraction not yet implemented")
            return {'success': False}
        except Exception as e:
            logger.debug(f"Marker extraction error: {e}")
            return {'success': False}
    
    async def _try_basic_pdf_extraction(self, file_bytes: bytes) -> Optional[Dict]:
        """Try basic PDF text extraction using available libraries."""
        try:
            loop = asyncio.get_event_loop()
            
            def _extract():
                try:
                    # Try PyMuPDF (fitz) first
                    try:
                        import fitz
                        doc = fitz.open(stream=file_bytes, filetype="pdf")
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        return {
                            'success': True,
                            'text': text,
                            'page_count': len(doc)
                        }
                    except ImportError:
                        pass
                    
                    # Try pypdf
                    try:
                        from pypdf import PdfReader
                        reader = PdfReader(BytesIO(file_bytes))
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        return {
                            'success': True,
                            'text': text,
                            'page_count': len(reader.pages)
                        }
                    except ImportError:
                        pass
                    
                    # Try pdfplumber
                    try:
                        import pdfplumber
                        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                            text = ""
                            for page in pdf.pages:
                                text += page.extract_text() or ""
                            return {
                                'success': True,
                                'text': text,
                                'page_count': len(pdf.pages)
                            }
                    except ImportError:
                        pass
                    
                    return {'success': False}
                    
                except Exception as e:
                    logger.debug(f"Basic PDF extraction error: {e}")
                    return {'success': False}
            
            result = await loop.run_in_executor(None, _extract)
            return result
            
        except Exception as e:
            logger.debug(f"Basic extraction failed: {e}")
            return {'success': False}
    
    async def _try_paddle_ocr_fallback(self, file_bytes: bytes) -> Dict:
        """Extract text from PDF using PaddleOCR as fallback for scanned PDFs."""
        try:
            loop = asyncio.get_event_loop()
            
            def _paddle_extract():
                try:
                    from paddleocr import PaddleOCR
                    import fitz
                    
                    # Initialize PaddleOCR
                    ocr = PaddleOCR(use_angle_cls=True, lang='en')
                    
                    # Convert PDF to images
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    
                    all_text = ""
                    for page_num, page in enumerate(doc):
                        # Render page to image
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_bytes = pix.tobytes('png')
                        
                        # Run OCR
                        results = ocr.ocr(img_bytes, cls=True)
                        
                        # Extract text from results
                        if results:
                            for line in results:
                                if line:
                                    for word_info in line:
                                        all_text += word_info[1][0] + " "
                                    all_text += "\n"
                    
                    return {
                        'success': True,
                        'text': all_text,
                        'page_count': len(doc)
                    }
                except ImportError as e:
                    logger.debug(f"PaddleOCR or dependencies not available: {e}")
                    return {'success': False}
                except Exception as e:
                    logger.error(f"PaddleOCR extraction failed: {e}")
                    return {'success': False}
            
            result = await loop.run_in_executor(None, _paddle_extract)
            return result
            
        except Exception as e:
            logger.error(f"PaddleOCR fallback error: {e}")
            return {'success': False}
    
    async def extract_docx(self, file_path: str) -> ExtractionResult:
        """Extract text from DOCX using python-docx."""
        # Implemented in next task
        raise NotImplementedError
    
    async def extract_text(self, file_path: str) -> ExtractionResult:
        """Extract plain text with encoding detection."""
        # Implemented in next task
        raise NotImplementedError
