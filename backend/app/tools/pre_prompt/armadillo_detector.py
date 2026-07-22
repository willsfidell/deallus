"""Armadillo detector - test tool to prove concept."""

import logging
from app.tools.base import AITool, ToolResult, ToolAction
from typing import Dict

logger = logging.getLogger(__name__)


class ArmadilloDetector(AITool):
    """Test tool: Detects the word 'armadillo' in prompts.

    This is a simple test tool to prove the pluggable tool system works.
    It detects mentions of armadillos and flags them.
    """

    name: str = "armadillo_detector"
    description: str = "Detects mentions of armadillos in user input"
    priority: int = 10
    stage: str = "pre_prompt"

    def _run(
        self,
        content: str,
        state: Dict = None,
        metadata: Dict = None,
    ) -> ToolResult:
        """Detect armadillo in content."""
        state = state or {}

        if "armadillo" in content.lower():
            logger.info(
                "Armadillo detected in prompt"
            )
            return ToolResult(
                modified_content=content.replace("armadillo", "[ARMADILLO_DETECTED]"),
                state={**state, "armadillo_detected": True},
                action=ToolAction.MODIFY,
                flags=["armadillo_detected"],
                metadata={
                    "detection_count": content.lower().count("armadillo")
                },
            )

        return ToolResult(
            modified_content=content,
            state=state,
            action=ToolAction.CONTINUE,
            flags=[],
        )
