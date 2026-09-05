import pathlib
import tempfile
import unittest
from unittest.mock import patch

from tools.inspection_tools import (
    execute_scan_workspace,
    execute_list_running_applications,
)


class TestInspectionTools(unittest.TestCase):
    """Unit test suite for tools.inspection_tools module."""

    def setUp(self):
        # Temp directory mocking WORKSPACE_DIR to keep tests isolated
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = pathlib.Path(self.temp_dir.name).resolve()

        self.workspace_patcher = patch(
            "tools.inspection_tools.WORKSPACE_DIR", self.temp_path
        )
        self.mock_workspace = self.workspace_patcher.start()

    def tearDown(self):
        self.workspace_patcher.stop()
        self.temp_dir.cleanup()

    def test_scan_workspace_empty_directory(self):
        """Test scan_workspace on an empty workspace directory."""
        res = execute_scan_workspace()
        self.assertIn("is currently empty", res)

    def test_scan_workspace_with_files_and_folders(self):
        """Test scan_workspace accurately lists files and subdirectories."""
        (self.temp_path / "notes.txt").write_text("Hello World", encoding="utf-8")
        (self.temp_path / "docs").mkdir()
        (self.temp_path / "docs" / "report.md").write_text("Report content", encoding="utf-8")

        res_root = execute_scan_workspace()
        self.assertIn("[FILE] notes.txt", res_root)
        self.assertIn("[DIR]  docs/", res_root)

        res_sub = execute_scan_workspace(subfolder="docs")
        self.assertIn("[FILE] report.md", res_sub)

    def test_scan_workspace_sandbox_breach_blocked(self):
        """Test that scan_workspace blocks path traversal outside sandbox."""
        res = execute_scan_workspace(subfolder="../../Windows/System32")
        self.assertIn("Security Exception", res)
        self.assertIn("Access denied", res)

    def test_list_running_applications_without_filter(self):
        """Test list_running_applications returns active process list without errors."""
        res = execute_list_running_applications()
        self.assertIn("Active Running Applications:", res)

    def test_list_running_applications_with_filter(self):
        """Test list_running_applications handles filter queries gracefully."""
        res_bogus = execute_list_running_applications(filter_name="non_existent_app_xyz_123")
        self.assertIn("No active processes found matching filter", res_bogus)


if __name__ == "__main__":
    unittest.main()