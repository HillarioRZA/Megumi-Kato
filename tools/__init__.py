"""
Tools Package for Project Anima.

Provides LLM function-calling definitions, execution handlers, and the central tool registry.
"""

from tools.memory_tools import (
    MEMORY_TOOLS,
    SAVE_MEMORY_SCHEMA,
    RECALL_MEMORY_SCHEMA,
    execute_save_memory,
    execute_recall_memory,
)
from tools.time_tools import TIME_TOOLS, execute_get_current_time
from tools.web_search_tools import WEB_SEARCH_TOOLS, execute_web_search
from tools.registry import ALL_TOOL_SCHEMAS, TOOL_HANDLER_MAP, MEMORY_DEPENDENT_TOOLS

__all__ = [
    "MEMORY_TOOLS",
    "SAVE_MEMORY_SCHEMA",
    "RECALL_MEMORY_SCHEMA",
    "execute_save_memory",
    "execute_recall_memory",
    "TIME_TOOLS",
    "execute_get_current_time",
    "WEB_SEARCH_TOOLS",
    "execute_web_search",
    "ALL_TOOL_SCHEMAS",
    "TOOL_HANDLER_MAP",
    "MEMORY_DEPENDENT_TOOLS",
]
