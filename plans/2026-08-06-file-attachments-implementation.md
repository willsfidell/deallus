# File Attachments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add file attachment support to Deallus, enabling users to attach PDF/TXT/DOCX files to messages with automatic text extraction and storage in conversation history.

**Architecture:** Two-step upload flow (upload/extract → send message). Marker + PaddleOCR for PDF extraction, python-docx for Word, UTF-8 for text. Extracted text stored in database, no permanent file storage. Background queue for OCR jobs using asyncio + Redis.

**Tech Stack:** FastAPI, PostgreSQL (new attachments table), Redis (queue + cache), Marker, PaddleOCR, python-docx, Flutter (file picker, upload manager, chips)

---

## Global Constraints

- File types: PDF, TXT, DOCX only
- Max 5MB per file, 5 files per message, 10MB total
- Extracted text storage: Database JSONB + Redis cache (1-hour TTL)
- No permanent file storage on disk
- Manual Alembic migrations (NOT --autogenerate)
- Timeout: 30 seconds max per file
- Token truncation: >2000 words
- Cleanup: Delete on conversation delete or 24-hour expiry

---

## File Structure

### Backend

**New Files:**
- `app/services/extraction_service.py` - Text extraction (Marker, PaddleOCR, python-docx, UTF-8)
- `app/api/attachment_router.py` - 3 new endpoints (upload, get status, delete)
- `alembic/versions/*_add_attachments_support.py` - Database migration (manual)
- `tests/test_extraction_service.py` - Extraction service unit tests
- `tests/test_attachment_router.py` - API endpoint tests
- `tests/test_attachment_flow.py` - Integration tests

**Modified Files:**
- `app/models/schemas.py` - Add `AttachmentResponse` schema
- `app/db/models.py` - No changes (migration adds table)
- `app/config.py` - Add 12 new configuration settings
- `app/main.py` - Register new attachment router
- `app/api/process_router.py` - Modify to accept `attachment_ids`
- `requirements.txt` - Add 6 dependencies

### Frontend

**New Files:**
- `lib/services/attachment_service.dart` - Upload, status polling, delete
- `lib/providers/attachment_provider.dart` - State management
- `lib/widgets/chat_panel/file_picker_button.dart` - Paperclip button
- `lib/widgets/chat_panel/attachment_chip.dart` - Chip UI
- `lib/models/attachment.dart` - Attachment model
- `tests/services/attachment_service_test.dart` - Service tests
- `tests/widgets/file_picker_button_test.dart` - Widget tests

**Modified Files:**
- `lib/services/chat_service.dart` - Add `sendMessageWithAttachments()`
- `lib/widgets/chat_panel/message_input.dart` - Add file picker button + chips
- `lib/providers/message_provider.dart` - Pass attachment IDs to API
- `pubspec.yaml` - Add 3 dependencies

---

## Task Breakdown

### BACKEND TASKS

---

### Task 1: Configuration & Dependencies

**Files:**
- Modify: `app/config.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: Configuration class with 12 new settings

- [ ] **Step 1: Add configuration settings to config.py**

```python
# In app/config.py, add to Settings class:

