"""
Memory Manager Module for Project Anima.

Coordinates high-level persistent memory storage, contextual memory retrieval,
activity logging, and session chat persistence for the Orchestrator.
"""

import logging
from typing import Any, Dict, List, Optional

from memory.schemas import init_db
from memory import repository
from memory.keyword_extractor import extract_keywords

logger = logging.getLogger("anima.memory.manager")


class MemoryManager:
    """
    High-level coordinator for persistent SQLite memory and chat history.

    Attributes:
        db_path (str): Filepath to SQLite database.
        session_id (str): Session identifier for grouping chat records.
    """

    def __init__(
        self,
        db_path: str = "memory/anima_memory.db",
        session_id: str = "default",
    ) -> None:
        """
        Initialize MemoryManager and ensure SQLite tables exist.

        Args:
            db_path (str): Filepath to the SQLite database.
            session_id (str): Active session identifier.
        """
        self.db_path = db_path
        self.session_id = session_id

        try:
            init_db(self.db_path)
            logger.info(f"MemoryManager initialized on database: {self.db_path}")
        except Exception as exc:
            logger.error(f"Failed to initialize database at {self.db_path}: {exc}")

    # -------------------------------------------------------------------------
    # Memories Management
    # -------------------------------------------------------------------------

    def remember(
        self,
        category: str,
        content: str,
        memory_id: Optional[int] = None,
    ) -> int:
        """
        Store a fact, preference, or detail into persistent memory.

        Args:
            category (str): Category (e.g. 'preference', 'fact', 'habit').
            content (str): Information to remember.
            memory_id (Optional[int]): Optional ID to update existing memory.

        Returns:
            int: Memory ID.
        """
        try:
            return repository.save_memory(
                db_path=self.db_path,
                category=category,
                content=content,
                memory_id=memory_id,
            )
        except Exception as exc:
            logger.error(f"Error saving memory ({category}: {content}): {exc}")
            return 0

    def recall(
        self,
        keyword: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories matching category and/or keyword search.

        Supports both single keyword (backward-compatible) and multiple keywords
        with OR logic via the ``keywords`` parameter.

        Args:
            keyword (Optional[str]): Single text search query (backward-compatible).
            keywords (Optional[List[str]]): Multiple keywords matched with OR logic.
            category (Optional[str]): Category filter.
            limit (int): Maximum memories to return.

        Returns:
            List[Dict[str, Any]]: List of matching memories.
        """
        try:
            return repository.search_memories(
                db_path=self.db_path,
                keyword=keyword,
                keywords=keywords,
                category=category,
                limit=limit,
            )
        except Exception as exc:
            logger.error(f"Error recalling memories (keywords={keywords or keyword}, category={category}): {exc}")
            return []

    def forget(self, memory_id: int) -> bool:
        """
        Delete a memory by its ID.

        Args:
            memory_id (int): Memory primary key ID.

        Returns:
            bool: True if deleted.
        """
        try:
            return repository.delete_memory(db_path=self.db_path, memory_id=memory_id)
        except Exception as exc:
            logger.error(f"Error deleting memory ID {memory_id}: {exc}")
            return False

    def get_memory_context_prompt(self, query: Optional[str] = None, limit: int = 5) -> str:
        """
        Build a formatted memory context block for injection into the System Prompt.

        Extracts meaningful keywords from the raw query text before searching,
        rather than passing the full raw sentence into SQL LIKE. This greatly
        improves match rate for natural language inputs.

        Args:
            query (Optional[str]): Raw user input text to extract keywords from.
            limit (int): Maximum memory entries to include.

        Returns:
            str: Formatted memory text block or empty string if no memories found.
        """
        extracted = extract_keywords(query) if query else []
        if not extracted:
            return ""

        logger.debug(f"Memory search keywords extracted from query: {extracted}")
        memories = self.recall(keywords=extracted, limit=limit)
        if not memories:
            return ""

        lines = ["[Relevant Long-Term Memories]"]
        for m in memories:
            lines.append(f"- ({m['category']}) {m['content']}")

        return "\n".join(lines).strip()

    # -------------------------------------------------------------------------
    # Chat History Persistence & Recovery
    # -------------------------------------------------------------------------

    def save_chat_turn(self, role: str, content: str) -> int:
        """
        Save a chat message to the persistent chat_history table.

        Args:
            role (str): 'user' or 'assistant'.
            content (str): Message content.

        Returns:
            int: Message ID.
        """
        try:
            return repository.insert_chat_message(
                db_path=self.db_path,
                role=role,
                content=content,
                session_id=self.session_id,
            )
        except Exception as exc:
            logger.error(f"Error saving chat message ({role}): {exc}")
            return 0

    def load_recent_chat(self, limit: int = 16) -> List[Dict[str, str]]:
        """
        Recover the last N messages from database for the current session.

        Args:
            limit (int): Maximum messages to recover.

        Returns:
            List[Dict[str, str]]: Chronological message turn dictionaries.
        """
        try:
            return repository.get_recent_chat_history(
                db_path=self.db_path,
                limit=limit,
                session_id=self.session_id,
            )
        except Exception as exc:
            logger.error(f"Error loading chat history: {exc}")
            return []

    def clear_chat(self, all_sessions: bool = False) -> bool:
        """
        Clear persistent chat history.

        Args:
            all_sessions (bool): If True, clears all session histories.

        Returns:
            bool: True on success.
        """
        target_session = None if all_sessions else self.session_id
        try:
            return repository.clear_chat_history(
                db_path=self.db_path,
                session_id=target_session,
            )
        except Exception as exc:
            logger.error(f"Error clearing chat history: {exc}")
            return False

    # -------------------------------------------------------------------------
    # Activity Log Operations
    # -------------------------------------------------------------------------

    def log_activity(self, app_name: str, window_title: str, duration_seconds: int = 0) -> int:
        """
        Record user desktop activity for contextual awareness.

        Args:
            app_name (str): Active application name.
            window_title (str): Window title.
            duration_seconds (int): Time spent in seconds.

        Returns:
            int: Activity ID.
        """
        try:
            return repository.insert_activity_log(
                db_path=self.db_path,
                app_name=app_name,
                window_title=window_title,
                duration_seconds=duration_seconds,
            )
        except Exception as exc:
            logger.error(f"Error logging activity: {exc}")
            return 0

    def get_recent_activities(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve recent user activities."""
        try:
            return repository.get_recent_activities(db_path=self.db_path, limit=limit)
        except Exception as exc:
            logger.error(f"Error retrieving activities: {exc}")
            return []

    # -------------------------------------------------------------------------
    # Full Reset Utility
    # -------------------------------------------------------------------------

    def reset_all(self) -> bool:
        """
        Wipe all persistent memory data from memories, activity_log, and chat_history.

        Schema and tables remain intact — only row data is deleted. Intended for
        the planned full database reset after Fase 5, before Fase 6 mood system
        goes live with clean state.

        Returns:
            bool: True if reset completed successfully, False on error.
        """
        try:
            result = repository.clear_all_data(db_path=self.db_path)
            logger.info("MemoryManager: Full data reset completed successfully.")
            return result
        except Exception as exc:
            logger.error(f"Error resetting all memory data: {exc}")
            return False
