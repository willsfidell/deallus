# Voice Recording Feature Design

**Date:** 2026-08-07  
**Author:** AI Assistant  
**Status:** Design Approved  
**Implementation Approach:** Whisper via Ollama (Consistent with existing architecture)

---

## Executive Summary

This document specifies the design for adding voice recording capability to Deallus (AIDI), enabling users to record up to 2 minutes of audio that is automatically transcribed to text via Ollama Whisper and populated into the message input box for editing before sending.

**Key Features:**
- Record voice messages up to 2 minutes in Flutter frontend
- Real-time waveform and timer display during recording
- Automatic transcription via Ollama Whisper model
- Transcribed text populates message input for editing
- Simple, intuitive toggle button UX (tap to start, tap to stop)
- Configurable transcription model

**Scope:**
- Backend: 1 new transcription service, 1 new API router/endpoint, configuration settings
- Frontend: Audio recording service, transcription API client, voice recording widget, updated message input
- Infrastructure: Whisper model in Ollama container (no new services)
- No file storage: Audio discarded after transcription

---

## Requirements

### Functional Requirements

1. **Voice Recording (Flutter Frontend)**
   - Users can tap microphone button to start recording
   - Recording replaces entire message input area
   - Timer displays remaining time (up to 2:00)
   - Waveform visualization shows audio activity (optional visual feedback)
   - User can cancel recording (discards audio, returns to text input)
   - User can stop recording (triggers transcription)
   - Auto-stop at 2:00 limit
   - Recording requires microphone permission

2. **Audio Processing**
   - Platform-specific recording: iOS (iOS)/Android/macOS/Linux/Windows via Flutter `record` package
   - Audio format: Flexible (WAV, MP3, M4A, WebM supported)
   - Temporary file storage on device (cleaned up after transcription or cancel)

3. **Transcription via Ollama**
   - Backend endpoint: `POST /api/transcribe`
   - Request: multipart/form-data with audio file
   - Process: Call Ollama Whisper API with audio
   - Response: JSON with transcribed text and language detection
   - Timeout: 60 seconds per transcription
   - File size limit: 10MB maximum
   - Supported formats: WAV, MP3, M4A, WebM (Whisper native support)

4. **Text Population & Editing**
   - After successful transcription, populate TextEditingController
   - Show loading state during transcription ("Transcribing..." spinner)
   - User can edit transcribed text before sending
   - Send button enabled after transcription completes
   - Clear flow: record → transcribe → edit → send

5. **Error Handling**
   - Permission denied: Show snackbar "Microphone permission required"
   - Recording failed: Show snackbar "Recording failed"
   - Transcription failed: Show snackbar "Transcription failed"
   - Timeout: Show snackbar "Transcription timed out"
   - Invalid format: Backend returns 400 error
   - File too large: Backend returns 413 error
   - Model unavailable: Backend returns 500 error
   - All errors revert to normal text input state

### Non-Functional Requirements

1. **Performance**
   - Recording: Start/stop within 500ms
   - Transcription: 60-second timeout (depends on audio length + model speed)
   - API response: <500ms for healthy Ollama service
   - UI responsiveness: No freezing during recording or transcription

2. **Reliability**
   - Graceful permission handling (request on first use)
   - Audio file cleanup on app crash or error
   - Transcript loss on network failure is acceptable (user sees error, can re-record)
   - No file persistence beyond single transcription job

3. **Authentication & Security**
   - All transcription requests require X-API-Key header
   - Audio files processed in-memory (not stored)
   - Transcription results tied to authenticated user's conversation

4. **Compatibility**
   - Flutter app: iOS 12+, Android 8+, macOS 10.11+, Windows 10+, Linux (GTK)
   - Ollama: Already in Docker Compose, requires Whisper model

---

## Architecture & Components

### High-Level Data Flow

```
User Interface (Flutter)
    ↓
Tap Microphone Button
    ↓
Recording UI (timer, waveform, cancel/stop)
    ↓
User taps Stop (or 2-min auto-stop)
    ↓
Audio File (temporary, device storage)
    ↓
Upload to POST /api/transcribe
    ↓
Backend Transcription Service
    ↓
Call Ollama Whisper API
    ↓
Return Transcribed Text
    ↓
Populate Message Input Box
    ↓
User Edits (if needed)
    ↓
Send Message as Normal
```

