"""Test result validator - simple validation tool."""

import logging
from app.tools.base import AITool, ToolResult, ToolAction
from typing import Dict

logger = logging.getLogger(__name__)


class TestResultValidator(AITool):
    """Test tool for validating model results.

    Performs basic validation checks:
    - Result length
    - Excessive apologies/disclaimers
    - Consistency with pre-prompt state
    """

    name: str = "test_result_validator"
    description: str = "Validates model output quality"
    priority: int = 10
    stage: str = "post_result"

    def _run(
        self,
        content: str,
        state: Dict = None,
        metadata: Dict = None,
    ) -> ToolResult:
        """Validate result."""
        state = state or {}
        flags = []
        issues = []

        # Check: Result not too short
        if len(content) < 10:
            flags.append("result_too_short")
            issues.append("result too short")
            logger.debug("Result is too short")

        # Check: Not excessive apologies
        apology_count = content.lower().count("sorry")
        if apology_count > 2:
            flags.append("excessive_apologies")
            issues.append(f"{apology_count} apologies")
            logger.debug(f"Found {apology_count} apologies in result")

        # Check: If armadillo was in prompt, note it in state
        if state.get("armadillo_detected"):
            flags.append("armadillo_was_in_prompt")
            issues.append("armadillo reference in original prompt")

        if issues:
            action_type = ToolAction.DETECTED
            action_desc = f"DETECTED: Validation issues ({', '.join(issues)})"
        else:
            action_type = ToolAction.CONTINUE
            action_desc = "Result validation passed (no issues detected)"

        return ToolResult(
            modified_content=content,
            state={**state, "validated": True},
            action=action_type,
            action_description=action_desc,
            flags=flags,
        )
