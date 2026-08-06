# Deallus Backend API - Flutter Integration Quick Start

**Generated:** July 24, 2026  
**For:** Flutter Frontend Development

---

## Documentation Files

This analysis includes three comprehensive documents:

### 1. **API_QUICK_REFERENCE.md** (6.9 KB) - START HERE
- 14-section quick reference
- Endpoint overview with examples
- Key request/response patterns
- Authentication flow
- Error handling quick guide
- Flutter implementation checklist
- cURL testing examples

**Best for:** Quick lookups, getting started, implementation reminders

### 2. **API_INTERFACE_GUIDE.md** (24 KB) - DETAILED REFERENCE
- Complete API overview
- 13 major sections covering:
  - All endpoints with full documentation
  - Request/response schemas (TypeScript notation)
  - Authentication mechanisms
  - Health check endpoints
  - Conversation management
  - Process/chat endpoints
  - WebSocket status & polling strategy
  - Error handling patterns
  - Performance considerations
  - Configuration guide

**Best for:** Comprehensive reference during development, schema validation

### 3. **BACKEND_API_ANALYSIS.md** (22 KB) - TECHNICAL DEEP DIVE
- Executive summary & architecture
- Database schema diagrams
- Detailed endpoint reference with:
  - Full request/response examples
  - Error scenarios
  - Contextual routing algorithm
  - Security implementation details
  - Caching strategy
  - Tool registry architecture
  - Performance characteristics
  - Known limitations & roadmap

**Best for:** Understanding system internals, optimization, debugging

---

## Key Insights for Flutter Development

### 1. Authentication is Simple but Two-Phase

**Phase 1: User Registration**
```dart
final user = await api.register(
  email: 'user@example.com',
  username: 'johndoe',
  password: 'SecurePass123',
);
```

**Phase 2: Get API Key (Recommended)**
```dart
final apiKey = await api.createApiKey(
  email: 'user@example.com',
  password: 'SecurePass123',
  name: 'Flutter App',
);
// Store securely: await secureStorage.write(key: 'aidi_api_key', value: apiKey.key);
```

**Phase 3: Use in All Requests**
```dart
final response = await api.process(
  prompt: userMessage,
  conversationId: currentConv.id,
  headers: {'X-API-Key': savedApiKey},
);
```

### 2. Conversations Manage Context Automatically

When you provide `conversation_id`, the backend:
- Loads previous messages (max 10, max 4000 tokens)
- Applies continuity bonus to previous model
- Routes intelligently based on context
- Returns `continuity_applied` flag

**Example Flow:**
```
User: "Draw a ball" 
  → Router: "Image Generator" (no continuity, first msg)
  → Response: continuity_applied = false

User: "Make it blue"
  → Router: "Image Generator" (continuity = true, same task)
  → Response: continuity_applied = true ← Same model maintained!

User: "Classify: This is amazing!"
  → Router: "Classifier" (topic switch detected)
  → Response: continuity_applied = false ← Model switched
```

### 3. Real-time Updates Use Polling (for now)

WebSocket not yet implemented. Recommended pattern:

```dart
Future<void> handleSendMessage(String message) async {
  final response = await api.process(
    prompt: message,
    conversationId: currentConv.id,
    apiKey: apiKey,
  );
  
  // Poll until assistant responds
  await pollForResponse(currentConv.id);
}

Future<void> pollForResponse(String conversationId) async {
  for (int i = 0; i < 150; i++) {  // 5 min timeout with 2s polls
    final conv = await api.getConversation(conversationId);
    
    if (conv.messages.isNotEmpty && 
        conv.messages.last.role == 'assistant') {
      setState(() => messages = conv.messages);
      break;
    }
    
    await Future.delayed(Duration(seconds: 2));
  }
}
```

### 4. Security: API Keys Over Sessions

**Use API Keys because:**
- Can be revoked independently
- Don't expire (unlike sessions)
- Can have descriptive names ("Flutter Production")
- Better for mobile apps (persistent storage)

**In Flutter:**
```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiKeyManager {
  final _storage = const FlutterSecureStorage();
  
  Future<void> saveKey(String key) async {
    await _storage.write(key: 'aidi_api_key', value: key);
  }
  
  Future<String?> getKey() async {
    return await _storage.read(key: 'aidi_api_key');
  }
  
  Future<void> deleteKey() async {
    await _storage.delete(key: 'aidi_api_key');
  }
}
```

### 5. Error Handling Strategy

| Status | Meaning | Action |
|--------|---------|--------|
| 200/201/204 | Success | Process response |
| 400 | Validation error | Show user: "Invalid input" |
| 401 | Auth failed | Redirect to login |
| 403 | Forbidden | Show: "Access denied" |
| 404 | Not found | Show: "Conversation deleted" |
| 422 | Field error | Show: "Invalid format" |
| 500 | Server error | Show: "Server error, retry" |
| 503 | Service down | Show: "AI unavailable, retry" |

