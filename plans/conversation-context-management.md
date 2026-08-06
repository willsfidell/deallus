# Conversation & Context Management Plan

**Project:** Deallus AI Orchestrator  
**Feature:** Multi-turn conversations with context management and compression  
**Date:** 2026-07-22  
**Status:** Planning Phase

---

## 📋 Executive Summary

Implement a conversation management system that allows multi-turn interactions with:
- **Persistent conversation storage** (PostgreSQL + Redis hybrid)
- **Smart context window management** (truncation with future summarization)
- **Per-message model routing** (flexible, leverages existing routing system)
- **Context compaction** when approaching token limits
- **Conversation switching** capability for users

---

## 🎯 Goals

### Primary Goals
1. Enable multi-turn conversations between user and AI
2. Manage context within model token limits (typically 2K-8K tokens)
3. Store conversation history persistently
4. Support model switching within conversations
5. Provide fast access to active conversations

### Secondary Goals
1. Enable conversation summarization (future enhancement)
2. Support context compaction strategies
3. Track token usage per conversation
4. Allow users to manage multiple conversations

---

## 🏗️ Architecture Overview

### Storage Strategy: **Hybrid (Redis + PostgreSQL)**

```
┌─────────────────────────────────────────────────────────────┐
│                    Conversation Flow                         │
└─────────────────────────────────────────────────────────────┘

User Message
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Load Conversation Context                                │
│    ├─ Check Redis (active conversations, TTL=1hr)           │
│    └─ Fallback to PostgreSQL (persistent storage)           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Build Context Window                                     │
│    ├─ Get last N messages (configurable, default=10)        │
│    ├─ Calculate total tokens                                │
│    └─ Apply compaction if needed (drop oldest or summarize) │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Run Tools & Route Model                                  │
│    ├─ Execute pre-prompt tools on user message              │
│    ├─ Route to model (per-message routing)                  │
│    └─ Include conversation context in LLM call              │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Store Messages                                           │
│    ├─ Save user message to PostgreSQL                       │
│    ├─ Save assistant message to PostgreSQL                  │
│    ├─ Update Redis cache with latest messages               │
│    └─ Track token counts and metadata                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### New Tables

#### `conversations`
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),  -- Auto-generated from first message
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',  -- Store preferences, settings, etc.
    
    INDEX idx_conversations_user_id (user_id),
    INDEX idx_conversations_user_active (user_id, is_active),
    INDEX idx_conversations_updated (updated_at DESC)
);
```

