"""
Database Schemas and Table Initialization for Project Anima.

Defines DDL definitions for memories, activity_log, and chat_history tables,
providing automated schema initialization.
"""

import logging
from memory.connection import get_connection

logger = logging.getLogger("anima.memory.schemas")

CREATE_MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_MEMORIES_INDEX = """
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories (category);
"""

CREATE_ACTIVITY_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    app_name TEXT,
    window_title TEXT,
    duration_seconds INTEGER DEFAULT 0
);
"""

CREATE_ACTIVITY_LOG_INDEX = """
CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log (timestamp);
"""

CREATE_CHAT_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    session_id TEXT DEFAULT 'default'
);
"""

CREATE_CHAT_HISTORY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history (session_id, timestamp);
"""

ALL_SCHEMA_STATEMENTS = [
    CREATE_MEMORIES_TABLE,
    CREATE_MEMORIES_INDEX,
    CREATE_ACTIVITY_LOG_TABLE,
    CREATE_ACTIVITY_LOG_INDEX,
    CREATE_CHAT_HISTORY_TABLE,
    CREATE_CHAT_HISTORY_INDEX,
]


def init_db(db_path: str = "memory/anima_memory.db") -> None:
    """
    Initialize SQLite database tables and indices if they do not already exist.

    Args:
        db_path (str): Filepath to the SQLite database.
    """
    logger.info(f"Initializing database schema at {db_path}...")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for statement in ALL_SCHEMA_STATEMENTS:
            cursor.execute(statement)
        cursor.close()
    logger.info("Database schema initialized successfully.")
