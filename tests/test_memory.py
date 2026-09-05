"""
Comprehensive Automated Test Suite for Phase 3 — Memory System.

Verifies:
1. Sliding window deque eviction (short-term memory capacity).
2. SQLite schema creation and CRUD operations (memories, activity_log, chat_history).
3. Cross-session persistence and state recovery in Orchestrator.
4. LLM tool wrappers (save_memory & recall_memory).
"""

import os
import sys
import shutil
import tempfile
import logging
from collections import deque
from pathlib import Path
from unittest.mock import MagicMock

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from core.config import Config
from core.llm_client import OllamaClient
from core.orchestrator import Orchestrator
from personality.personality_builder import PersonalityBuilder
from memory.connection import get_connection
from memory.schemas import init_db
from memory import repository
from memory.manager import MemoryManager
from tools.memory_tools import (
    MEMORY_TOOLS,
    execute_save_memory,
    execute_recall_memory,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def test_sliding_window_deque() -> None:
    print("\n[1] Testing Short-Term Memory Sliding Window (collections.deque)...")
    limit = 16
    history: deque = deque(maxlen=limit)

    # Insert 20 messages
    for i in range(1, 21):
        history.append({"role": "user" if i % 2 == 1 else "assistant", "content": f"Message {i}"})

    assert len(history) == limit, f"Expected deque length {limit}, got {len(history)}"
    assert history[0]["content"] == "Message 5", f"Expected oldest message to be Message 5, got {history[0]['content']}"
    assert history[-1]["content"] == "Message 20", f"Expected newest message to be Message 20, got {history[-1]['content']}"
    print("    Sliding Window Deque Eviction: PASSED!")


def test_sqlite_crud() -> None:
    print("\n[2] Testing SQLite Schema & CRUD Operations across all 3 tables...")
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_memory.db")

    try:
        # Schema Init
        init_db(temp_db)
        assert os.path.exists(temp_db), "Database file was not created"

        # 2.1 Memories CRUD
        mem_id = repository.save_memory(
            db_path=temp_db,
            category="preference",
            content="Reza suka kopi hitam tanpa gula.",
        )
        assert mem_id > 0, "Failed to insert memory"

        results = repository.search_memories(db_path=temp_db, keyword="kopi")
        assert len(results) == 1, "Expected 1 search result for 'kopi'"
        assert results[0]["content"] == "Reza suka kopi hitam tanpa gula."

        # Update memory
        repository.save_memory(
            db_path=temp_db,
            category="preference",
            content="Reza suka kopi hitam robusta.",
            memory_id=mem_id,
        )
        updated = repository.search_memories(db_path=temp_db, keyword="robusta")
        assert len(updated) == 1
        assert updated[0]["content"] == "Reza suka kopi hitam robusta."

        # Delete memory
        deleted = repository.delete_memory(db_path=temp_db, memory_id=mem_id)
        assert deleted is True
        assert len(repository.search_memories(db_path=temp_db, keyword="robusta")) == 0

        # 2.2 Activity Log CRUD
        act_id = repository.insert_activity_log(
            db_path=temp_db,
            app_name="Code.exe",
            window_title="Project Anima - VS Code",
            duration_seconds=120,
        )
        assert act_id > 0

        activities = repository.get_recent_activities(db_path=temp_db, limit=5)
        assert len(activities) == 1
        assert activities[0]["app_name"] == "Code.exe"

        # 2.3 Chat History CRUD
        m1 = repository.insert_chat_message(db_path=temp_db, role="user", content="Halo Megumi!")
        m2 = repository.insert_chat_message(db_path=temp_db, role="assistant", content="Halo.")
        assert m1 > 0 and m2 > 0

        chat = repository.get_recent_chat_history(db_path=temp_db, limit=10)
        assert len(chat) == 2
        assert chat[0]["role"] == "user"
        assert chat[1]["role"] == "assistant"

        # Clear chat
        repository.clear_chat_history(db_path=temp_db)
        assert len(repository.get_recent_chat_history(db_path=temp_db, limit=10)) == 0

        print("    SQLite Schemas & CRUD Operations: PASSED!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_cross_session_persistence() -> None:
    print("\n[3] Testing Cross-Session History Persistence & Recovery...")
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "persistence_test.db")

    try:
        # Mock LLM Client
        mock_client = MagicMock(spec=OllamaClient)
        mock_client.chat.return_value = "Aku ingat, Reza."

        # --- SESSION 1 ---
        mem_mgr_1 = MemoryManager(db_path=temp_db, session_id="test_session")
        orchestrator_1 = Orchestrator(
            llm_client=mock_client,
            memory_manager=mem_mgr_1,
        )

        assert len(orchestrator_1.history) == 0, "New session history should initially be empty"

        # User chats in Session 1
        reply1 = orchestrator_1.process_message("Aku suka main game Delta Force.")
        assert len(orchestrator_1.history) == 2

        reply2 = orchestrator_1.process_message("Nanti malam mau main lagi.")
        assert len(orchestrator_1.history) == 4

        # Verify DB directly
        persisted_chat = mem_mgr_1.load_recent_chat(limit=10)
        assert len(persisted_chat) == 4
        assert persisted_chat[0]["content"] == "Aku suka main game Delta Force."

        # Destroy Session 1 objects (simulating application exit)
        del orchestrator_1
        del mem_mgr_1

        # --- SESSION 2 (Restarting App) ---
        mem_mgr_2 = MemoryManager(db_path=temp_db, session_id="test_session")
        orchestrator_2 = Orchestrator(
            llm_client=mock_client,
            memory_manager=mem_mgr_2,
        )

        # Verify recovery on startup!
        assert len(orchestrator_2.history) == 4, f"Expected 4 restored messages, got {len(orchestrator_2.history)}"
        assert orchestrator_2.history[0]["content"] == "Aku suka main game Delta Force."
        assert orchestrator_2.history[2]["content"] == "Nanti malam mau main lagi."

        print("    Cross-Session Persistence & Recovery: PASSED!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_memory_tools() -> None:
    print("\n[4] Testing LLM Memory Tool Wrappers & Schema...")
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "tools_test.db")

    try:
        mem_mgr = MemoryManager(db_path=temp_db)

        # Check Schema validity
        assert len(MEMORY_TOOLS) == 2
        assert MEMORY_TOOLS[0]["function"]["name"] == "save_memory"
        assert MEMORY_TOOLS[1]["function"]["name"] == "recall_memory"

        # Execute save_memory tool
        res_save = execute_save_memory(
            category="habit",
            content="Sering tidur jam 2 pagi karena coding.",
            memory_manager=mem_mgr,
        )
        assert "Successfully saved memory" in res_save

        # Execute recall_memory tool
        res_recall = execute_recall_memory(
            query="coding",
            memory_manager=mem_mgr,
        )
        assert "[HABIT]" in res_recall
        assert "Sering tidur jam 2 pagi" in res_recall

        print("    LLM Memory Tool Interface & Wrappers: PASSED!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 60)
    print("   PROJECT ANIMA — PHASE 3 MEMORY SYSTEM VERIFICATION")
    print("=" * 60)
    test_sliding_window_deque()
    test_sqlite_crud()
    test_cross_session_persistence()
    test_memory_tools()
    print("\n" + "=" * 60)
    print("   [=== ALL PHASE 3 MEMORY TESTS PASSED SUCCESSFULLY ===]")
    print("=" * 60)
