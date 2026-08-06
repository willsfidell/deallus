# Conversation Management - Implementation Checklist

Quick reference for implementing the conversation system.

## 📦 Dependencies

```bash
# Add to requirements.txt
redis>=5.0.0
```

## 🗂️ Files to Create

### Phase 1: Database & Models
- [ ] `backend/app/db/models.py` - Add Conversation & Message models
- [ ] `backend/alembic/versions/xxx_add_conversations.py` - Migration
- [ ] `backend/app/models/schemas.py` - Add conversation schemas

### Phase 2: Services
- [ ] `backend/app/services/redis_service.py` - NEW
- [ ] `backend/app/services/context_manager.py` - NEW
- [ ] `backend/app/services/__init__.py` - Export new services

### Phase 3: Business Logic
- [ ] `backend/app/services/conversation_service.py` - NEW

### Phase 4: API
- [ ] `backend/app/api/conversation_router.py` - NEW
- [ ] `backend/app/api/process_router.py` - MODIFY (add conversation support)
- [ ] `backend/app/services/llm_service.py` - MODIFY (add generate_with_context)
- [ ] `backend/app/main.py` - MODIFY (register conversation router)

### Phase 5: Tests
- [ ] `backend/tests/test_context_manager.py` - NEW
- [ ] `backend/tests/test_conversation_service.py` - NEW
- [ ] `backend/tests/test_redis_service.py` - NEW
- [ ] `backend/tests/test_conversation_flow.py` - NEW
- [ ] `backend/tests/test_conversation_api.py` - NEW

## 🔑 Key Models

### Conversation
```python
{
    "id": "uuid",
    "user_id": 123,
    "title": "Auto-generated or custom",
    "created_at": "2026-07-22T10:00:00",
    "updated_at": "2026-07-22T11:30:00",
    "is_active": true,
    "metadata": {}
}
```

### Message
```python
{
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "user|assistant|system",
    "content": "Message text...",
    "model_used": "ollama/llama2",
    "token_count": 42,
    "tool_executions": [...],
    "created_at": "2026-07-22T10:00:00"
}
```

## 🔄 Updated ProcessRequest/Response

### Request
```python
{
    "prompt": "User message",
    "model": null,  # Optional - will auto-route
    "conversation_id": "uuid"  # NEW - optional
}
```

### Response
```python
{
    "request_id": "uuid",
    "conversation_id": "uuid",  # NEW
    "model_used": "ollama/llama2",
    "prompt": "User message",
    "response": "AI response",
    "execution_time_ms": 1234.56,
    "tools_executed": [...],
    "tool_flags": {...},
    "context_used": 5,  # NEW - number of previous messages
    "total_tokens": 1200  # NEW - total context tokens
}
```

## 🚀 Quick Start Commands

### Phase 1
```bash
# Create migration
cd backend
alembic revision -m "add_conversation_and_message_tables"

# Edit migration file, then:
alembic upgrade head
```

### Phase 2-4
```bash
# Install redis dependency
pip install redis>=5.0.0

# Run tests as you implement
pytest tests/test_context_manager.py -v
pytest tests/test_conversation_service.py -v
```

### Phase 5
```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=app --cov-report=html
```

## ⚠️ Important Notes

1. **Redis is optional** - system degrades gracefully to PostgreSQL-only
2. **conversation_id is optional** - if not provided, creates new conversation
3. **Tools run on every message** - for consistent security
4. **Token estimation is approximate** - ~4 chars per token
5. **Default context limit** - 10 messages or 4000 tokens

## 🔍 Verification Steps

After each phase:

### Phase 1
```bash
# Verify tables created
docker compose exec postgres psql -U aidi_user -d aidi_db -c "\dt"
# Should see: conversations, messages
```

### Phase 2
```bash
# Verify Redis connection
docker compose exec redis redis-cli ping
# Should return: PONG
```

### Phase 4
```bash
# Test conversation creation
curl -X POST http://localhost:8000/api/conversations \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Conversation"}'

# Test message in conversation
curl -X POST http://localhost:8000/api/process \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "conversation_id": "CONV_UUID"}'
```

## 📊 Timeline

- **Week 1:** Phases 1-2 (Database, Redis, Context Manager)
- **Week 2:** Phases 3-4 (Services, API Integration)
- **Week 3:** Phases 5-6 (Testing, Documentation)

**Total:** ~3 weeks for full MVP

## ✅ Definition of Done

- [ ] All database tables created and migrated
- [ ] Redis caching working with TTL
- [ ] Context truncation working (10 messages, 4K tokens)
- [ ] Conversation CRUD endpoints functional
- [ ] Process endpoint accepts conversation_id
- [ ] Multi-turn conversations work end-to-end
- [ ] All tests passing (>85% coverage)
- [ ] API documentation updated
- [ ] No performance regression (<2s response time)

---

See `conversation-context-management.md` for full details.
