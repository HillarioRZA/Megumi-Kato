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
from tools.weather_tools import WEATHER_TOOLS, execute_get_weather
from tools.web_reader_tools import WEB_READER_TOOLS, execute_read_web_page
from tools.system_tools import (
    SYSTEM_TOOLS,
    execute_manage_local_file,
    execute_manage_application,
    execute_get_system_status,
)
from tools.inspection_tools import (
    INSPECTION_TOOLS,
    execute_scan_workspace,
    execute_list_running_applications,
)
# All tool schemas combined, sent to Ollama's `tools` parameter
ALL_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    *MEMORY_TOOLS,
    *TIME_TOOLS,
    *WEB_SEARCH_TOOLS,
    *WEATHER_TOOLS,
    *WEB_READER_TOOLS,
    *SYSTEM_TOOLS,
    *INSPECTION_TOOLS,
]

# Tool name → execution handler mapping, used by ToolDispatcher
TOOL_HANDLER_MAP: Dict[str, Callable[..., str]] = {
    "save_memory": execute_save_memory,
    "recall_memory": execute_recall_memory,
    "verify_exact_system_clock": execute_get_current_time,
    "web_search": execute_web_search,
    "get_weather": execute_get_weather,
    "read_web_page": execute_read_web_page,
    "manage_local_file": execute_manage_local_file,
    "manage_application": execute_manage_application,
    "get_system_status": execute_get_system_status,
    "scan_workspace": execute_scan_workspace,
    "list_running_applications": execute_list_running_applications,
}


# Tools that require memory_manager to be injected by the dispatcher
MEMORY_DEPENDENT_TOOLS: frozenset = frozenset({"save_memory", "recall_memory"})