### 6. Context Display to User (Optional)

```dart
// Show in message details or footer
Text('Model: ${response.modelUsed}'),
Text('Context: ${response.contextUsed} messages, ${response.totalTokens} tokens'),
Text('Time: ${response.executionTimeMs.toStringAsFixed(2)}ms'),
Text('Routing: ${response.routingReason}'),

// Show continuity badge
if (response.continuityApplied)
  Chip(label: Text('Continuing conversation'))
else
  Chip(label: Text('New context')),
```

### 7. Database Schema for Understanding

```
Users
├── id (PK)
├── email (UNIQUE)
├── username (UNIQUE)
├── hashed_password
├── is_active
└── created_at, updated_at

APIKeys
├── id (PK)
├── key (SHA256 hash, UNIQUE)
├── user_id (FK → Users)
├── name
├── is_active
├── last_used_at
└── created_at, updated_at

Conversations
├── id (UUID, PK)
├── user_id (FK → Users)
├── title
├── is_active (soft delete)
├── conversation_metadata (JSON)
└── created_at, updated_at

Messages
├── id (UUID, PK)
├── conversation_id (FK → Conversations)
├── role (user|assistant|system)
├── content (TEXT)
├── model_used (nullable)
├── token_count
├── tool_executions (JSON)
└── created_at
```

### 8. Endpoints by Priority

**Must Have (MVP):**
1. `POST /api/auth/register` - Sign up
2. `POST /api/auth/keys` - Get API key
3. `POST /api/conversations` - Create chat
4. `POST /api/process` - Send message
5. `GET /api/conversations/{id}` - Load chat history

**Should Have (v1):**
6. `GET /api/conversations` - List chats
7. `GET /api/health` - Check if API alive
8. `PATCH /api/conversations/{id}` - Rename chat
9. `DELETE /api/conversations/{id}` - Archive chat
10. `POST /api/auth/login` - Alternative auth

**Nice to Have (v2):**
11. `POST /api/conversations/{id}/clear` - Reset chat
12. `GET /api/auth/keys` - List keys
13. `GET /api/process/health` - Check tools

### 9. Recommended Flutter Stack

```yaml
dependencies:
  # HTTP
  dio: ^5.3.0              # Better than http package

  # Security  
  flutter_secure_storage: ^9.0.0

  # State Management
  provider: ^6.0.0         # Simple
  # OR
  riverpod: ^2.4.0         # Advanced
  # OR
  bloc: ^8.1.0             # Complex apps

  # Serialization
  json_serializable: ^6.7.0
  json_annotation: ^4.8.0

  # Utilities
  uuid: ^4.0.0             # For UUIDs
  timeago: ^3.5.0          # Timestamp display
  intl: ^0.19.0            # Localization

dev_dependencies:
  build_runner: ^2.4.0
  json_serializable: ^6.7.0
```

### 10. Environment Configuration

Store API base URL securely:

```dart
// lib/config/api_config.dart
class ApiConfig {
  // Development
  static const String devBaseUrl = 'http://localhost:8000';
  
  // Staging
  static const String stagingBaseUrl = 'https://api-staging.deallus.com';
  
  // Production
  static const String prodBaseUrl = 'https://api.deallus.com';
  
  static String getBaseUrl() {
    const String env = String.fromEnvironment('ENV', defaultValue: 'dev');
    switch (env) {
      case 'prod':
        return prodBaseUrl;
      case 'staging':
        return stagingBaseUrl;
      default:
        return devBaseUrl;
    }
  }
}

// Usage in main.dart
void main() {
  // Run with: flutter run --dart-define=ENV=prod
  ApiClient.baseUrl = ApiConfig.getBaseUrl();
  runApp(const MyApp());
}
```

### 11. Response Time Expectations

Set appropriate timeouts:

```dart
final dio = Dio(
  BaseOptions(
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 30),  // Normal calls
  ),
);

// For /api/process specifically, use longer timeout:
await dio.post(
  '/api/process',
  options: Options(
    receiveTimeout: const Duration(minutes: 5),  // LLM can be slow
  ),
);
```

### 12. Pagination for Conversation List

```dart
Future<List<Conversation>> getConversations({
  int limit = 50,
  int offset = 0,
  bool activeOnly = true,
}) async {
  final response = await dio.get(
    '/api/conversations',
    queryParameters: {
      'limit': limit,
      'offset': offset,
      'active_only': activeOnly,
    },
  );
  
  return (response.data as List)
    .map((json) => Conversation.fromJson(json))
    .toList();
}
```

