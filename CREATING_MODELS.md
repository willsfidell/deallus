# Creating Custom Model Definitions for Deallus

## Overview

Deallus uses a **pluggable model definition system** to determine which model should handle each user request. Model definitions are simple Python modules that you can add to the `app/orchestrator/models/` directory.

Each model definition:
- Specifies **when** it should handle a request (via custom validators)
- Defines its **priority** (which model gets tried first)
- Returns a **confidence score** for the routing decision

The system automatically discovers and registers new models on startup—no configuration needed!

---

## Quick Start: Create Your First Model

### Step 1: Create a New File

Create a new Python file in `backend/app/orchestrator/models/`:

```bash
touch backend/app/orchestrator/models/my_custom_model.py
```

### Step 2: Implement the Model

```python
"""Custom model for my special use case."""

from typing import Optional, Tuple
from app.orchestrator.model_base import BaseModelDefinition


class MyCustomModel(BaseModelDefinition):
    """Model for handling my specific task."""

    @property
    def name(self) -> str:
        """Display name for logging."""
        return "My Custom Model"

    @property
    def model_id(self) -> str:
        """Model identifier used by the LLM service."""
        return "ollama/custom-model"

    @property
    def priority(self) -> int:
        """Priority (0-100). Higher = tried first."""
        return 75

    @property
    def description(self) -> str:
        """Human-readable description (optional)."""
        return "Handles specialized tasks for my domain"

    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """
        Determine if this model should handle the prompt.

        Args:
            prompt: User input
            context: Optional context dict with additional information

        Returns:
            (should_route, confidence, reason)
        """
        prompt_lower = prompt.lower()

        # Check for specific keywords
        if "special keyword" in prompt_lower:
            return (True, 0.95, "Exact keyword match")

        if "related topic" in prompt_lower:
            return (True, 0.75, "Related topic detected")

        # Not for this model
        return (False, 0.0, "Not a match for this model")

    @property
    def enabled(self) -> bool:
        """Set to False to disable without deleting the file."""
        return True
```

### Step 3: Restart the Server

```bash
docker compose down
docker compose up -d --build
```

Check the logs to verify your model was discovered:

```bash
docker compose logs aidi_api | grep "Model definitions"
```

---

## Architecture: How It Works

### Model Definition Interface

All models must inherit from `BaseModelDefinition` and implement these abstract methods:

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Display name for logs (e.g., "Llama2 Classifier") |
| `model_id` | str | Model identifier for LLM service (e.g., "ollama/llama2") |
| `priority` | int | Priority 0-100 (higher = tried first) |
| `should_route_to_me()` | method | Returns (bool, float, str) tuple |
| `description` | str | Optional description |
| `enabled` | bool | Whether model is active |

### Routing Algorithm

When a request arrives:

1. **Model Registry** evaluates all enabled models in priority order
2. For each model, calls `should_route_to_me(prompt, context)`
3. Collects all matches (where result[0] == True)
4. **Selects best match** by:
   - Primary: Higher priority
   - Tiebreaker: Higher confidence
5. If best match's confidence < threshold (0.80):
   - Falls back to **LLM classifier**
6. Returns final model to use

### Confidence Scores

Return confidence as a float 0.0-1.0:

- **0.0-0.2**: Low confidence, falls back to LLM classifier
- **0.2-0.5**: Medium-low, likely uses LLM classifier
- **0.5-0.8**: Medium, borderline for fallback
- **0.8-0.95**: High, usually accepted
- **0.95-1.0**: Very high, almost always accepted

Example:
```python
def should_route_to_me(self, prompt: str, context=None):
    prompt_lower = prompt.lower()
    
    # Very specific match
    if "write python code" in prompt_lower:
        return (True, 0.98, "Exact code generation request")
    
    # General match
    if "code" in prompt_lower:
        return (True, 0.60, "Generic code keyword")
    
    # Not a match
    return (False, 0.0, "Not for this model")
```

---

## Advanced Examples

### Example 1: Domain-Specific Model

For medical/legal/finance domain:

