"""Base tool class and models for pluggable tool system."""

from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import abc


class ToolAction(str, Enum):
    """Action to take after tool execution."""

    CONTINUE = "continue"  # Continue to next tool/stage (nothing detected)
    DETECTED = "detected"  # Something detected but no action taken (flagged for monitoring)
    MODIFY = "modify"  # Content was modified, continue processing
    BLOCK = "block"  # Stop processing, return error immediately


class ToolResult(BaseModel):
    """Result returned by a tool."""

    modified_content: str = Field(
        ..., description="Content after tool processing (may be modified)"
    )
    state: Dict = Field(
        default_factory=dict, description="Free-form state dict passed to next tool"
    )
    action: ToolAction = Field(
        ..., description="Action to take after this tool execution"
    )
    action_description: str = Field(
        default="",
        description="Human-readable description of what action was taken"
    )
    flags: List[str] = Field(
        default_factory=list, description="Flags/warnings from tool execution"
    )
    metadata: Dict = Field(
        default_factory=dict, description="Additional metadata from tool"
    )


class AITool(BaseTool):
    """Base class for all AIDI tools (LangChain-compatible).

    All tools must inherit from this class and implement _run method.
    """

    name: str = Field(default="", description="Tool name")
    description: str = Field(default="", description="Tool description")
    priority: int = Field(
        default=50,
        description="Execution priority (0-99, lower = runs first)",
        ge=0,
        le=99,
    )
    stage: Literal["pre_prompt", "post_result"] = Field(
        default="pre_prompt", description="Stage when tool executes"
    )

    @abc.abstractmethod
    def _run(
        self,
        content: str,
        state: Dict = None,
        metadata: Dict = None,
    ) -> ToolResult:
        """Execute tool logic.

        Args:
            content: Input text to process (prompt or result)
            state: State dict from previous tools (free-form)
            metadata: Request metadata (user_id, timestamp, etc.)

        Returns:
            ToolResult with modified content and state
        """
        raise NotImplementedError

    def run(self, *args, **kwargs):
        """Override LangChain's run method for compatibility."""
        # This is required by LangChain but we use _run directly
        pass
