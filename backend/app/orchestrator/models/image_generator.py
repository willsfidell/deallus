"""Image generation model definition."""

from typing import Optional, Tuple

from app.orchestrator.model_base import BaseModelDefinition


class ImageGenerationModel(BaseModelDefinition):
    """
    Image generation specialized model.

    Handles requests for creating, generating, or producing images.
    This is a test model to demonstrate multi-modal capability.
    """

    @property
    def name(self) -> str:
        """Human-readable name."""
        return "Image Generator"

    @property
    def model_id(self) -> str:
        """Model identifier for image generation service."""
        return "ollama/stable-diffusion"

    @property
    def priority(self) -> int:
        """High priority for image generation (specific task)."""
        return 85

    @property
    def description(self) -> str:
        """Description of the model."""
        return "Specialized for image generation, creation, and visual content production"

    @property
    def enabled(self) -> bool:
        """Enabled for testing - disable when not needed."""
        return True

    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """
        Route to this model for image generation tasks.

        Matches:
        - Explicit image creation requests (generate, create, draw, etc.)
        - Visual content descriptors
        - Art and design requests

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            Tuple of (should_route, confidence, reason)
        """
        prompt_lower = prompt.lower()

        # Strong image generation keywords
        image_keywords = [
            "generate image",
            "create image",
            "draw",
            "paint",
            "illustrate",
            "picture",
            "image",
            "visual",
            "artwork",
            "design",
            "render",
            "generate art",
            "create art",
            "create a picture",
            "create artwork",
            "show me",
            "generate a",
            "create a",
        ]

        # Art style keywords (increases confidence)
        style_keywords = [
            "oil painting",
            "watercolor",
            "sketch",
            "digital art",
            "photorealistic",
            "cartoon",
            "anime",
            "abstract",
            "surreal",
            "steampunk",
        ]

        # Check for image keywords
        has_image_keyword = any(kw in prompt_lower for kw in image_keywords)
        has_style_keyword = any(kw in prompt_lower for kw in style_keywords)

        # Both image keyword and style: very high confidence
        if has_image_keyword and has_style_keyword:
            return (
                True,
                0.95,
                "Image generation with art style specified",
            )

        # Just image keyword: high confidence
        if has_image_keyword:
            return (True, 0.85, "Image generation request detected")

        # Just style keyword (could be image-related): medium confidence
        if has_style_keyword:
            return (True, 0.65, "Art style mentioned, possible image request")

        # Not an image generation request
        return (False, 0.0, "Not an image generation request")
