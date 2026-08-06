# Deallus Backend API - Comprehensive Interface Guide for Flutter Frontend

**Generated:** July 24, 2026  
**API Version:** 0.1.0  
**Base URL:** `http://localhost:8000` (development)

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Available Endpoints](#available-endpoints)
4. [Request/Response Schemas](#requestresponse-schemas)
5. [WebSocket & Real-time Communication](#websocket--real-time-communication)
6. [Error Handling](#error-handling)
7. [Implementation Guidelines](#implementation-guidelines)

---

## API Overview

The Deallus backend is a **FastAPI** application that provides:
- User authentication and API key management
- Intelligent prompt processing with automatic model routing
- Multi-turn conversation management with contextual awareness
- Tool execution (PII redaction, security checks, etc.)
- Redis-backed caching with PostgreSQL persistence

### Key Features
- **Contextual Routing**: Automatically selects appropriate model based on prompt content
- **Continuity Bonus**: Maintains context within conversations with +0.15 confidence boost
- **Conversation History**: Full message history with token tracking
- **Tool Execution**: Pre-prompt and post-result security/transformation tools

---

## Authentication

### Authentication Methods

#### 1. API Key Authentication (Primary)
- **Header**: `X-API-Key`
- **Format**: `aidi_<random_tokens>`
- **Generation**: Via `/api/auth/keys` endpoint (requires credentials)

#### 2. Session Token Authentication (Alternative)
- **Returned from**: `/api/auth/login`
- **Format**: `token_{user_id}_{username}` (placeholder format, will be JWT in production)
- **Note**: Currently bearer token format, will upgrade to JWT

### Authentication Flow

```
User Registration
    ↓
POST /api/auth/register
    ↓
User Login (get access_token)
    ↓
POST /api/auth/login
    ↓
Create API Key (recommended for backend apps)
    ↓
POST /api/auth/keys (with credentials)
    ↓
Use API_KEY in X-API-Key header for API calls
```

### Authentication Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login and get token | No |
| POST | `/api/auth/keys` | Create new API key | User credentials |
| GET | `/api/auth/keys` | List API keys | User credentials |

---

## Available Endpoints

### Health & Diagnostics

#### GET /api/health
Health check for main API

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "ollama": "available",
  "timestamp": "2026-07-22T14:30:00.000Z"
}
```

#### GET /api/process/health
Health check for process service (tools, models)

**Response:**
```json
{
  "status": "healthy",
  "tools_loaded": 5,
  "pre_prompt_tools": ["pii_detector", "armadillo_detector", "prompt_injection_detector"],
  "post_result_tools": ["test_result_validator", "ai_slop_detector"]
}
```

---

### Authentication Endpoints

#### POST /api/auth/register
Register a new user

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securePassword123"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2026-07-22T14:30:00.000000",
  "updated_at": "2026-07-22T14:30:00.000000"
}
```

**Errors:**
- `400`: Email or username already exists
- `422`: Validation error (email format, password length, etc.)

#### POST /api/auth/login
Login and receive access token

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "is_active": true,
    "created_at": "2026-07-22T14:30:00.000000",
    "updated_at": "2026-07-22T14:30:00.000000"
  },
  "access_token": "token_1_johndoe",
  "token_type": "bearer"
}
```

**Errors:**
- `401`: Invalid credentials
- `422`: Validation error

#### POST /api/auth/keys
Create a new API key

**Request Body:**
```json
{
  "name": "Flutter App Key"
}
```

**Additional Headers:**
- Send credentials in request body (non-standard, see note below)

**Response (201):**
```json
{
  "id": 5,
  "key": "aidi_A7K9...X2pL",
  "name": "Flutter App Key",
  "is_active": true,
  "last_used_at": null,
  "created_at": "2026-07-22T14:30:00.000000",
  "updated_at": "2026-07-22T14:30:00.000000"
}
```

**Note:** The full key is only shown on creation. Save it securely in your app.

**Errors:**
- `400`: Failed to create API key
- `401`: Invalid credentials
- `422`: Validation error

#### GET /api/auth/keys
List all API keys for user

**Authentication:** User credentials in request body

**Response (200):**
```json
[
  {
    "id": 5,
    "key": "aidi_A7K9...X2pL",
    "name": "Flutter App Key",
    "is_active": true,
    "last_used_at": "2026-07-22T15:00:00.000000",
    "created_at": "2026-07-22T14:30:00.000000",
    "updated_at": "2026-07-22T14:30:00.000000"
  }
]
```

**Note:** Keys are masked for security

---

### Process/Chat Endpoints

#### POST /api/process
Main prompt processing endpoint with intelligent routing

**Authentication Required:** `X-API-Key` header

**Request Body:**
```json
{
  "prompt": "Write a Python function to reverse a string",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "force_model": null
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | User's input prompt |
| `conversation_id` | string | No | UUID of conversation; creates new if not provided |
| `force_model` | string | No | Force routing to specific model (overrides automatic routing) |

**Response (200):**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "conv-123-abc",
  "model_used": "ollama/llama2",
  "routing_reason": "Code Generation: [Continuing] Code generation request detected",
  "continuity_applied": true,
  "prompt": "Write a Python function to reverse a string",
  "response": "def reverse_string(s):\n    return s[::-1]",
  "execution_time_ms": 2450.5,
  "tools_executed": ["pii_detector", "armadillo_detector"],
  "tool_flags": {
    "pii_detected": [],
    "armadillo_detected": false
  },
  "context_used": 4,
  "total_tokens": 342
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique request identifier |
| `conversation_id` | string | Conversation this request belongs to |
| `model_used` | string | Model that processed the request |
| `routing_reason` | string | Explanation of routing decision |
| `continuity_applied` | boolean | Whether continuity bonus was applied |
| `prompt` | string | Original user prompt |
| `response` | string | Generated response |
| `execution_time_ms` | float | Time in milliseconds |
| `tools_executed` | array | List of tools executed |
| `tool_flags` | object | Tool execution results |
| `context_used` | integer | Number of previous messages used |
| `total_tokens` | integer | Total tokens in context |

**Errors:**
- `400`: Validation error (empty prompt)
- `401`: Invalid API key
- `403`: Conversation doesn't exist or not owned by user
- `422`: Missing required fields
- `500`: Internal server error
- `503`: LLM service unavailable

**Contextual Routing Details:**
- First message in conversation: `continuity_applied = false`
- Follow-up messages: `continuity_applied = true` if same task continues
- Strong topic change: `continuity_applied = false` (overrides bonus)
- Force model: Disables contextual routing, uses specified model

---

### Conversation Endpoints

#### POST /api/conversations
Create a new conversation

**Authentication Required:** `X-API-Key` header

**Request Body:**
```json
{
  "title": "Image Design Task"
}
```

**Response (201):**
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

**Errors:**
- `401`: Invalid API key
- `500`: Internal server error

#### GET /api/conversations
List user's conversations (paginated)

**Authentication Required:** `X-API-Key` header

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max conversations to return |
| `offset` | integer | 0 | Pagination offset |
| `active_only` | boolean | true | Only return active conversations |

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": 1,
    "title": "Image Design Task",
    "is_active": true,
    "created_at": "2026-07-22T14:30:00.000000",
    "updated_at": "2026-07-22T14:30:00.000000",
    "message_count": 6
  }
]
```

**Errors:**
- `401`: Invalid API key
- `500`: Internal server error

#### GET /api/conversations/{conversation_id}
Get full conversation with all messages

**Authentication Required:** `X-API-Key` header

**Response (200):**
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

**Errors:**
- `401`: Invalid API key
- `403`: Conversation not owned by user
- `404`: Conversation not found
- `500`: Internal server error

#### PATCH /api/conversations/{conversation_id}
Update conversation title

**Authentication Required:** `X-API-Key` header

**Request Body:**
```json
{
  "title": "Updated Title"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "title": "Updated Title",
  "is_active": true,
  "created_at": "2026-07-22T14:30:00.000000",
  "updated_at": "2026-07-22T14:30:05.000000"
}
```

**Errors:**
- `401`: Invalid API key
- `404`: Conversation not found
- `500`: Internal server error

#### DELETE /api/conversations/{conversation_id}
Archive (soft delete) a conversation

**Authentication Required:** `X-API-Key` header

**Response (204):** No content

**Errors:**
- `401`: Invalid API key
- `404`: Conversation not found
- `500`: Internal server error

#### POST /api/conversations/{conversation_id}/clear
Clear all messages from conversation

**Authentication Required:** `X-API-Key` header

**Response (200):**
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

**Errors:**
- `401`: Invalid API key
- `404`: Conversation not found
- `500`: Internal server error

---

## Request/Response Schemas

### Authentication Schemas

```typescript
// User Registration
interface UserCreateRequest {
  email: string;        // Must be valid email
  username: string;     // 3-100 characters
  password: string;     // Minimum 8 characters
}

interface UserResponse {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;   // ISO 8601
  updated_at: string;   // ISO 8601
}

// Login
interface UserLoginRequest {
  email: string;
  password: string;
}

interface UserLoginResponse {
  user: UserResponse;
  access_token: string;
  token_type: "bearer";
}

// API Key
interface APIKeyCreateRequest {
  name: string;         // 1-100 characters
}

interface APIKeyResponse {
  id: number;
  key: string;          // Full key on creation, masked on list
  name: string;
  is_active: boolean;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}
```

### Process/Chat Schemas

```typescript
// Process Request
interface ProcessRequest {
  prompt: string;                    // Non-empty string
  conversation_id?: string;          // UUID format, optional
  force_model?: string;              // Optional model override
  model?: string;                    // Deprecated, use force_model
}

// Process Response
interface ProcessResponse {
  request_id: string;
  conversation_id: string;
  model_used: string;
  routing_reason?: string;
  continuity_applied: boolean;
  prompt: string;
  response: string;
  execution_time_ms: number;
  tools_executed: string[];
  tool_flags: Record<string, any>;
  context_used: number;
  total_tokens?: number;
}
```

### Conversation Schemas

```typescript
// Conversation Create
interface ConversationCreateRequest {
  title?: string;       // Optional, auto-generated if not provided
}

// Conversation Response (List View)
interface ConversationResponse {
  id: string;           // UUID
  user_id: number;
  title?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

// Conversation Response (Detail View)
interface ConversationDetailResponse extends ConversationResponse {
  messages: Message[];
}

// Message
interface MessageResponse {
  id: string;           // UUID
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  model_used?: string;  // Only set for assistant messages
  token_count: number;
  tool_executions: object[];
  created_at: string;
}
```

### Health Check Schema

```typescript
interface HealthCheckResponse {
  status: "healthy" | "degraded" | "unavailable";
  version: string;
  database: "connected" | "disconnected";
  ollama: "available" | "unavailable";
  timestamp: string;    // ISO 8601
}

interface ProcessHealthResponse {
  status: "healthy";
  tools_loaded: number;
  pre_prompt_tools: string[];
  post_result_tools: string[];
}
```

---

## WebSocket & Real-time Communication

### Current Status
**Not yet implemented**

### Planned Future Features
- WebSocket support for streaming responses
- Real-time conversation updates
- Server-sent events (SSE) as interim solution

### Current Alternatives for Real-time
1. **Polling**: Implement client-side polling to `/api/conversations/{conversation_id}`
2. **Long-polling**: Extended timeout with immediate response on updates
3. **Events**: Track request_id and poll for completion status

### Recommended Implementation Pattern

```dart
// Polling implementation in Flutter
Future<ConversationDetailResponse> pollConversation(
  String conversationId,
  Duration pollInterval = const Duration(seconds: 2),
  Duration timeout = const Duration(minutes: 5),
) async {
  final startTime = DateTime.now();
  
  while (DateTime.now().difference(startTime) < timeout) {
    final response = await getConversation(conversationId);
    
    if (response.messages.isNotEmpty &&
        response.messages.last.role == 'assistant') {
      return response;
    }
    
    await Future.delayed(pollInterval);
  }
  
  throw TimeoutException('Conversation did not complete in time');
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Validation failed, invalid prompt |
| 401 | Unauthorized | Invalid/missing API key or credentials |
| 403 | Forbidden | User doesn't own resource |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error in request body |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | LLM service or Ollama not available |

### Error Response Format

```json
{
  "detail": "Error message describing the problem"
}
```

### Common Error Scenarios

#### Missing/Invalid API Key
```
Response: 401 Unauthorized
Body: {"detail": "Invalid API key"}
```

#### Conversation Not Found
```
Response: 404 Not Found
Body: {"detail": "Conversation not found"}
```

#### LLM Service Down
```
Response: 503 Service Unavailable
Body: {"detail": "LLM service error: Connection refused"}
```

#### Validation Error
```
Response: 422 Unprocessable Entity
Body: {"detail": "1 validation error for UserCreate..."}
```

---

## Implementation Guidelines

### For Flutter Frontend

#### 1. Authentication Flow

```dart
// Step 1: Register user
final user = await api.register(
  email: 'user@example.com',
  username: 'johndoe',
  password: 'SecurePass123',
);

// Step 2: Create API key (recommended)
final apiKey = await api.createApiKey(
  email: 'user@example.com',
  password: 'SecurePass123',
  name: 'Flutter App',
);

// Step 3: Store API key securely (use flutter_secure_storage)
await secureStorage.write(
  key: 'aidi_api_key',
  value: apiKey.key,
);

// Step 4: Use API key for all requests
const headers = {'X-API-Key': savedApiKey};
```

#### 2. Conversation Management

```dart
// Create new conversation
final conversation = await api.createConversation(
  title: 'Design Discussion',
  apiKey: savedApiKey,
);

// Send message with automatic conversation context
final response = await api.process(
  prompt: 'Make it blue',
  conversationId: conversation.id,
  apiKey: savedApiKey,
);

// Check if continuity was applied
if (response.continuityApplied) {
  print('Same model maintained: ${response.modelUsed}');
}

// Load full conversation history
final detail = await api.getConversation(
  conversation.id,
  apiKey: savedApiKey,
);
```

#### 3. Error Handling

```dart
try {
  final response = await api.process(
    prompt: userInput,
    conversationId: currentConversation.id,
    apiKey: apiKey,
  );
} on UnauthorizedException {
  // Handle invalid API key - redirect to login
  redirectToLogin();
} on ForbiddenException {
  // Handle resource access denied
  showErrorSnackbar('Conversation not found or not owned by you');
} on ServiceUnavailableException {
  // Handle LLM service down
  showErrorSnackbar('AI service temporarily unavailable');
} on TimeoutException {
  // Handle timeout
  showErrorSnackbar('Request took too long, please try again');
} catch (e) {
  // Generic error handler
  logError(e);
  showErrorSnackbar('An error occurred: $e');
}
```

#### 4. Context Awareness

```dart
// Determine if starting new conversation
if (conversations.isEmpty) {
  final conversation = await api.createConversation();
  currentConversation = conversation;
}

// Monitor context usage
final response = await api.process(
  prompt: userMessage,
  conversationId: currentConversation.id,
  apiKey: apiKey,
);

// Display context info
debugPrint('Context used: ${response.contextUsed} previous messages');
debugPrint('Total tokens: ${response.totalTokens}');
debugPrint('Execution time: ${response.executionTimeMs}ms');

// Show routing decision to user (optional)
if (response.continuityApplied) {
  showInfo('Continuing with ${response.modelUsed}');
} else {
  showInfo('Switched to ${response.modelUsed} for this task');
}
```

#### 5. Storage & Caching

```dart
// Recommended local caching strategy
class ApiCache {
  // Cache conversation list
  List<Conversation> cachedConversations = [];
  DateTime lastFetch = DateTime(2000);
  
  Future<List<Conversation>> getConversations({
    Duration cacheDuration = const Duration(minutes: 5),
  }) async {
    if (DateTime.now().difference(lastFetch) < cacheDuration) {
      return cachedConversations;
    }
    
    // Fetch fresh data
    cachedConversations = await api.listConversations();
    lastFetch = DateTime.now();
    return cachedConversations;
  }
  
  // Invalidate cache on updates
  void invalidateCache() {
    lastFetch = DateTime(2000);
  }
}
```

#### 6. Recommended Dependencies

```yaml
dependencies:
  # HTTP
  http: ^1.1.0
  dio: ^5.3.0

  # Security
  flutter_secure_storage: ^9.0.0

  # State Management
  provider: ^6.0.0
  # or
  riverpod: ^2.4.0

  # Serialization
  json_serializable: ^6.7.0

  # Error Handling
  fpdart: ^1.1.0  # Functional programming approach
```

#### 7. Request Headers Template

```dart
// All requests require these headers
Map<String, String> getHeaders(String apiKey) {
  return {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey,
    // Add custom user agent for debugging
    'User-Agent': 'Deallus-Flutter-Client/1.0',
  };
}
```

#### 8. Timeout Configuration

```dart
// Recommended timeout values
const Duration shortTimeout = Duration(seconds: 10);     // Auth endpoints
const Duration normalTimeout = Duration(seconds: 30);    // API calls
const Duration llmTimeout = Duration(minutes: 5);        // LLM generation
```

---

## Performance Considerations

### Context Window Management
- **Max Messages**: 10 by default (configurable)
- **Max Tokens**: 4000 by default (configurable)
- Older messages truncated when limits exceeded
- Token estimation: ~0.25 tokens per character

### Caching Strategy
- **Redis Cache**: 1st choice (fast, ~50ms)
- **PostgreSQL**: Fallback if Redis unavailable
- Cache invalidation: On new messages
- TTL: Configurable per deployment

### Estimated Latencies
| Operation | Time |
|-----------|------|
| Health check | <100ms |
| Simple prompt (cached) | 1-2s |
| Complex prompt (new model load) | 5-30s |
| Context loading (cached) | 100-200ms |
| Context loading (database) | 300-500ms |

---

## Configuration

### Environment Variables

```bash
# Application
APP_NAME=Deallus
APP_VERSION=0.1.0
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aidi

# Redis
REDIS_URL=redis://localhost:6379/0

# Models
TEXT_MODEL=ollama/llama2
CLASSIFIER_MODEL=ollama/llama2
OLLAMA_BASE_URL=http://localhost:11434

# Routing
RULE_CONFIDENCE_THRESHOLD=0.80
LLM_CONFIDENCE_THRESHOLD=0.60
CONTINUITY_BONUS=0.15

# Context
CONTEXT_MAX_MESSAGES=10
CONTEXT_MAX_TOKENS=4000
TOKEN_ESTIMATE_MULTIPLIER=0.25

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Testing with cURL

### Quick Start

```bash
# Set variables
export BASE_URL="http://localhost:8000"
export EMAIL="test@example.com"
export PASSWORD="TestPass123"
export USERNAME="testuser"

# 1. Register
curl -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'${EMAIL}'",
    "username": "'${USERNAME}'",
    "password": "'${PASSWORD}'"
  }'

# 2. Create API key
API_KEY=$(curl -s -X POST "${BASE_URL}/api/auth/keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-key",
    "email": "'${EMAIL}'",
    "password": "'${PASSWORD}'"
  }' | jq -r '.key')

# 3. Create conversation
CONV_ID=$(curl -s -X POST "${BASE_URL}/api/conversations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"title": "Test"}' | jq -r '.id')

# 4. Send message
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Hello, how are you?",
    "conversation_id": "'${CONV_ID}'"
  }' | jq '.'
```

---

## Summary for Flutter Implementation

### Must-Have Features
- [ ] Secure API key storage (flutter_secure_storage)
- [ ] Authentication with email/password and API key management
- [ ] Multi-turn conversation management
- [ ] Error handling with user-friendly messages
- [ ] Conversation list with message counts
- [ ] Context awareness display (tokens, execution time)

### Nice-to-Have Features
- [ ] Offline message queueing
- [ ] Local conversation caching
- [ ] Real-time updates via polling
- [ ] Typing indicators
- [ ] Message search within conversation
- [ ] Export conversation history

### API Rate Considerations
- No rate limiting currently implemented
- Plan for future: Implement rate limits if needed
- Recommended: Implement client-side throttling to prevent abuse

---

**Documentation Version:** 1.0  
**Last Updated:** July 24, 2026  
**Status:** Production Ready for Flutter Integration
