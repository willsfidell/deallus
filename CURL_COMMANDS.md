# Deallus API - cURL Test Commands Reference

This file contains all cURL commands for testing Deallus API endpoints, including multi-turn conversations and contextual routing.

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

---

## NEW: Conversation Management & Contextual Routing Tests

### Prerequisites for Conversation Tests

These tests require Deallus with the conversation management feature enabled.

```bash
# Set environment variables
export BASE_URL="http://localhost:8000"
export API_KEY="your_api_key_here"

# Helper function for pretty JSON output
function json_pretty() {
  jq '.' 2>/dev/null || cat
}
```

---

## 14. Create a Conversation

```bash
curl -X POST "${BASE_URL}/api/conversations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "title": "Image Design Task"
  }' | json_pretty
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "title": "Image Design Task",
  "is_active": true,
  "created_at": "2026-07-22T14:30:00.000000",
  "updated_at": "2026-07-22T14:30:00.000000"
}
```

**Save the conversation ID:**
```bash
export CONVERSATION_ID="550e8400-e29b-41d4-a716-446655440000"
```

---

## 15. List User's Conversations

```bash
curl -X GET "${BASE_URL}/api/conversations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" | json_pretty
```

**Optional: Filter by active conversations only**
```bash
curl -X GET "${BASE_URL}/api/conversations?active_only=true&limit=10" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" | json_pretty
```

---

## 16. Get Full Conversation with Messages

```bash
curl -X GET "${BASE_URL}/api/conversations/${CONVERSATION_ID}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" | json_pretty
```

**Expected Response (with messages):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "title": "Image Design Task",
  "is_active": true,
  "created_at": "2026-07-22T14:30:00.000000",
  "updated_at": "2026-07-22T14:30:00.000000",
  "messages": [
    {
      "id": "msg-001",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "Draw an image of a ball",
      "model_used": null,
      "token_count": 8,
      "tool_executions": [],
      "created_at": "2026-07-22T14:30:10.000000"
    },
    {
      "id": "msg-002",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "assistant",
      "content": "[Generated image of a ball]",
      "model_used": "ollama/stable-diffusion",
      "token_count": 10,
      "tool_executions": [],
      "created_at": "2026-07-22T14:30:15.000000"
    }
  ]
}
```

---

## 17. Update Conversation Title

```bash
curl -X PATCH "${BASE_URL}/api/conversations/${CONVERSATION_ID}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "title": "Ball Design - Updated"
  }' | json_pretty
```

---

## 18. Clear All Messages from Conversation

```bash
curl -X POST "${BASE_URL}/api/conversations/${CONVERSATION_ID}/clear" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" | json_pretty
```

---

## 19. Archive (Soft Delete) Conversation

```bash
curl -X DELETE "${BASE_URL}/api/conversations/${CONVERSATION_ID}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}"
```

---

# CONTEXTUAL ROUTING TESTS

## Understanding Contextual Routing

Deallus now intelligently routes messages based on conversation context:

- **Continuity Bonus**: Previous model gets +0.15 confidence boost
- **Task Continuation**: "Make it blue" after "Draw an image" stays with Image Generator
- **Topic Switching**: Strong topic changes override continuity bonus
- **Transparent Routing**: Response includes `routing_reason` and `continuity_applied` flag

---

## 20. Test 1: Initial Image Generation Request

First, create a new conversation:

```bash
CONV=$(curl -s -X POST "${BASE_URL}/api/conversations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"title": "Image Generation Test"}' | jq -r '.id')

echo "Created conversation: $CONV"
export CONV_ID=$CONV
```

Send initial image generation request:

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Draw an image of a red ball",
    "conversation_id": "'${CONV_ID}'"
  }' | json_pretty
```

**What to look for:**
- `model_used`: Should route to image generation model
- `continuity_applied`: Should be `false` (first message)
- `routing_reason`: Should explain why image model was selected
- `context_used`: Should be `0` (no previous context)

---

## 21. Test 2: Follow-up Message (Continuity Test)

Send a follow-up message to the same conversation:

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Make it blue",
    "conversation_id": "'${CONV_ID}'"
  }' | json_pretty
```

**What to look for:**
- `model_used`: Should STILL be image generation model (continuity maintained!)
- `continuity_applied`: Should be `true` ✅
- `routing_reason`: Should contain "[Continuing]" tag
- `context_used`: Should be `2` (user + assistant from previous turn)

**This demonstrates continuity bonus working correctly!**

---

## 22. Test 3: Add More Detail (Still Continuity)

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Add some shine to it",
    "conversation_id": "'${CONV_ID}'"
  }' | json_pretty
```

**What to look for:**
- `model_used`: Still image generation
- `continuity_applied`: Should be `true`
- `context_used`: Should be `4` (accumulating messages)

---

## 23. Test 4: Topic Switch (Override Continuity)