### 13. Continuity vs Topic Switch Logic

```dart
// Detect if continuity was applied
if (response.continuityApplied) {
  // Same model maintained - show subtle indicator
  showSubtleIndicator('Continuing with ${response.modelUsed}');
} else if (response.contextUsed > 0) {
  // Context loaded but model changed
  showNotification('Switched to ${response.modelUsed}');
} else {
  // First message or no context
  showNothing();
}

// Explain to user if model changed unexpectedly
if (previousModel != response.modelUsed && response.contextUsed > 0) {
  showInfo('Topic detected: ${response.routingReason}');
}
```

### 14. Error Recovery Pattern

```dart
Future<T> makeApiCall<T>(Future<T> Function() call) async {
  int retries = 0;
  const maxRetries = 3;
  
  while (retries < maxRetries) {
    try {
      return await call();
    } on DioException catch (e) {
      retries++;
      
      if (e.response?.statusCode == 401) {
        // Auth failed - clear key and redirect
        await apiKeyManager.deleteKey();
        Navigator.of(context).pushReplacementNamed('/login');
        rethrow;
      }
      
      if (e.response?.statusCode == 503 && retries < maxRetries) {
        // Service unavailable - retry with backoff
        await Future.delayed(Duration(seconds: retries));
        continue;
      }
      
      if (retries >= maxRetries) rethrow;
    }
  }
  
  throw Exception('Failed after $maxRetries retries');
}
```

---

## Quick Implementation Roadmap

### Week 1: Foundation
- [ ] Setup Dio HTTP client with X-API-Key header
- [ ] Implement secure API key storage
- [ ] Create Auth screens (register, login, key creation)
- [ ] Test with `/api/health` endpoint

### Week 2: Core Chat
- [ ] Create Conversation model & service
- [ ] Build chat UI (messages, input box)
- [ ] Implement `/api/process` endpoint
- [ ] Test basic message sending

### Week 3: Context & Features
- [ ] Add conversation list screen
- [ ] Implement polling for response updates
- [ ] Display context info (tokens, execution time)
- [ ] Show routing decisions

### Week 4: Polish
- [ ] Error handling & user feedback
- [ ] Offline message queue (optional)
- [ ] Local caching (optional)
- [ ] Performance testing

---

## Testing Your Integration

### Before Submitting PR:

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"TestPass123"}'

# 2. Create API key
API_KEY=$(curl -s -X POST http://localhost:8000/api/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"test@example.com","password":"TestPass123"}' | jq -r '.key')

# 3. Create conversation
CONV=$(curl -s -X POST http://localhost:8000/api/conversations \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}' | jq -r '.id')

# 4. Send message
curl -X POST http://localhost:8000/api/process \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello","conversation_id":"'$CONV'"}'
```

---

## Where to Find Information

| Question | Document |
|----------|----------|
| "How do I authenticate?" | API_QUICK_REFERENCE.md §2 |
| "What's the /api/process response?" | API_INTERFACE_GUIDE.md POST /api/process |
| "How does context work?" | BACKEND_API_ANALYSIS.md Context Management |
| "What are error codes?" | API_QUICK_REFERENCE.md §7 |
| "How do I implement polling?" | API_QUICK_REFERENCE.md §13 |
| "What's the database schema?" | BACKEND_API_ANALYSIS.md Database Schema |
| "What tools are available?" | BACKEND_API_ANALYSIS.md Tools & Extensibility |
| "How do I handle errors?" | API_INTERFACE_GUIDE.md Error Handling |

---

## Key Takeaways

1. **Authentication:** Register → Create API Key → Use in X-API-Key header
2. **Conversations:** Create once, then provide `conversation_id` with each message
3. **Context:** Automatically loaded and managed by backend (10 messages, 4000 tokens max)
4. **Routing:** Smart model selection with continuity bonus (+0.15 for same task)
5. **Updates:** Use polling until WebSocket available (check every 2-5 seconds)
6. **Errors:** Handle all HTTP status codes, retry on 503
7. **Security:** Store API key in flutter_secure_storage, never commit to git
8. **Performance:** First LLM request takes 5-30s (model loading), expect 1-2s for cached
9. **Tools:** Automatic PII redaction, injection detection, quality checks
10. **Extensible:** Tool registry system allows adding custom pre/post-processing

---

## Next Steps

1. Read **API_QUICK_REFERENCE.md** (5-10 min)
2. Review **API_INTERFACE_GUIDE.md** endpoints you need
3. Start with authentication & conversation endpoints
4. Implement polling for message responses
5. Add error handling for edge cases
6. Test with provided cURL commands

---

**Documentation Package Version:** 1.0  
**API Version:** 0.1.0  
**Status:** Ready for Integration  
**Contact:** See repo for developer info
