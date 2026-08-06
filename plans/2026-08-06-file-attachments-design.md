# File Attachments Feature Design

**Date:** 2026-08-06  
**Author:** AI Assistant  
**Status:** Design Approved  
**Implementation Approach:** Approach B (Production-Ready)

---

## Executive Summary

This document specifies the design for adding file attachment support to Deallus (AIDI), enabling users to attach PDF, TXT, and DOCX files to messages. The system will extract text from documents using modern libraries (Marker for PDFs, PaddleOCR for scanned PDFs, python-docx for Word), store extracted content in the database, and include it in LLM prompts for analysis.

**Key Features:**
- Support PDF, TXT, DOCX files (max 5MB per file)
- Multiple files per message (max 5 files, 10MB total)
- Two-step upload flow: upload/extract → send message
- Smart extraction: direct text extraction preferred, OCR fallback for scanned PDFs
- Extracted text stored in database (no permanent file storage)
- Background processing for OCR jobs (async, non-blocking)

**Scope:**
- Backend: 3 new API endpoints, 1 database table, extraction service, background queue
- Frontend: File picker UI, upload manager, attachment chips, status polling
- No permanent file storage - extracted text only
- Delete when conversation deleted

---

## Requirements

### Functional Requirements

1. **File Upload**
   - Users can attach PDF, TXT, DOCX files to messages
   - Max 5MB per file, 5 files per message, 10MB total
   - Files validated client-side and server-side
   - Immediate upload when selected (not on message send)

2. **Text Extraction**
   - PDF: Marker library for text-based PDFs
   - PDF (scanned): PaddleOCR for OCR extraction
   - DOCX: python-docx library
   - TXT: UTF-8 with encoding fallback detection
   - Timeout: 30 seconds max per file
   - Partial results returned on timeout

3. **Storage**
   - Extracted text stored in database (Message.attachments JSONB)
   - Temporary storage pre-send in `attachments` table
   - Redis cache for fast lookups (1-hour TTL)
   - No permanent file storage on disk
   - Cleanup: Delete when conversation deleted

4. **LLM Integration**
   - Extracted text included in prompt with file markers
   - Multiple files: clearly separated with headers
   - Token management: Truncate >2000 words with warning
   - Context preserved in conversation history

5. **UI/UX**
   - Paperclip icon in message input
   - File picker with type filters (.pdf, .txt, .docx)
   - Attachment chips below input with status
   - Progress indicators for OCR jobs
   - Remove button per attachment
   - Send disabled while processing

### Non-Functional Requirements

1. **Performance**
   - Text extraction: <5 seconds for most files
   - OCR extraction: <30 seconds with timeout
   - Background processing for OCR (non-blocking)
   - Status polling: 2-second intervals

2. **Reliability**
   - Graceful error handling with specific messages
   - Partial extraction on timeout
   - Redis fallback to database
   - Auto-cleanup of expired attachments

3. **Security**
   - File type validation (MIME + extension)
   - Size limits enforced
   - User ownership verification
   - API key authentication required

4. **Maintainability**
   - Modular extraction service per file type
   - Clear separation of concerns
   - Comprehensive test coverage
   - Configuration-driven limits

---

## Architecture Overview

### System Components

Backend API with extraction service, background task queue, and storage layer.

### Data Flow

**Upload Flow:**
1. User selects files → Frontend validates
2. POST /api/attachments/upload per file
3. Backend validates → Saves temp file
4. Extraction service processes (fast <5s returns immediately, slow triggers async)
5. Store in Redis + Database
6. Return attachment metadata
7. Frontend polls GET /api/attachments/{id} if processing
8. All files ready → User can send message

**Message Send Flow:**
1. User clicks send with attachment IDs
2. POST /api/process {prompt, conversation_id, attachment_ids}
3. Backend loads extracted text
4. Build enhanced prompt with file markers
5. Send to LLM
6. Store message with attachments JSONB
7. Delete temporary attachment records
8. Return response

