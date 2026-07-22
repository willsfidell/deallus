"""AI slop detector - detects generic/low-quality AI phrases."""

import logging
from typing import ClassVar, Dict, List
from app.tools.base import AITool, ToolResult, ToolAction

logger = logging.getLogger(__name__)


class AISlopDetector(AITool):
    """Detects generic/low-quality AI-generated phrases ('slop').

    Looks for common AI-generated phrases that indicate low quality:
    - "as an AI language model"
    - "it's important to note that"
    - "delve into"
    - "robust solution"
    - etc.
    """

    name: str = "ai_slop_detector"
    description: str = "Detects generic AI-generated phrases"
    priority: int = 20
    stage: str = "post_result"

    # Common AI slop phrases
    SLOP_PHRASES: ClassVar[List[str]] = [
        "as an ai language model",
        "i don't have personal opinions",
        "it's important to note that",
        "in today's digital landscape",
        "delve into",
        "robust solution",
        "leverage",
        "paradigm shift",
        "at the end of the day",
        "it is crucial to understand",
    ]

    def _run(
        self,
        content: str,
        state: Dict = None,
        metadata: Dict = None,
    ) -> ToolResult:
        """Detect AI slop."""
        state = state or {}
        content_lower = content.lower()

        detected = [p for p in self.SLOP_PHRASES if p in content_lower]
        slop_score = len(detected) / len(self.SLOP_PHRASES)  # 0.0 to 1.0

        flags = []
        if detected:
            flags.append("ai_slop_detected")
            flags.append(f"slop_score_{int(slop_score * 100)}")
            logger.debug(
                f"Detected {len(detected)} slop phrases: {detected}"
            )
            action_type = ToolAction.DETECTED
            action_desc = f"DETECTED: {len(detected)} generic AI phrases (slop_score: {slop_score:.0%})"
        else:
            action_type = ToolAction.CONTINUE
            action_desc = "No generic AI phrases detected in response"

        return ToolResult(
            modified_content=content,
            state={
                **state,
                "slop_detected": detected,
                "slop_score": slop_score,
            },
            action=action_type,
            action_description=action_desc,
            flags=flags,
            metadata={
                "slop_phrases": detected,
                "slop_score": slop_score,
            },
        )
