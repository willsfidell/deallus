# Test Models Added to Deallus

For testing purposes, two new model definitions have been added to demonstrate multi-modal capabilities:

## 1. Image Generator Model

**File:** `backend/app/orchestrator/models/image_generator.py`

### Purpose
Demonstrates image generation routing (e.g., DALL-E, Stable Diffusion)

### Configuration
- **Name:** Image Generator
- **Model ID:** `ollama/stable-diffusion`
- **Priority:** 85
- **Status:** **DISABLED** (by default)
- **Description:** Specialized for image generation, creation, and visual content production

### How It Works
Detects image generation requests by looking for:
- Image keywords: "generate image", "create image", "draw", "paint", "illustrate", etc.
- Art styles: "oil painting", "watercolor", "sketch", "digital art", "photorealistic", etc.

### Confidence Scoring
| Condition | Confidence | Example |
|-----------|-----------|---------|
| Image keyword + Art style | 0.95 | "Create oil painting of sunset" |
| Image keyword only | 0.85 | "Generate an image of cats" |
| Art style only | 0.65 | "I like watercolor paintings" |
| No match | 0.0 | (no routing) |

### Test Prompts
```
✅ "Generate an image of a sunset" → 0.85
✅ "Create artwork in oil painting style" → 0.95
✅ "Draw a picture of a cat" → 0.85
✅ "Render a photorealistic car" → 0.95
✅ "Design a logo for my company" → 0.85
❌ "What is an image?" → 0.0 (falls through to general model)
```

### To Enable
1. Edit `backend/app/orchestrator/models/image_generator.py`
2. Change `enabled` property to `return True`
3. Restart: `docker compose up -d --build`

---

## 2. Voice-to-Text Model

**File:** `backend/app/orchestrator/models/voice_to_text.py`

### Purpose
Demonstrates speech recognition routing (e.g., Whisper, speech-to-text APIs)

### Configuration
- **Name:** Voice to Text
- **Model ID:** `ollama/whisper`
- **Priority:** 88
- **Status:** **DISABLED** (by default)
- **Description:** Specialized for speech recognition, audio transcription, and voice-to-text conversion

### How It Works
Detects voice-to-text requests by looking for:
- Voice keywords: "transcribe", "speech to text", "recognize speech", "convert voice", etc.
- Audio formats: "mp3", "wav", "audio file", "voice recording", etc.
- Speech-related: "pronunciation", "how to pronounce", "accent", etc.

### Confidence Scoring
| Condition | Confidence | Example |
|-----------|-----------|---------|
| Voice keyword + Audio format | 0.95 | "Transcribe this MP3 file" |
| Voice keyword only | 0.90 | "Convert speech to text" |
| Audio format only | 0.70 | "Process this WAV file" |
| Speech-related | 0.60 | "How to pronounce this word?" |
| No match | 0.0 | (no routing) |

### Test Prompts
```
✅ "Transcribe this audio file to text" → 0.95
✅ "Convert speech to text from recording" → 0.95
✅ "Recognize speech with audio/mp3" → 0.95
✅ "How do you pronounce that?" → 0.60
❌ "What is voice?" → 0.0 (falls through to general model)
```

### To Enable
1. Edit `backend/app/orchestrator/models/voice_to_text.py`
2. Change `enabled` property to `return True`
3. Restart: `docker compose up -d --build`

---

## Enabling for Testing

### Option 1: Enable Individually

Edit each model file and change:
```python
@property
def enabled(self) -> bool:
    return True  # Was: return False
```

### Option 2: Enable All Test Models

Quick way to enable both:
```bash
sed -i 's/return False  # Disabled/return True  # Enabled/g' \
  backend/app/orchestrator/models/image_generator.py \
  backend/app/orchestrator/models/voice_to_text.py

docker compose up -d --build
```

### Option 3: Keep Disabled (Recommended for Now)

The models are set to disabled by default. This is safe for production as they won't interfere with routing. To test:

```bash
cd backend
python -c "
from app.orchestrator.model_registry import ModelRegistry
registry = ModelRegistry()
registry.discover_models()
print(f'Discovered {len(registry.models)} models')
for m in registry.models:
    print(f'  {m.priority:2d} | {m.name:25s} | {\"✓\" if m.enabled else \"✗\"}')
"
```

---

## How to Test Routing

### When Disabled (Current)
- New models are discovered but skipped during routing
- Requests fall through to enabled models (Classifier, General)
- No impact on existing routing

### When Enabled
- Image requests route to Image Generator (priority 85)
- Voice requests route to Voice-to-Text (priority 88)
- Other requests route normally

Example with both enabled:
```
"Create a watercolor painting" 
  → Image Generator (0.95, priority 85) ✓

"Transcribe this MP3 to text"
  → Voice-to-Text (0.95, priority 88) ✓

"Classify this text"
  → Llama2 Classifier (0.90, priority 90) ✓

"Tell me something interesting"
  → Llama2 General (0.50, priority 50) ✓
```

---

## Files Added

```
backend/app/orchestrator/models/
├── image_generator.py      (116 lines)
└── voice_to_text.py        (118 lines)
```

Both files follow the same structure as existing models:
- Inherit from `BaseModelDefinition`
- Implement required properties: `name`, `model_id`, `priority`
- Implement `should_route_to_me()` with custom routing logic
- Optional `enabled` property (defaults to `True`)

---

## Integration Points

These models integrate seamlessly with:
- Model registry auto-discovery ✓
- Priority-based routing ✓
- Confidence scoring ✓
- LLM classifier fallback ✓
- Existing logging ✓

No changes to core infrastructure needed!

---

## Use Cases for Testing

### 1. Test New Model Type Integration
- Ensure new model types are discovered correctly
- Verify priority ordering (Image 85, Voice 88, Classifier 90)
- Confirm fallback behavior

### 2. Test Multi-Modal Requests
- "Generate an image of a sunset and tell me its history"
- Should trigger Image Generator (0.95) due to keyword matching

### 3. Test Priority Conflicts
- Enable both Image and Voice models
- Verify higher priority gets selected when both match

### 4. Test Confidence Fallback
- Enable with lower confidence (e.g., change 0.95 → 0.70)
- Below 0.80 threshold triggers LLM classifier fallback
- Observe fallback behavior in logs

### 5. Test Disabled Model Behavior
- Keep disabled and verify no impact on routing
- Enable and verify routing changes
- Re-disable and confirm revert to previous behavior

---

## Next Steps

Once these are working well:

1. **Add more specialized models**
   - SQL query optimizer (for database queries)
   - API documentation generator
   - Test case generator
   - Bug fix suggester

2. **Implement real model integrations**
   - Replace "ollama/stable-diffusion" with real service
   - Replace "ollama/whisper" with real Whisper service
   - Add health checks for model availability

3. **Add context-aware routing**
   - Use user preferences from context
   - Track successful routing decisions
   - Optimize priorities based on usage patterns

4. **Monitor and optimize**
   - Track which models are used most
   - Measure routing accuracy
   - Adjust confidence thresholds

---

## Summary

The two new test models demonstrate:
- ✅ How easy it is to add multi-modal capabilities
- ✅ Priority-based routing with smart confidence scoring
- ✅ Graceful handling of disabled models
- ✅ Fallback to existing models when disabled

They're production-ready but disabled by default for safety. Enable them to test the routing system with real-world multi-modal scenarios!
