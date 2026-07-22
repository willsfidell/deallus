"""Tool registry and execution engine."""

from typing import Dict, List, Literal, Optional
import importlib
import inspect
import os
import logging

from app.tools.base import AITool, ToolResult, ToolAction

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and executing pluggable tools."""

    def __init__(self):
        """Initialize tool registry."""
        self.pre_prompt_tools: List[AITool] = []
        self.post_result_tools: List[AITool] = []

    def register_tool(self, tool: AITool) -> None:
        """Register a tool in the appropriate stage.

        Tools are sorted by priority after registration.

        Args:
            tool: Tool instance to register
        """
        if tool.stage == "pre_prompt":
            self.pre_prompt_tools.append(tool)
            self.pre_prompt_tools.sort(key=lambda t: t.priority)
            logger.info(
                f"Registered pre-prompt tool: {tool.name} (priority: {tool.priority})"
            )
        elif tool.stage == "post_result":
            self.post_result_tools.append(tool)
            self.post_result_tools.sort(key=lambda t: t.priority)
            logger.info(
                f"Registered post-result tool: {tool.name} (priority: {tool.priority})"
            )
        else:
            raise ValueError(f"Unknown tool stage: {tool.stage}")

    def discover_tools(self, tools_dir: str = "app/tools") -> None:
        """Auto-discover and register tools by scanning directory.

        Looks for classes inheriting from AITool in the tools directory.

        Args:
            tools_dir: Root directory to scan for tools
        """
        logger.info(f"Discovering tools in {tools_dir}...")

        # Scan pre_prompt and post_result directories
        for stage_dir in ["pre_prompt", "post_result"]:
            stage_path = os.path.join(tools_dir, stage_dir)
            if not os.path.exists(stage_path):
                continue

            for filename in os.listdir(stage_path):
                if filename.startswith("_") or not filename.endswith(".py"):
                    continue

                module_name = filename[:-3]  # Remove .py
                full_module_path = f"app.tools.{stage_dir}.{module_name}"

                try:
                    module = importlib.import_module(full_module_path)

                    # Find all AITool subclasses in module
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, AITool)
                            and obj is not AITool
                        ):
                            tool_instance = obj()
                            self.register_tool(tool_instance)

                except Exception as e:
                    logger.error(f"Error loading tool {full_module_path}: {e}")

    async def execute_chain(
        self,
        stage: Literal["pre_prompt", "post_result"],
        content: str,
        initial_state: Dict = None,
        metadata: Dict = None,
    ) -> ToolResult:
        """Execute tool chain sequentially in priority order.

        Each tool receives output from previous tool. If any tool
        returns BLOCK action, execution stops immediately.

        Args:
            stage: Which stage to execute ("pre_prompt" or "post_result")
            content: Content to process
            initial_state: Initial state dict to pass to first tool
            metadata: Request metadata

        Returns:
            ToolResult with final content, state, and flags
        """
        state = initial_state or {}
        current_content = content
        all_flags = []
        executed_tools = []

        tools = (
            self.pre_prompt_tools if stage == "pre_prompt" else self.post_result_tools
        )

        logger.debug(f"Executing {stage} chain with {len(tools)} tools")

        for tool in tools:
            logger.debug(f"Executing tool: {tool.name} (priority: {tool.priority})")

            result = tool._run(
                content=current_content, state=state, metadata=metadata
            )

            # Track executed tool
            executed_tools.append(tool.name)

            # If tool blocks, return immediately (error)
            if result.action == ToolAction.BLOCK:
                logger.warning(f"Tool {tool.name} blocked execution with flags: {result.flags}")
                # Include executed tools in state before returning
                state["executed_tools"] = executed_tools
                return result

            # Update for next tool
            current_content = result.modified_content
            state.update(result.state)
            all_flags.extend(result.flags)

            logger.debug(
                f"Tool {tool.name} completed: action={result.action}, flags={result.flags}"
            )

        # Add executed tools to state
        state["executed_tools"] = executed_tools

        return ToolResult(
            modified_content=current_content,
            state=state,
            action=ToolAction.CONTINUE,
            flags=all_flags,
        )


# Global registry instance
tool_registry = ToolRegistry()


# Convenience wrapper classes for process router
class ProcessToolResult:
    """Wrapper for tool result in process endpoint."""

    def __init__(self, tool_result: ToolResult):
        self.content = tool_result.modified_content
        self.state = tool_result.state
        self.executed_tools = tool_result.state.get("executed_tools", [])
        self.action = tool_result.action
        self.flags = tool_result.flags


# Synchronous convenience methods for the process router
def run_pre_prompt_tools(content: str, state: Dict = None, metadata: Dict = None) -> ProcessToolResult:
    """Run pre-prompt tools synchronously."""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            tool_registry.execute_chain("pre_prompt", content, state, metadata)
        )
        return ProcessToolResult(result)
    finally:
        loop.close()


def run_post_result_tools(content: str, state: Dict = None, metadata: Dict = None) -> ProcessToolResult:
    """Run post-result tools synchronously."""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            tool_registry.execute_chain("post_result", content, state, metadata)
        )
        return ProcessToolResult(result)
    finally:
        loop.close()


# Add methods to registry for easy access
ToolRegistry.run_pre_prompt_tools = lambda self, content, state=None, metadata=None: run_pre_prompt_tools(content, state, metadata)
ToolRegistry.run_post_result_tools = lambda self, content, state=None, metadata=None: run_post_result_tools(content, state, metadata)
