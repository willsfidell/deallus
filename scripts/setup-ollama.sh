#!/bin/bash
# Setup Ollama with vision model for local development

set -e

echo "🔧 Setting up Ollama with vision models..."
echo ""

# Check if ollama container is running
if ! docker ps | grep -q aidi_ollama; then
    echo "❌ Ollama container not running. Start it with: docker-compose up -d ollama"
    exit 1
fi

echo "📦 Pulling qwen2-vl:7b vision model (5-10 minutes, ~4.5GB)..."
docker exec aidi_ollama ollama pull qwen2-vl:7b

echo ""
echo "📦 Pulling whisper model for voice transcription (2-5 minutes, ~3GB)..."
docker exec aidi_ollama ollama pull whisper

echo ""
echo "✅ Models pulled successfully!"
echo ""
echo "📋 Available models:"
docker exec aidi_ollama ollama list

echo ""
echo "🚀 To enable vision OCR in development:"
echo "   1. Add to docker-compose.yml (aidi_api service):"
echo "      VISION_OCR_ENABLED: \"true\""
echo "   2. Restart: docker-compose restart aidi_api"
echo ""
echo "💡 Test it:"
echo "   cd backend && pytest tests/test_extraction_service.py::TestVisionOCR -xvs"