### Backend Components

#### 1. Configuration (`backend/app/config.py`)

Add to Settings class:

```python
# Voice Transcription Settings
TRANSCRIPTION_ENABLED: bool = True
TRANSCRIPTION_MODEL: str = "whisper"  # Ollama model identifier
TRANSCRIPTION_TIMEOUT_SECONDS: int = 60
TRANSCRIPTION_MAX_FILE_SIZE_MB: int = 10
ALLOWED_AUDIO_FORMATS: list = [
    "audio/wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/m4a",
    "audio/webm"
]
```

#### 2. Transcription Service (`backend/app/services/transcription_service.py`)

New service class:
- **Method:** `async transcribe(file_path: str, language: Optional[str] = None) -> TranscriptionResult`
- **Function:** Accept audio file, call Ollama Whisper API, return text
- **Error Handling:** TimeoutError, FileNotFoundError, APIConnectionError
- **Model:** Configurable via settings, defaults to "whisper"
- **Retry Logic:** 1 retry on transient failures
- **Logging:** Debug transcription attempts, warnings on errors

**TranscriptionResult dataclass:**
```python
@dataclass
class TranscriptionResult:
    text: str  # Transcribed text
    language: str  # Detected language (e.g., "en")
    duration_seconds: float  # Audio duration
    model: str  # Model used
    error: Optional[str] = None
```

#### 3. API Router (`backend/app/api/transcription_router.py`)

New router with single endpoint:

**POST /api/transcribe**
- Authentication: X-API-Key header (required)
- Request: multipart/form-data with "audio" file
- Validation:
  - File present
  - MIME type in ALLOWED_AUDIO_FORMATS
  - File size ≤ TRANSCRIPTION_MAX_FILE_SIZE_MB
- Response (200):
  ```json
  {
    "text": "transcribed content here",
    "language": "en",
    "duration_seconds": 45.2,
    "model": "whisper"
  }
  ```
- Response (400): Invalid file format or missing file
- Response (413): File too large
- Response (503): Transcription service unavailable
- Response (500): Transcription failed

#### 4. Integration with Conversation Flow

- Transcribed text is independent of message sending
- User receives text in UI before sending
- Text can be edited before message creation
- No database changes needed for transcription itself

### Frontend Components

#### 1. Audio Recording Service (`frontend/lib/services/audio_service.dart`)

Manages platform-specific audio recording:
- **Class:** `AudioRecorderService`
- **State:** Enum `RecordingState { idle, recording, processing }`
- **Methods:**
  - `Future<void> requestPermission()` - Request microphone permission
  - `Future<void> startRecording()` - Begin recording
  - `Future<File> stopRecording()` - End recording, return audio file
  - `Future<void> cancelRecording()` - Discard recording
  - `Stream<double> getAmplitudeStream()` - Real-time waveform amplitude
  - `Stream<Duration> getTimerStream()` - Timer updates for display

**Implementation Details:**
- Use `record` package (cross-platform)
- Platform-specific audio paths via `path_provider`
- Timer stream emits every 100ms
- Amplitude stream for waveform visualization
- Auto-cleanup on cancel/error
- 2-minute hard limit enforced

#### 2. Transcription API Service (`frontend/lib/services/transcription_service.dart`)

Handles API communication:
- **Class:** `TranscriptionService`
- **Methods:**
  - `Future<String> transcribeAudio(File audioFile) -> String` - Upload and get text
  - Error types: NetworkError, TimeoutError, InvalidFormatError, ServerError

**Implementation:**
- Use existing HTTP client from project
- Multipart file upload to `/api/transcribe`
- Pass X-API-Key header (from auth provider)
- 60-second timeout
- Return transcribed text only (ignore language/duration in UI)

#### 3. Voice Recording Widget (`frontend/lib/widgets/chat_panel/voice_recording_widget.dart`)

Replaces message input during recording:

