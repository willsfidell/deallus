"""Llama2 General model definition."""

from typing import Optional, Tuple

from app.orchestrator.model_base import BaseModelDefinition


class Llama2GeneralModel(BaseModelDefinition):
    """
    General-purpose text generation model.

    This is the default fallback model for general text tasks like
    analysis, explanation, and other non-specialized requests.
    """

    @property
    def name(self) -> str:
        """Human-readable name."""
        return "Llama2 General"

    @property
    def model_id(self) -> str:
        """Model identifier for LLM service."""
        return "ollama/llama2"

    @property
    def priority(self) -> int:
        """Medium priority - default fallback."""
        return 50

    @property
    def description(self) -> str:
        """Description of the model."""
        return "General-purpose text generation for analysis, explanations, and discussions"

    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """
        Route to this model for general text tasks.

        Matches:
        - Analysis requests (analyze, explain, summary, compare, etc.)
        - Code/technical questions (lower confidence)
        - Default fallback for unmatched requests

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            Tuple of (should_route, confidence, reason)
        """
        prompt_lower = prompt.lower()

        # Rule 1: Analysis requests (higher confidence)
        analysis_keywords = [
            "analyze",
            "analysis",
            "explain",
            "explanation",
            "summary",
            "summarize",
            "compare",
            "contrast",
            "discuss",
            "evaluate",
            "assess",
            "what is",
            "how does",
            "why",
        ]
        if any(keyword in prompt_lower for keyword in analysis_keywords):
            return (True, 0.85, "Analysis request detected")

        # Rule 2: Code/Technical requests (medium confidence)
        code_keywords = [
            "code",
            "function",
            "method",
            "class",
            "import",
            "python",
            "javascript",
            "java",
            "sql",
            "error",
            "debug",
            "fix",
            "implement",
            "algorithm",
        ]
        if any(keyword in prompt_lower for keyword in code_keywords):
            return (True, 0.80, "Code/technical request detected")

        # Rule 3: Question-based requests
        if prompt_lower.strip().endswith("?") and len(prompt) > 10:
            return (True, 0.75, "Question format detected")

        # Default: Accept as general request with low confidence
        return (True, 0.50, "Default general text model")