#### `messages`
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    model_used VARCHAR(100),  -- Which model generated this (null for user messages)
    token_count INTEGER,  -- Approximate token count for context management
    tool_executions JSONB DEFAULT '[]',  -- Array of tool execution details
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    INDEX idx_messages_conversation (conversation_id, created_at),
    INDEX idx_messages_created (created_at DESC)
);
```

---

## 🚀 Implementation Phases

### Phase 1: Database & Models (Week 1)
**Goal:** Set up data storage foundation

- [ ] Create database models (Conversation, Message)
- [ ] Create Alembic migration
- [ ] Run migration in dev environment
- [ ] Create Pydantic schemas
- [ ] Write unit tests for models

**Deliverable:** Database schema ready, models defined

---

### Phase 2: Redis & Context Manager (Week 1-2)
**Goal:** Implement caching and context management

- [ ] Add redis dependency
- [ ] Create RedisService
- [ ] Create ContextManager
- [ ] Implement token estimation
- [ ] Implement message truncation
- [ ] Write unit tests

**Deliverable:** Context management working, Redis caching operational

---

### Phase 3: Conversation Service (Week 2)
**Goal:** Business logic for conversations

- [ ] Create ConversationService
- [ ] Implement CRUD operations
- [ ] Implement auto-title generation
- [ ] Add ownership verification
- [ ] Write unit tests

**Deliverable:** Conversation management logic complete

---

### Phase 4: API Integration (Week 2-3)
**Goal:** Expose conversation functionality via API

- [ ] Create conversation_router
- [ ] Update process_router to support conversations
- [ ] Update LLM service for context support
- [ ] Register routers in main.py
- [ ] Write integration tests

**Deliverable:** API endpoints working, multi-turn conversations functional

---

### Phase 5: Testing & Refinement (Week 3)
**Goal:** Ensure reliability and performance

- [ ] Write comprehensive integration tests
- [ ] Test context compaction under load
- [ ] Test Redis failover behavior
- [ ] Performance testing (latency with context)
- [ ] Fix bugs and edge cases

**Deliverable:** Production-ready conversation system

---

### Phase 6: Documentation (Week 3)
**Goal:** Document for frontend integration

- [ ] API documentation (OpenAPI/Swagger)
- [ ] Usage examples
- [ ] Frontend integration guide
- [ ] Context management guide

**Deliverable:** Complete documentation

---

## 📝 Detailed Implementation Specs

See full plan with code examples, schemas, and detailed architecture in this file.

Key components to implement:
1. Database models (Conversation, Message in `app/db/models.py`)
2. Pydantic schemas (conversation schemas in `app/models/schemas.py`)
3. Redis service (`app/services/redis_service.py`)
4. Context manager (`app/services/context_manager.py`)
5. Conversation service (`app/services/conversation_service.py`)
6. Updated LLM service with context support
7. Conversation router (`app/api/conversation_router.py`)
8. Updated process router with conversation support

---

## 🎯 Success Metrics

### Functional Metrics
- ✅ Users can have multi-turn conversations
- ✅ Conversations persist across sessions
- ✅ Context window stays within token limits
- ✅ Model routing works per-message
- ✅ Tools execute correctly in conversations

### Performance Metrics
- Response time < 2s (with context, avg)
- Redis cache hit rate > 80%
- Context retrieval < 100ms
- Database queries < 50ms

### Quality Metrics
- Test coverage > 85%
- No data loss on Redis failure
- Graceful degradation (Redis down → PostgreSQL only)
- Clear error messages

---

## 💡 Key Design Decisions

1. **Hybrid Storage (Redis + PostgreSQL)**
   - PostgreSQL: Persistent storage, durability
   - Redis: Active conversation cache, speed
   - Fallback: If Redis unavailable, use PostgreSQL only

2. **Per-Message Routing**
   - Each message evaluated independently
   - Leverages existing model routing system
   - Allows flexible model switching

3. **Simple Truncation (MVP)**
   - Keep last 10 messages by default
   - Drop oldest messages when over token limit
   - Future: Add summarization

4. **Server-Managed conversation_id**
   - Backend creates and tracks conversations
   - Easier for frontend to manage
   - Better for analytics

5. **Tool Execution on Every Message**
   - Security tools (PII, injection) run each time
   - Consistent protection
   - Slight performance cost acceptable

---

## 🔒 Security Considerations

- All conversations scoped to user_id
- Ownership verification on all endpoints
- Soft delete retains data (is_active=false)
- API key authentication required
- No cross-user data leakage

---

## 📋 API Endpoints

### New Endpoints
```
POST   /api/conversations              # Create conversation
GET    /api/conversations              # List conversations
GET    /api/conversations/{id}         # Get conversation with messages
DELETE /api/conversations/{id}         # Delete (archive) conversation
```

### Modified Endpoints
```
POST   /api/process                    # Now accepts optional conversation_id
```

---

## 🎓 Summary

This plan implements a robust conversation management system for Deallus that:

1. **Stores conversations** in PostgreSQL for persistence
2. **Caches active conversations** in Redis for performance
3. **Manages context** within token limits via truncation
4. **Routes per-message** for flexible model selection
5. **Tracks token usage** for context window management
6. **Provides API** for frontend integration

**Estimated Total Time:** 3 weeks for MVP (Phases 1-6)

**Next Step:** Review plan, address open questions, then begin Phase 1 implementation.

---

## 🔗 ADDENDUM: Contextual Routing (Conversation-Aware Model Selection)

**Added:** 2026-07-22  
**Status:** Design Enhancement

### Problem Statement

When users have multi-turn conversations, routing each message independently can break task continuity.

**Example:**
```
User: "Draw an image of a ball"
  → Routes to: Image Generator ✓