```dart
class VoiceRecordingWidget extends ConsumerStatefulWidget {
  final Function(String) onTranscriptionComplete;
  final VoidCallback onCancel;

  const VoiceRecordingWidget({
    required this.onTranscriptionComplete,
    required this.onCancel,
    Key? key,
  }) : super(key: key);
}
```

**UI Elements:**
- Timer display: "0:45 / 2:00" (red when near limit)
- Animated microphone icon (pulsing during recording)
- Waveform visualization (optional animated bars)
- Cancel button (bottom left)
- Stop button (bottom right, prominent)
- Recording indicator: "Recording..." text or pulsing dot

**Behavior:**
- Show "Transcribing..." after stop, disable buttons
- Handle stream updates from AudioRecorderService
- Auto-stop at 2:00, show "Recording stopped"
- On transcription complete: emit text via callback
- On error: show snackbar, call onCancel()

#### 4. Updated Message Input (`frontend/lib/widgets/chat_panel/message_input.dart`)

Modifications to existing widget:

- Add state: `bool _isRecording = false`
- Add methods:
  - `void _toggleRecording()` - Switch between text input and recording UI
  - `void _handleTranscription(String text)` - Populate controller with transcribed text

- UI changes:
  - Add microphone button next to attachment button
  - Show/hide VoiceRecordingWidget based on `_isRecording`
  - Disable send button during recording
  - Show "Transcribing..." overlay during API call

- Logic:
  - Microphone button: Set `_isRecording = true`
  - VoiceRecordingWidget cancel: Set `_isRecording = false`
  - VoiceRecordingWidget stop: Call transcription service
  - On transcription success: Populate `_messageController.text`, set `_isRecording = false`
  - On transcription error: Show snackbar, set `_isRecording = false`

### Infrastructure Components

#### Ollama Whisper Model

- Already in Ollama container (docker-compose.yml)
- Model name: `whisper` (Ollama standard)
- Pull command: `ollama pull whisper`
- Size: ~3GB
- API endpoint: `http://ollama:11434/api/transcribe` (via Ollama HTTP API)

#### Docker Compose Updates

Update `docker-compose.yml` aidi_api service environment:
```yaml
TRANSCRIPTION_ENABLED: "true"
TRANSCRIPTION_MODEL: "whisper"
TRANSCRIPTION_TIMEOUT_SECONDS: "60"
TRANSCRIPTION_MAX_FILE_SIZE_MB: "10"
```

#### Setup Script

Update `scripts/setup-ollama.sh` to include:
```bash
echo "Pulling Whisper model..."
ollama pull whisper
```

---

## Error Handling

### Frontend Error Scenarios

| Scenario | User Impact | Recovery |
|----------|------------|----------|
| Microphone permission denied | Cannot start recording | Request permission on next attempt |
| Recording failed (hardware error) | Snackbar "Recording failed" | Return to text input, can retry |
| Network error during upload | Snackbar "Transcription failed" | Return to text input, can re-record |
| Timeout (>60 seconds) | Snackbar "Transcription timed out" | Return to text input, can re-record |
| Invalid audio format | Snackbar "Transcription failed" | Return to text input, check file format |

### Backend Error Scenarios

| Error | Status | Response | Handling |
|-------|--------|----------|----------|
| Missing audio file | 400 | `{"error": "Audio file required"}` | Client validation |
| Invalid MIME type | 400 | `{"error": "Unsupported audio format"}` | Accept only ALLOWED_AUDIO_FORMATS |
| File too large | 413 | `{"error": "Audio file too large"}` | Check file size before upload |
| Ollama unavailable | 503 | `{"error": "Transcription service unavailable"}` | Health check before process |
| Model not found | 500 | `{"error": "Transcription model not available"}` | Verify model pulled in Ollama |
| Transcription timeout | 500 | `{"error": "Transcription timeout"}` | Retry logic with logging |

---

## Testing Strategy

### Backend Unit Tests (`backend/tests/test_transcription_service.py`)

Test the `TranscriptionService` class:

1. **Successful transcription** - Mock Ollama response, verify text extraction
2. **Timeout handling** - Mock slow Ollama response, verify timeout error
3. **Invalid audio file** - Verify proper error handling
4. **Language detection** - Verify language returned in result
5. **Retry logic** - Verify retries on transient failures
6. **Model configuration** - Verify model setting from config

