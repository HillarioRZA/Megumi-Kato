"""
System Tools for Project Anima.

Provides schema definitions and execution handlers for desktop management:
1. manage_local_file: Sandboxed file CRUD operations restricted to D:\\Megumi Kato.
2. manage_application: Open or close desktop applications with blocklist safety.
3. get_system_status: Read-only system metrics (CPU, RAM, Battery).
"""

import os
import logging
import subprocess
import pathlib
from typing import Any, Dict, List, Optional
import psutil
from fpdf import FPDF

logger = logging.getLogger("anima.tools.system")

# Hardcoded absolute workspace sandbox directory
WORKSPACE_DIR = pathlib.Path(r"D:\Megumi Kato").resolve()

# Process blocklist to prevent self-termination or system instability
PROCESS_BLOCKLIST = [
    "python.exe",
    "cmd.exe",
    "powershell.exe",
    "code.exe",  # VS Code
    "antigravity.exe",  # IDE / Runner
    "explorer.exe",
    "taskmgr.exe",
]

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}

# --- Tool Schemas ---

MANAGE_LOCAL_FILE_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "manage_local_file",
        "description": (
            "Perform CRUD file management strictly inside the workspace 'D:\\Megumi Kato'. "
            "Supported file types: .txt, .md, .pdf (create/write only). "
            "Do NOT use this tool for reading PDF files or accessing outside the sandbox."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "read", "delete"],
                    "description": "File action to perform: 'create' (or overwrite), 'read', or 'delete'.",
                },
                "file_name": {
                    "type": "string",
                    "description": "Name or relative path of the file inside 'D:\\Megumi Kato' (e.g., 'notes.md', 'reports/jurnal.txt').",
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write when action is 'create'. Ignored for 'read' and 'delete'.",
                },
            },
            "required": ["action", "file_name"],
        },
    },
}

MANAGE_APPLICATION_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "manage_application",
        "description": (
            "Open or close desktop applications on the host operating system. "
            "System-critical processes and development IDEs are protected by a blocklist."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["open", "close"],
                    "description": "Action to perform: 'open' or 'close'.",
                },
                "app_name": {
                    "type": "string",
                    "description": "Name or executable of the application (e.g., 'notepad', 'spotify', 'chrome').",
                },
            },
            "required": ["action", "app_name"],
        },
    },
}

GET_SYSTEM_STATUS_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_system_status",
        "description": "Retrieve current system hardware status including CPU usage, RAM utilization, and battery level.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

SYSTEM_TOOLS: List[Dict[str, Any]] = [
    MANAGE_LOCAL_FILE_SCHEMA,
    MANAGE_APPLICATION_SCHEMA,
    GET_SYSTEM_STATUS_SCHEMA,
]

# --- Helper Functions ---

def _validate_sandbox_path(file_name: str) -> pathlib.Path:
    """
    Resolve and validate that the target path resides strictly inside WORKSPACE_DIR.

    Raises:
        PermissionError: If the resolved path breaches the sandbox boundary.
        ValueError: If the file extension is not in the whitelist.
    """
    # Ensure workspace directory exists
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    target_path = (WORKSPACE_DIR / file_name).resolve()

    # Path traversal check
    if not str(target_path).startswith(str(WORKSPACE_DIR)):
        logger.error(f"Sandbox Breach Attempt: {file_name} resolved to {target_path}")
        raise PermissionError(f"Access denied: Path '{file_name}' is outside the allowed workspace ('{WORKSPACE_DIR}').")

    # Extension whitelist check
    if target_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        logger.warning(f"Disallowed file extension requested: {target_path.suffix}")
        raise ValueError(f"Unsupported file type '{target_path.suffix}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")

    return target_path


