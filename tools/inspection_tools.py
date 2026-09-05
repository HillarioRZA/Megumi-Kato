"""
Inspection Tools for Project Anima.

Provides read-only observation capabilities:
1. scan_workspace: Inspects all files and directories inside 'D:\Megumi Kato'.
2. list_running_applications: Scans active OS processes to check running desktop apps.
"""

import logging
import pathlib
from typing import Any, Dict, List, Optional
import psutil

logger = logging.getLogger("anima.tools.inspection")

# Hardcoded absolute workspace sandbox directory
WORKSPACE_DIR = pathlib.Path(r"D:\Megumi Kato").resolve()

# --- Tool Schemas ---

SCAN_WORKSPACE_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "scan_workspace",
        "description": (
            "Scan the workspace directory 'D:\\Megumi Kato' to list all currently existing "
            "files and subdirectories with their file sizes. "
            "ALWAYS use this tool to verify file existence before making claims about workspace content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "subfolder": {
                    "type": "string",
                    "description": "Optional relative subfolder path inside workspace to scan (e.g., 'reports'). Leave empty to scan root workspace.",
                }
            },
            "required": [],
        },
    },
}

LIST_RUNNING_APPLICATIONS_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "list_running_applications",
        "description": (
            "Get the list of currently running applications... "
            "IMPORTANT: Even if you already answered a similar question earlier "
            "in this conversation, ALWAYS call this tool again for a fresh check. "
            "Application states change constantly — a previous answer (even from "
            "moments ago) may already be stale. Never reuse a prior answer from "
            "conversation history without re-verifying."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filter_name": {
                    "type": "string",
                    "description": "Optional app/process name filter (e.g., 'chrome', 'notepad'). For multiple apps, separate with commas (e.g., 'chrome, notepad'). Leave empty to list common active desktop applications.",
                }
            },
            "required": [],
        },
    },
}

INSPECTION_TOOLS: List[Dict[str, Any]] = [
    SCAN_WORKSPACE_SCHEMA,
    LIST_RUNNING_APPLICATIONS_SCHEMA,
]


# --- Execution Handlers ---

def execute_scan_workspace(subfolder: Optional[str] = None) -> str:
    """
    Scan files and folders inside workspace sandbox D:\\Megumi Kato.
    """
    try:
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        target_dir = (WORKSPACE_DIR / subfolder.strip()).resolve() if subfolder else WORKSPACE_DIR

        # Sandbox boundary check
        if not str(target_dir).startswith(str(WORKSPACE_DIR)):
            logger.error(f"Sandbox Breach Attempt in scan_workspace: {subfolder}")
            return f"Security Exception: Access denied. '{subfolder}' resolves outside allowed workspace."

        if not target_dir.exists() or not target_dir.is_dir():
            return f"Error: Target directory '{target_dir.name}' does not exist inside workspace."

        items = list(target_dir.iterdir())
        if not items:
            return f"Workspace directory '{target_dir.relative_to(WORKSPACE_DIR)}' is currently empty."

        file_list: List[str] = []
        dir_list: List[str] = []

        for item in items:
            if item.is_file():
                size_kb = round(item.stat().st_size / 1024, 2)
                file_list.append(f"  - [FILE] {item.name} ({size_kb} KB)")
            elif item.is_dir():
                dir_list.append(f"  - [DIR]  {item.name}/")

        output_lines = [f"Workspace Inspection for 'D:\\Megumi Kato\\{target_dir.relative_to(WORKSPACE_DIR)}':"]
        if dir_list:
            output_lines.append("Subdirectories:")
            output_lines.extend(dir_list)
        if file_list:
            output_lines.append("Files:")
            output_lines.extend(file_list)

        logger.info(f"Successfully scanned workspace directory: {target_dir}")
        return "\n".join(output_lines)

    except Exception as exc:
        logger.error(f"Error scanning workspace: {exc}")
        return f"Error: Failed to scan workspace directory. Details: {exc}"


def execute_list_running_applications(filter_name: Optional[str] = None) -> str:
    """
    Scan active OS processes to check running applications.
    Supports comma-separated filter names (e.g., 'chrome, notepad').
    """
    try:
        raw_filters = [f.strip().lower() for f in filter_name.split(",") if f.strip()] if filter_name else []
        running_apps: set = set()

        for proc in psutil.process_iter(["name"]):
            try:
                p_name = proc.info["name"]
                if not p_name:
                    continue

                p_name_lower = p_name.lower()
                if raw_filters:
                    # Match if process name contains ANY of the comma-separated filters
                    if any(f_item in p_name_lower for f_item in raw_filters):
                        running_apps.add(p_name)
                else:
                    # Ignore background system binaries for cleaner output
                    if p_name_lower.endswith(".exe") and not p_name_lower.startswith("svchost"):
                        running_apps.add(p_name)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not running_apps:
            if raw_filters:
                return f"No active processes found matching filters: {', '.join(raw_filters)}."
            return "No active desktop application processes identified."

        sorted_apps = sorted(list(running_apps))
        
        # Limit output length if no filter was passed to avoid context overflow
        if not raw_filters and len(sorted_apps) > 30:
            display_apps = sorted_apps[:30]
            truncated_msg = f"\n... and {len(sorted_apps) - 30} more processes."
        else:
            display_apps = sorted_apps
            truncated_msg = ""

        formatted_list = "\n".join([f"  - {app}" for app in display_apps])
        logger.info(f"Successfully listed running processes (Filters: {raw_filters or 'None'}).")
        
        return f"Active Running Applications:\n{formatted_list}{truncated_msg}"

    except Exception as exc:
        logger.error(f"Error listing running applications: {exc}")
        return f"Error: Failed to list running applications. Details: {exc}"