**Test count:** 6-8 tests

### Backend Integration Tests (`backend/tests/test_transcription_router.py`)

Test the `/api/transcribe` endpoint:

1. **Successful upload and transcription** - Real or mocked audio file
2. **Authentication required** - Missing X-API-Key header should return 401
3. **Missing audio file** - POST without file should return 400
4. **Invalid file format** - Upload non-audio file, verify 400 response
5. **File too large** - Upload >10MB file, verify 413 response
6. **Malformed request** - Invalid multipart data, verify 400 response

**Test count:** 6 tests

### Frontend Unit Tests

Audio service state management:
- Recording state transitions (idle → recording → stopped)
- Timer stream emits correctly
- Amplitude stream provides values
- Permission handling
- File cleanup on cancel

Voice recording widget:
- Timer display updates
- Cancel button reverts to text input
- Stop button triggers transcription callback

### Frontend Integration Tests

End-to-end flow:
1. User taps microphone → recording UI appears
2. User records audio (or mock recording)
3. User taps stop → transcription spinner shows
4. API response received → text populates message input
5. User edits text → message sends normally

---

## Configuration & Deployment

### Backend Configuration

In `backend/app/config.py`, add these settings:

```python
# Voice Transcription Settings
TRANSCRIPTION_ENABLED: bool = True  # Feature toggle
TRANSCRIPTION_MODEL: str = "whisper"  # Ollama model name
TRANSCRIPTION_TIMEOUT_SECONDS: int = 60  # API timeout
TRANSCRIPTION_MAX_FILE_SIZE_MB: int = 10  # Upload size limit
ALLOWED_AUDIO_FORMATS: list = [
    "audio/wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/m4a",
    "audio/webm"
]
```

### Environment Variables

In Docker Compose or .env:

```
TRANSCRIPTION_ENABLED=true
TRANSCRIPTION_MODEL=whisper
TRANSCRIPTION_TIMEOUT_SECONDS=60
TRANSCRIPTION_MAX_FILE_SIZE_MB=10
```

### Ollama Setup

1. **Pull Whisper model:**
   ```bash
   docker exec aidi_ollama ollama pull whisper
   ```

2. **Verify model:**
   ```bash
   docker exec aidi_ollama ollama list | grep whisper
   ```

3. **Update setup script** (`scripts/setup-ollama.sh`):
   ```bash
   echo "Pulling Whisper model for voice transcription..."
   ollama pull whisper
   echo "Whisper model ready for transcription"
   ```

### Flutter Dependencies

Add to `frontend/pubspec.yaml`:

```yaml
dependencies:
  # Existing dependencies...
  record: ^5.0.0              # Audio recording (cross-platform)
  permission_handler: ^11.0.0 # Microphone permissions
  # path_provider already present
  # http already present
```

Platform-specific configuration (if needed):
- iOS: Add microphone permission to Info.plist
- Android: Add RECORD_AUDIO permission to AndroidManifest.xml

---

## File Structure

### New Backend Files

```
backend/app/services/transcription_service.py
  - TranscriptionService class
  - TranscriptionResult dataclass
  - Integration with Ollama

backend/app/api/transcription_router.py
  - POST /api/transcribe endpoint
  - Request validation
  - Error responses

backend/tests/test_transcription_service.py
  - 6-8 unit tests for TranscriptionService

backend/tests/test_transcription_router.py
  - 6 integration tests for endpoint

backend/docs/VOICE_TRANSCRIPTION_SETUP.md
  - Setup instructions
  - Configuration guide
  - Troubleshooting
  - Performance notes
```

### New Frontend Files

```
frontend/lib/services/audio_service.dart
  - AudioRecorderService class
  - RecordingState enum
  - Platform integration

frontend/lib/services/transcription_service.dart
  - TranscriptionService class
  - API communication

frontend/lib/widgets/chat_panel/voice_recording_widget.dart
  - VoiceRecordingWidget UI
  - Recording controls
  - Transcription status display
```

### Modified Files