---

## Database Schema

### New Table: `attachments`

Temporary storage for uploaded files before message send.

```sql
CREATE TABLE attachments (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    
    extracted_text TEXT,
    extraction_status VARCHAR(20) NOT NULL,
    extraction_error TEXT,
    page_count INTEGER,
    word_count INTEGER,
    
    extraction_method VARCHAR(50),
    processing_time_ms FLOAT,
    ocr_applied BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_attachments_user_id ON attachments(user_id);
CREATE INDEX idx_attachments_status ON attachments(extraction_status);
CREATE INDEX idx_attachments_expires ON attachments(expires_at);
```

### Modified Table: `messages`

Add JSONB column for permanent attachment storage.

```sql
ALTER TABLE messages 
ADD COLUMN attachments JSONB DEFAULT '[]';
```

### Redis Keys

```
attachment:{attachment_id}          → Full attachment object (JSON)
attachment:{attachment_id}:text     → Just extracted text
attachment:queue                    → List of attachment IDs pending OCR
```

TTL: 1 hour for all keys

---

## API Endpoints

### New Endpoints

#### 1. POST /api/attachments/upload

Upload file and extract text.

**Response (Fast Extraction):**
```json
{
  "id": "att_abc123",
  "filename": "report.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 2456789,
  "status": "completed",
  "extracted_text_preview": "First 200 chars...",
  "page_count": 12,
  "word_count": 4523,
  "extraction_method": "marker",
  "ocr_applied": false,
  "processing_time_ms": 2340
}
```

**Response (OCR Queued):**
```json
{
  "id": "att_def456",
  "filename": "scanned.pdf",
  "status": "processing",
  "message": "Document is being processed with OCR. This may take 10-30 seconds.",
  "estimated_completion_seconds": 20
}
```

#### 2. GET /api/attachments/{attachment_id}

Get attachment status and extracted text.

#### 3. DELETE /api/attachments/{attachment_id}

Delete attachment before message send.

### Modified Endpoint

#### POST /api/process

Add `attachment_ids` parameter.

**Request:**
```json
{
  "prompt": "What are the key findings?",
  "conversation_id": "conv_123",
  "attachment_ids": ["att_abc123", "att_def456"]
}
```

---

## Extraction Service

### Service Architecture

**File:** `app/services/extraction_service.py`

```python
class ExtractionService:
    async def extract_from_file(file_path: str, mime_type: str) -> ExtractionResult
    async def extract_pdf(file_path: str) -> ExtractionResult
    async def extract_docx(file_path: str) -> ExtractionResult
    async def extract_text(file_path: str) -> ExtractionResult
```

### PDF Extraction Strategy

**Step 1:** Try Marker extraction (fast, 2-5 seconds)
- If text found (>100 words) → Success
- If minimal text → Proceed to OCR

**Step 2:** PaddleOCR fallback (slow, 10-30 seconds)
- Convert pages to images
- Run OCR
- Add warning about accuracy

**Timeout:** 30 seconds max

### Background Task Queue

```python
async def queue_ocr_extraction(attachment_id: str, file_path: str):
    await redis.lpush("attachment:queue", attachment_id)
    asyncio.create_task(_process_ocr_task(attachment_id, file_path))

async def _process_ocr_task(attachment_id: str, file_path: str):
    # Run PaddleOCR
    # Update database
    # Update Redis cache
    # Cleanup temp file
```

### Error Handling

| Error | Message | Action |
|-------|---------|--------|
| Corrupted file | "Could not read {filetype} file..." | User must fix |
| Empty result | "No text found in document..." | Allow with warning |
| OCR timeout | "Extracted {N} of {M} pages..." | Return partial |
| Unsupported type | "File type not supported..." | User must convert |

---

## Frontend Implementation

### New Components

#### 1. File Picker Button
**File:** `lib/widgets/chat_panel/file_picker_button.dart`

