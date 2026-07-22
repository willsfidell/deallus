# AIDI API - cURL Test Commands Reference

This file contains all cURL commands for testing AIDI API endpoints.

## Prerequisites

```bash
# Set base URL (adjust if not local)
export BASE_URL="http://localhost:8000"

# Optional: Install jq for pretty JSON output
# Ubuntu/Debian: sudo apt install jq
# macOS: brew install jq
```

## 1. Health Check

```bash
curl -X GET "${BASE_URL}/api/health"
```

## 2. Register User

```bash
curl -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "securepass123"
  }'
```

## 3. Login User

```bash
curl -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123"
  }' | jq '.access_token'
```

## 4. Create API Key

```bash
curl -X POST "${BASE_URL}/api/auth/keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-api-key",
    "email": "test@example.com",
    "password": "securepass123"
  }' | jq '.key'

# Save the output as your API key:
# export API_KEY="<paste_the_key_here>"
```

## 5. List API Keys

```bash
curl -X GET "${BASE_URL}/api/auth/keys" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123"
  }' | jq '.'
```

## 6. Process Service Health

```bash
curl -X GET "${BASE_URL}/api/process/health" | jq '.'
```

## 7. Classification Request

Routes to classifier model (llama3.2:3b)

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Classify the sentiment of this review: This product is amazing and I love it!"
  }' | jq '.'
```

## 8. Explanation Request

Routes to text model (llama3.2:8b)

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Explain how neural networks work in simple terms"
  }' | jq '.'
```

## 9. Code Generation Request

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Write a Python function to reverse a string"
  }' | jq '.'
```

## 10. Analysis Request

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Analyze the pros and cons of remote work"
  }' | jq '.'
```

## 11. PII Redaction Test

The email and phone should be redacted before sending to LLM

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "My email is john@example.com and my phone is 555-1234. Can you help me?"
  }' | jq '.'
```

## 12. Armadillo Detection Test

Test the armadillo detector tool (marks content as modified)

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Tell me about armadillos"
  }' | jq '.'
```

## 13. Error Tests

### Invalid API Key (401)

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid_key_12345" \
  -d '{"prompt": "test"}' | jq '.'
```

### Missing API Key (422)

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}' | jq '.'
```

### Empty Prompt (422)

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"prompt": ""}' | jq '.'
```

## Testing Tips

### View Response Headers
```bash
curl -i -X GET "${BASE_URL}/api/health"
```

### View Full Request/Response
```bash
curl -v -X GET "${BASE_URL}/api/health"
```

### Time the Request
```bash
curl -w "\nTime: %{time_total}s\n" -X GET "${BASE_URL}/api/health"
```

### Save Response to File
```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"prompt": "test"}' \
  > response.json
```

### Extract Specific Fields with jq
```bash
# Get just the response text
curl -s "${BASE_URL}/api/process" \
  ... | jq '.response'

# Get just the model used
curl -s "${BASE_URL}/api/process" \
  ... | jq '.model_used'

# Get execution time
curl -s "${BASE_URL}/api/process" \
  ... | jq '.execution_time_ms'

# Get tools executed
curl -s "${BASE_URL}/api/process" \
  ... | jq '.tools_executed'
```

## Complete Workflow

Here's a complete workflow from scratch:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

# 1. Check API is running
echo "Checking API health..."
curl -s "${BASE_URL}/api/health" | jq '.status'

# 2. Register user
echo "Registering user..."
curl -s -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "username": "demouser",
    "password": "demopass123"
  }' > /dev/null

# 3. Create API key
echo "Creating API key..."
API_KEY=$(curl -s -X POST "${BASE_URL}/api/auth/keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo-key",
    "email": "demo@example.com",
    "password": "demopass123"
  }' | jq -r '.key')

echo "API Key: $API_KEY"

# 4. Test classification
echo -e "\nTesting classification..."
curl -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"prompt": "Classify: Amazing product!"}' | jq '.model_used'

# 5. Test explanation
echo -e "\nTesting explanation..."
curl -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"prompt": "Explain neural networks"}' | jq '.execution_time_ms'

echo -e "\n✅ All tests complete!"
```

## Debugging

### Check if API is running
```bash
curl -v "${BASE_URL}/api/health"
```

### Check database connection
Try to register a user. If database isn't running, you'll get an error.

### Check Ollama is running
Try a process request. If Ollama isn't running, you'll get a 503 error.

### Check API logs
```bash
# If using Docker
docker-compose logs -f aidi_api

# If running locally
# Watch the terminal where you started the API
```

## Response Examples

### Successful Health Check
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "ollama": "available",
  "timestamp": "2026-07-22T14:30:00.000Z"
}
```

### Successful Process Response
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_used": "ollama/llama3.2:8b",
  "prompt": "Explain how neural networks work",
  "response": "Neural networks are computing systems inspired by biological...",
  "execution_time_ms": 2500.5,
  "tools_executed": [
    "armadillo_detector",
    "pii_detector",
    "prompt_injection_detector",
    "test_result_validator",
    "ai_slop_detector"
  ],
  "tool_flags": {}
}
```

### Error Response (Invalid API Key)
```json
{
  "detail": "Invalid API key"
}
```

## Common Issues

**Issue**: "Connection refused"
- **Solution**: Make sure API is running: `docker-compose up aidi_api` or `python backend/run.py`

**Issue**: "401 Unauthorized"
- **Solution**: Check your API key with `cat .aidi_api_key` and make sure it's valid

**Issue**: "503 Service Unavailable"
- **Solution**: Ollama is not running. Start it with `docker-compose up ollama`

**Issue**: Response takes very long
- **Solution**: Normal for first request (model load time). LLM requests typically take 5-30 seconds

**Issue**: Database connection error
- **Solution**: Make sure PostgreSQL is running: `docker-compose up postgres`