```
frontend/lib/widgets/chat_panel/message_input.dart
  - Add recording state management
  - Add microphone button
  - Integrate VoiceRecordingWidget
  - Handle transcription callback

frontend/pubspec.yaml
  - Add record package
  - Add permission_handler package

backend/app/config.py
  - Add transcription settings

backend/app/main.py or similar
  - Register transcription router

docker-compose.yml
  - Add transcription env vars to aidi_api service
```

---

## Dependencies

### Backend

- **No new backend dependencies** required
- Uses existing: FastAPI, Pydantic, aiohttp (via LiteLLM)
- Ollama handles audio processing (Whisper model)

### Frontend

- `record: ^5.0.0` - Cross-platform audio recording
- `permission_handler: ^11.0.0` - Android/iOS permissions
- Existing: `flutter_riverpod`, `logger`, `http`

---

## Documentation

### Backend Documentation (`backend/docs/VOICE_TRANSCRIPTION_SETUP.md`)

Contents:
1. **Quick Start**
   - Pull Whisper model
   - Verify setup
   - Test endpoint

2. **Configuration**
   - Environment variables
   - Model selection
   - Timeout tuning
   - File size limits

3. **Troubleshooting**
   - Model not found (pull instructions)
   - Timeout issues (increase timeout setting)
   - Ollama unavailable (health check)
   - Unsupported format (list supported formats)

4. **Performance**
   - Expected transcription times (by audio length)
   - Resource usage (GPU/CPU)
   - Concurrent transcriptions (Ollama limits)

5. **Supported Audio Formats**
   - WAV, MP3, M4A, WebM
   - Sample rates: 16kHz recommended

---

## Success Criteria

### Backend

- ✅ Transcription service accepts audio file
- ✅ Returns transcribed text via API endpoint
- ✅ Proper error handling for invalid files
- ✅ Timeout protection (60 seconds)
- ✅ All tests passing (12+ test cases)
- ✅ Authentication enforced (X-API-Key required)

### Frontend

- ✅ Microphone button visible in message input
- ✅ Recording UI displays timer and waveform
- ✅ 2-minute limit enforced (auto-stop)
- ✅ Transcribed text populates message input
- ✅ User can edit before sending
- ✅ Error handling with snackbar notifications
- ✅ Permissions requested on first use

### Integration

- ✅ End-to-end flow: record → transcribe → send
- ✅ No file persistence after transcription
- ✅ Works on iOS, Android, and desktop platforms (Flutter)
- ✅ Ollama Whisper model available in Docker Compose

### Non-Functional

- ✅ Recording starts/stops within 500ms
- ✅ UI responsive during recording/transcription
- ✅ No memory leaks from audio file cleanup
- ✅ Works with 60-120 second audio files

---

## Implementation Tasks

### Phase 1: Backend (4 tasks)

1. Create TranscriptionService with Ollama integration
2. Create transcription_router.py with POST /api/transcribe endpoint
3. Write backend unit and integration tests
4. Create VOICE_TRANSCRIPTION_SETUP.md documentation

### Phase 2: Frontend (3 tasks)

1. Create AudioRecorderService (recording/timer/amplitude)
2. Create TranscriptionService (API calls) + VoiceRecordingWidget
3. Update MessageInput to integrate recording feature

### Phase 3: Integration & Testing (2 tasks)

1. End-to-end testing (record → transcribe → send)
2. Platform testing (iOS, Android, desktop)

---

## Timeline Estimate

- **Backend:** 1-2 hours (straightforward Ollama integration)
- **Frontend:** 2-3 hours (audio recording, UI integration)
- **Testing:** 1 hour (unit + integration tests)
- **Total:** ~4-6 hours for POC

---

## Notes & Assumptions

1. **Ollama already running** - Setup assumes Ollama is active in Docker Compose
2. **Whisper model availability** - Assumes `ollama pull whisper` succeeds
3. **Flutter recording package** - Uses `record` package (actively maintained)
4. **No cloud APIs** - All processing local (no OpenAI/cloud Whisper)
5. **Audio discarded after transcription** - No permanent storage
6. **Single transcription at a time** - No queuing for concurrent requests
7. **English-primary** - Whisper handles all languages, default to user's locale

---

**Design approved:** ✅ Ready for implementation planning