User: "Make it blue"
  → Without context: Routes to General Text ✗ (breaks task)
  → With context: Should route to Image Generator ✓ (continues task)
```

### Solution: Previous Model Bias with Continuity Bonus

Apply a **continuity bonus** to the previously used model when routing follow-up messages.

#### Design Parameters

1. **Bonus Amount:** `+0.15` confidence boost
   - Gentle enough to allow genuine topic switches
   - Strong enough to maintain task continuity
   - Configurable via settings

2. **Bonus Decay:** Constant (no decay for POC)
   - Same bonus applied regardless of turn count
   - Simpler implementation
   - Can add decay in future iterations

3. **User Override:** Support explicit model hints (future UX)
   - POC: Direct model specification via `force_model` parameter
   - Future: User-friendly categories ("image creation", "text composition")
   - Allows user control without knowing technical model names

4. **Logging:** Prominent logging of continuity decisions
   - Log when bonus is applied
   - Include in response for debugging
   - Show original vs. boosted confidence

---

### Technical Implementation

#### 1. Configuration (`app/config.py`)

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Contextual routing
    CONTINUITY_BONUS: float = 0.15
    CONTINUITY_ENABLED: bool = True
```

#### 2. Context Manager Enhancement (`app/services/context_manager.py`)

**Change return type to include last model:**

```python
class ContextManager:
    async def get_conversation_context(
        self, 
        conversation_id: str, 
        db: Session
    ) -> dict:
        """
        Get conversation context INCLUDING last model used.
        
        Returns:
            dict with keys:
                - messages: List of message dicts
                - last_model_used: str or None
                - total_tokens: int
        """
        # Load messages (existing logic)
        messages = await self._load_from_db(conversation_id, db)
        
        # Get last assistant message to find which model was used
        last_assistant_msg = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .filter(Message.role == "assistant")\
            .order_by(Message.created_at.desc())\
            .first()
        
        last_model = last_assistant_msg.model_used if last_assistant_msg else None
        
        return {
            "messages": messages,
            "last_model_used": last_model,
            "total_tokens": sum(m.get("token_count", 0) for m in messages)
        }
```

#### 3. Hybrid Orchestrator Update (`app/orchestrator/hybrid_router.py`)

**Add previous_model parameter:**

```python
class HybridOrchestrator:
    async def route(
        self, 
        prompt: str,
        previous_model: Optional[str] = None
    ) -> OrchestrationResult:
        """
        Route a prompt using hybrid orchestration.
        
        Args:
            prompt: User prompt to route
            previous_model: Model used in previous turn (for continuity)
        
        Returns:
            OrchestrationResult with final model decision
        """
        reasoning = {
            "prompt_preview": prompt[:100],
            "previous_model": previous_model,
            "steps": [],
        }

        # Step 1: Model registry routing WITH context
        model_decision = self.model_registry.route(
            prompt,
            context={
                "previous_model": previous_model
            }
        )
        
        reasoning["steps"].append({
            "stage": "model_registry",
            "model": model_decision.model,
            "confidence": model_decision.confidence,
            "reason": model_decision.reason,
            "continuity_applied": previous_model is not None
        })
        
        # ... rest of routing logic unchanged ...
```

#### 4. Model Registry Enhancement (`app/orchestrator/model_registry.py`)

**Apply continuity bonus:**

