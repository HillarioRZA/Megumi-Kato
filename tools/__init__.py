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
from tools.weather_tools import WEATHER_TOOLS, GET_WEATHER_SCHEMA, execute_get_weather
from tools.web_reader_tools import WEB_READER_TOOLS, READ_WEB_PAGE_SCHEMA, execute_read_web_page
from tools.system_tools import (
    SYSTEM_TOOLS,
    MANAGE_LOCAL_FILE_SCHEMA,
    MANAGE_APPLICATION_SCHEMA,
    GET_SYSTEM_STATUS_SCHEMA,
    execute_manage_local_file,
    execute_manage_application,
    execute_get_system_status,
)
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
    "WEATHER_TOOLS",
    "GET_WEATHER_SCHEMA",
    "execute_get_weather",
    "WEB_READER_TOOLS",
    "READ_WEB_PAGE_SCHEMA",
    "execute_read_web_page",
    "SYSTEM_TOOLS",
    "MANAGE_LOCAL_FILE_SCHEMA",
    "MANAGE_APPLICATION_SCHEMA",
    "GET_SYSTEM_STATUS_SCHEMA",
    "execute_manage_local_file",
    "execute_manage_application",
    "execute_get_system_status",
    "ALL_TOOL_SCHEMAS",
    "TOOL_HANDLER_MAP",
    "MEMORY_DEPENDENT_TOOLS",
]