Send a completely different request to test topic switching:

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Classify the sentiment: This product is amazing!",
    "conversation_id": "'${CONV_ID}'"
  }' | json_pretty
```

**What to look for:**
- `model_used`: Should SWITCH to classifier model ✅
- `continuity_applied`: Should be `false` (topic switch detected)
- `routing_reason`: Should NOT contain "[Continuing]"
- Shows strong topic change overrides continuity bonus

**This demonstrates smart topic detection working!**

---

## 24. Test 5: Force Model Override

Test the `force_model` parameter for explicit user control:

```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Write a poem about a sunset",
    "conversation_id": "'${CONV_ID}'",
    "force_model": "ollama/llama2"
  }' | json_pretty
```

**What to look for:**
- `model_used`: Should be exactly `ollama/llama2` ✅
- `routing_reason`: Should say "User specified model"
- `continuity_applied`: Should be `false` (user override)

---

## 25. Full Multi-Turn Conversation Workflow

Here's a complete workflow demonstrating contextual routing:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
API_KEY="${API_KEY}"

echo "🚀 Starting Contextual Routing Test..."
echo ""

# 1. Create conversation
echo "1️⃣  Creating conversation..."
CONV_ID=$(curl -s -X POST "${BASE_URL}/api/conversations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"title": "Multi-turn Test"}' | jq -r '.id')

echo "   Conversation ID: $CONV_ID"
echo ""

# 2. Image generation request
echo "2️⃣  Image generation request..."
RESP1=$(curl -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Draw a landscape with mountains and a lake",
    "conversation_id": "'${CONV_ID}'"
  }')

MODEL1=$(echo $RESP1 | jq -r '.model_used')
CONT1=$(echo $RESP1 | jq -r '.continuity_applied')
echo "   Model: $MODEL1"
echo "   Continuity Applied: $CONT1 (should be false)"
echo ""

# 3. Follow-up to same task
echo "3️⃣  Follow-up message (same task)..."
RESP2=$(curl -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Make the sky orange",
    "conversation_id": "'${CONV_ID}'"
  }')

MODEL2=$(echo $RESP2 | jq -r '.model_used')
CONT2=$(echo $RESP2 | jq -r '.continuity_applied')
REASON2=$(echo $RESP2 | jq -r '.routing_reason')
echo "   Model: $MODEL2"
echo "   Continuity Applied: $CONT2 (should be true ✅)"
echo "   Reason: $REASON2"
echo ""

# 4. Topic switch
echo "4️⃣  Topic switch (different task)..."
RESP3=$(curl -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Classify sentiment: Absolutely beautiful!",
    "conversation_id": "'${CONV_ID}'"
  }')

MODEL3=$(echo $RESP3 | jq -r '.model_used')
CONT3=$(echo $RESP3 | jq -r '.continuity_applied')
REASON3=$(echo $RESP3 | jq -r '.routing_reason')
echo "   Model: $MODEL3"
echo "   Continuity Applied: $CONT3 (should be false ✅)"
echo "   Reason: $REASON3"
echo ""

# 5. Show full conversation
echo "5️⃣  Full conversation history..."
curl -s -X GET "${BASE_URL}/api/conversations/${CONV_ID}" \
  -H "X-API-Key: ${API_KEY}" | jq '.messages | length'
echo "   Total messages in conversation"
echo ""

echo "✅ Contextual Routing Test Complete!"
echo ""
echo "🔍 Key Observations:"
echo "   • Turn 1: No continuity (first message)"
echo "   • Turn 2: Continuity applied (same task)"
echo "   • Turn 3: Continuity NOT applied (topic switch)"
echo "   • All messages stored in conversation history"
```

**Save this as `test_contextual_routing.sh` and run:**
```bash
chmod +x test_contextual_routing.sh
./test_contextual_routing.sh
```

---

## 26. Response Examples with Contextual Routing

### Turn 1: Initial Request (No Continuity)
```json
{
  "request_id": "req-001",
  "conversation_id": "conv-123",
  "model_used": "ollama/stable-diffusion",
  "routing_reason": "Image Generator: Image generation request detected",
  "continuity_applied": false,
  "prompt": "Draw a landscape with mountains and a lake",
  "response": "[Generated landscape image]",
  "execution_time_ms": 3250.5,
  "tools_executed": [...],
  "tool_flags": {},
  "context_used": 0,
  "total_tokens": null
}
```

### Turn 2: Follow-up (Continuity Applied ✅)
```json
{
  "request_id": "req-002",
  "conversation_id": "conv-123",
  "model_used": "ollama/stable-diffusion",
  "routing_reason": "Image Generator: [Continuing] Image request detected",
  "continuity_applied": true,
  "prompt": "Make the sky orange",
  "response": "[Updated landscape with orange sky]",
  "execution_time_ms": 2850.3,
  "tools_executed": [...],
  "tool_flags": {},
  "context_used": 2,
  "total_tokens": 342
}
```

