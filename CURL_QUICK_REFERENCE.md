# Deallus API - Quick Reference Guide

**Updated:** July 22, 2026 with Conversation & Contextual Routing Tests

---

## 🚀 Quick Start

```bash
export BASE_URL="http://localhost:8000"
export API_KEY="your_api_key_here"
```

---

## 📋 All Tests Summary

### Original Tests (1-13)
- Health check, user registration, login, API keys
- Classification, explanation, code generation
- PII redaction, tool execution
- Error handling

### Conversation Management (14-19)
- ✅ **Test #14**: Create conversation
- ✅ **Test #15**: List conversations
- ✅ **Test #16**: Get conversation with messages
- ✅ **Test #17**: Update conversation
- ✅ **Test #18**: Clear messages
- ✅ **Test #19**: Archive conversation

### Contextual Routing (20-24)
- ✅ **Test #20**: Initial image generation (continuity = false)
- ✅ **Test #21**: Follow-up message (continuity = true) 🔥
- ✅ **Test #22**: Add detail (context accumulation)
- ✅ **Test #23**: Topic switch (continuity override) 🔥
- ✅ **Test #24**: Force model override

### Complete Workflows & Scripts (25-29)
- ✅ **Test #25**: Full multi-turn workflow script
- ✅ **Test #26**: Response examples
- ✅ **Test #27**: Troubleshooting guide
- ✅ **Test #28**: Performance testing
- ✅ **Test #29**: Automated test suite script

---

## 🔑 Key Tests for Contextual Routing

### Test #20: Initial Request (No Continuity)
```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Draw an image of a red ball",
    "conversation_id": "CONV_ID"
  }' | jq '.'
```
**Look for:** `continuity_applied: false` (first message)

### Test #21: Follow-up (Continuity Applied) ✅
```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Make it blue",
    "conversation_id": "CONV_ID"
  }' | jq '.'
```
**Look for:** 
- `continuity_applied: true` 🔥
- `routing_reason` contains "[Continuing]"
- Same model selected

### Test #23: Topic Switch (Override Continuity) 🔥
```bash
curl -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "prompt": "Classify sentiment: This product is amazing!",
    "conversation_id": "CONV_ID"
  }' | jq '.'
```
**Look for:**
- `continuity_applied: false` (despite bonus)
- Different model selected
- Strong signal overrides continuity

---

## 📊 Key Response Fields

| Field | Type | New | Meaning |
|-------|------|-----|---------|
| `conversation_id` | string | ✅ | Conversation identifier |
| `model_used` | string | - | Which model was selected |
| `routing_reason` | string | ✅ | Why this model was selected |
| `continuity_applied` | bool | ✅ | Whether continuity bonus was applied |
| `context_used` | int | ✅ | Number of previous messages in context |
| `total_tokens` | int | ✅ | Total tokens in context window |

---

## 🎯 Most Important Tests

1. **Test #14** - Create conversation (needed for all multi-turn tests)
2. **Test #20** - First request (baseline)
3. **Test #21** - Follow-up (demonstrates continuity ✅)
4. **Test #23** - Topic switch (demonstrates override ✅)
5. **Test #25** - Full workflow (complete end-to-end)

---

## 🛠️ Helper Commands

### Create Conversation & Save ID
```bash
CONV_ID=$(curl -s -X POST "${BASE_URL}/api/conversations" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"title": "Test"}' | jq -r '.id')
echo "Conversation: $CONV_ID"
```

### Send Message & Check Continuity
```bash
curl -s -X POST "${BASE_URL}/api/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"prompt": "Make it blue", "conversation_id": "'${CONV_ID}'"}' \
  | jq '{model: .model_used, continuity: .continuity_applied, reason: .routing_reason}'
```

### Check Conversation History
```bash
curl -s -X GET "${BASE_URL}/api/conversations/${CONV_ID}" \
  -H "X-API-Key: ${API_KEY}" | jq '.messages | length'
```

---

## 🧪 Full Workflow One-Liner

```bash
# Setup
export BASE_URL="http://localhost:8000"
export API_KEY="your_key"
export CONV=$(curl -s -X POST "${BASE_URL}/api/conversations" -H "X-API-Key: ${API_KEY}" -H "Content-Type: application/json" -d '{"title":"Test"}' | jq -r '.id')

# Test continuity
echo "Initial (no continuity):"
curl -s -X POST "${BASE_URL}/api/process" -H "X-API-Key: ${API_KEY}" -H "Content-Type: application/json" -d "{\"prompt\":\"Draw a ball\",\"conversation_id\":\"${CONV}\"}" | jq '.continuity_applied'

echo "Follow-up (continuity = true):"
curl -s -X POST "${BASE_URL}/api/process" -H "X-API-Key: ${API_KEY}" -H "Content-Type: application/json" -d "{\"prompt\":\"Make it blue\",\"conversation_id\":\"${CONV}\"}" | jq '.continuity_applied'

echo "Topic switch (continuity = false):"
curl -s -X POST "${BASE_URL}/api/process" -H "X-API-Key: ${API_KEY}" -H "Content-Type: application/json" -d "{\"prompt\":\"Classify sentiment: Great!\",\"conversation_id\":\"${CONV}\"}" | jq '.continuity_applied'
```

---

## ✅ Verification Checklist

- [ ] Test #14: Can create conversation
- [ ] Test #15: Can list conversations
- [ ] Test #20: Initial request shows `continuity_applied: false`
- [ ] Test #21: Follow-up shows `continuity_applied: true` ✅
- [ ] Test #23: Topic switch shows `continuity_applied: false` ✅
- [ ] Response includes `routing_reason` field
- [ ] Response includes `context_used` counter
- [ ] Force model override works (Test #24)

---

## 🐛 Debugging

### Check if continuity bonus worked:
```bash
curl -s "..." | jq '.continuity_applied'
# Should be: true (for follow-ups) or false (for new topics)
```

### Check routing decision:
```bash
curl -s "..." | jq '.routing_reason'
# Should explain why model was selected
# Should contain "[Continuing]" for follow-ups
```

### Check context:
```bash
curl -s "..." | jq '.context_used'
# Should increase with each turn (0 → 2 → 4 → etc)
```

---

## 📚 Full Documentation

See `CURL_COMMANDS.md` for:
- All 29 tests with detailed explanations
- Complete workflow scripts
- Response examples
- Troubleshooting guide
- Performance testing
- Automated test suite

---

## 🎓 Key Concepts

**Continuity Bonus**: +0.15 confidence to previous model
- Maintains task continuity ("Draw image" → "Make it blue")
- Strong topic changes still override (high confidence wins)
- Configurable and disableable via settings

**Context Window**: Last 10 messages or 4000 tokens
- Accumulated across turns
- Automatically truncated when full
- Tracked via `context_used` and `total_tokens`

**Routing Decision**: Based on model evaluation
- All models checked in priority order
- Continuity bonus applied to previous model
- Best match selected (priority + confidence)
- Reason provided in response

---

**Last Updated:** July 22, 2026
**Status:** ✅ Ready for testing

See `CURL_COMMANDS.md` for complete test suite.
