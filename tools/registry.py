"""
Central Tool Registry for Project Anima.

Aggregates all tool schemas and maps tool names to their execution handlers
for dispatch by ToolDispatcher. This module contains no logic — it is purely
an aggregation and registration point.
"""

from typing import Any, Callable, Dict, List

from tools.memory_tools import (
    MEMORY_TOOLS,
    execute_save_memory,
    execute_recall_memory,
)
from tools.time_tools import TIME_TOOLS, execute_get_current_time
from tools.web_search_tools import WEB_SEARCH_TOOLS, execute_web_search

# All tool schemas combined, sent to Ollama's `tools` parameter
ALL_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    *MEMORY_TOOLS,
    *TIME_TOOLS,
    *WEB_SEARCH_TOOLS,
]

# Tool name → execution handler mapping, used by ToolDispatcher
TOOL_HANDLER_MAP: Dict[str, Callable[..., str]] = {
    "save_memory": execute_save_memory,
    "recall_memory": execute_recall_memory,
    "verify_exact_system_clock": execute_get_current_time,
    "web_search": execute_web_search,
}

# Tools that require memory_manager to be injected by the dispatcher
MEMORY_DEPENDENT_TOOLS: frozenset = frozenset({"save_memory", "recall_memory"})
