"""
Tool Call Dispatcher for Project Anima.

Resolves and executes tool calls requested by the LLM, mapping tool names
to their registered handler functions and formatting results for re-injection
into the conversation as tool role messages.

This module has a single responsibility: dispatch. It contains no tool logic,
no memory management, and no conversation orchestration.
"""

import logging
from typing import Any, Dict, List, Optional

from tools.registry import TOOL_HANDLER_MAP, MEMORY_DEPENDENT_TOOLS
from memory.manager import MemoryManager

logger = logging.getLogger("anima.tool_dispatcher")


class ToolDispatcher:
    """
    Dispatches parsed LLM tool calls to their corresponding handler functions.

    Tool handlers are resolved via the central registry (``TOOL_HANDLER_MAP``).
    Memory-dependent tools receive the injected ``MemoryManager`` automatically.

    Attributes:
        memory_manager (Optional[MemoryManager]): Persistent memory coordinator,
            passed to memory-related tool handlers that require it.
    """

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        """
        Initialize ToolDispatcher.

        Args:
            memory_manager (Optional[MemoryManager]): Memory coordinator instance
                required by save_memory and recall_memory tool handlers.
        """
        self.memory_manager = memory_manager
        logger.debug(f"ToolDispatcher initialized [Memory enabled: {memory_manager is not None}]")

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute the handler for a given tool name with provided arguments.

        Memory-dependent tools (``save_memory``, ``recall_memory``) automatically
        receive ``memory_manager`` injected as a keyword argument.

        Args:
            tool_name (str): Name of the requested tool as returned by the LLM.
            arguments (Dict[str, Any]): Arguments parsed from the model's tool call.

        Returns:
            str: Tool execution result as a plain string. Never raises — all errors
                are caught and returned as descriptive error strings so the model
                can respond in-character rather than crashing.
        """
        handler = TOOL_HANDLER_MAP.get(tool_name)
        if handler is None:
            logger.warning(f"Unknown tool requested by model: '{tool_name}'")
            return f"Error: tool '{tool_name}' is not registered or available."

        try:
            if tool_name in MEMORY_DEPENDENT_TOOLS:
                if self.memory_manager is None:
                    logger.error(f"Tool '{tool_name}' requires MemoryManager but none was injected.")
                    return f"Error: memory is not available — cannot execute '{tool_name}'."
                result = handler(memory_manager=self.memory_manager, **arguments)
            else:
                result = handler(**arguments)

            logger.info(f"Tool '{tool_name}' executed successfully.")
            return result

        except TypeError as exc:
            # Argument mismatch — likely a model hallucinating wrong params
            logger.error(f"Tool '{tool_name}' received invalid arguments {arguments}: {exc}")
            return f"Error: invalid arguments provided for tool '{tool_name}'."
        except Exception as exc:
            logger.error(f"Tool '{tool_name}' execution failed unexpectedly: {exc}")
            return f"Error executing tool '{tool_name}': {exc}"

    def dispatch_all(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Execute all tool calls from a single LLM response and format results.

        Each result is packaged as a ``tool`` role message dict compatible with
        Ollama's conversation format for re-injection.

        Args:
            tool_calls (List[Dict[str, Any]]): Raw tool_calls list from Ollama response.

        Returns:
            List[Dict[str, str]]: List of tool result message dicts, each with
                ``role``, ``content``, and ``name`` keys.
        """
        results: List[Dict[str, str]] = []

        for call in tool_calls:
            # Ollama tool_call structure: {"function": {"name": ..., "arguments": {...}}}
            func_info = call.get("function", {})
            tool_name: str = func_info.get("name", "")
            arguments: Dict[str, Any] = func_info.get("arguments", {})

            if not tool_name:
                logger.warning(f"Skipping malformed tool call (no name): {call}")
                continue

            logger.info(f"Dispatching tool call: '{tool_name}' with args={arguments}")
            result_content = self.dispatch(tool_name=tool_name, arguments=arguments)

            results.append({
                "role": "tool",
                "content": result_content,
                "name": tool_name,
            })

        return results