```python
from app.config import settings

class ModelRegistry:
    def route(
        self, 
        prompt: str, 
        context: Optional[dict] = None
    ) -> RoutingDecision:
        """Route with conversation context awareness."""
        
        previous_model = context.get("previous_model") if context else None
        continuity_bonus = settings.CONTINUITY_BONUS if settings.CONTINUITY_ENABLED else 0
        
        matches = []
        logger.info(f"🔍 RULE-BASED ROUTING: Evaluating {len(self.models)} models")
        if previous_model:
            logger.info(f"🔗 Previous model: {previous_model} (bonus: +{continuity_bonus})")
        
        # Evaluate each model
        for model in self.models:
            if not model.enabled:
                continue
            
            try:
                should_route, confidence, reason = model.should_route_to_me(
                    prompt, context
                )
                
                # Apply continuity bonus to previous model
                original_confidence = confidence
                bonus_applied = False
                
                if previous_model and model.model_id == previous_model and should_route:
                    confidence = min(confidence + continuity_bonus, 0.99)
                    bonus_applied = True
                    reason = f"[Continuing] {reason}"
                    
                    logger.info(
                        f"🔗 Continuity bonus: {model.name} "
                        f"{original_confidence:.2f} → {confidence:.2f}"
                    )

                logger.info(
                    f"🔍   ↳ {model.name}: should_route={should_route}, "
                    f"confidence={confidence:.2f}"
                    + (f" (bonus: +{continuity_bonus:.2f})" if bonus_applied else "")
                )

                if should_route:
                    matches.append({
                        "model": model,
                        "model_id": model.model_id,
                        "priority": model.priority,
                        "confidence": confidence,
                        "original_confidence": original_confidence,
                        "bonus_applied": bonus_applied,
                        "reason": reason,
                    })
                    
            except Exception as e:
                logger.error(f"Error evaluating model {model.name}: {e}", exc_info=True)
        
        # Select best match (same logic, but with boosted confidence)
        if not matches:
            logger.info("🔍 ⚠️  NO MODELS MATCHED")
            return RoutingDecision(
                model="",
                confidence=0.0,
                reason="No models matched the prompt",
                requires_llm_classification=True,
            )
        
        best_match = sorted(
            matches,
            key=lambda m: (m["priority"], m["confidence"]),
            reverse=True,
        )[0]
        
        logger.info(
            f"🔍 ✅ SELECTED: {best_match['model'].name} "
            f"(priority={best_match['priority']}, confidence={best_match['confidence']:.2f}"
            + (f", with continuity bonus" if best_match['bonus_applied'] else "") + ")"
        )
        
        return RoutingDecision(
            model=best_match["model_id"],
            confidence=best_match["confidence"],
            reason=f"{best_match['model'].name}: {best_match['reason']}",
            requires_llm_classification=False,
        )
```

#### 5. Process Router Update (`app/api/process_router.py`)

**Pass previous model to orchestrator:**

```python
@router.post("", response_model=ProcessResponse)
async def process(
    request: ProcessRequest,
    user=Depends(verify_api_key_header),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    # ... existing setup code ...
    
    # Load conversation context
    context_data = await context_manager.get_conversation_context(
        conversation_id, db
    )
    
    context_messages = context_data["messages"]
    previous_model = context_data["last_model_used"]
    total_tokens = context_data["total_tokens"]
    
    logger.info(
        f"[{request_id}] Conversation context: "
        f"{len(context_messages)} messages, "
        f"previous_model={previous_model}"
    )
    
    # ... tool execution ...
    
    # Step 2: Route to model WITH previous model context
    logger.info(f"[{request_id}] Routing prompt to model")
    
    from app.main import orchestrator
    
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )
    
    # Route with previous model for continuity
    orchestration_result = await orchestrator.route(
        modified_prompt,
        previous_model=previous_model
    )
    model_to_use = orchestration_result.model
    
    logger.info(
        f"[{request_id}] Routed to model: {model_to_use} "
        f"(confidence: {orchestration_result.confidence:.2f})"
    )
    
    # ... rest of processing ...
```

#### 6. Updated ProcessRequest Schema (`app/models/schemas.py`)

**Add optional force_model parameter:**

