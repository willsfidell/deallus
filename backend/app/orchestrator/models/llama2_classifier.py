"""Llama2 Classifier model definition."""

from typing import Optional, Tuple

from app.orchestrator.model_base import BaseModelDefinition


class Llama2ClassifierModel(BaseModelDefinition):
    """
    Classification-specific model.

    Specialized for tasks like sentiment analysis, intent detection,
    categorization, and similar classification problems.
    """

    @property
    def name(self) -> str:
        """Human-readable name."""
        return "Llama2 Classifier"

    @property
    def model_id(self) -> str:
        """Model identifier for LLM service."""
        return "ollama/llama2"

    @property
    def priority(self) -> int:
        """High priority - classification is specific."""
        return 90

    @property
    def description(self) -> str:
        """Description of the model."""
        return "Specialized for classification, sentiment analysis, intent detection, and categorization tasks"

    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """
        Route to this model for classification tasks.

        Matches classification-specific keywords with high confidence.
        If keywords are present, returns True with high confidence.
        Otherwise returns False.

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            Tuple of (should_route, confidence, reason)
        """
        prompt_lower = prompt.lower()

        # Classification keywords - high confidence if present
        classification_keywords = [
            "classify",
            "categorize",
            "category",
            "categories",
            "classification",
            "sentiment",
            "emotion",
            "intent",
            "predict",
            "prediction",
            "label",
            "annotation",
            "classify me",
        ]

        if any(keyword in prompt_lower for keyword in classification_keywords):
            return (True, 0.90, "Classification keywords detected")

        # Not a classification request
        return (False, 0.0, "Not a classification request")
