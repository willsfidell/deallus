"""PII detector and redactor."""

import re
import logging
from typing import ClassVar, Dict
from app.tools.base import AITool, ToolResult, ToolAction

logger = logging.getLogger(__name__)


class PIIDetector(AITool):
    """Detects and redacts personally identifiable information (PII).

    Detects and redacts:
    - Email addresses
    - Phone numbers
    - Social Security Numbers (SSNs)
    """

    name: str = "pii_detector"
    description: str = "Detects and redacts personally identifiable information"
    priority: int = 20
    stage: str = "pre_prompt"

    # Simple regex patterns for PII detection
    EMAIL_PATTERN: ClassVar[str] = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    PHONE_PATTERN: ClassVar[str] = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    SSN_PATTERN: ClassVar[str] = r"\b\d{3}-\d{2}-\d{4}\b"

    def _run(
        self,
        content: str,
        state: Dict = None,
        metadata: Dict = None,
    ) -> ToolResult:
        """Detect and redact PII."""
        state = state or {}
        modified = content
        flags = []
        pii_found = {}

        # Detect and redact emails
        emails = re.findall(self.EMAIL_PATTERN, content)
        if emails:
            modified = re.sub(self.EMAIL_PATTERN, "[EMAIL_REDACTED]", modified)
            pii_found["emails"] = len(emails)
            flags.append("pii_email_detected")
            logger.info(f"Detected {len(emails)} email(s)")

        # Detect and redact phone numbers
        phones = re.findall(self.PHONE_PATTERN, content)
        if phones:
            modified = re.sub(self.PHONE_PATTERN, "[PHONE_REDACTED]", modified)
            pii_found["phones"] = len(phones)
            flags.append("pii_phone_detected")
            logger.info(f"Detected {len(phones)} phone number(s)")

        # Detect and redact SSNs
        ssns = re.findall(self.SSN_PATTERN, content)
        if ssns:
            modified = re.sub(self.SSN_PATTERN, "[SSN_REDACTED]", modified)
            pii_found["ssns"] = len(ssns)
            flags.append("pii_ssn_detected")
            logger.info(f"Detected {len(ssns)} SSN(s)")

        if pii_found:
            pii_summary = ", ".join([f"{count} {ptype}" for ptype, count in pii_found.items()])
            action_desc = f"MODIFIED: PII redacted ({pii_summary})"
            action = ToolAction.MODIFY
        else:
            action_desc = "No PII detected in prompt"
            action = ToolAction.CONTINUE

        return ToolResult(
            modified_content=modified,
            state={**state, "pii_detected": pii_found},
            action=action,
            action_description=action_desc,
            flags=flags,
            metadata={"pii_types": list(pii_found.keys())},
        )
