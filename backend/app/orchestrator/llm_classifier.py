"""LLM-based classifier for AIDI orchestrator."""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMClassifierResult:
    """Result from LLM classification."""
    model: str
    confidence: float
    reason: str
    raw_response: str


class LLMClassifier:
    """LLM-based classifier using Llama for intelligent routing."""

    def __init__(self, classifier_model: str, text_model: str, confidence_threshold: float = 0.60):
        """
        Initialize the LLM classifier.

        Args:
            classifier_model: Model to use for classification (typically smaller model)
            text_model: Model name for text generation
            confidence_threshold: Minimum confidence for classification
        """
        self.classifier_model = classifier_model
        self.text_model = text_model
        self.confidence_threshold = confidence_threshold

        # LiteLLM will be imported and used in the hybrid router
        # This class focuses on prompt engineering for classification

    def build_classification_prompt(self, prompt: str) -> str:
        """
        Build a prompt for the LLM to classify the request.

        Args:
            prompt: User prompt to classify

        Returns:
            System prompt for classification
        """
        system_prompt = """You are a routing classifier for an AI system. 
Your job is to determine which model should handle the user's request.

The available models are:
1. CLASSIFICATION_MODEL: Best for sentiment analysis, categorization, intent detection, predictions
2. TEXT_MODEL: Best for general writing, analysis, code, explanations, creative content

Respond ONLY in this JSON format:
{
    "model": "CLASSIFICATION_MODEL" or "TEXT_MODEL",
    "confidence": 0.0-1.0,
    "reason": "brief reason for this choice"
}

User request: """ + prompt

        return system_prompt

    async def classify(self, prompt: str) -> LLMClassifierResult:
        """
        Classify a prompt using the LLM.

        This is async-ready for integration with FastAPI.

        Args:
            prompt: User prompt to classify

        Returns:
            LLMClassifierResult with model decision and confidence
        """
        # Note: Actual LLM call will be made in the hybrid router
        # This method provides the structure for async classification

        classification_prompt = self.build_classification_prompt(prompt)

        # Placeholder for actual LLM call via LiteLLM
        # Will be implemented in hybrid_router.py with actual LLM integration
        logger.info(f"LLM classification requested for prompt: {prompt[:50]}...")

        # For now, return a default structure
        # This will be populated by the hybrid router with actual LLM response
        return LLMClassifierResult(
            model=self.text_model,
            confidence=0.50,
            reason="Awaiting LLM classification",
            raw_response="",
        )

    def parse_classification_response(self, response: str) -> Optional[dict]:
        """
        Parse the LLM classification response.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed classification dict or None if parsing fails
        """
        try:
            # Try to extract JSON from response
            # LLM might include extra text before/after JSON
            import json as json_module

            # Find JSON in response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                classification = json_module.loads(json_str)

                # Validate response structure
                if "model" in classification and "confidence" in classification and "reason" in classification:
                    return classification

            logger.warning(f"Failed to parse classification response: {response[:100]}")
            return None

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing classification response: {e}")
            return None