Paperclip icon, opens native file picker, multi-select up to 5 files.

#### 2. Attachment Chip
**File:** `lib/widgets/chat_panel/attachment_chip.dart`

Shows file info, status, progress indicator, remove button.

#### 3. Attachment Service
**File:** `lib/services/attachment_service.dart`

```dart
class AttachmentService {
  Future<Attachment> uploadFile(File file);
  Future<Attachment> getStatus(String attachmentId);
  Future<void> deleteAttachment(String attachmentId);
  Stream<Attachment> pollStatus(String attachmentId);
}
```

#### 4. Attachment Provider
**File:** `lib/providers/attachment_provider.dart`

Manages list of attachments, polls status, handles state.

#### 5. Modified Message Input
**File:** `lib/widgets/chat_panel/message_input.dart`

Add file picker button, attachment chips, disable send while processing.

### Frontend Models

**New:** `lib/models/attachment.dart`

```dart
@JsonSerializable()
class Attachment {
  final String id;
  final String filename;
  final String mimeType;
  final int sizeBytes;
  final String status;
  final String? extractedTextPreview;
  final int? pageCount;
  final int? wordCount;
  final String? extractionMethod;
  final bool? ocrApplied;
  final double? processingTimeMs;
  final List<String>? warnings;
  final String? error;
}
```

---

## Configuration

### Backend Settings (app/config.py)

```python
MAX_FILE_SIZE_MB: int = 5
MAX_FILES_PER_MESSAGE: int = 5
MAX_TOTAL_SIZE_MB: int = 10
ALLOWED_MIME_TYPES: list = [
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

EXTRACTION_TIMEOUT_SECONDS: int = 30
OCR_ENABLED: bool = True
OCR_LANGUAGE: str = "en"
MIN_TEXT_WORDS_FOR_OCR: int = 100

ATTACHMENT_EXPIRY_HOURS: int = 24
ATTACHMENT_CACHE_TTL_SECONDS: int = 3600
MAX_ATTACHMENT_WORDS_IN_PROMPT: int = 2000
TRUNCATE_LONG_ATTACHMENTS: bool = True
```

### Backend Dependencies (requirements.txt)

```
marker-pdf>=0.2.0
paddlepaddle>=2.5.0
paddleocr>=2.7.0
python-docx>=1.0.0
chardet>=5.2.0
python-multipart>=0.0.6
```

### Frontend Dependencies (pubspec.yaml)

```
file_picker: ^6.0.0
mime: ^1.0.4
path: ^1.8.3
```

---

## Testing Strategy

### Backend Tests

- Unit tests for extraction service (all file types, timeouts, errors)
- Integration tests for upload/extract/send flow
- API endpoint tests
- Database persistence tests
- OCR background queue tests

### Frontend Tests

- Unit tests for attachment service
- Widget tests for UI components
- Integration tests for full upload flow
- Error handling and retry tests

---

## Deployment Plan

### Pre-Deployment

1. Install Python dependencies
2. Pre-download PaddleOCR models (~100MB)
3. Create manual Alembic migration
4. Test migration on staging
5. Add configuration to environment
6. Run all tests

### Deployment Phases

**Phase 1:** Deploy backend (endpoints ready, not used)
**Phase 2:** Deploy frontend (feature available)
**Phase 3:** Monitor metrics and optimize

### Monitoring

Track:
- File upload success rate
- Extraction method distribution
- Average extraction time
- OCR timeout rate (target: <5%)
- Failed extraction reasons
- Attachment storage size

Set alerts:
- OCR timeout rate >20%
- Extraction failure rate >10%
- Redis queue backup >100 items

---

## Success Criteria

- Users can attach PDF, TXT, DOCX files
- Text extracted from 95%+ of files
- Fast extraction: <5s for 90% of files
- OCR completion: <30s with timeout
- Upload success rate: >98%
- Extraction success rate: >95%
- Clear status indicators and error messages

---

End of Design Document
