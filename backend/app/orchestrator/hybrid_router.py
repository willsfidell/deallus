"""Hybrid orchestrator that combines rule-based and LLM-based routing."""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Optional

from app.orchestrator.rule_router import RuleRouter, RoutingDecision
from app.orchestrator.llm_classifier import LLMClassifier, LLMClassifierResult
from app.services import get_llm_service, LLMError

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Final orchestration decision."""
    model: str
    reasoning: dict  # Contains details of decision process
    confidence: float


class HybridOrchestrator:
    """
    Hybrid orchestrator combining rule-based and LLM-based routing.

    Decision flow:
    1. Run rule-based router on prompt
    2. If confidence above threshold → use that model
    3. If confidence below threshold → run LLM classifier
    4. Use LLM's decision as final routing
    """

    def __init__(
        self,
        text_model: str,
        classifier_model: str,
        rule_confidence_threshold: float = 0.80,
        llm_confidence_threshold: float = 0.60,
    ):
        """
        Initialize hybrid orchestrator.

        Args:
            text_model: Model for general text generation
            classifier_model: Model for classification tasks
            rule_confidence_threshold: Min confidence for rule-based decision
            llm_confidence_threshold: Min confidence for LLM decision
        """
        self.text_model = text_model
        self.classifier_model = classifier_model
        self.rule_confidence_threshold = rule_confidence_threshold
        self.llm_confidence_threshold = llm_confidence_threshold

        self.rule_router = RuleRouter(
            text_model=text_model,
            classifier_model=classifier_model,
            confidence_threshold=rule_confidence_threshold,
        )

        self.llm_classifier = LLMClassifier(
            classifier_model=classifier_model,
            text_model=text_model,
            confidence_threshold=llm_confidence_threshold,
        )

    async def route(self, prompt: str) -> OrchestrationResult:
        """
        Route a prompt using hybrid orchestration.

        Async method for FastAPI integration.

        Args:
            prompt: User prompt to route

        Returns:
            OrchestrationResult with final model decision
        """
        reasoning = {
            "prompt_preview": prompt[:100],
            "steps": [],
        }

        # Step 1: Rule-based routing
        rule_decision = self.rule_router.route(prompt)
        reasoning["steps"].append({
            "stage": "rule_based",
            "model": rule_decision.model,
            "confidence": rule_decision.confidence,
            "reason": rule_decision.reason,
        })

        logger.info(
            f"Rule-based routing result: model={rule_decision.model}, "
            f"confidence={rule_decision.confidence:.2f}"
        )

        # Step 2: Check if rule confidence is sufficient
        if not self.rule_router.should_use_llm_classifier(rule_decision):
            logger.info(f"Rule-based decision accepted (confidence: {rule_decision.confidence:.2f})")
            return OrchestrationResult(
                model=rule_decision.model,
                reasoning=reasoning,
                confidence=rule_decision.confidence,
            )

        # Step 3: Use LLM classifier for final decision
        logger.info(f"LLM classification needed (rule confidence: {rule_decision.confidence:.2f})")

        # For now, we'll use a simulated LLM response
        # In production, this would call the actual LLM via LiteLLM
        llm_decision = await self._run_llm_classification(prompt)

        reasoning["steps"].append({
            "stage": "llm_classification",
            "model": llm_decision.model,
            "confidence": llm_decision.confidence,
            "reason": llm_decision.reason,
        })

        logger.info(
            f"LLM classification result: model={llm_decision.model}, "
            f"confidence={llm_decision.confidence:.2f}"
        )

        return OrchestrationResult(
            model=llm_decision.model,
            reasoning=reasoning,
            confidence=llm_decision.confidence,
        )

    async def _run_llm_classification(self, prompt: str) -> LLMClassifierResult:
        """
        Run LLM classification using actual LLM via LiteLLM.

        Args:
            prompt: User prompt to classify

        Returns:
            LLMClassifierResult with model decision

        Note:
            Uses LiteLLM to query the classifier model for routing decision.
        """
        try:
            llm_service = get_llm_service()

            # Build classification prompt
            classification_prompt = self.llm_classifier.build_classification_prompt(prompt)

            logger.info(f"Running LLM classification with model: {self.classifier_model}")

            # Call LLM for classification
            response = await llm_service.generate(
                prompt=prompt,
                model=self.classifier_model,
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent routing
                system_prompt=classification_prompt,
            )

            logger.debug(f"LLM classification response: {response[:100]}")

            # Parse response
            parsed = self.llm_classifier.parse_classification_response(response)

            if parsed and "model" in parsed and "confidence" in parsed:
                # Convert model name if needed (LLM might return simplified names)
                model_choice = parsed.get("model", self.text_model)
                if "CLASSIFICATION" in model_choice:
                    final_model = self.classifier_model
                else:
                    final_model = self.text_model

                confidence = float(parsed.get("confidence", 0.60))
                reason = parsed.get("reason", "LLM classification")

                logger.info(
                    f"LLM classification result: model={final_model}, "
                    f"confidence={confidence:.2f}, reason={reason}"
                )

                return LLMClassifierResult(
                    model=final_model,
                    confidence=min(confidence, 0.99),  # Cap at 0.99
                    reason=reason,
                    raw_response=response,
                )
            else:
                logger.warning("Failed to parse LLM classification response, using fallback")
                return LLMClassifierResult(
                    model=self.text_model,
                    confidence=0.60,
                    reason="Failed to parse LLM response, using default",
                    raw_response=response,
                )

        except LLMError as e:
            logger.error(f"LLM service error during classification: {e}")
            # Fallback to text_model on error
            return LLMClassifierResult(
                model=self.text_model,
                confidence=0.50,
                reason=f"LLM classification failed: {str(e)}",
                raw_response="",
            )

        except Exception as e:
            logger.error(f"Unexpected error during LLM classification: {e}", exc_info=True)
            return LLMClassifierResult(
                model=self.text_model,
                confidence=0.50,
                reason=f"Classification error: {str(e)}",
                raw_response="",
            )

    async def route_with_details(self, prompt: str) -> dict:
        """
        Route a prompt and return detailed routing information.

        Useful for debugging and monitoring.

        Args:
            prompt: User prompt to route

        Returns:
            Dict with orchestration result and metadata
        """
        result = await self.route(prompt)

        return {
            "model": result.model,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "text_model": self.text_model,
            "classifier_model": self.classifier_model,
        }
