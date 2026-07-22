"""Prompt injection detector."""

import re
import logging
from typing import ClassVar, Dict, List
from app.tools.base import AITool, ToolResult, ToolAction

logger = logging.getLogger(__name__)


class PromptInjectionDetector(AITool):
    """Detects potential prompt injection attempts.

    Looks for common prompt injection patterns:
    - "ignore previous instructions"
    - "system prompt"
    - "as an AI you must"
    - etc.
    """

    name: str = "prompt_injection_detector"
    description: str = "Detects potential prompt injection attacks"
    priority: int = 30
    stage: str = "pre_prompt"

    # Patterns that suggest prompt injection attempts
    INJECTION_PATTERNS: ClassVar[List[str]] = [
        r"ignore\s+previous\s+instructions?",
        r"forget\s+everything\s+you",
        r"system\s+prompt",
        r"as\s+an\s+ai\s+you\s+must",
        r"disregard\s+all\s+previous",
        r"pretend\s+you\s+are",
        r"your\s+instructions\s+are",
    ]

    def _run(
        self,
        content: str,
        state: Dict = None,
        metadata: Dict = None,
    ) -> ToolResult:
        """Detect prompt injection."""
        state = state or {}
        content_lower = content.lower()
        flags = []
        injections = []

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, content_lower):
                injections.append(pattern)
                flags.append("prompt_injection_detected")

        if injections:
            logger.warning(f"Potential prompt injection detected: {injections}")
            return ToolResult(
                modified_content=content,
                state={**state, "injection_detected": injections},
                action=ToolAction.BLOCK,
                flags=flags,
                metadata={"injections": injections},
            )

        return ToolResult(
            modified_content=content,
            state=state,
            action=ToolAction.CONTINUE,
            flags=[],
        )
