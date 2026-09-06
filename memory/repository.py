"""
Low-Level SQL Repository for Project Anima Memory System.

Provides pure CRUD database operations for memories, activity logs, and chat history.
All SQL LIKE wildcards are sanitized to prevent unintended matches.
"""

import logging
from typing import Any, Dict, List, Optional
from memory.connection import get_connection

logger = logging.getLogger("anima.memory.repository")


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------

def _escape_like(value: str) -> str:
    """
    Escape SQL LIKE wildcard characters in user-provided search terms.

    Prevents literal '%' or '_' in keyword values from being treated
    as wildcards in SQL LIKE expressions.

    Args:
        value (str): Raw keyword string.

    Returns:
        str: Escaped string safe for use in SQL LIKE clauses.
    """
    return value.replace("%", r"\%").replace("_", r"\_")


# -----------------------------------------------------------------------------
# Memories CRUD Operations
# -----------------------------------------------------------------------------

def save_memory(
    db_path: str,
    category: str,
    content: str,
    memory_id: Optional[int] = None,
) -> int:
    """
    Insert a new memory or update an existing memory record.

    Args:
        db_path (str): Database path.
        category (str): Memory category (e.g. 'preference', 'fact', 'schedule').
        content (str): Textual memory information.
        memory_id (Optional[int]): If provided, updates the existing memory.

    Returns:
        int: The memory ID created or updated.
    """
    category_clean = category.strip().lower()
    content_clean = content.strip()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if memory_id is not None:
            cursor.execute(
                """
                UPDATE memories
                SET category = ?, content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (category_clean, content_clean, memory_id),
            )
            target_id = memory_id
        else:
            cursor.execute(
                """
                INSERT INTO memories (category, content, created_at, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (category_clean, content_clean),
            )
            target_id = cursor.lastrowid or 0
        cursor.close()

    logger.debug(f"Saved memory [ID: {target_id}, Category: {category_clean}]")
    return target_id


def search_memories(
    db_path: str,
    keyword: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    category: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search memories filtered by category and/or keyword matching.

    If ``keywords`` (plural) is provided, matches ANY of the given keywords
    (OR condition). ``keyword`` (singular) is kept for backward compatibility
    and treated as a single-item list when ``keywords`` is not given.
    All keyword values are sanitized against SQL LIKE wildcard injection.

    Args:
        db_path (str): Database path.
        keyword (Optional[str]): Single text to search inside memory content.
        keywords (Optional[List[str]]): Multiple keywords matched with OR logic.
        category (Optional[str]): Category to filter by.
        limit (int): Maximum number of records to return.

    Returns:
        List[Dict[str, Any]]: List of dictionary representations of memory records.
    """
    query = "SELECT id, category, content, created_at, updated_at FROM memories WHERE 1=1"
    params: List[Any] = []

    if category:
        query += " AND category = ?"
        params.append(category.strip().lower())

    # Merge singular and plural keyword arguments; keywords list takes precedence
    effective_keywords: List[str] = keywords if keywords else ([keyword] if keyword else [])
    effective_keywords = [k for k in effective_keywords if k and k.strip()]

    if effective_keywords:
        escaped = [_escape_like(kw.strip()) for kw in effective_keywords]
        conditions = " OR ".join([r"content LIKE ? ESCAPE '\'" ] * len(escaped))
        query += f" AND ({conditions})"
        params.extend([f"%{kw}%" for kw in escaped])

    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    results: List[Dict[str, Any]] = []
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        for row in cursor.fetchall():
            results.append(dict(row))
        cursor.close()

    return results


def delete_memory(db_path: str, memory_id: int) -> bool:
    """
    Delete a specific memory by its ID.

    Args:
        db_path (str): Database path.
        memory_id (int): Primary key ID of the memory.

    Returns:
        bool: True if a row was deleted, False otherwise.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        cursor.close()

    return deleted


def clear_all_data(db_path: str) -> bool:
    """
    Delete ALL rows from memories, activity_log, and chat_history tables.

    Does not drop tables — schema remains intact for continued use.
    Intended for full database resets between phases (e.g., after Fase 5).

    Args:
        db_path (str): Database path.

    Returns:
        bool: True if executed successfully.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories")
        cursor.execute("DELETE FROM activity_log")
        cursor.execute("DELETE FROM chat_history")
        cursor.execute("DELETE FROM mood_log")
        cursor.close()

    logger.info(f"Cleared ALL data (memories, activity_log, chat_history) from {db_path}.")
    return True


# -----------------------------------------------------------------------------
# Activity Log Operations
# -----------------------------------------------------------------------------

def insert_activity_log(
    db_path: str,
    app_name: str,
    window_title: str,
    duration_seconds: int = 0,
) -> int:
    """
    Insert a user desktop activity event into activity_log.

    Args:
        db_path (str): Database path.
        app_name (str): Active application executable or name.
        window_title (str): Active window title string.
        duration_seconds (int): Duration spent on the window in seconds.

    Returns:
        int: Created activity record ID.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activity_log (app_name, window_title, duration_seconds, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (app_name.strip(), window_title.strip(), duration_seconds),
        )
        row_id = cursor.lastrowid or 0
        cursor.close()

    return row_id


def get_recent_activities(
    db_path: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most recent activity log records.

    Args:
        db_path (str): Database path.
        limit (int): Number of activity records.

    Returns:
        List[Dict[str, Any]]: List of activity records ordered by timestamp descending.
    """
    results: List[Dict[str, Any]] = []
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, app_name, window_title, duration_seconds
            FROM activity_log
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        for row in cursor.fetchall():
            results.append(dict(row))
        cursor.close()

    return results


# -----------------------------------------------------------------------------
# Chat History Operations
# -----------------------------------------------------------------------------

def insert_chat_message(
    db_path: str,
    role: str,
    content: str,
    session_id: str = "default",
) -> int:
    """
    Persist a conversation message to chat_history.

    Args:
        db_path (str): Database path.
        role (str): Message role ('user', 'assistant', 'system').
        content (str): Message text.
        session_id (str): Session identifier.

    Returns:
        int: Created message ID.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_history (role, content, session_id, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (role.strip(), content.strip(), session_id.strip()),
        )
        msg_id = cursor.lastrowid or 0
        cursor.close()

    return msg_id


def get_recent_chat_history(
    db_path: str,
    limit: int = 16,
    session_id: Optional[str] = "default",
) -> List[Dict[str, str]]:
    """
    Retrieve the last ``limit`` messages in chronological order (oldest to newest).

    Args:
        db_path (str): Database path.
        limit (int): Number of messages to retrieve.
        session_id (Optional[str]): If specified, filters by session identifier.

    Returns:
        List[Dict[str, str]]: Chronologically ordered list of message dictionaries with 'role' and 'content'.
    """
    query = """
    SELECT role, content FROM (
        SELECT id, role, content, timestamp
        FROM chat_history
        WHERE (session_id = ? OR ? IS NULL)
        ORDER BY id DESC
        LIMIT ?
    ) ORDER BY id ASC
    """
    results: List[Dict[str, str]] = []
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id, session_id, limit))
        for row in cursor.fetchall():
            results.append({"role": str(row["role"]), "content": str(row["content"])})
        cursor.close()

    return results


def clear_chat_history(
    db_path: str,
    session_id: Optional[str] = None,
) -> bool:
    """
    Delete chat history messages.

    Args:
        db_path (str): Database path.
        session_id (Optional[str]): If provided, deletes only that session's chat. If None, deletes all.

    Returns:
        bool: True if executed successfully.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if session_id is not None:
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        else:
            cursor.execute("DELETE FROM chat_history")
        cursor.close()

    logger.info(f"Cleared chat history from {db_path} (Session: {session_id or 'ALL'}).")
    return True

# -----------------------------------------------------------------------------
# Mood Log Operations
# -----------------------------------------------------------------------------

def insert_mood_event(db_path: str, score: int, delta: int, event_type: str) -> int:
    """
    Insert a new mood change event into mood_log table.

    Args:
        db_path (str): Path to SQLite database file.
        score (int): Updated mood score after applying delta.
        delta (int): The score change value.
        event_type (str): Type of trigger event.

    Returns:
        int: The inserted row ID, or -1 if execution failed.
    """
    query = """
    INSERT INTO mood_log (score, delta, event_type)
    VALUES (?, ?, ?);
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (score, delta, event_type))
            row_id = cursor.lastrowid or -1
            cursor.close()
            return row_id
    except Exception as exc:
        logger.error(f"Failed to insert mood event into database: {exc}")
        return -1


def get_latest_mood_entry(db_path: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recent entry from mood_log table.

    Args:
        db_path (str): Path to SQLite database file.

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing score, delta, event_type,
        and timestamp, or None if table is empty or error occurs.
    """
    query = """
    SELECT score, delta, event_type, timestamp
    FROM mood_log
    ORDER BY id DESC
    LIMIT 1;
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
            if row:
                return dict(row)
            return None
    except Exception as exc:
        logger.error(f"Failed to retrieve latest mood entry: {exc}")
        return None


def get_mood_history(db_path: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve recent mood log entries for analysis and debugging.

    Args:
        db_path (str): Path to SQLite database file.
        limit (int): Maximum number of records to return.

    Returns:
        List[Dict[str, Any]]: List of mood log records.
    """
    query = """
    SELECT id, score, delta, event_type, timestamp
    FROM mood_log
    ORDER BY id DESC
    LIMIT ?;
    """
    results: List[Dict[str, Any]] = []
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            for row in cursor.fetchall():
                results.append(dict(row))
            cursor.close()
            return results
    except Exception as exc:
        logger.error(f"Failed to retrieve mood history: {exc}")
        return []
