"""
Time Tool for Project Anima.

Provides schema definition and execution handler for the get_current_time tool,
which returns the current local system datetime in a readable format.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger("anima.tools.time")

GET_CURRENT_TIME_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "verify_exact_system_clock",
        "description": (
            "Get the exact live system date and time. "
            "Use this tool when the user explicitly asks to re-check, verify, or requests exact live current time. "
            "Do NOT call this tool for general conversational time questions when approximate time is already provided in the system context."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

TIME_TOOLS: List[Dict[str, Any]] = [GET_CURRENT_TIME_SCHEMA]


def execute_get_current_time() -> str:
    """
    Return the current local system date and time as a human-readable string.

    Attempts to format with full locale-aware representation first; falls back
    to ISO 8601 format on any locale or timezone error.

    Returns:
        str: Formatted current datetime string ready for LLM consumption.
    """
    try:
        now = datetime.now()
        day_name = now.strftime("%A")          # e.g. Wednesday
        date_str = now.strftime("%d %B %Y")    # e.g. 03 September 2026
        time_str = now.strftime("%H:%M:%S")    # e.g. 02:15:30
        result = f"{day_name}, {date_str} — {time_str} (local system time)"
        logger.info(f"get_current_time executed: {result}")
        return result
    except Exception as exc:
        fallback = datetime.now().isoformat()
        logger.warning(f"get_current_time formatting failed ({exc}), falling back to ISO: {fallback}")
        return fallback