```python
class MedicalExpertModel(BaseModelDefinition):
    @property
    def name(self) -> str:
        return "Medical Expert"

    @property
    def model_id(self) -> str:
        return "ollama/medical-expert"

    @property
    def priority(self) -> int:
        return 85  # High priority for medical questions

    def should_route_to_me(self, prompt: str, context=None):
        prompt_lower = prompt.lower()
        
        # Medical keywords
        medical_keywords = [
            "symptom", "disease", "treatment", "medication",
            "diagnosis", "medical", "doctor", "patient",
            "health", "clinical", "disorder"
        ]
        
        if any(kw in prompt_lower for kw in medical_keywords):
            return (True, 0.85, "Medical domain keywords detected")
        
        return (False, 0.0, "Not a medical question")
```

### Example 2: Use Context Information

Leverage context passed from the request:

```python
class PersonalizedModel(BaseModelDefinition):
    @property
    def name(self) -> str:
        return "Personalized Response Model"

    @property
    def priority(self) -> int:
        return 60

    def should_route_to_me(self, prompt: str, context=None):
        prompt_lower = prompt.lower()
        
        # Check user's preferences from context
        if context and context.get("user_level") == "advanced":
            if "technical" in prompt_lower:
                return (True, 0.85, "Advanced user requesting technical content")
        
        # Default behavior
        if "explain simply" in prompt_lower:
            return (True, 0.80, "Request for simplified explanation")
        
        return (False, 0.0, "No personalization needed")
```

### Example 3: Disabled Model (for testing)

Create a model that's visible in code but disabled:

```python
class ExperimentalModel(BaseModelDefinition):
    @property
    def name(self) -> str:
        return "Experimental Model"

    @property
    def model_id(self) -> str:
        return "ollama/experimental"

    @property
    def priority(self) -> int:
        return 95  # Would be high priority if enabled

    @property
    def enabled(self) -> bool:
        return False  # Disabled for now

    def should_route_to_me(self, prompt: str, context=None):
        # This won't be called since enabled=False
        return (True, 0.90, "Experimental model")
```

Enable it later by just changing `enabled` to `True` and restarting.

### Example 4: Complex Scoring Logic

Multi-factor confidence calculation:

```python
class SmartModel(BaseModelDefinition):
    @property
    def name(self) -> str:
        return "Smart Router"

    @property
    def model_id(self) -> str:
        return "ollama/smart"

    @property
    def priority(self) -> int:
        return 70

    def should_route_to_me(self, prompt: str, context=None):
        prompt_lower = prompt.lower()
        score = 0.0
        reasons = []
        
        # Keyword matches (each worth 0.1-0.3)
        if any(kw in prompt_lower for kw in ["code", "function"]):
            score += 0.2
            reasons.append("code keywords")
        
        if any(kw in prompt_lower for kw in ["explain", "why"]):
            score += 0.15
            reasons.append("explanation request")
        
        if len(prompt) > 200:
            score += 0.1
            reasons.append("long prompt")
        
        if score == 0.0:
            return (False, 0.0, "No matching patterns")
        
        return (True, min(score, 0.99), f"Matched: {', '.join(reasons)}")
```

---

## Priority Reference Table

Use these priority ranges as guidelines:

| Range | Use Case |
|-------|----------|
| **90-100** | Highly specific, domain-expert models |
| **70-89** | Specialized models (code, analysis, classification) |
| **50-69** | General-purpose models with some specialization |
| **25-49** | Broad fallback models |
| **0-24** | Default catchall models |

Current models in Deallus:
- **Llama2 Classifier:** priority 90 (classification-specific)
- **Llama2 General:** priority 50 (default fallback)
- **Llama2 Code:** priority 80 (disabled, code-specific)

---

## Testing Your Model

### 1. Local Testing

```python
# In your models file or a test file
from app.orchestrator.model_registry import ModelRegistry

registry = ModelRegistry()
registry.discover_models()

test_prompts = [
    "Your first test prompt",
    "Your second test prompt",
]

for prompt in test_prompts:
    decision = registry.route(prompt)
    print(f"Prompt: {prompt}")
    print(f"  Model: {decision.model}")
    print(f"  Confidence: {decision.confidence:.2f}")
    print()
```

