"""
Mood Tools Module for Project Anima.

Defines the JSON schema and handler execution logic for adjusting Megumi's
internal mood state based on emotional user interactions.
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from memory.mood_manager import MoodManager

logger = logging.getLogger("anima.tools.mood")

ADJUST_MOOD_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "adjust_mood",
        "description": (
            "Call this when Reza's message genuinely affects how you feel "
            "about the interaction right now — being praised, having a "
            "nice/warm exchange, sharing something personal (all positive), "
            "or being dismissed, ignored, or called by the wrong name "
            "(negative). Do NOT call this for neutral/routine exchanges — "
            "only when something in this specific message actually stands "
            "out emotionally, not just because the conversation is ongoing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": [
                        "praised",
                        "nice_conversation",
                        "shared_something_personal",
                        "wrong_name_used",
                        "dismissed_or_ignored",
                    ],
                    "description": "The type of emotional event that just happened.",
                },
            },
            "required": ["event_type"],
        },
    },
}

MOOD_TOOLS: List[Dict[str, Any]] = [ADJUST_MOOD_SCHEMA]


def execute_adjust_mood(event_type: str, mood_manager: Optional["MoodManager"] = None) -> str:
    """
    Execute the adjust_mood tool to update Megumi's mood score in the database.

    Args:
        event_type (str): Key matching one of the supported mood event triggers.
        mood_manager (Optional[MoodManager]): Injected MoodManager instance.

    Returns:
        str: Result message string sent back to LLM context.
    """
    if not mood_manager:
        logger.error("execute_adjust_mood called but mood_manager is None.")
        return "Error: MoodManager is not available."

    try:
        new_score = mood_manager.apply_event(event_type)
        logger.info(
            f"Tool 'adjust_mood' executed successfully [Event: {event_type}, New Score: {new_score}]"
        )
        return f"Mood adjusted (event: {event_type}). Current internal state updated."
    except Exception as exc:
        logger.error(f"Failed to adjust mood ({event_type}): {exc}")
        return "Error adjusting mood state."