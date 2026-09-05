"""
Unit tests for core.log_manager module.
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from core.log_manager import get_next_log_file, setup_session_logging, SessionLogger


class TestLogManager(unittest.TestCase):
    """Test suite for log file naming, attempt incrementation, and session recording."""

    def setUp(self) -> None:
        """Create a temporary directory for test logs."""
        self.test_log_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(self.test_log_dir, ignore_errors=True)

    def test_log_filename_format(self) -> None:
        """Test that log filename matches [tanggal][waktu]-[n].txt format."""
        ref_time = datetime(2026, 9, 2, 1, 30, 45)
        log_path, attempt = get_next_log_file(
            log_dir=self.test_log_dir,
            extension="txt",
            current_time=ref_time,
        )

        self.assertEqual(attempt, 1)
        self.assertEqual(log_path.name, "20260902_013045-1.txt")

    def test_attempt_sequential_increment(self) -> None:
        """Test that consecutive log files on the same day increment 'n' (1, 2, 3...)."""
        ref_time_1 = datetime(2026, 9, 2, 1, 30, 0)
        log_path_1, attempt_1 = get_next_log_file(
            log_dir=self.test_log_dir,
            extension="txt",
            current_time=ref_time_1,
        )
        # Create file 1
        log_path_1.touch()
        self.assertEqual(attempt_1, 1)

        # Generate file 2
        ref_time_2 = datetime(2026, 9, 2, 1, 35, 0)
        log_path_2, attempt_2 = get_next_log_file(
            log_dir=self.test_log_dir,
            extension="txt",
            current_time=ref_time_2,
        )
        log_path_2.touch()
        self.assertEqual(attempt_2, 2)
        self.assertEqual(log_path_2.name, "20260902_013500-2.txt")

        # Generate file 3
        ref_time_3 = datetime(2026, 9, 2, 1, 40, 0)
        log_path_3, attempt_3 = get_next_log_file(
            log_dir=self.test_log_dir,
            extension="txt",
            current_time=ref_time_3,
        )
        self.assertEqual(attempt_3, 3)
        self.assertEqual(log_path_3.name, "20260902_014000-3.txt")

    def test_session_logger_recording(self) -> None:
        """Test SessionLogger turn recording and session summary generation."""
        with SessionLogger(log_dir=self.test_log_dir, extension="txt") as session:
            session.record_turn("Halo Megumi", "Yeah.")
            session.record_turn("Lagi ngapain?", "Cuma di sini.")

            log_file = session.log_file_path

        self.assertTrue(log_file.exists())
        content = log_file.read_text(encoding="utf-8")

        self.assertIn("PROJECT ANIMA — TERMINAL TEST & SESSION LOG", content)
        self.assertIn("Percobaan Ke : #1", content)
        self.assertIn("Anda   > Halo Megumi", content)
        self.assertIn("Megumi > Yeah.", content)
        self.assertIn("Total Interaksi  : 2 turn", content)
        self.assertIn("SESSION SUMMARY", content)


if __name__ == "__main__":
    unittest.main()