### 2. Docker Logs

After restarting:

```bash
docker compose logs aidi_api | grep "Model definitions"
```

You should see your model listed:
```
Registered model: My Custom Model (model_id: ollama/custom-model, priority: 75)
```

### 3. Process Endpoint

Send a test request through the API and check routing decision in logs:
```bash
curl -X POST http://localhost:8000/api/process \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your test prompt"}'
```

Check logs for routing trace:
```bash
docker compose logs aidi_api | tail -20
```

---

## Troubleshooting

### Model Not Discovered

**Problem:** Your model doesn't appear in startup logs

**Solutions:**
1. Check file is in `app/orchestrator/models/` directory
2. Filename must end with `.py` (not `_backup.py`)
3. Class must inherit from `BaseModelDefinition`
4. Check for import errors in logs: `docker compose logs aidi_api`

### Always Matches Too Broadly

**Problem:** Your model matches too many prompts

**Solution:** Make validators more specific:
```python
# Too broad
if "the" in prompt_lower:  # Too many false positives

# Better
if "classify" in prompt_lower and any(kw in prompt_lower for kw in ["sentiment", "category"]):
```

### Model Never Gets Selected

**Problem:** Other models always match first

**Solutions:**
1. Increase your model's priority (higher number = tried first)
2. Increase confidence scores
3. Make your validators more specific to avoid conflicts

### Confidence Threshold Never Met

**Problem:** Model always falls back to LLM classifier

**Idea:** The fallback threshold is 0.80 by default. Make sure your confidence scores are >= 0.80 for matches you want accepted:
```python
# This will often fall back (too conservative)
if match:
    return (True, 0.70, "Match found")

# Better
if strong_match:
    return (True, 0.85, "Strong match")
```

---

## Best Practices

1. **Be Specific**: Don't match too broadly with your validators
2. **Realistic Confidence**: Confidence should reflect actual confidence in routing decision
3. **Prioritize Carefully**: Higher priority = tried first, but must be domain-specific
4. **Test Locally First**: Test with sample prompts before deploying
5. **Use Descriptions**: Add meaningful descriptions for debugging
6. **Log Reasons**: Return clear reason strings for understanding routing decisions

---

## Model Definition Template

Copy and modify this template for new models:

```python
"""[Description of what this model handles]."""

from typing import Optional, Tuple
from app.orchestrator.model_base import BaseModelDefinition


class [YourModelClassName](BaseModelDefinition):
    """[Docstring: What is this model for?]."""

    @property
    def name(self) -> str:
        return "[Human-readable name]"

    @property
    def model_id(self) -> str:
        return "ollama/[model-name]"

    @property
    def priority(self) -> int:
        return 75  # Adjust as needed

    @property
    def description(self) -> str:
        return "[Describe what prompts this model handles]"

    @property
    def enabled(self) -> bool:
        return True  # Set to False to disable

    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """Route logic here."""
        prompt_lower = prompt.lower()

        # Your routing logic:
        # 1. Check keywords
        # 2. Calculate confidence
        # 3. Return (should_route, confidence, reason)

        return (False, 0.0, "Not a match for this model")
```

---

## Deployment Checklist

- [ ] Model file created in `app/orchestrator/models/`
- [ ] Class inherits from `BaseModelDefinition`
- [ ] All abstract methods implemented
- [ ] Tested locally with sample prompts
- [ ] Appropriate priority set (0-100)
- [ ] Confidence scores realistic (0.0-1.0)
- [ ] Model logs meaningful reason strings
- [ ] Docker image rebuilt: `docker compose up -d --build`
- [ ] Logs verified: `docker compose logs aidi_api | grep "Model definitions"`
- [ ] API tested with sample requests

---

## Questions?

Refer to the example models in `app/orchestrator/models/` for reference implementations:
- `llama2_classifier.py`: Classification-focused model
- `llama2_general.py`: General fallback model
- `llama2_code.py`: Disabled example model

Good luck! 🚀
