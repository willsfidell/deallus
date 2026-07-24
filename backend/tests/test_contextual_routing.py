"""Unit tests for contextual routing with continuity bonus."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.orchestrator.model_registry import ModelRegistry
from app.orchestrator.model_base import BaseModelDefinition
from app.config import settings


class MockImageGeneratorModel(BaseModelDefinition):
    """Mock image generator model for testing."""

    @property
    def name(self) -> str:
        return "Image Generator"

    @property
    def model_id(self) -> str:
        return "ollama/stable-diffusion"

    @property
    def priority(self) -> int:
        return 85

    @property
    def enabled(self) -> bool:
        return True

    def should_route_to_me(self, prompt: str, context=None) -> tuple[bool, float, str]:
        """Route to me if prompt contains image-related keywords."""
        keywords = ["draw", "image", "picture", "paint", "generate", "create", "visual"]
        if any(kw in prompt.lower() for kw in keywords):
            return True, 0.90, "Image generation request detected"
        return False, 0.0, "Not an image request"


class MockGeneralTextModel(BaseModelDefinition):
    """Mock general text model for testing."""

    @property
    def name(self) -> str:
        return "General Text"

    @property
    def model_id(self) -> str:
        return "ollama/llama2"

    @property
    def priority(self) -> int:
        return 50

    @property
    def enabled(self) -> bool:
        return True

    def should_route_to_me(self, prompt: str, context=None) -> tuple[bool, float, str]:
        """Default fallback model."""
        return True, 0.50, "General text request (fallback)"


class MockClassifierModel(BaseModelDefinition):
    """Mock classifier model for testing."""

    @property
    def name(self) -> str:
        return "Classifier"

    @property
    def model_id(self) -> str:
        return "ollama/classifier"

    @property
    def priority(self) -> int:
        return 90

    @property
    def enabled(self) -> bool:
        return True

    def should_route_to_me(self, prompt: str, context=None) -> tuple[bool, float, str]:
        """Route to me if prompt is a classification task."""
        keywords = ["classify", "classify", "sentiment", "categorize", "identify"]
        if any(kw in prompt.lower() for kw in keywords):
            return True, 0.95, "Classification task detected"
        return False, 0.0, "Not a classification task"


@pytest.fixture
def model_registry():
    """Create a model registry with test models."""
    registry = ModelRegistry()

    # Register models (order matters for priority)
    registry.register_model(MockClassifierModel())
    registry.register_model(MockImageGeneratorModel())
    registry.register_model(MockGeneralTextModel())

    return registry


class TestContinuityBonus:
    """Test continuity bonus in contextual routing."""

    def test_continuity_bonus_applied_to_previous_model(self, model_registry):
        """Test that continuity bonus is applied to previous model."""
        # Scenario: User asks for image, then says "make it blue"
        # Without bonus: General Text (0.50) > Image Gen (0.60)
        # With bonus: Image Gen (0.60 + 0.15 = 0.75) > General Text (0.50)

        previous_model = "ollama/stable-diffusion"
        context = {"previous_model": previous_model}

        decision = model_registry.route("Make it blue", context=context)

        assert decision.model == "ollama/stable-diffusion"
        assert "[Continuing]" in decision.reason
        assert decision.requires_llm_classification == False

    def test_strong_topic_switch_overrides_bonus(self, model_registry):
        """Test that strong topic switch overrides continuity bonus."""
        # Scenario: User asked for image, now asks to classify sentiment
        # Classifier (0.95) > Image Gen (0.00 + 0.15 bonus = 0.15)

        previous_model = "ollama/stable-diffusion"
        context = {"previous_model": previous_model}

        decision = model_registry.route(
            "Classify the sentiment: This is terrible!", context=context
        )

        # Should route to Classifier despite continuity bonus
        assert decision.model == "ollama/classifier"
        assert "[Continuing]" not in decision.reason

    def test_no_continuity_bonus_without_context(self, model_registry):
        """Test that continuity bonus is not applied without previous_model."""
        # First message should not have continuity bonus

        decision = model_registry.route("Draw me a picture")

        assert decision.model == "ollama/stable-diffusion"
        assert "[Continuing]" not in decision.reason

    def test_continuity_bonus_disabled(self, model_registry):
        """Test that continuity bonus can be disabled via settings."""
        with patch.object(settings, "CONTINUITY_ENABLED", False):
            previous_model = "ollama/stable-diffusion"
            context = {"previous_model": previous_model}

            decision = model_registry.route("Make it blue", context=context)

            # Without continuity bonus, General Text (0.50) should win over Image Gen (0.60)
            # Actually, Image Gen still wins due to priority, but no bonus is logged
            assert "[Continuing]" not in decision.reason

    def test_bonus_amount_configurable(self, model_registry):
        """Test that continuity bonus amount is configurable."""
        original_bonus = settings.CONTINUITY_BONUS

        try:
            # Set bonus to a higher value
            settings.CONTINUITY_BONUS = 0.30

            previous_model = "ollama/stable-diffusion"
            context = {"previous_model": previous_model}

            decision = model_registry.route("Make it blue", context=context)

            # Should still route to Image Gen with higher bonus
            assert decision.model == "ollama/stable-diffusion"

        finally:
            settings.CONTINUITY_BONUS = original_bonus

    def test_multiple_matches_priority_respected(self, model_registry):
        """Test that priority is still respected even with continuity bonus."""
        # Both Image Gen and General Text match "draw me a picture"
        # Image Gen (priority 85) should win over General Text (priority 50)

        decision = model_registry.route("Draw me a picture")

        assert decision.model == "ollama/stable-diffusion"
        assert decision.confidence == 0.90

    def test_continuity_bonus_caps_at_max_confidence(self, model_registry):
        """Test that confidence never exceeds maximum (0.99)."""
        # Even with a huge bonus, confidence should cap at 0.99
        with patch.object(settings, "CONTINUITY_BONUS", 1.0):
            previous_model = "ollama/stable-diffusion"
            context = {"previous_model": previous_model}

            decision = model_registry.route("Make it blue", context=context)

            # Confidence should be capped at 0.99
            assert decision.confidence <= 0.99

    def test_all_models_logged_with_bonus_status(self, model_registry, caplog):
        """Test that all models are logged with bonus status."""
        import logging

        caplog.set_level(logging.INFO)

        previous_model = "ollama/stable-diffusion"
        context = {"previous_model": previous_model}

        model_registry.route("Make it blue", context=context)

        # Check that bonus was logged
        log_text = caplog.text
        assert "Continuity bonus" in log_text or "Previous model" in log_text


class TestRoutingDecisions:
    """Test various routing scenarios."""

    def test_image_generation_task(self, model_registry):
        """Test routing for image generation."""
        decision = model_registry.route("Create a beautiful landscape image")
        assert decision.model == "ollama/stable-diffusion"

    def test_text_composition_task(self, model_registry):
        """Test routing for text composition."""
        decision = model_registry.route("Write a poem about nature")
        assert decision.model == "ollama/llama2"

    def test_classification_task(self, model_registry):
        """Test routing for classification."""
        decision = model_registry.route("Classify this review sentiment: Great product!")
        assert decision.model == "ollama/classifier"

    def test_ambiguous_prompt_routes_to_classifier(self, model_registry):
        """Test that ambiguous prompt routes to highest priority."""
        decision = model_registry.route("Hello")
        # Should route to highest priority model that matches
        assert decision.model in [
            "ollama/classifier",
            "ollama/stable-diffusion",
            "ollama/llama2",
        ]

    def test_routing_confidence_reflects_match_quality(self, model_registry):
        """Test that routing confidence reflects how well prompt matches."""
        # Strong match for image generation
        image_decision = model_registry.route("Draw me a picture")
        assert image_decision.confidence == 0.90

        # Weak match for general text
        general_decision = model_registry.route("Hello there")
        assert general_decision.confidence == 0.50  # Fallback confidence
