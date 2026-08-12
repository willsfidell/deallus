"""Rule-based router for AIDI orchestrator."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Decision made by the router."""
    model: str
    confidence: float
    reason: str
    requires_llm_classification: bool = False


class RuleRouter:
    """Rule-based router using simple keyword and pattern matching."""

    def __init__(self, text_model: str, classifier_model: str, confidence_threshold: float = 0.80):
        """
        Initialize the rule-based router.

        Args:
            text_model: Model name for general text generation
            classifier_model: Model name for classification
            confidence_threshold: Minimum confidence to use rule-based routing
        """
        self.text_model = text_model
        self.classifier_model = classifier_model
        self.confidence_threshold = confidence_threshold

    def route(self, prompt: str) -> RoutingDecision:
        """
        Route a prompt using rule-based logic.

        Rules (in priority order):
        1. Classification keywords → classifier_model (high confidence)
        2. Analysis keywords → text_model (medium confidence)
        3. Code keywords → text_model (medium confidence)
        4. Default → text_model (fallback)

        Args:
            prompt: User prompt to route

        Returns:
            RoutingDecision with model, confidence, and reason
        """
        prompt_lower = prompt.lower()

        # Rule 1: Classification requests
        classification_keywords = [
            "classify", "categorize", "category", "categories",
            "sentiment", "emotion", "intent", "predict",
            "label", "annotation", "classify me",
        ]
        if any(keyword in prompt_lower for keyword in classification_keywords):
            logger.info("Rule-based routing: classification keywords detected")
            return RoutingDecision(
                model=self.classifier_model,
                confidence=0.90,
                reason="Classification keywords detected",
                requires_llm_classification=False,
            )

        # Rule 2: Analysis requests (longer, detailed responses expected)
        analysis_keywords = [
            "analyze", "analysis", "explain", "summary", "summarize",
            "compare", "contrast", "discuss", "evaluate", "assess",
            "what is", "how does", "why",
        ]
        if any(keyword in prompt_lower for keyword in analysis_keywords):
            logger.info("Rule-based routing: analysis keywords detected")
            return RoutingDecision(
                model=self.text_model,
                confidence=0.85,
                reason="Analysis keywords detected",
                requires_llm_classification=False,
            )

        # Rule 3: Code/Technical requests
        code_keywords = [
            "code", "function", "method", "class", "import",
            "python", "javascript", "java", "sql", "error",
            "debug", "fix", "implement", "algorithm",
        ]
        if any(keyword in prompt_lower for keyword in code_keywords):
            logger.info("Rule-based routing: code/technical keywords detected")
            return RoutingDecision(
                model=self.text_model,
                confidence=0.80,
                reason="Code/technical keywords detected",
                requires_llm_classification=False,
            )

        # Rule 4: Question-based (likely needs LLM for better understanding)
        if prompt_lower.strip().endswith("?") and len(prompt) > 10:
            logger.info("Rule-based routing: question detected")
            return RoutingDecision(
                model=self.text_model,
                confidence=0.70,
                reason="Question pattern detected",
                requires_llm_classification=False,
            )

        # Default: Use text model with low confidence (needs LLM review)
        logger.info("Rule-based routing: no rules matched, defaulting to text model")
        return RoutingDecision(
            model=self.text_model,
            confidence=0.50,
            reason="No specific rules matched (default routing)",
            requires_llm_classification=True,  # LLM should verify this
        )

    def should_use_llm_classifier(self, decision: RoutingDecision) -> bool:
        """
        Determine if LLM classifier should make the final decision.

        Args:
            decision: RoutingDecision from rule-based router

        Returns:
            True if confidence is below threshold or LLM verification is needed
        """
        return decision.confidence < self.confidence_threshold or decision.requires_llm_classification
