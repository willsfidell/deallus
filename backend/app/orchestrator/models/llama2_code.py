"""Llama2 Code Specialist model definition (disabled example).

This is an example of how to create a specialized model for specific tasks.
It's disabled by default - enable it only if the actual model is available.
"""

from typing import Optional, Tuple

from app.orchestrator.model_base import BaseModelDefinition


class Llama2CodeModel(BaseModelDefinition):
    """
    Code-specific model (example - disabled by default).

    This model would be specialized for code generation tasks.
    In a real setup, you'd point to a code-optimized model like CodeLlama.

    This example shows how to:
    1. Disable a model without deleting the file
    2. Route to it only for strong code indicators
    3. Set different priorities
    """

    @property
    def name(self) -> str:
        """Human-readable name."""
        return "Llama2 Code Specialist"

    @property
    def model_id(self) -> str:
        """Model identifier - would be a code-specific model if enabled."""
        return "ollama/codellama:7b"

    @property
    def priority(self) -> int:
        """High priority for code requests (but only if enabled)."""
        return 80

    @property
    def description(self) -> str:
        """Description of the model."""
        return "Specialized for code generation, debugging, and technical implementation"

    @property
    def enabled(self) -> bool:
        """Disabled by default - enable only if codellama is available."""
        return False

    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """
        Route to this model only for strong code generation requests.

        This is more selective than the general model - it requires
        explicit code generation indicators plus language keywords.

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            Tuple of (should_route, confidence, reason)
        """
        prompt_lower = prompt.lower()

        # Strong code generation indicators
        code_patterns = [
            "write code",
            "write a function",
            "write a class",
            "implement",
            "create a function",
            "create a class",
            "show me code",
        ]

        language_keywords = [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "rust",
            "go",
            "php",
            "sql",
        ]

        has_code_pattern = any(p in prompt_lower for p in code_patterns)
        has_language = any(lang in prompt_lower for lang in language_keywords)

        # Both pattern and language: very high confidence
        if has_code_pattern and has_language:
            return (
                True,
                0.95,
                "Strong code generation request with language specified",
            )

        # Just one of them: medium-high confidence
        if has_code_pattern or has_language:
            return (True, 0.75, "Potential code generation request")

        # Not a code request
        return (False, 0.0, "Not a code generation request")
