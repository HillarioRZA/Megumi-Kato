"""
Database Connection Manager for Project Anima Memory System.

Provides thread-safe SQLite connection context managers configured with WAL mode,
foreign key enforcement, and dictionary-accessible rows.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

logger = logging.getLogger("anima.memory.connection")


@contextmanager
def get_connection(db_path: str = "memory/anima_memory.db") -> Generator[sqlite3.Connection, None, None]:
    """
    Provide a transactional SQLite database connection context.

    Ensures WAL PRAGMA and foreign key enforcement are enabled. Automatically commits
    on success or rolls back on exception, closing the connection cleanly.

    Args:
        db_path (str): Filepath to the SQLite database.

    Yields:
        sqlite3.Connection: Configured SQLite connection with Row row_factory.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(path),
        timeout=10.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()

        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error(f"Database transaction error on {db_path}: {exc}")
        raise
    finally:
        conn.close()
