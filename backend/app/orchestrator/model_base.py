"""Base class for pluggable model definitions."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BaseModelDefinition(ABC):
    """
    Abstract base class for model definitions.

    Model definitions encapsulate the logic for determining when a specific
    model should handle a user request. Each model has:
    - A priority (higher = tried first)
    - Custom validators to determine if it should handle a prompt
    - Configuration about the model itself

    Subclasses must implement should_route_to_me() with custom logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name of the model.

        Returns:
            str: Display name (e.g., "Llama2 General")
        """
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """
        Actual model identifier used by the LLM service.

        Returns:
            str: Model ID (e.g., "ollama/llama2")
        """
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Priority level for this model (0-100).

        Higher priority models are evaluated first. When multiple models
        match with same priority, the one with highest confidence wins.

        Returns:
            int: Priority level (0-100)
        """
        pass

    @abstractmethod
    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """
        Determine if this model should handle the given prompt.

        This is the core routing logic. Implement custom validators here
        to decide if a prompt matches this model's capabilities.

        Args:
            prompt: The user's input prompt
            context: Optional context dict with additional info
                    (e.g., user preferences, conversation history)

        Returns:
            Tuple of (should_route, confidence, reason):
            - should_route (bool): True if this model can handle it
            - confidence (float): 0.0-1.0 confidence score
            - reason (str): Human-readable explanation for routing decision
        """
        pass

    @property
    def description(self) -> str:
        """
        Optional human-readable description of the model.

        Returns:
            str: Description of what this model is good for
        """
        return ""

    @property
    def enabled(self) -> bool:
        """
        Whether this model is currently enabled.

        Set to False to disable a model without removing the file.
        Disabled models are skipped during routing.

        Returns:
            bool: True if enabled, False if disabled
        """
        return True
