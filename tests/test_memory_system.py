"""
Unit tests for memory package and tools.memory_tools.
"""

import os
import shutil
import tempfile
import unittest
from collections import deque
from unittest.mock import MagicMock

from core.orchestrator import Orchestrator
from core.llm_client import OllamaClient
from memory.connection import get_connection
from memory.schemas import init_db
from memory.manager import MemoryManager
from tools.memory_tools import execute_save_memory, execute_recall_memory, MEMORY_TOOLS


class TestMemorySystem(unittest.TestCase):
    """Test suite for Memory package components and tools."""

    def setUp(self) -> None:
        """Create temporary database directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.manager = MemoryManager(db_path=self.db_path, session_id="test_session")

    def tearDown(self) -> None:
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_schema_initialization(self) -> None:
        """Test database tables exist after initialization."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row["name"] for row in cursor.fetchall()]
            cursor.close()

        self.assertIn("memories", tables)
        self.assertIn("activity_log", tables)
        self.assertIn("chat_history", tables)

    def test_memories_crud_and_prompt(self) -> None:
        """Test remember, recall, prompt formatting, and forget operations."""
        mem_id = self.manager.remember("preference", "Suka matcha latte.")
        self.assertGreater(mem_id, 0)

        recalled = self.manager.recall(keyword="matcha")
        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["content"], "Suka matcha latte.")

        prompt = self.manager.get_memory_context_prompt(query="matcha")
        self.assertIn("[Relevant Long-Term Memories]", prompt)
        self.assertIn("Suka matcha latte.", prompt)

        deleted = self.manager.forget(mem_id)
        self.assertTrue(deleted)
        self.assertEqual(len(self.manager.recall(keyword="matcha")), 0)

    def test_chat_persistence_and_sliding_window(self) -> None:
        """Test chat persistence and sliding window recovery."""
        mock_client = MagicMock(spec=OllamaClient)
        mock_client.chat.return_value = "Hai Reza."

        orchestrator = Orchestrator(
            llm_client=mock_client,
            memory_manager=self.manager,
        )

        orchestrator.process_message("Pesan 1")
        orchestrator.process_message("Pesan 2")

        chat_history = self.manager.load_recent_chat()
        self.assertEqual(len(chat_history), 4)

        # Re-instantiate Orchestrator with the same manager
        orchestrator_2 = Orchestrator(
            llm_client=mock_client,
            memory_manager=self.manager,
        )
        self.assertEqual(len(orchestrator_2.history), 4)
        self.assertEqual(orchestrator_2.history[0]["content"], "Pesan 1")

    def test_memory_tools_execution(self) -> None:
        """Test tool execution handlers."""
        save_res = execute_save_memory(
            category="fact",
            content="Ulang tahun Reza tanggal 10 Oktober.",
            memory_manager=self.manager,
        )
        self.assertIn("Successfully saved memory", save_res)

        recall_res = execute_recall_memory(
            query="Oktober",
            memory_manager=self.manager,
        )
        self.assertIn("[FACT]", recall_res)
        self.assertIn("10 Oktober", recall_res)


if __name__ == "__main__":
    unittest.main()
