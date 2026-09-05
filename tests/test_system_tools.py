"""
Unit tests for System Tools (Phase 5) in Project Anima.

Tests sandboxing security, path traversal prevention, file creation (.txt, .md, .pdf),
PDF read blocking, application blocklist, and system status metrics retrieval.
"""

import pathlib
import unittest
from tools.system_tools import (
    WORKSPACE_DIR,
    execute_manage_local_file,
    execute_manage_application,
    execute_get_system_status,
)


class TestSystemTools(unittest.TestCase):
    """Test suite for system_tools.py handlers and guardrails."""

    def setUp(self) -> None:
        """Ensure test directory exists before each test."""
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    def test_sandbox_path_traversal_blocked(self) -> None:
        """Verify that attempting path traversal outside D:\\Megumi Kato is blocked."""
        malicious_file = "../../Windows/System32/test_hack.txt"
        result = execute_manage_local_file(action="create", file_name=malicious_file, content="hack")
        self.assertIn("Security Exception", result)
        self.assertIn("outside the allowed workspace", result)

    def test_unsupported_file_extension_blocked(self) -> None:
        """Verify that creating files with unsupported extensions (.exe, .py, etc.) is blocked."""
        result = execute_manage_local_file(action="create", file_name="script.py", content="print('hello')")
        self.assertIn("Security Exception", result)
        self.assertIn("Unsupported file type", result)

    def test_create_read_delete_valid_txt_and_md(self) -> None:
        """Verify full CRUD cycle for allowed .txt and .md files inside the sandbox."""
        test_file = "test_note.md"
        content = "# Anima Test Journal\nTesting Phase 5 system_tools."

        # 1. Create
        create_res = execute_manage_local_file(action="create", file_name=test_file, content=content)
        self.assertIn("Successfully created/updated file", create_res)

        # 2. Read
        read_res = execute_manage_local_file(action="read", file_name=test_file)
        self.assertIn(content, read_res)

        # 3. Delete
        delete_res = execute_manage_local_file(action="delete", file_name=test_file)
        self.assertIn("Successfully deleted file", delete_res)

    def test_pdf_creation_and_read_restriction(self) -> None:
        """Verify PDF generation works via fpdf2 and PDF reading returns RAG restriction message."""
        pdf_file = "test_report.pdf"
        content = "This is a generated PDF report test."

        # 1. Create PDF
        create_res = execute_manage_local_file(action="create", file_name=pdf_file, content=content)
        self.assertIn("Successfully generated PDF file", create_res)

        # 2. Attempt Read PDF (Must be blocked)
        read_res = execute_manage_local_file(action="read", file_name=pdf_file)
        self.assertIn("Reading PDF files is not supported yet", read_res)

        # Cleanup
        execute_manage_local_file(action="delete", file_name=pdf_file)

    def test_application_blocklist_protection(self) -> None:
        """Verify that attempts to terminate protected processes in PROCESS_BLOCKLIST are denied."""
        protected_apps = ["python.exe", "code.exe", "cmd.exe"]
        for app in protected_apps:
            result = execute_manage_application(action="close", app_name=app)
            self.assertIn("Security Denial", result)
            self.assertIn("protected by safety blocklist", result)

    def test_get_system_status_returns_valid_metrics(self) -> None:
        """Verify system status handler returns CPU and RAM metrics without error."""
        result = execute_get_system_status()
        self.assertIn("System Status Metrics:", result)
        self.assertIn("CPU Usage:", result)
        self.assertIn("RAM Usage:", result)


if __name__ == "__main__":
    unittest.main()