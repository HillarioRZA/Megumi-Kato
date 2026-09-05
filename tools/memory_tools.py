"""
LLM Memory Tools Interface for Project Anima.

Provides tool schemas (JSON / function-calling specifications) and execution wrappers
for saving and recalling long-term memories via MemoryManager.
"""

import logging
from typing import Any, Dict, List, Optional
from memory.manager import MemoryManager

logger = logging.getLogger("anima.tools.memory")


# -----------------------------------------------------------------------------
# Function Calling Tool Definitions (Ollama / OpenAI Compatible Schemas)
# -----------------------------------------------------------------------------

SAVE_MEMORY_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "save_memory",
        "description": (
            "Save an important fact, user preference, habit, or new hobby/activity to long-term persistent memory. "
            "Call this function proactively whenever the user mentions learning something new, a habit, preference, "
            "or personal detail (e.g. learning guitar, favorite things), even without an explicit command."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["preference", "fact", "habit", "schedule", "personal"],
                    "description": "Category of memory. Pick the closest match from the allowed list.",
                },
                "content": {
                    "type": "string",
                    "description": "The concise fact or information to remember about Reza or the environment.",
                },
            },
            "required": ["category", "content"],
        },
    },
}

RECALL_MEMORY_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "recall_memory",
        "description": (
            "Search and retrieve past facts, preferences, or details from long-term persistent memory. "
            "Call this function whenever the user mentions or asks about topics, hobbies, or past events that "
            "might have been discussed before (e.g. guitar, hobbies, habits)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keyword or concept to search for in memory (e.g. 'coffee', 'sleeping', 'project').",
                },
                "category": {
                    "type": "string",
                    "enum": ["preference", "fact", "habit", "schedule", "personal"],
                    "description": "Optional category filter. Must be one of the allowed values.",
                },
            },
        },
    },
}

MEMORY_TOOLS: List[Dict[str, Any]] = [
    SAVE_MEMORY_SCHEMA,
    RECALL_MEMORY_SCHEMA,
]


# -----------------------------------------------------------------------------
# Tool Execution Handlers
# -----------------------------------------------------------------------------

def execute_save_memory(
    category: str,
    content: str,
    memory_manager: MemoryManager,
) -> str:
    """
    Execute save_memory tool by persisting data through MemoryManager.

    Args:
        category (str): Memory category.
        content (str): Memory content text.
        memory_manager (MemoryManager): Active memory manager instance.

    Returns:
        str: Status response string for LLM tool return.
    """
    if not memory_manager:
        return "Error: MemoryManager is not available."

    mem_id = memory_manager.remember(category=category, content=content)
    if mem_id > 0:
        msg = f"Successfully saved memory (ID: {mem_id}) under category '{category}'."
        logger.info(msg)
        return msg
    else:
        return "Failed to save memory to database."


def execute_recall_memory(
    memory_manager: MemoryManager,
    query: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """
    Execute recall_memory tool by querying MemoryManager.

    Args:
        memory_manager (MemoryManager): Active memory manager instance.
        query (Optional[str]): Keyword search query.
        category (Optional[str]): Category filter.

    Returns:
        str: Formatted string of retrieved memories.
    """
    if not memory_manager:
        return "Error: MemoryManager is not available."

    results = memory_manager.recall(keyword=query, category=category, limit=5)
    if not results:
        return f"No memories found matching query='{query or ''}' and category='{category or ''}'."

    formatted = []
    for r in results:
        formatted.append(f"[{r['category'].upper()}] (ID: {r['id']}): {r['content']}")

    return "\n".join(formatted)
