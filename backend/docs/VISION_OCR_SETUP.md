# Vision OCR Setup Guide

## Overview

The backend supports vision model OCR for scanned PDFs via LiteLLM/Ollama. This provides higher quality text extraction than PaddleOCR for complex documents while keeping the API container CPU-only.

## Architecture

- **API Container:** Runs on CPU-only nodes (no GPU needed)
- **Ollama Container:** Runs on GPU nodes with vision models
- **Fallback:** Basic PDF → Vision OCR (if enabled) → PaddleOCR CPU

## Configuration

### Environment Variables

```bash
# Enable/disable vision OCR
VISION_OCR_ENABLED=false  # Set to 'true' to enable

# Vision model configuration
VISION_OCR_MODEL=ollama/qwen2-vl:7b  # Recommended: qwen2-vl for OCR
VISION_OCR_BASE_URL=http://ollama:11434  # Ollama service URL (Docker Compose)
VISION_OCR_TIMEOUT_SECONDS=45  # Per-page timeout
VISION_OCR_MAX_RETRIES=1  # Retries on transient failures
VISION_OCR_PROMPT="Extract all text from this document page..."

# Fallback configuration
OCR_FALLBACK_ENABLED=true  # Enable PaddleOCR CPU fallback
PADDLEOCR_USE_GPU=false  # Always false for API container
```

## Local Development with Docker Compose

### 1. Verify Ollama Service

The `docker-compose.yml` already includes the Ollama service on port 11434.

```bash
docker-compose up -d ollama
```

### 2. Pull Vision Model

```bash
docker exec aidi_ollama ollama pull qwen2-vl:7b
```

This downloads the 7B parameter vision model (~4.5GB). First time will take 5-10 minutes.

### 3. Verify Model is Available

```bash
docker exec aidi_ollama ollama list
```

Should show `qwen2-vl:7b` in the list.

### 4. Enable Vision OCR (Optional)

To test vision OCR in development, add to docker-compose.yml's `aidi_api` service environment:

```yaml
environment:
  VISION_OCR_ENABLED: "true"
  VISION_OCR_BASE_URL: "http://ollama:11434"
```

Or set via Python:

```bash
export VISION_OCR_ENABLED=true
export VISION_OCR_BASE_URL=http://ollama:11434
python run.py
```

## Testing

### 1. Test PaddleOCR CPU Fallback (Vision Disabled)

```bash
cd backend
VISION_OCR_ENABLED=false pytest tests/test_extraction_service.py -xvs
```

### 2. Test Vision OCR Configuration

```bash
cd backend
pytest tests/test_extraction_service.py::TestVisionOCR -xvs
```

Expected output: 7/7 tests passing

### 3. Test Full Extraction Pipeline

```bash
cd backend
pytest tests/test_extraction_service.py -q
```

Expected output: 36+ tests passing

## Recommended Vision Models

| Model | Size | VRAM | OCR Quality | Use Case |
|-------|------|------|-------------|----------|
| **qwen2-vl:7b** | 7B | ~8GB | ⭐⭐⭐⭐⭐ | **Recommended** - Best OCR quality |
| llava:13b | 13B | ~16GB | ⭐⭐⭐⭐ | General vision, good OCR |
| minicpm-v:latest | 2.6B | ~4GB | ⭐⭐⭐ | Lightweight, faster (if VRAM constrained) |

## Performance Benchmarks

| Method | Hardware | Speed (per page) | Quality |
|--------|----------|------------------|---------|
| Basic PDF extraction | CPU | <1s | High (clean PDFs) |
| Vision OCR (qwen2-vl) | GPU (Ollama) | 5-15s | Very High |
| PaddleOCR CPU | CPU | 2-5s | Medium |

## Troubleshooting

### Vision OCR not working

1. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Verify model is pulled:**
   ```bash
   docker exec aidi_ollama ollama list
   ```
   Should show `qwen2-vl:7b`

3. **Check logs:**
   ```bash
   docker logs aidi_api | grep "Vision OCR"
   ```

4. **Test directly:**
   ```python
   import asyncio
   from app.services.extraction_service import ExtractionService
   from app.config import settings
   
   async def test():
       settings.VISION_OCR_ENABLED = True
       service = ExtractionService()
       result = await service._try_vision_ocr(b"...pdf bytes...")
       print(result)
   
   asyncio.run(test())
   ```

### High latency

- Vision models are slower than PaddleOCR (~10-20s vs 2-5s per page)
- Consider disabling for clean PDFs: use vision only for scanned/complex docs
- Check GPU is being used: `docker exec aidi_ollama nvidia-smi` (if GPU available)

### Out of GPU memory

- Reduce model size: try `minicpm-v` (2.6B) instead of `qwen2-vl` (7B)
- Check concurrent LLM requests aren't exhausting VRAM
- Monitor: `docker stats aidi_ollama`

## Production Deployment Notes

For Kubernetes deployment:
- API pods: CPU-only nodes (no GPU)
- Ollama pods: GPU nodes with resource limits
- Communication: HTTP service discovery (no changes needed for Docker Compose setup)
- Scaling: API pods scale horizontally; Ollama typically 1-2 replicas on GPU nodes
