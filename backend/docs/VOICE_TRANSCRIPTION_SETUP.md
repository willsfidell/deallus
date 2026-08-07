# Voice Transcription Setup & Configuration

**Last Updated:** 2026-08-07

## Quick Start

### 1. Pull Whisper Model

```bash
docker exec aidi_ollama ollama pull whisper
```

### 2. Verify Model

```bash
docker exec aidi_ollama ollama list | grep whisper
```

Expected output shows `whisper` in the model list.

### 3. Test Endpoint

```bash
# First, get an API key from the auth system
# Then test transcribe endpoint
curl -X POST http://localhost:8000/api/transcribe \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@test.wav"
```

## Configuration

### Environment Variables

Set these in `docker-compose.yml` or `.env` file:

```
TRANSCRIPTION_ENABLED=true              # Enable/disable feature
TRANSCRIPTION_MODEL=whisper             # Ollama model name
TRANSCRIPTION_TIMEOUT_SECONDS=60        # API call timeout
TRANSCRIPTION_MAX_FILE_SIZE_MB=10       # File upload size limit
```

### Supported Audio Formats

- **audio/wav** - WAV (recommended, uncompressed)
- **audio/mpeg** - MP3
- **audio/mp3** - MP3 (alternate MIME type)
- **audio/m4a** - AAC/M4A
- **audio/webm** - WebM

## Troubleshooting

### Error: "Transcription service unavailable"

**Cause:** Ollama not running or not responding

**Solution:**
```bash
# Check Ollama container status
docker ps | grep ollama

# Check Ollama health
curl http://localhost:11434/api/tags

# Restart Ollama
docker restart aidi_ollama
```

### Error: "Transcription model not available"

**Cause:** Whisper model not pulled or failing to load

**Solution:**
```bash
# Pull model
docker exec aidi_ollama ollama pull whisper

# Verify pull succeeded
docker exec aidi_ollama ollama list

# Check model file exists
docker exec aidi_ollama ls -lh ~/.ollama/models/blobs/
```

### Error: "Transcription timeout"

**Cause:** Audio processing taking longer than timeout (default 60s)

**Solution:**
1. Increase timeout: `TRANSCRIPTION_TIMEOUT_SECONDS=120`
2. Check Ollama performance: `docker stats aidi_ollama`
3. If CPU/memory maxed, adjust audio bitrate or limit concurrent transcriptions

### Error: "Unsupported audio format: ..."

**Cause:** File MIME type not in ALLOWED_AUDIO_FORMATS

**Solution:**
- Convert file to WAV: `ffmpeg -i input.mp3 output.wav`
- Or add MIME type to config (requires backend change)

### Whisper Model Stuck/Not Responding

**Cause:** Model loading or inference hanging

**Solution:**
```bash
# Kill and restart Ollama
docker restart aidi_ollama

# If that doesn't work, rebuild
docker-compose down
docker volume rm aidi_ollama_data  # WARNING: removes model cache
docker-compose up -d
docker exec aidi_ollama ollama pull whisper
```

## Performance Notes

### Expected Transcription Times

These are rough estimates on modern hardware:

| Audio Length | Model Speed | Time |
|--------------|-------------|------|
| 10 seconds | GPU (4GB VRAM) | 2-3s |
| 60 seconds | GPU (4GB VRAM) | 5-10s |
| 120 seconds | GPU (4GB VRAM) | 10-20s |
| 10 seconds | CPU only | 5-10s |
| 60 seconds | CPU only | 30-60s |
| 120 seconds | CPU only | 60-120s |

### Resource Usage

- **Whisper Model Size:** ~3GB disk space
- **VRAM (GPU):** ~4GB (if available)
- **CPU (no GPU):** 1-2 cores, intensive

### Concurrent Transcriptions

Ollama processes one inference at a time. If multiple transcription requests arrive:
- Requests queue in Ollama
- Total time = sum of individual transcription times
- Consider scaling if high concurrency needed

## API Documentation

### POST /api/transcribe

Transcribe audio file using Ollama Whisper model.

**Request:**
```
POST /api/transcribe
X-API-Key: your_api_key
Content-Type: multipart/form-data

file: (audio file)
```

**Response (200 OK):**
```json
{
  "text": "transcribed text content",
  "language": "en",
  "duration_seconds": 45.5,
  "model": "whisper"
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Unsupported audio format | File MIME type not in ALLOWED_AUDIO_FORMATS |
| 400 | Audio file required | No file in request |
| 403 | Invalid or missing API key | Missing or invalid X-API-Key header |
| 413 | Audio file too large | File exceeds TRANSCRIPTION_MAX_FILE_SIZE_MB |
| 500 | Transcription failed | Ollama error or timeout |
| 503 | Transcription service disabled | TRANSCRIPTION_ENABLED=false |

## Notes

- Whisper model auto-detects language (results in "language" field)
- Accuracy depends on audio quality (clearer audio = better results)
- Ollama runs Whisper in CPU or GPU mode depending on availability
- First transcription may take longer as model loads into memory