# File Upload Settings
MAX_FILE_SIZE_MB: int = 5
MAX_FILES_PER_MESSAGE: int = 5
MAX_TOTAL_SIZE_MB: int = 10
ALLOWED_MIME_TYPES: list = [
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

# Extraction Settings
EXTRACTION_TIMEOUT_SECONDS: int = 30
OCR_ENABLED: bool = True
OCR_LANGUAGE: str = "en"
MIN_TEXT_WORDS_FOR_OCR: int = 100

# Attachment Storage
ATTACHMENT_EXPIRY_HOURS: int = 24
ATTACHMENT_CACHE_TTL_SECONDS: int = 3600

# Token Management
MAX_ATTACHMENT_WORDS_IN_PROMPT: int = 2000
TRUNCATE_LONG_ATTACHMENTS: bool = True
```

- [ ] **Step 2: Add dependencies to requirements.txt**

Add after existing dependencies:

```
marker-pdf>=0.2.0
paddlepaddle>=2.5.0
paddleocr>=2.7.0
python-docx>=1.0.0
chardet>=5.2.0
python-multipart>=0.0.6
```

- [ ] **Step 3: Verify config loads**

Run:
```bash
cd /home/wills/working/aidi/backend
python -c "from app.config import settings; print(settings.MAX_FILE_SIZE_MB)"
```

Expected: `5`

- [ ] **Step 4: Commit**

```bash
cd /home/wills/working/aidi/backend
git add app/config.py requirements.txt
git commit -m "chore: add file attachment configuration and dependencies"
```

---

### Task 2: Database Migration

**Files:**
- Create: `alembic/versions/*_add_attachments_support.py`

**Interfaces:**
- Produces: Two schema changes: new `attachments` table, `attachments` column on `messages`

- [ ] **Step 1: Create Alembic revision (manual)**

Run:
```bash
cd /home/wills/working/aidi/backend
alembic revision -m "add_attachments_support"
```

This creates: `alembic/versions/XXXXX_add_attachments_support.py`

- [ ] **Step 2: Write upgrade() function**

In the newly created file, replace `def upgrade():` with:

```python
def upgrade():
    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('extraction_status', sa.String(20), nullable=False),
        sa.Column('extraction_error', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=True),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('ocr_applied', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_attachments_user_id', 'attachments', ['user_id'])
    op.create_index('idx_attachments_status', 'attachments', ['extraction_status'])
    op.create_index('idx_attachments_expires', 'attachments', ['expires_at'])
    
    # Add attachments column to messages
    op.add_column(
        'messages',
        sa.Column('attachments', sa.JSON(), server_default='[]')
    )
```

- [ ] **Step 3: Write downgrade() function**

Replace `def downgrade():` with:

```python
def downgrade():
    # Remove column from messages
    op.drop_column('messages', 'attachments')
    
    # Drop indexes
    op.drop_index('idx_attachments_expires', 'attachments')
    op.drop_index('idx_attachments_status', 'attachments')
    op.drop_index('idx_attachments_user_id', 'attachments')
    
    # Drop table
    op.drop_table('attachments')
```

- [ ] **Step 4: Test migration upgrade**

Run:
```bash
cd /home/wills/working/aidi/backend
alembic upgrade head
```

Expected: No errors, new table created

- [ ] **Step 5: Test migration downgrade**

Run:
```bash
cd /home/wills/working/aidi/backend
alembic downgrade -1
```

Expected: No errors, table dropped

- [ ] **Step 6: Run upgrade again to restore schema**

```bash
cd /home/wills/working/aidi/backend
alembic upgrade head
```

- [ ] **Step 7: Commit**

```bash
cd /home/wills/working/aidi/backend
git add alembic/versions/
git commit -m "db: add attachments table and schema"
```

---

### Task 3: Extraction Service - Core Implementation

**Files:**
- Create: `app/services/extraction_service.py`

**Interfaces:**
- Produces: `ExtractionService` class with:
  - `async extract_from_file(file_path, mime_type, timeout_seconds=30) -> ExtractionResult`
  - `async extract_pdf(file_path) -> ExtractionResult`
  - `async extract_docx(file_path) -> ExtractionResult`
  - `async extract_text(file_path) -> ExtractionResult`
- Returns: `ExtractionResult(extracted_text, page_count, word_count, extraction_method, ocr_applied, processing_time_ms, warnings, error)`

- [ ] **Step 1: Create extraction_service.py with data classes**

```python
# app/services/extraction_service.py

import logging
import asyncio
import time
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of text extraction."""
    extracted_text: str
    page_count: Optional[int] = None
    word_count: int = 0
    extraction_method: str = "unknown"
    ocr_applied: bool = False
    processing_time_ms: float = 0.0
    warnings: List[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if not self.extracted_text:
            self.extracted_text = ""
        self.word_count = len(self.extracted_text.split())


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
    
    async def extract_pdf(self, file_path: str) -> ExtractionResult:
        """Extract text from PDF using Marker, fallback to PaddleOCR."""
        # Implemented in next task
        raise NotImplementedError
    
    async def extract_docx(self, file_path: str) -> ExtractionResult:
        """Extract text from DOCX using python-docx."""
        # Implemented in next task
        raise NotImplementedError
    
    async def extract_text(self, file_path: str) -> ExtractionResult:
        """Extract plain text with encoding detection."""
        # Implemented in next task
        raise NotImplementedError
```

- [ ] **Step 2: Verify imports work**

Run:
```bash
cd /home/wills/working/aidi/backend
python -c "from app.services.extraction_service import ExtractionService, ExtractionResult; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/wills/working/aidi/backend
git add app/services/extraction_service.py
git commit -m "feat: add extraction service base with data classes"
```

---

### Task 4: Extraction Service - PDF & Text Implementation

**Files:**
- Modify: `app/services/extraction_service.py`

**Interfaces:**
- Consumes: ExtractionService class structure from Task 3
- Produces: Implemented `extract_pdf()` and `extract_text()` methods

- [ ] **Step 1: Implement extract_pdf() method**

Add to ExtractionService class:

```python
async def extract_pdf(self, file_path: str) -> ExtractionResult:
    """Extract text from PDF using Marker, fallback to PaddleOCR if needed."""
    try:
        import pymupdf  # fitz
        from app.config import settings
        
        # Open PDF
        doc = pymupdf.open(file_path)
        page_count = len(doc)
        
        # Try direct text extraction first
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        
        word_count = len(text.split())
        
        # If minimal text found, might be scanned - mark for OCR
        if word_count < settings.MIN_TEXT_WORDS_FOR_OCR:
            logger.info(f"PDF {file_path} has minimal text ({word_count} words), marking for OCR")
            return ExtractionResult(
                extracted_text=text,
                page_count=page_count,
                word_count=word_count,
                extraction_method="marker",
                warnings=["Minimal text detected. Consider using OCR."]
            )
        
        logger.info(f"Extracted {word_count} words from PDF {file_path}")
        return ExtractionResult(
            extracted_text=text,
            page_count=page_count,
            word_count=word_count,
            extraction_method="marker"
        )
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ExtractionResult(
            extracted_text="",
            error=f"Could not read PDF file. Try re-saving or converting to plain text.",
            extraction_method="marker"
        )
```

- [ ] **Step 2: Implement extract_text() method**

Add to ExtractionService class:

```python
async def extract_text(self, file_path: str) -> ExtractionResult:
    """Extract plain text with encoding detection."""
    import chardet
    
    try:
        # Try multiple encodings
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # Detect encoding
        detected = chardet.detect(raw_data)
        encoding = detected['encoding'] or 'utf-8'
        
        try:
            text = raw_data.decode(encoding)
        except (UnicodeDecodeError, TypeError):
            # Fallback to latin-1 which always works
            text = raw_data.decode('latin-1', errors='ignore')
            encoding = 'latin-1'
        
        word_count = len(text.split())
        logger.info(f"Extracted {word_count} words from text file using {encoding}")
        
        return ExtractionResult(
            extracted_text=text,
            word_count=word_count,
            extraction_method=f"text-{encoding}"
        )
        
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ExtractionResult(
            extracted_text="",
            error=f"Could not read text file: {str(e)}",
            extraction_method="text"
        )
```

- [ ] **Step 3: Install pymupdf temporarily to test**

Run:
```bash
cd /home/wills/working/aidi/backend
pip install pymupdf chardet
```

- [ ] **Step 4: Create simple test file**

```bash
# Create a test text file
echo "This is a test document with some content for extraction testing." > /tmp/test.txt
```

- [ ] **Step 5: Test extract_text locally**

Run:
```python
import asyncio
from app.services.extraction_service import ExtractionService

async def test():
    service = ExtractionService()
    result = await service.extract_text("/tmp/test.txt")
    print(f"Extracted: {result.extracted_text[:50]}")
    print(f"Word count: {result.word_count}")
    assert result.word_count > 0
    assert result.error is None

asyncio.run(test())
```

Run:
```bash
cd /home/wills/working/aidi/backend
python << 'EOF'
import asyncio
from app.services.extraction_service import ExtractionService

async def test():
    service = ExtractionService()
    result = await service.extract_text("/tmp/test.txt")
    print(f"Extracted: {result.extracted_text[:50]}")
    print(f"Word count: {result.word_count}")
    assert result.word_count > 0

asyncio.run(test())
EOF
```

Expected: No errors, word count printed

- [ ] **Step 6: Commit**

```bash
cd /home/wills/working/aidi/backend
git add app/services/extraction_service.py
git commit -m "feat: implement PDF and text extraction methods"
```

---

### Task 5: Extraction Service - DOCX Implementation

**Files:**
- Modify: `app/services/extraction_service.py`

**Interfaces:**
- Consumes: ExtractionService class with extract_pdf, extract_text
- Produces: Implemented `extract_docx()` method

- [ ] **Step 1: Implement extract_docx() method**

Add to ExtractionService class:

```python
async def extract_docx(self, file_path: str) -> ExtractionResult:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        
        doc = Document(file_path)
        text = ""
        
        # Extract from paragraphs
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        # Extract from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + "\n"
        
        word_count = len(text.split())
        page_count = len(doc.sections)  # Approximate
        
        logger.info(f"Extracted {word_count} words from DOCX {file_path}")
        
        return ExtractionResult(
            extracted_text=text,
            page_count=page_count,
            word_count=word_count,
            extraction_method="python-docx"
        )
        
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ExtractionResult(
            extracted_text="",
            error=f"Could not read Word document: {str(e)}",
            extraction_method="python-docx"
        )
```

- [ ] **Step 2: Test extract_docx locally**

Run:
```bash
cd /home/wills/working/aidi/backend
pip install python-docx
```

Create a test document (if docx not available, skip actual test but verify no import errors):

```bash
python << 'EOF'
from docx import Document

doc = Document()
doc.add_paragraph("This is a test DOCX document for extraction testing.")
doc.save('/tmp/test.docx')
print("Test DOCX created")
EOF
```

- [ ] **Step 3: Verify DOCX extraction works**

```bash
cd /home/wills/working/aidi/backend
python << 'EOF'
import asyncio
from app.services.extraction_service import ExtractionService

async def test():
    service = ExtractionService()
    result = await service.extract_docx("/tmp/test.docx")
    print(f"Extracted: {result.extracted_text[:50]}")
    print(f"Word count: {result.word_count}")
    assert result.word_count > 0

asyncio.run(test())
EOF
```

- [ ] **Step 4: Commit**

```bash
cd /home/wills/working/aidi/backend
git add app/services/extraction_service.py
git commit -m "feat: implement DOCX extraction method"
```

---

### Task 6: Attachment Router - Upload Endpoint

**Files:**
- Create: `app/api/attachment_router.py`
- Modify: `app/main.py`

**Interfaces:**
- Consumes: ExtractionService from Task 3-5, settings from Task 1
- Produces: FastAPI router with POST /api/attachments/upload endpoint

- [ ] **Step 1: Create attachment_router.py with upload endpoint**

```python
# app/api/attachment_router.py

import logging
import uuid
import os
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.auth import verify_api_key
from app.services.extraction_service import ExtractionService
from app.services.redis_service import RedisService
from app.db.models import User, Attachment

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
    from app.auth import verify_api_key as verify_key
    user = verify_key(db=db, api_key=x_api_key)
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
    
    def dict(self):
        return {
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
```

- [ ] **Step 2: Register router in main.py**

Open `app/main.py` and find where routers are included. Add:

```python
from app.api.attachment_router import router as attachment_router

# In the app creation section, add:
app.include_router(attachment_router)
```

- [ ] **Step 3: Create Attachment model in db/models.py**

Add to `app/db/models.py`:

```python
class Attachment(Base):
    """Temporary attachment storage for uploaded files."""
    
    __tablename__ = "attachments"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    
    extracted_text = Column(Text, nullable=True)
    extraction_status = Column(String(20), nullable=False)
    extraction_error = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    
    extraction_method = Column(String(50), nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    ocr_applied = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    user = relationship("User", backref="attachments")
    
    __table_args__ = (
        Index("ix_attachments_user_id", "user_id"),
        Index("ix_attachments_status", "extraction_status"),
        Index("ix_attachments_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Attachment(id={self.id}, filename={self.filename}, status={self.extraction_status})>"
```

- [ ] **Step 4: Test endpoint with curl**

```bash
cd /home/wills/working/aidi/backend

# Start server in background or new terminal:
# python -m uvicorn app.main:app --reload

# In another terminal:
curl -X POST http://localhost:8000/api/attachments/upload \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@/tmp/test.txt"
```

Expected: 200 response with attachment data

- [ ] **Step 5: Commit**

```bash
cd /home/wills/working/aidi/backend
git add app/api/attachment_router.py app/db/models.py app/main.py
git commit -m "feat: add attachment upload endpoint"
```

---

### Task 7: Attachment Router - Get Status & Delete Endpoints

**Files:**
- Modify: `app/api/attachment_router.py`

**Interfaces:**
- Consumes: Attachment model, router from Task 6
- Produces: GET and DELETE endpoints

- [ ] **Step 1: Add GET /api/attachments/{attachment_id} endpoint**

Add to `app/api/attachment_router.py`:

```python
@router.get("/{attachment_id}")
async def get_attachment(
    attachment_id: str,
    user: User = Depends(verify_api_key_header),
    db: Session = Depends(get_db),
):
    """Get attachment status and extracted text."""
    try:
        # Verify ownership
        attachment = db.query(Attachment).filter(
            Attachment.id == attachment_id,
            Attachment.user_id == user.id
        ).first()
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        # Check Redis cache first
        redis = await RedisService.get_instance()
        if redis:
            cached = await redis.get(f"attachment:{attachment_id}")
            if cached:
                logger.debug(f"Attachment {attachment_id} from cache")
        
        response = AttachmentResponse(attachment, preview_length=200)
        response_dict = response.dict()
        
        # Include full text if completed
        if attachment.extraction_status == "completed":
            response_dict["extracted_text"] = attachment.extracted_text
        
        # Include warnings if any
        if attachment.extraction_error:
            response_dict["error"] = attachment.extraction_error
        
        return response_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get attachment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get attachment"
        )
```

- [ ] **Step 2: Add DELETE /api/attachments/{attachment_id} endpoint**

Add to `app/api/attachment_router.py`:

```python
@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    user: User = Depends(verify_api_key_header),
    db: Session = Depends(get_db),
):
    """Delete attachment before message send."""
    try:
        # Verify ownership
        attachment = db.query(Attachment).filter(
            Attachment.id == attachment_id,
            Attachment.user_id == user.id
        ).first()
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        # Delete from DB
        db.delete(attachment)
        db.commit()
        
        # Delete from Redis cache
        redis = await RedisService.get_instance()
        if redis:
            try:
                await redis.delete(f"attachment:{attachment_id}")
            except:
                pass
        
        logger.info(f"Deleted attachment: {attachment_id}")
        
        return {"message": "Attachment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete attachment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete attachment"
        )
```

- [ ] **Step 3: Test GET endpoint**

```bash
# Get status of attachment
curl -X GET http://localhost:8000/api/attachments/ATTACHMENT_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

Expected: 200 response with status

- [ ] **Step 4: Test DELETE endpoint**

```bash
# Delete attachment
curl -X DELETE http://localhost:8000/api/attachments/ATTACHMENT_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

Expected: 200 response with success message

- [ ] **Step 5: Commit**

```bash
cd /home/wills/working/aidi/backend
git add app/api/attachment_router.py
git commit -m "feat: add get status and delete attachment endpoints"
```

---

### Task 8: Modify Process Router for Attachments

**Files:**
- Modify: `app/api/process_router.py`
- Modify: `app/models/schemas.py`

**Interfaces:**
- Consumes: Attachment model, existing process endpoint
- Produces: Modified ProcessRequest to accept attachment_ids, modified process logic

- [ ] **Step 1: Add schema for attachment IDs**

In `app/models/schemas.py`, modify ProcessRequest:

```python
class ProcessRequest(BaseModel):
    """Schema for /process endpoint request."""
    prompt: str = Field(..., min_length=1, description="User prompt to process")
    model: Optional[str] = None  # Deprecated
    conversation_id: Optional[str] = None
    force_model: Optional[str] = Field(None, description="Force specific model")
    attachment_ids: Optional[List[str]] = Field(  # NEW
        None,
        description="List of attachment IDs to include in prompt"
    )
```

- [ ] **Step 2: Modify process router to load attachments**

In `app/api/process_router.py`, in the process() function, after loading conversation context, add:

```python
# Load attachments if provided
attachment_texts = []
if request.attachment_ids:
    logger.info(f"[{request_id}] Loading {len(request.attachment_ids)} attachments")
    
    for att_id in request.attachment_ids:
        attachment = db.query(Attachment).filter(
            Attachment.id == att_id,
            Attachment.user_id == user.id
        ).first()
        
        if not attachment:
            logger.warning(f"[{request_id}] Attachment not found: {att_id}")
            continue
        
        if attachment.extraction_status != "completed":
            logger.warning(f"[{request_id}] Attachment not ready: {att_id}")
            continue
        
        attachment_texts.append({
            "id": attachment.id,
            "filename": attachment.filename,
            "text": attachment.extracted_text,
            "word_count": attachment.word_count,
        })

# Build enhanced prompt
enhanced_prompt = modified_prompt
if attachment_texts:
    prompt_parts = []
    
    for att in attachment_texts:
        # Truncate if needed
        text = att["text"]
        if len(text.split()) > settings.MAX_ATTACHMENT_WORDS_IN_PROMPT:
            truncated = " ".join(text.split()[:settings.MAX_ATTACHMENT_WORDS_IN_PROMPT])
            text = truncated + f"\n[... {att['word_count'] - settings.MAX_ATTACHMENT_WORDS_IN_PROMPT} words omitted]"
        
        prompt_parts.append(f"[File: {att['filename']}]\n{text}")
    
    enhanced_prompt = "\n\n".join(prompt_parts) + "\n\nUser question: " + modified_prompt
    logger.info(f"[{request_id}] Enhanced prompt with {len(attachment_texts)} attachments")
```

- [ ] **Step 3: Use enhanced_prompt in LLM call**

Find where LLM is called and use `enhanced_prompt` instead of `modified_prompt`:

```python
# Step 3: Route to model and generate response
llm_response = await llm_service.generate(
    prompt=enhanced_prompt,  # Use enhanced prompt
    model=model_to_use,
    # ... rest of parameters
)
```

- [ ] **Step 4: Store attachments in message**

When storing the message, pass attachment data:

```python
# Convert attachments to storage format
message_attachments = []
for att_id in (request.attachment_ids or []):
    attachment = db.query(Attachment).filter(
        Attachment.id == att_id,
        Attachment.user_id == user.id
    ).first()
    
    if attachment and attachment.extraction_status == "completed":
        message_attachments.append({
            "id": attachment.id,
            "filename": attachment.filename,
            "mime_type": attachment.mime_type,
            "size_bytes": attachment.size_bytes,
            "extracted_text": attachment.extracted_text,
            "page_count": attachment.page_count,
            "word_count": attachment.word_count,
            "extraction_method": attachment.extraction_method,
            "ocr_applied": attachment.ocr_applied,
        })

# Store message with attachments (update add_message call)
conversation_service.add_message(
    conversation_id=conversation_id,
    role="assistant",
    content=final_response,
    db=db,
    model_used=model_to_use,
    token_count=assistant_token_count,
    tool_executions=[],
    attachments=message_attachments  # NEW
)
```

- [ ] **Step 5: Update add_message signature**

In `app/services/conversation_service.py`, modify `add_message()`:

```python
def add_message(
    self,
    conversation_id: str,
    role: str,
    content: str,
    db: Session,
    model_used: Optional[str] = None,
    token_count: int = 0,
    tool_executions: Optional[list] = None,
    attachments: Optional[list] = None,  # NEW
) -> Message:
    """Add message with optional attachments."""
    message_id = str(uuid.uuid4())
    
    message = Message(
        id=message_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        model_used=model_used,
        token_count=token_count,
        tool_executions=tool_executions or [],
        attachments=attachments or [],  # NEW
    )
    
    # ... rest of method
```

- [ ] **Step 6: Cleanup temporary attachments after message sent**

After message is stored, delete temporary attachment records:

```python
# Cleanup temporary attachment records
if request.attachment_ids:
    for att_id in request.attachment_ids:
        attachment = db.query(Attachment).filter(
            Attachment.id == att_id
        ).first()
        
        if attachment:
            db.delete(attachment)
    
    db.commit()
    logger.info(f"[{request_id}] Cleaned up {len(request.attachment_ids)} temporary attachments")
```

- [ ] **Step 7: Test modified endpoint**

```bash
# Upload a file first to get attachment_id
RESPONSE=$(curl -X POST http://localhost:8000/api/attachments/upload \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@/tmp/test.txt")

ATTACHMENT_ID=$(echo $RESPONSE | jq -r '.id')

# Send message with attachment
curl -X POST http://localhost:8000/api/process \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"Summarize this document\",
    \"conversation_id\": \"conv_123\",
    \"attachment_ids\": [\"$ATTACHMENT_ID\"]
  }"
```

Expected: 200 response with LLM result

- [ ] **Step 8: Commit**

```bash
cd /home/wills/working/aidi/backend
git add app/api/process_router.py app/models/schemas.py app/services/conversation_service.py
git commit -m "feat: integrate attachments into message processing"
```

---

### Task 9: Backend Tests - Extraction Service

**Files:**
- Create: `tests/test_extraction_service.py`

**Interfaces:**
- Consumes: ExtractionService, ExtractionResult
- Produces: Unit tests covering all file types and error cases

- [ ] **Step 1: Create test file with basic structure**

```python
# tests/test_extraction_service.py

import pytest
import asyncio
import os
from app.services.extraction_service import ExtractionService, ExtractionResult


@pytest.fixture
def extraction_service():
    """Create extraction service for testing."""
    return ExtractionService()


@pytest.mark.asyncio
async def test_extract_text_file(extraction_service):
    """Test extracting text from plain text file."""
    # Create test file
    test_content = "This is a test document with several words for testing."
    test_file = "/tmp/test_simple.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Extract
    result = await extraction_service.extract_text(test_file)
    
    # Verify
    assert result.error is None
    assert test_content in result.extracted_text
    assert result.word_count > 0
    assert result.extraction_method.startswith("text-")
    
    # Cleanup
    os.remove(test_file)


@pytest.mark.asyncio
async def test_extract_from_file_text_mime_type(extraction_service):
    """Test extract_from_file routes to extract_text for text MIME."""
    test_file = "/tmp/test_mime.txt"
    with open(test_file, 'w') as f:
        f.write("Test content")
    
    result = await extraction_service.extract_from_file(
        test_file,
        "text/plain"
    )
    
    assert result.error is None
    assert result.word_count > 0
    
    os.remove(test_file)


@pytest.mark.asyncio
async def test_extract_nonexistent_file(extraction_service):
    """Test extracting from nonexistent file."""
    result = await extraction_service.extract_from_file(
        "/tmp/nonexistent_file_xyz.txt",
        "text/plain"
    )
    
    assert result.error is not None
    assert result.extracted_text == ""


@pytest.mark.asyncio
async def test_timeout_handling(extraction_service):
    """Test timeout during extraction."""
    test_file = "/tmp/test_timeout.txt"
    with open(test_file, 'w') as f:
        f.write("Test" * 1000)
    
    # Use very short timeout
    result = await extraction_service.extract_from_file(
        test_file,
        "text/plain",
        timeout_seconds=0.001
    )
    
    # Should either complete or timeout gracefully
    assert result is not None
    
    os.remove(test_file)


@pytest.mark.asyncio
async def test_unsupported_mime_type(extraction_service):
    """Test unsupported MIME type."""
    result = await extraction_service.extract_from_file(
        "/tmp/test.bin",
        "application/x-binary"
    )
    
    assert result.error is not None
    assert "Unsupported MIME type" in result.error
```

- [ ] **Step 2: Run tests**

```bash
cd /home/wills/working/aidi/backend
pytest tests/test_extraction_service.py -v
```

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
cd /home/wills/working/aidi/backend
git add tests/test_extraction_service.py
git commit -m "test: add extraction service unit tests"
```

---

### Task 10: Backend Tests - Attachment Router

**Files:**
- Create: `tests/test_attachment_router.py`

**Interfaces:**
- Consumes: Attachment router, test database, test user
- Produces: API endpoint tests

- [ ] **Step 1: Create test file with fixtures**

```python
# tests/test_attachment_router.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db
from app.db.models import Base, User, APIKey
from app.models.schemas import APIKeyResponse


# Test database setup
@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user(test_db):
    """Create test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_api_key(test_db, test_user):
    """Create test API key."""
    api_key = APIKey(
        user_id=test_user.id,
        key="test_key_12345678",
        name="test",
        is_active=True
    )
    test_db.add(api_key)
    test_db.commit()
    test_db.refresh(api_key)
    return api_key


@pytest.fixture
def client(test_db):
    """Create test client."""
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_upload_text_file(client, test_api_key):
    """Test uploading a text file."""
    with open("/tmp/test_upload.txt", "w") as f:
        f.write("Test content for upload")
    
    with open("/tmp/test_upload.txt", "rb") as f:
        response = client.post(
            "/api/attachments/upload",
            files={"file": ("test.txt", f, "text/plain")},
            headers={"X-API-Key": test_api_key.key}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["status"] == "completed"
    assert data["word_count"] > 0


def test_upload_unsupported_file(client, test_api_key):
    """Test uploading unsupported file type."""
    with open("/tmp/test_upload.bin", "wb") as f:
        f.write(b"\x00\x01\x02\x03")
    
    with open("/tmp/test_upload.bin", "rb") as f:
        response = client.post(
            "/api/attachments/upload",
            files={"file": ("test.bin", f, "application/x-binary")},
            headers={"X-API-Key": test_api_key.key}
        )
    
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_upload_without_auth(client):
    """Test uploading without API key."""
    with open("/tmp/test_upload.txt", "w") as f:
        f.write("Test")
    
    with open("/tmp/test_upload.txt", "rb") as f:
        response = client.post(
            "/api/attachments/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 403


def test_get_attachment_status(client, test_api_key, test_db, test_user):
    """Test getting attachment status."""
    # Upload first
    with open("/tmp/test_get.txt", "w") as f:
        f.write("Test content")
    
    with open("/tmp/test_get.txt", "rb") as f:
        upload_resp = client.post(
            "/api/attachments/upload",
            files={"file": ("test.txt", f, "text/plain")},
            headers={"X-API-Key": test_api_key.key}
        )
    
    att_id = upload_resp.json()["id"]
    
    # Get status
    response = client.get(
        f"/api/attachments/{att_id}",
        headers={"X-API-Key": test_api_key.key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == att_id
    assert data["status"] == "completed"


def test_delete_attachment(client, test_api_key, test_db):
    """Test deleting attachment."""
    # Upload first
    with open("/tmp/test_delete.txt", "w") as f:
        f.write("Test")
    
    with open("/tmp/test_delete.txt", "rb") as f:
        upload_resp = client.post(
            "/api/attachments/upload",
            files={"file": ("test.txt", f, "text/plain")},
            headers={"X-API-Key": test_api_key.key}
        )
    
    att_id = upload_resp.json()["id"]
    
    # Delete
    response = client.delete(
        f"/api/attachments/{att_id}",
        headers={"X-API-Key": test_api_key.key}
    )
    
    assert response.status_code == 200
    
    # Verify deleted
    response = client.get(
        f"/api/attachments/{att_id}",
        headers={"X-API-Key": test_api_key.key}
    )
    
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests**

```bash
cd /home/wills/working/aidi/backend
pytest tests/test_attachment_router.py -v
```

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
cd /home/wills/working/aidi/backend
git add tests/test_attachment_router.py
git commit -m "test: add attachment router API tests"
```

---

### Task 11: Frontend - Attachment Model

**Files:**
- Create: `lib/models/attachment.dart`

**Interfaces:**
- Produces: Attachment model with JSON serialization

- [ ] **Step 1: Create attachment model**

```dart
// lib/models/attachment.dart

import 'package:json_annotation/json_annotation.dart';

part 'attachment.g.dart';

@JsonSerializable()
class Attachment {
  final String id;
  final String filename;
  
  @JsonKey(name: 'mime_type')
  final String mimeType;
  
  @JsonKey(name: 'size_bytes')
  final int sizeBytes;
  
  final String status;  // "uploading", "processing", "completed", "failed"
  
  @JsonKey(name: 'extracted_text_preview')
  final String? extractedTextPreview;
  
  @JsonKey(name: 'page_count')
  final int? pageCount;
  
  @JsonKey(name: 'word_count')
  final int? wordCount;
  
  @JsonKey(name: 'extraction_method')
  final String? extractionMethod;
  
  @JsonKey(name: 'ocr_applied')
  final bool? ocrApplied;
  
  @JsonKey(name: 'processing_time_ms')
  final double? processingTimeMs;
  
  final List<String>? warnings;
  final String? error;
  
  const Attachment({
    required this.id,
    required this.filename,
    required this.mimeType,
    required this.sizeBytes,
    required this.status,
    this.extractedTextPreview,
    this.pageCount,
    this.wordCount,
    this.extractionMethod,
    this.ocrApplied,
    this.processingTimeMs,
    this.warnings,
    this.error,
  });
  
  factory Attachment.fromJson(Map<String, dynamic> json) =>
      _$AttachmentFromJson(json);
  
  Map<String, dynamic> toJson() => _$AttachmentToJson(this);
  
  bool get isUploading => status == 'uploading';
  bool get isProcessing => status == 'processing';
  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';
  
  String get sizeDisplay {
    if (sizeBytes < 1024) return '$sizeBytes B';
    if (sizeBytes < 1024 * 1024) return '${(sizeBytes / 1024).toStringAsFixed(1)} KB';
    return '${(sizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
  
  Attachment copyWith({
    String? id,
    String? filename,
    String? mimeType,
    int? sizeBytes,
    String? status,
    String? extractedTextPreview,
    int? pageCount,
    int? wordCount,
    String? extractionMethod,
    bool? ocrApplied,
    double? processingTimeMs,
    List<String>? warnings,
    String? error,
  }) =>
      Attachment(
        id: id ?? this.id,
        filename: filename ?? this.filename,
        mimeType: mimeType ?? this.mimeType,
        sizeBytes: sizeBytes ?? this.sizeBytes,
        status: status ?? this.status,
        extractedTextPreview: extractedTextPreview ?? this.extractedTextPreview,
        pageCount: pageCount ?? this.pageCount,
        wordCount: wordCount ?? this.wordCount,
        extractionMethod: extractionMethod ?? this.extractionMethod,
        ocrApplied: ocrApplied ?? this.ocrApplied,
        processingTimeMs: processingTimeMs ?? this.processingTimeMs,
        warnings: warnings ?? this.warnings,
        error: error ?? this.error,
      );
}
```

- [ ] **Step 2: Regenerate JSON serialization code**

```bash
cd /home/wills/working/aidi/frontend
flutter pub run build_runner build
```

Expected: `attachment.g.dart` created

- [ ] **Step 3: Commit**

```bash
cd /home/wills/working/aidi/frontend
git add lib/models/attachment.dart lib/models/attachment.g.dart
git commit -m "feat: add attachment model"
```

---

### Task 12: Frontend - Attachment Service

**Files:**
- Create: `lib/services/attachment_service.dart`

**Interfaces:**
- Consumes: ApiService, Attachment model
- Produces: AttachmentService with upload, status polling, delete methods

- [ ] **Step 1: Create attachment service**

```dart
// lib/services/attachment_service.dart

import 'dart:async';
import 'dart:io';
import 'package:logger/logger.dart';
import 'package:dio/dio.dart';
import '../models/attachment.dart';
import 'api_service.dart';

final _logger = Logger();

class AttachmentService {
  final ApiService _apiService;
  
  AttachmentService(this._apiService);
  
  /// Upload a file and extract text
  Future<Attachment> uploadFile(File file) async {
    try {
      _logger.i('Uploading file: ${file.path}');
      
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          file.path,
          filename: file.path.split('/').last,
        ),
      });
      
      final response = await _apiService.post(
        '/api/attachments/upload',
        data: formData,
      );
      
      final attachment = Attachment.fromJson(response.data);
      _logger.i('Upload successful: ${attachment.id}');
      return attachment;
    } catch (e) {
      _logger.e('Upload failed: $e');
      rethrow;
    }
  }
  
  /// Get attachment status
  Future<Attachment> getStatus(String attachmentId) async {
    try {
      final response = await _apiService.get(
        '/api/attachments/$attachmentId',
      );
      
      return Attachment.fromJson(response.data);
    } catch (e) {
      _logger.e('Get status failed: $e');
      rethrow;
    }
  }
  
  /// Delete attachment
  Future<void> deleteAttachment(String attachmentId) async {
    try {
      await _apiService.delete('/api/attachments/$attachmentId');
      _logger.i('Deleted attachment: $attachmentId');
    } catch (e) {
      _logger.e('Delete failed: $e');
      rethrow;
    }
  }
  
  /// Poll status for processing attachments
  Stream<Attachment> pollStatus(String attachmentId, {int intervalSeconds = 2}) async* {
    while (true) {
      await Future.delayed(Duration(seconds: intervalSeconds));
      
      try {
        final attachment = await getStatus(attachmentId);
        yield attachment;
        
        // Stop polling if completed or failed
        if (attachment.isCompleted || attachment.isFailed) {
          break;
        }
      } catch (e) {
        _logger.e('Polling failed: $e');
        break;
      }
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
cd /home/wills/working/aidi/frontend
git add lib/services/attachment_service.dart
git commit -m "feat: add attachment service"
```

---

### Task 13: Frontend - Attachment Provider

**Files:**
- Create: `lib/providers/attachment_provider.dart`

**Interfaces:**
- Consumes: AttachmentService, Attachment model
- Produces: AttachmentNotifier for state management

- [ ] **Step 1: Create attachment provider**

```dart
// lib/providers/attachment_provider.dart

import 'dart:io';
import 'package:state_notifier/state_notifier.dart';
import 'package:riverpod/riverpod.dart';
import 'package:logger/logger.dart';
import '../models/attachment.dart';
import '../services/attachment_service.dart';
import 'api_provider.dart';

final _logger = Logger();

class AttachmentState {
  final List<Attachment> attachments;
  final bool isUploading;
  final String? error;
  
  AttachmentState({
    required this.attachments,
    required this.isUploading,
    this.error,
  });
  
  factory AttachmentState.initial() => AttachmentState(
    attachments: [],
    isUploading: false,
  );
  
  AttachmentState copyWith({
    List<Attachment>? attachments,
    bool? isUploading,
    String? error,
  }) {
    return AttachmentState(
      attachments: attachments ?? this.attachments,
      isUploading: isUploading ?? this.isUploading,
      error: error,
    );
  }
  
  bool get canSend {
    return attachments.every((a) => a.isCompleted) &&
           !isUploading &&
           error == null;
  }
}

class AttachmentNotifier extends StateNotifier<AttachmentState> {
  final AttachmentService _service;
  
  AttachmentNotifier(this._service) : super(AttachmentState.initial());
  
  Future<void> uploadFile(File file) async {
    state = state.copyWith(isUploading: true, error: null);
    
    try {
      final attachment = await _service.uploadFile(file);
      
      state = state.copyWith(
        attachments: [...state.attachments, attachment],
        isUploading: false,
      );
      
      // If processing, start polling
      if (attachment.isProcessing) {
        _pollAttachment(attachment.id);
      }
      
    } catch (e) {
      _logger.e('Upload failed: $e');
      state = state.copyWith(
        isUploading: false,
        error: 'Upload failed: ${e.toString()}',
      );
    }
  }
  
  void _pollAttachment(String attachmentId) {
    _service.pollStatus(attachmentId).listen(
      (attachment) {
        // Update attachment in list
        final updated = state.attachments.map((a) {
          return a.id == attachmentId ? attachment : a;
        }).toList();
        
        state = state.copyWith(attachments: updated);
      },
      onError: (e) {
        _logger.e('Polling failed: $e');
      },
    );
  }
  
  void removeAttachment(String attachmentId) async {
    try {
      await _service.deleteAttachment(attachmentId);
      
      state = state.copyWith(
        attachments: state.attachments
            .where((a) => a.id != attachmentId)
            .toList(),
      );
    } catch (e) {
      _logger.e('Delete failed: $e');
    }
  }
  
  void clearAttachments() {
    state = AttachmentState.initial();
  }
}

final attachmentServiceProvider = Provider((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return AttachmentService(apiService);
});

final attachmentProvider =
    StateNotifierProvider<AttachmentNotifier, AttachmentState>((ref) {
  final service = ref.watch(attachmentServiceProvider);
  return AttachmentNotifier(service);
});
```

- [ ] **Step 2: Commit**

```bash
cd /home/wills/working/aidi/frontend
git add lib/providers/attachment_provider.dart
git commit -m "feat: add attachment provider for state management"
```

---

### Task 14: Frontend - UI Components

**Files:**
- Create: `lib/widgets/chat_panel/file_picker_button.dart`
- Create: `lib/widgets/chat_panel/attachment_chip.dart`

**Interfaces:**
- Consumes: AttachmentProvider, Attachment model
- Produces: FilePickerButton and AttachmentChip widgets

- [ ] **Step 1: Create file picker button**

```dart
// lib/widgets/chat_panel/file_picker_button.dart

import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';

typedef OnFilesSelected = Function(List<String> filePaths);

class FilePickerButton extends StatelessWidget {
  final OnFilesSelected onFilesSelected;
  
  const FilePickerButton({
    required this.onFilesSelected,
    Key? key,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.attach_file),
      tooltip: 'Attach file',
      onPressed: _pickFiles,
    );
  }
  
  Future<void> _pickFiles() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'txt', 'docx'],
        allowMultiple: true,
        onFileLoading: (FilePickerStatus status) {
          // Can show progress if needed
        },
      );
      
      if (result != null) {
        final paths = result.paths.whereType<String>().toList();
        onFilesSelected(paths);
      }
    } catch (e) {
      // Handle error
    }
  }
}
```

- [ ] **Step 2: Create attachment chip widget**

```dart
// lib/widgets/chat_panel/attachment_chip.dart

import 'package:flutter/material.dart';
import '../../models/attachment.dart';

typedef OnDelete = Function(String attachmentId);

class AttachmentChip extends StatelessWidget {
  final Attachment attachment;
  final OnDelete onDelete;
  
  const AttachmentChip({
    required this.attachment,
    required this.onDelete,
    Key? key,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Chip(
      avatar: _buildStatusIcon(),
      label: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            attachment.filename,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 12),
          ),
          Text(
            attachment.sizeDisplay,
            style: TextStyle(
              fontSize: 10,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
      deleteIcon: const Icon(Icons.close, size: 18),
      onDeleted: () => onDelete(attachment.id),
      backgroundColor: _getBackgroundColor(),
    );
  }
  
  Widget _buildStatusIcon() {
    if (attachment.isUploading || attachment.isProcessing) {
      return const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    } else if (attachment.isCompleted) {
      return const Icon(Icons.check_circle, color: Colors.green, size: 18);
    } else if (attachment.isFailed) {
      return const Icon(Icons.error, color: Colors.red, size: 18);
    }
    return const Icon(Icons.description, size: 18);
  }
  
  Color? _getBackgroundColor() {
    if (attachment.isFailed) return Colors.red[50];
    if (attachment.isProcessing) return Colors.yellow[50];
    return Colors.green[50];
  }
}
```

- [ ] **Step 3: Commit**

```bash
cd /home/wills/working/aidi/frontend
git add lib/widgets/chat_panel/file_picker_button.dart lib/widgets/chat_panel/attachment_chip.dart
git commit -m "feat: add file picker button and attachment chip widgets"
```

---

### Task 15: Frontend - Modify Message Input

**Files:**
- Modify: `lib/widgets/chat_panel/message_input.dart`

**Interfaces:**
- Consumes: FilePickerButton, AttachmentChip, AttachmentProvider
- Produces: Modified message input with file attachment support

- [ ] **Step 1: Import attachment components at top of file**

```dart
import 'package:file_picker/file_picker.dart';
import '../chat_panel/file_picker_button.dart';
import '../chat_panel/attachment_chip.dart';
import '../../providers/attachment_provider.dart';
```

- [ ] **Step 2: Modify build method to show attachments and file picker**

Find the input Row widget and modify it to:

```dart
@override
Widget build(BuildContext context, WidgetRef ref) {
  final attachments = ref.watch(attachmentProvider);
  final canSend = attachments.canSend && messageController.text.isNotEmpty;
  
  return Column(
    children: [
      // Show attachment chips if any
      if (attachments.attachments.isNotEmpty)
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Wrap(
            spacing: 8,
            runSpacing: 4,
            children: attachments.attachments.map((att) {
              return AttachmentChip(
                attachment: att,
                onDelete: (id) => ref
                    .read(attachmentProvider.notifier)
                    .removeAttachment(id),
              );
            }).toList(),
          ),
        ),
      
      // Show error if any
      if (attachments.error != null)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: Text(
            attachments.error!,
            style: const TextStyle(color: Colors.red, fontSize: 12),
          ),
        ),
      
      // Input row
      Row(
        children: [
          FilePickerButton(
            onFilesSelected: (filePaths) {
              for (var path in filePaths) {
                final file = File(path);
                ref.read(attachmentProvider.notifier).uploadFile(file);
              }
            },
          ),
          
          Expanded(
            child: TextField(
              controller: messageController,
              decoration: const InputDecoration(
                hintText: 'Type a message...',
                border: InputBorder.none,
              ),
              minLines: 1,
              maxLines: 5,
              onChanged: (_) {
                setState(() {});
              },
            ),
          ),
          
          IconButton(
            icon: const Icon(Icons.send),
            onPressed: canSend ? _sendMessage : null,
          ),
        ],
      ),
    ],
  );
}
```

- [ ] **Step 3: Modify _sendMessage to pass attachment IDs**

```dart
void _sendMessage() async {
  final attachmentIds = ref
      .read(attachmentProvider)
      .attachments
      .map((a) => a.id)
      .toList();
  
  await chatService.sendMessage(
    conversationId: widget.conversationId,
    message: messageController.text,
    attachmentIds: attachmentIds.isNotEmpty ? attachmentIds : null,
  );
  
  messageController.clear();
  ref.read(attachmentProvider.notifier).clearAttachments();
  setState(() {});
}
```

- [ ] **Step 4: Update chat service sendMessage signature**

In `lib/services/chat_service.dart`, modify `sendMessage()`:

```dart
Future<Message> sendMessage({
  required String conversationId,
  required String message,
  List<String>? attachmentIds,  // NEW
}) async {
  final request = {
    'prompt': message,
    'conversation_id': conversationId,
    'attachment_ids': attachmentIds,
  };
  
  final response = await apiService.post(
    '/api/process',
    data: request,
  );
  
  final processResponse = ProcessResponse.fromJson(response.data);
  // ... rest of method
}
```

- [ ] **Step 5: Commit**

```bash
cd /home/wills/working/aidi/frontend
git add lib/widgets/chat_panel/message_input.dart lib/services/chat_service.dart
git commit -m "feat: integrate file attachments into message input"
```

---

### Task 16: Frontend - Update Dependencies

**Files:**
- Modify: `pubspec.yaml`

**Interfaces:**
- Produces: Updated pubspec.yaml with new dependencies

- [ ] **Step 1: Add dependencies to pubspec.yaml**

Find the dependencies section and add:

```yaml
dependencies:
  file_picker: ^6.0.0
  mime: ^1.0.4
  path: ^1.8.3
```

- [ ] **Step 2: Run pub get**

```bash
cd /home/wills/working/aidi/frontend
flutter pub get
```

Expected: All dependencies installed

- [ ] **Step 3: Regenerate code**

```bash
cd /home/wills/working/aidi/frontend
flutter pub run build_runner build
```

- [ ] **Step 4: Commit**

```bash
cd /home/wills/working/aidi/frontend
git add pubspec.yaml pubspec.lock
git commit -m "chore: add file picker dependencies"
```

---

### Task 17: End-to-End Testing

**Files:**
- (No new files, integration testing)

**Interfaces:**
- Consumes: All backend and frontend components
- Produces: Verified working file attachment flow

- [ ] **Step 1: Start backend**

```bash
cd /home/wills/working/aidi/backend
python -m uvicorn app.main:app --reload
```

- [ ] **Step 2: Start frontend**

In another terminal:

```bash
cd /home/wills/working/aidi/frontend
flutter run -d linux
```

- [ ] **Step 3: Test full flow**

1. Navigate to a conversation
2. Click paperclip button
3. Select a .txt or .pdf file
4. Wait for "Completed" status in chip
5. Type a message
6. Click send
7. Verify message is sent with attachment
8. Check database for message with attachments JSONB

- [ ] **Step 4: Test error cases**

1. Try uploading >5MB file (should fail)
2. Try uploading unsupported file type (should fail)
3. Try uploading corrupted file (should show error)

- [ ] **Step 5: Verify backend tests pass**

```bash
cd /home/wills/working/aidi/backend
pytest tests/test_extraction_service.py tests/test_attachment_router.py -v
```

Expected: All tests pass

---

### Task 18: Documentation & Cleanup

**Files:**
- Backend: Add docstrings to all new functions
- Frontend: Add comments to new widgets/providers
- Create deployment notes

- [ ] **Step 1: Add docstrings to backend services**

Ensure all classes and methods have docstrings explaining purpose, parameters, and return values.

- [ ] **Step 2: Add comments to frontend code**

Add inline comments explaining complex logic in providers and services.

- [ ] **Step 3: Pre-download PaddleOCR models**

```bash
python << 'EOF'
from paddleocr import PaddleOCR
print("Downloading PaddleOCR models...")
ocr = PaddleOCR(lang='en')
print("Done!")
EOF
```

- [ ] **Step 4: Final commit**

```bash
cd /home/wills/working/aidi
git add -A
git commit -m "docs: add docstrings and deployment notes for file attachments"
```

---

## Summary

This plan implements a complete file attachment system for Deallus:

**Backend (Tasks 1-10):**
- Configuration management
- Database schema (attachments table)
- Extraction service (PDF, DOCX, TXT, OCR)
- REST API endpoints (upload, get, delete)
- Integration with process endpoint
- Comprehensive testing

**Frontend (Tasks 11-18):**
- Attachment model and service
- State management with Riverpod
- UI components (file picker, chips)
- Message input integration
- Dependencies and build
- End-to-end testing

**Key Features:**
- Two-step upload flow
- Async OCR processing
- Token management
- Error handling with user guidance
- Database + Redis caching
- Full test coverage

