"""Model registry and discovery engine."""

import logging
import importlib
import inspect
import os
from typing import List, Optional

from app.orchestrator.model_base import BaseModelDefinition
from app.orchestrator.rule_router import RoutingDecision

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for discovering and managing pluggable model definitions.

    The registry:
    1. Auto-discovers model definitions by scanning a directory
    2. Maintains a prioritized list of available models
    3. Routes prompts to the best matching model
    4. Falls back to LLM classification if no models match confidently
    """

    def __init__(self):
        """Initialize the model registry."""
        self.models: List[BaseModelDefinition] = []
        self.fallback_model: Optional[str] = None

    def register_model(self, model: BaseModelDefinition) -> None:
        """
        Register a model definition.

        Models are automatically sorted by priority after registration
        (highest priority first).

        Args:
            model: Model definition instance to register
        """
        if not model.enabled:
            logger.info(f"Skipping disabled model: {model.name}")
            return

        self.models.append(model)
        self.models.sort(key=lambda m: m.priority, reverse=True)

        logger.info(
            f"Registered model: {model.name} "
            f"(model_id: {model.model_id}, priority: {model.priority})"
        )

    def discover_models(self, models_dir: str = "app/orchestrator/models") -> None:
        """
        Auto-discover and register model definitions by scanning directory.

        Looks for Python files in the models directory and instantiates
        any classes that inherit from BaseModelDefinition.

        Args:
            models_dir: Root directory to scan for model definitions
        """
        logger.info(f"Discovering model definitions in {models_dir}...")

        if not os.path.exists(models_dir):
            logger.warning(f"Models directory does not exist: {models_dir}")
            return

        discovered_count = 0

        for filename in os.listdir(models_dir):
            # Skip private files and non-Python files
            if filename.startswith("_") or not filename.endswith(".py"):
                continue

            module_name = filename[:-3]  # Remove .py extension
            full_module_path = f"app.orchestrator.models.{module_name}"

            try:
                module = importlib.import_module(full_module_path)
                logger.debug(f"Loaded module: {full_module_path}")

                # Find all BaseModelDefinition subclasses in module
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseModelDefinition)
                        and obj is not BaseModelDefinition
                    ):
                        try:
                            model_instance = obj()
                            self.register_model(model_instance)
                            discovered_count += 1
                        except Exception as e:
                            logger.error(
                                f"Failed to instantiate {obj.__name__} "
                                f"from {full_module_path}: {e}"
                            )

            except Exception as e:
                logger.error(
                    f"Error loading model module {full_module_path}: {e}",
                    exc_info=True,
                )

        logger.info(
            f"Model discovery complete: {discovered_count} models registered"
        )

        if not self.models:
            logger.warning("No model definitions discovered!")

    def route(
        self, prompt: str, context: Optional[dict] = None
    ) -> RoutingDecision:
        """
        Route a prompt to the best matching model.

        Algorithm:
        1. Evaluate all enabled models in priority order
        2. Collect models where should_route_to_me() returns True
        3. Select best match by priority + confidence
        4. If no matches or low confidence, mark for LLM classification

        Tie-breaking rules:
        - Higher priority wins
        - If same priority, highest confidence wins
        - If still tied, first registered model wins

        Args:
            prompt: User prompt to route
            context: Optional context information

        Returns:
            RoutingDecision with selected model and reasoning
        """
        if not self.models:
            logger.warning("No models available for routing")
            return RoutingDecision(
                model="",
                confidence=0.0,
                reason="No models available (discovery failed?)",
                requires_llm_classification=True,
            )

        matches = []
        logger.debug(f"Evaluating {len(self.models)} models for routing")

        # Evaluate each model
        for model in self.models:
            try:
                should_route, confidence, reason = model.should_route_to_me(
                    prompt, context
                )

                if should_route:
                    matches.append(
                        {
                            "model": model,
                            "model_id": model.model_id,
                            "priority": model.priority,
                            "confidence": confidence,
                            "reason": reason,
                        }
                    )
                    logger.debug(
                        f"Model {model.name} matches: "
                        f"priority={model.priority}, confidence={confidence:.2f}"
                    )

            except Exception as e:
                logger.error(
                    f"Error evaluating model {model.name}: {e}", exc_info=True
                )

        # Select best match
        if not matches:
            logger.info("No models matched the prompt")
            return RoutingDecision(
                model="",
                confidence=0.0,
                reason="No models matched the prompt",
                requires_llm_classification=True,
            )

        # Sort by priority (desc) then confidence (desc)
        best_match = sorted(
            matches,
            key=lambda m: (m["priority"], m["confidence"]),
            reverse=True,
        )[0]

        logger.info(
            f"Best model match: {best_match['model'].name} "
            f"(priority={best_match['priority']}, "
            f"confidence={best_match['confidence']:.2f})"
        )

        return RoutingDecision(
            model=best_match["model_id"],
            confidence=best_match["confidence"],
            reason=f"{best_match['model'].name}: {best_match['reason']}",
            requires_llm_classification=False,
        )

    def get_model_by_id(self, model_id: str) -> Optional[BaseModelDefinition]:
        """
        Get a model definition by its model_id.

        Args:
            model_id: Model identifier (e.g., "ollama/llama2")

        Returns:
            Model definition or None if not found
        """
        for model in self.models:
            if model.model_id == model_id:
                return model
        return None

    def get_all_models(self) -> List[BaseModelDefinition]:
        """
        Get all registered models in priority order.

        Returns:
            List of model definitions (highest priority first)
        """
        return self.models.copy()


# Global registry instance
model_registry = ModelRegistry()