### Turn 3: Topic Switch (Continuity Overridden)
```json
{
  "request_id": "req-003",
  "conversation_id": "conv-123",
  "model_used": "ollama/classifier",
  "routing_reason": "Classifier: Classification task detected",
  "continuity_applied": false,
  "prompt": "Classify sentiment: Absolutely beautiful!",
  "response": "Sentiment: POSITIVE (confidence: 0.98)",
  "execution_time_ms": 1250.7,
  "tools_executed": [...],
  "tool_flags": {},
  "context_used": 4,
  "total_tokens": 456
}
```

---

## 27. Troubleshooting Contextual Routing

### Issue: Continuity not applied when expected

**Diagnostic:**
```bash
curl -s -X GET "${BASE_URL}/api/conversations/${CONV_ID}" \
  -H "X-API-Key: ${API_KEY}" | jq '.messages[-1].model_used'
```

Check if previous assistant message has `model_used` set. If not, continuity can't be applied.

### Issue: Context showing 0 messages used

**Diagnostic:**
Check if conversation has at least 2 previous messages:
```bash
curl -s -X GET "${BASE_URL}/api/conversations/${CONV_ID}" \
  -H "X-API-Key: ${API_KEY}" | jq '.messages | length'
```

### Issue: Wrong model selected

**Solution:** Use `force_model` to override:
```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Your message",
    "conversation_id": "'${CONV_ID}'",
    "force_model": "ollama/llama2"
  }' | json_pretty
```

### Issue: Redis cache not working

Check if Redis is running:
```bash
docker-compose logs redis
```

System will gracefully fall back to PostgreSQL if Redis unavailable.

---

## 28. Performance Testing

### Measure context loading time:

```bash
time curl -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Test message",
    "conversation_id": "'${CONV_ID}'"
  }' > /dev/null
```

Expected: <2 seconds with context

### Compare with/without Redis:

```bash
# WITH Redis (should be faster)
curl -w "Time: %{time_total}s\n" -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Repeat message to use cache",
    "conversation_id": "'${CONV_ID}'"
  }' > /dev/null

# Repeat same request (should hit Redis cache)
curl -w "Time: %{time_total}s\n" -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Repeat message to use cache",
    "conversation_id": "'${CONV_ID}'"
  }' > /dev/null
```

Second request should be faster due to Redis cache hit.

---

## Complete Test Suite Script

Save this as `test_all_conversations.sh`:

```bash
#!/bin/bash

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY}"

PASS=0
FAIL=0

function test_endpoint() {
  local name=$1
  local method=$2
  local endpoint=$3
  local data=$4
  local expected_status=$5

  echo -n "Testing: $name... "

  if [ -z "$data" ]; then
    status=$(curl -s -o /dev/null -w "%{http_code}" -X $method "${BASE_URL}${endpoint}" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${API_KEY}")
  else
    status=$(curl -s -o /dev/null -w "%{http_code}" -X $method "${BASE_URL}${endpoint}" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${API_KEY}" \
      -d "$data")
  fi

  if [ "$status" = "$expected_status" ]; then
    echo "✅ PASS (HTTP $status)"
    ((PASS++))
  else
    echo "❌ FAIL (Expected $expected_status, got $status)"
    ((FAIL++))
  fi
}

echo "🧪 Running Conversation API Tests..."
echo ""

# Create test conversation
CONV_ID=$(curl -s -X POST "${BASE_URL}/api/conversations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"title": "Test"}' | jq -r '.id')

echo "Test Conversation ID: $CONV_ID"
echo ""

# Run tests
test_endpoint "Create Conversation" "POST" "/api/conversations" \
  '{"title":"Test"}' "201"

test_endpoint "List Conversations" "GET" "/api/conversations" "" "200"

test_endpoint "Get Conversation" "GET" "/api/conversations/$CONV_ID" "" "200"

test_endpoint "Update Conversation" "PATCH" "/api/conversations/$CONV_ID" \
  '{"title":"Updated"}' "200"

test_endpoint "Process with Conversation" "POST" "/api/process" \
  '{"prompt":"Test","conversation_id":"'$CONV_ID'"}' "200"

test_endpoint "Clear Conversation" "POST" "/api/conversations/$CONV_ID/clear" "" "200"

test_endpoint "Delete Conversation" "DELETE" "/api/conversations/$CONV_ID" "" "204"

echo ""
echo "📊 Results: $PASS passed, $FAIL failed"

if [ $FAIL -eq 0 ]; then
  echo "✅ All tests passed!"
  exit 0
else
  echo "❌ Some tests failed"
  exit 1
fi
```

Run it:
```bash
chmod +x test_all_conversations.sh
./test_all_conversations.sh
```