def _generate_pdf(target_path: pathlib.Path, content: str) -> None:
    """Helper to convert plain text into a basic PDF file using FPDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Split content by lines to write cleanly
    for line in content.split("\n"):
        # FPDF latin-1 encoding fallback for unexpected characters
        clean_line = line.encode("latin-1", "replace").decode("latin-1")
        # Gunakan 'text' menggantikan 'txt', dan pdf.ln() untuk pindah baris baru
        pdf.cell(w=0, h=10, text=clean_line)
        pdf.ln(10)

    pdf.output(str(target_path))


# --- Execution Handlers ---

def execute_manage_local_file(action: str, file_name: str, content: Optional[str] = None) -> str:
    """
    Execute sandboxed file CRUD operation inside D:\\Megumi Kato.
    """
    try:
        target_path = _validate_sandbox_path(file_name)
        ext = target_path.suffix.lower()

        if action == "create":
            file_content = content or ""
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if ext == ".pdf":
                _generate_pdf(target_path, file_content)
                logger.info(f"Successfully created PDF file: {target_path}")
                return f"Successfully generated PDF file '{target_path.name}' in workspace."
            
            # Plain text writing for .txt and .md
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            logger.info(f"Successfully written file: {target_path}")
            return f"Successfully created/updated file '{target_path.name}'."

        elif action == "read":
            if ext == ".pdf":
                return "Error: Reading PDF files is not supported yet. RAG pipeline is required for PDF parsing."

            if not target_path.exists():
                return f"Error: File '{target_path.name}' does not exist."

            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                data = f.read()
            logger.info(f"Successfully read file: {target_path}")
            return f"Content of '{target_path.name}':\n\n{data}"

        elif action == "delete":
            if not target_path.exists():
                return f"Error: File '{target_path.name}' does not exist."

            target_path.unlink()
            logger.info(f"Successfully deleted file: {target_path}")
            return f"Successfully deleted file '{target_path.name}'."

        else:
            return f"Error: Invalid action '{action}'. Valid actions: create, read, delete."

    except (PermissionError, ValueError) as exc:
        return f"Security Exception: {exc}"
    except Exception as exc:
        logger.error(f"Unexpected error in manage_local_file: {exc}")
        return f"Error: Failed to perform file operation. Details: {exc}"


def execute_manage_application(action: str, app_name: str) -> str:
    """
    Open or close desktop applications with blocklist protection.
    """
    if not app_name or not isinstance(app_name, str):
        return "Error: Application name must be a valid non-empty string."

    clean_app = app_name.strip().lower()
    if not clean_app.endswith(".exe"):
        exe_name = f"{clean_app}.exe"
    else:
        exe_name = clean_app

    try:
        if action == "open":
            logger.info(f"Attempting to launch application: {clean_app}")
            # Use OS start command for detached process execution
            subprocess.Popen(f"start {clean_app}", shell=True)
            return f"Command issued to launch application '{clean_app}'."

        elif action == "close":
            # Safety Blocklist Check
            if exe_name in PROCESS_BLOCKLIST or clean_app in [p.replace(".exe", "") for p in PROCESS_BLOCKLIST]:
                logger.warning(f"Blocked attempt to terminate critical process: {exe_name}")
                return f"Security Denial: Process '{exe_name}' is protected by safety blocklist and cannot be terminated."

            terminated_count = 0
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    p_name = proc.info["name"]
                    if p_name and p_name.lower() == exe_name:
                        proc.terminate()
                        terminated_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if terminated_count > 0:
                logger.info(f"Terminated {terminated_count} instance(s) of {exe_name}.")
                return f"Successfully closed {terminated_count} instance(s) of '{exe_name}'."
            else:
                return f"No running process found matching '{exe_name}'."

        else:
            return f"Error: Invalid action '{action}'. Valid actions: open, close."

    except Exception as exc:
        logger.error(f"Error in manage_application for {clean_app}: {exc}")
        return f"Error: Failed to execute application command. Details: {exc}"


def execute_get_system_status() -> str:
    """
    Read current system CPU, Memory, and Battery metrics.
    """
    try:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        ram_free_gb = round(memory.available / (1024 ** 3), 2)
        ram_total_gb = round(memory.total / (1024 ** 3), 2)

        battery_info = "N/A"
        battery = psutil.sensors_battery()
        if battery:
            plugged = "Plugged in" if battery.power_plugged else "On Battery"
            battery_info = f"{battery.percent}% ({plugged})"

        result = (
            "System Status Metrics:\n"
            f"- CPU Usage: {cpu_usage}%\n"
            f"- RAM Usage: {ram_usage}% ({ram_free_gb} GB free / {ram_total_gb} GB total)\n"
            f"- Battery: {battery_info}"
        )
        logger.info("Successfully retrieved system status.")
        return result

    except Exception as exc:
        logger.error(f"Error reading system status: {exc}")
        return f"Error: Unable to fetch system status. Details: {exc}"