```python
class ProcessRequest(BaseModel):
    """Schema for /process endpoint request."""
    prompt: str = Field(..., min_length=1, description="User prompt to process")
    model: Optional[str] = None  # Deprecated: use force_model instead
    conversation_id: Optional[str] = None
    force_model: Optional[str] = Field(
        None, 
        description="Force routing to specific model (overrides automatic routing)"
    )
```

**Handle force_model in process endpoint:**

```python
# In process_router.py, before routing:

if request.force_model:
    # User explicitly requested a specific model
    logger.info(f"[{request_id}] Force model requested: {request.force_model}")
    model_to_use = request.force_model
else:
    # Normal routing with continuity
    orchestration_result = await orchestrator.route(
        modified_prompt,
        previous_model=previous_model
    )
    model_to_use = orchestration_result.model
```

#### 7. Updated ProcessResponse Schema

**Add routing metadata:**

```python
class ProcessResponse(BaseModel):
    """Schema for /process endpoint response."""
    request_id: str
    conversation_id: Optional[str]
    model_used: str
    routing_reason: Optional[str] = Field(
        None,
        description="Explanation of why this model was selected"
    )
    continuity_applied: bool = Field(
        default=False,
        description="Whether continuity bonus was applied in routing"
    )
    prompt: str
    response: str
    execution_time_ms: float
    tools_executed: list[dict]
    tool_flags: dict[str, list[str]]
    context_used: int
    total_tokens: Optional[int]
```

---

### Behavior Examples

#### Example 1: Image Generation Task Continuation ✓

```
Turn 1:
User: "Draw an image of a ball"

Routing:
  Image Generator: 0.95 (keywords: draw, image)
  General Text: 0.50 (default)
→ Selected: Image Generator (0.95)
  
Response:
{
  "model_used": "ollama/stable-diffusion",
  "routing_reason": "Image Generator: Image generation request detected",
  "continuity_applied": false
}

---

Turn 2:
User: "Make it blue"

Routing (without bonus):
  Image Generator: 0.60 (weak keywords)
  General Text: 0.50 (default)

Routing (with bonus):
  Image Generator: 0.75 (0.60 + 0.15 continuity)
  General Text: 0.50 (no bonus)
→ Selected: Image Generator (0.75)

Response:
{
  "model_used": "ollama/stable-diffusion",
  "routing_reason": "Image Generator: [Continuing] Image request detected",
  "continuity_applied": true
}
```

#### Example 2: Genuine Topic Switch ✓

```
Turn 1:
User: "Draw an image of a ball"
→ Image Generator (0.95)

Turn 2:
User: "Classify the sentiment: This product is terrible!"

Routing (with bonus):
  Classifier: 0.90 (strong classification keywords)
  Image Generator: 0.15 (0.00 + 0.15 continuity, but no match)
→ Selected: Classifier (0.90)

✓ Correctly switches despite continuity bonus
```

#### Example 3: Force Model Override ✓

```
Request:
{
  "prompt": "Make it blue",
  "conversation_id": "...",
  "force_model": "ollama/llama2"
}

→ Skips routing entirely, uses forced model

Response:
{
  "model_used": "ollama/llama2",
  "routing_reason": "User specified model",
  "continuity_applied": false
}
```

---

### Future UX Enhancement: User-Friendly Model Categories

**POC:** Direct model IDs (`force_model: "ollama/stable-diffusion"`)

**Future:** User-friendly categories mapped to models:

```python
# Category → Model mapping
MODEL_CATEGORIES = {
    "image_creation": "ollama/stable-diffusion",
    "image_generation": "ollama/stable-diffusion",
    "text_composition": "ollama/llama2",
    "writing": "ollama/llama2",
    "classification": "ollama/llama2",
    "voice_transcription": "ollama/whisper",
    "speech_to_text": "ollama/whisper",
}

# API accepts category or model ID
class ProcessRequest(BaseModel):
    force_model: Optional[str] = Field(
        None,
        description="Model ID (e.g., 'ollama/llama2') or category (e.g., 'image_creation')"
    )
```

