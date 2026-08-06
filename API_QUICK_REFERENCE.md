# Deallus Backend API - Quick Summary for Flutter

## 1. Endpoints Overview

### Health Check
- `GET /api/health` - Main API health
- `GET /api/process/health` - Process service health

### Authentication  
- `POST /api/auth/register` - Create user account
- `POST /api/auth/login` - Get access token
- `POST /api/auth/keys` - Create API key (recommended)
- `GET /api/auth/keys` - List API keys

### Chat/Process
- `POST /api/process` - Send prompt, get response with contextual routing
- Returns: model_used, response, continuity_applied, context info

### Conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations` - List conversations (paginated)
- `GET /api/conversations/{id}` - Get conversation with messages
- `PATCH /api/conversations/{id}` - Update title
- `DELETE /api/conversations/{id}` - Archive conversation
- `POST /api/conversations/{id}/clear` - Clear all messages

## 2. Authentication

**Primary Method:** API Key Authentication
- Header: `X-API-Key: aidi_<token>`
- Get key via: `POST /api/auth/keys`
- Store securely in app (use flutter_secure_storage)

**Flow:**
```
Register → Login → Create API Key → Store Key → Use in X-API-Key header
```

## 3. Key Request/Response Patterns

### POST /api/process
**Request:**
```json
{
  "prompt": "Your message",
  "conversation_id": "uuid-optional",
  "force_model": "model-name-optional"
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "conversation_id": "uuid",
  "model_used": "ollama/llama2",
  "routing_reason": "explanation",
  "continuity_applied": true,
  "response": "AI response text",
  "execution_time_ms": 2450.5,
  "tools_executed": ["tool1", "tool2"],
  "context_used": 4,
  "total_tokens": 342
}
```

### Key Fields Explained
- `continuity_applied`: true if continuing with same model (context aware)
- `context_used`: number of previous messages loaded
- `total_tokens`: token count in context window
- `routing_reason`: why this model was selected

## 4. Contextual Routing Features

The API intelligently routes requests:
- **First message**: `continuity_applied = false`
- **Follow-up same task**: `continuity_applied = true` (+0.15 confidence boost)
- **Topic switch**: `continuity_applied = false` (detects new task)
- **Force model**: User override, disables routing

Example flow:
1. "Draw a ball" → Image Generator (no continuity)
2. "Make it blue" → Image Generator (continuity applied!)
3. "Classify sentiment" → Classifier (topic switch, no continuity)

## 5. Authentication Schemas

### User Registration
```json
{
  "email": "user@example.com",
  "username": "john",
  "password": "SecurePass123"  // Min 8 chars
}
```

### Login
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
Returns: user, access_token, token_type
```

### Create API Key
```json
{
  "name": "Flutter App"
}
```
**Note:** Full key only shown once on creation

## 6. Conversation Schemas

### Create Conversation
```json
{
  "title": "Optional title"
}
```
Returns: id, user_id, title, is_active, created_at, updated_at

### Message Structure
```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "user|assistant|system",
  "content": "message text",
  "model_used": "model-name",  // Only for assistant
  "token_count": 42,
  "tool_executions": [],
  "created_at": "2026-07-22T14:30:00"
}
```

## 7. Error Handling

| Code | Scenario |
|------|----------|
| 200/201 | Success |
| 204 | Deleted successfully |
| 400 | Validation error (empty prompt, etc) |
| 401 | Invalid API key or credentials |
| 403 | Conversation not owned by user |
| 404 | Resource not found |
| 422 | Field validation error |
| 500 | Server error |
| 503 | LLM service unavailable |

All errors return: `{"detail": "error message"}`

## 8. Context Management

**Max Context Window:**
- Messages: 10 (configurable)
- Tokens: 4000 (configurable)
- Token estimation: ~0.25 tokens per character
- Older messages truncated when exceeded

**Caching:**
- Redis: 1st choice (~50ms)
- PostgreSQL: Fallback (~300-500ms)
- Invalidated on new messages

## 9. Tools Executed

Pre-prompt tools:
- `pii_detector` - Redacts email, phone, SSN
- `armadillo_detector` - Content flagging
- `prompt_injection_detector` - Security check

Post-result tools:
- `test_result_validator` - Validates response
- `ai_slop_detector` - Detects low-quality content

## 10. Flutter Implementation Checklist

- [ ] Setup HTTP client with X-API-Key header
- [ ] Use flutter_secure_storage for API key
- [ ] Implement registration/login/key creation
- [ ] Create conversation on app launch
- [ ] Send messages with conversation_id
- [ ] Handle continuity_applied field
- [ ] Display context info (tokens, execution time)
- [ ] Implement error handling for all status codes
- [ ] Cache conversations locally (optional)
- [ ] Implement polling for real-time updates (optional)

## 11. Performance Notes

- Health check: <100ms
- Simple prompt (cached): 1-2s
- Complex prompt (new): 5-30s
- Context load (cached): 100-200ms
- Context load (DB): 300-500ms

First request to new model slower due to model loading.

## 12. Environment Configuration

```bash
# Key env vars for backend
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0
TEXT_MODEL=ollama/llama2
CLASSIFIER_MODEL=ollama/llama2
OLLAMA_BASE_URL=http://localhost:11434
CONTINUITY_BONUS=0.15
CONTEXT_MAX_MESSAGES=10
CONTEXT_MAX_TOKENS=4000
```

## 13. WebSocket / Real-time

**Status:** Not implemented yet

**Current workaround:**
- Poll `/api/conversations/{id}` every 2-5 seconds
- Check if latest message role is "assistant"
- Stop polling when response received

```dart
Future<void> pollForResponse(String conversationId) async {
  for (int i = 0; i < 150; i++) {  // 5 min timeout
    final conv = await api.getConversation(conversationId);
    if (conv.messages.isNotEmpty && 
        conv.messages.last.role == 'assistant') {
      updateUI(conv.messages.last);
      break;
    }
    await Future.delayed(Duration(seconds: 2));
  }
}
```

## 14. Testing Quick Commands

```bash
export BASE_URL="http://localhost:8000"
export EMAIL="test@example.com"
export PASSWORD="TestPass123"

# Register
curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"'$EMAIL'","username":"testuser","password":"'$PASSWORD'"}'

# Create API key
API_KEY=$(curl -s -X POST "$BASE_URL/api/auth/keys" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"'$EMAIL'","password":"'$PASSWORD'"}' | jq -r '.key')

# Create conversation
CONV=$(curl -s -X POST "$BASE_URL/api/conversations" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}' | jq -r '.id')

# Send message
curl -X POST "$BASE_URL/api/process" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello","conversation_id":"'$CONV'"}'
```

---

**Full documentation available in:** API_INTERFACE_GUIDE.md
**API Version:** 0.1.0
**Status:** Production Ready