**Frontend can provide user-friendly options:**
```
[ ] Text Composition
[ ] Image Creation
[x] Voice Transcription
[ ] Classification
[ ] Custom (specify model)
```

---

### Configuration Options

Add to `app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Contextual Routing
    CONTINUITY_BONUS: float = 0.15  # Confidence boost for previous model
    CONTINUITY_ENABLED: bool = True  # Enable/disable continuity routing
    CONTINUITY_MIN_CONFIDENCE: float = 0.10  # Only apply if model has some match
```

---

### Testing Strategy

#### Unit Tests (`tests/test_contextual_routing.py`)

```python
def test_continuity_bonus_applied():
    """Test continuity bonus boosts previous model."""
    # Given: Previous model was Image Generator
    # When: New prompt has weak image match
    # Then: Continuity bonus should make it win

def test_topic_switch_overrides_bonus():
    """Test strong new match beats continuity bonus."""
    # Given: Previous model was Image Generator
    # When: New prompt is strong classification request
    # Then: Should switch to Classifier

def test_force_model_bypasses_routing():
    """Test force_model overrides all routing logic."""
    # Given: Any conversation state
    # When: force_model is specified
    # Then: Use forced model, skip routing

def test_no_previous_model():
    """Test first message in conversation."""
    # Given: No previous messages
    # When: Routing first message
    # Then: No bonus applied, normal routing
```

#### Integration Tests (`tests/test_conversation_continuity.py`)

```python
async def test_multi_turn_image_task():
    """Test image generation task spanning multiple turns."""
    # Turn 1: "Draw a ball" → Image Gen
    # Turn 2: "Make it blue" → Image Gen (continuity)
    # Turn 3: "Add shadows" → Image Gen (continuity)

async def test_topic_switch_mid_conversation():
    """Test switching between different task types."""
    # Turn 1: "Draw a ball" → Image Gen
    # Turn 2: "Classify this: great product" → Classifier (switch)
    # Turn 3: "What about: terrible product" → Classifier (new continuity)
```

---

### Logging Examples

With enhanced logging, users will see:

```
INFO - 🔍 RULE-BASED ROUTING: Evaluating 4 models
INFO - 🔗 Previous model: ollama/stable-diffusion (bonus: +0.15)
INFO - 🔍 Checking model: Llama2 Classifier (priority=90, enabled=True)
INFO - 🔍   ↳ Llama2 Classifier: should_route=False, confidence=0.00
INFO - 🔍 Checking model: Voice to Text (priority=88, enabled=True)
INFO - 🔍   ↳ Voice to Text: should_route=False, confidence=0.00
INFO - 🔍 Checking model: Image Generator (priority=85, enabled=True)
INFO - 🔗 Continuity bonus: Image Generator 0.60 → 0.75
INFO - 🔍   ↳ Image Generator: should_route=True, confidence=0.75 (bonus: +0.15)
INFO - 🔍 Checking model: Llama2 General (priority=50, enabled=True)
INFO - 🔍   ↳ Llama2 General: should_route=True, confidence=0.50
INFO - 🔍 ✅ SELECTED: Image Generator (priority=85, confidence=0.75, with continuity bonus)
```

---

### Impact on Implementation Timeline

**Added to existing phases:**

- **Phase 2** (Context Manager): +1 day for last_model_used tracking
- **Phase 4** (API Integration): +2 days for continuity logic + force_model
- **Phase 5** (Testing): +1 day for continuity tests

**Total added time:** ~4 days  
**Revised timeline:** 3 weeks + 4 days ≈ **3.5 weeks**

---

### Summary

This enhancement ensures conversation continuity while maintaining flexibility:

✅ **Continuity bonus (+0.15)** keeps tasks on the right model  
✅ **Strong topic switches** still work (high confidence overrides bonus)  
✅ **User control** via force_model (POC) → categories (future)  
✅ **Transparent logging** for debugging and user feedback  
✅ **Simple implementation** with minimal overhead  

The system now handles multi-turn tasks naturally while remaining flexible enough to switch when needed.

