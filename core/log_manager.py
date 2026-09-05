"""
Session Logging and Attempt Manager for Project Anima.

Handles sequential test attempt indexing, automated log file generation ([tanggal][waktu]-[n]),
and unified dual-logging (Console and File) for interactive terminal sessions and test runs.
"""

import os
import re
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple


def get_next_log_file(
    log_dir: str = "logs",
    extension: str = "txt",
    current_time: Optional[datetime] = None,
) -> Tuple[Path, int]:
    """
    Generate the next sequential log file path with format: [tanggal][waktu]-[n].[extension].

    Example:
        `logs/20260902_011530-1.txt`
        where:
        - `20260902` is the date (YYYYMMDD)
        - `011530` is the timestamp (HHMMSS)
        - `1` is the sequential attempt index (percobaan ke-n) for that date.

    Args:
        log_dir (str): Target directory to save logs. Defaults to 'logs'.
        extension (str): Log file extension (e.g. 'txt' or 'log'). Defaults to 'txt'.
        current_time (Optional[datetime]): Reference datetime. Defaults to datetime.now().

    Returns:
        Tuple[Path, int]: The full Path object of the new log file and the attempt index `n`.
    """
    now = current_time or datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")

    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Scan for existing log files for today to determine attempt number 'n'
    existing_files = list(target_dir.glob(f"*{date_str}*-*.{extension}"))
    attempt_numbers = []

    pattern = re.compile(rf"^{date_str}_\d{{6}}-(\d+)\.{re.escape(extension)}$")

    for file_path in existing_files:
        match = pattern.match(file_path.name)
        if match:
            try:
                attempt_numbers.append(int(match.group(1)))
            except ValueError:
                pass

    if attempt_numbers:
        next_attempt = max(attempt_numbers) + 1
    else:
        # Fallback: total existing files for today + 1
        next_attempt = len(existing_files) + 1

    filename = f"{date_str}_{time_str}-{next_attempt}.{extension}"
    return target_dir / filename, next_attempt


def setup_session_logging(
    log_level_name: str = "INFO",
    log_dir: str = "logs",
    extension: str = "txt",
) -> Tuple[logging.Logger, Path, int]:
    """
    Configure dual-stream logging (Console + File) for a terminal session or test run.

    Args:
        log_level_name (str): Log level string (DEBUG, INFO, WARNING, ERROR).
        log_dir (str): Directory where log files are stored. Defaults to 'logs'.
        extension (str): Log file extension. Defaults to 'txt'.

    Returns:
        Tuple[logging.Logger, Path, int]: (root_logger, log_file_path, attempt_index)
    """
    log_file_path, attempt_index = get_next_log_file(log_dir=log_dir, extension=extension)

    level = getattr(logging, log_level_name.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates on reloads
    root_logger.handlers.clear()

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. File Stream Handler (UTF-8 encoding)
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Write initial header directly into the file
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write(f"PROJECT ANIMA — TERMINAL TEST & SESSION LOG\n")
        f.write(f"Percobaan Ke : #{attempt_index}\n")
        f.write(f"Waktu Mulai  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"File Log     : {log_file_path.name}\n")
        f.write("=" * 70 + "\n\n")

    return root_logger, log_file_path, attempt_index


class SessionLogger:
    """
    Context manager and helper for recording terminal chat sessions and test runs.

    Attributes:
        log_file_path (Path): Path to the log file.
        attempt_index (int): Attempt number (percobaan ke-n).
        turn_count (int): Count of conversation turns recorded.
    """

    def __init__(
        self,
        log_dir: str = "logs",
        log_level_name: str = "INFO",
        extension: str = "txt",
    ) -> None:
        """
        Initialize SessionLogger with automatic file naming.

        Args:
            log_dir (str): Directory to save log files.
            log_level_name (str): Logging severity level.
            extension (str): Log file format extension ('txt' or 'log').
        """
        self.log_dir = log_dir
        self.log_level_name = log_level_name
        self.extension = extension
        self.logger, self.log_file_path, self.attempt_index = setup_session_logging(
            log_level_name=self.log_level_name,
            log_dir=self.log_dir,
            extension=self.extension,
        )
        self.turn_count = 0
        self.start_time = datetime.now()

    def record_turn(self, user_input: str, assistant_response: str) -> None:
        """
        Record a single user-assistant conversation turn cleanly into the log file.

        Args:
            user_input (str): User message.
            assistant_response (str): Assistant model response.
        """
        self.turn_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = (
            f"\n[TURN {self.turn_count}] [{timestamp}]\n"
            f"Anda   > {user_input}\n"
            f"Megumi > {assistant_response}\n"
            + ("-" * 50) + "\n"
        )
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            self.logger.warning(f"Failed to record turn into log file: {e}")

    def close(self, status: str = "Completed") -> None:
        """
        Append session summary footer and finalize log file.

        Args:
            status (str): Termination status summary.
        """
        end_time = datetime.now()
        duration = end_time - self.start_time
        summary = (
            "\n" + "=" * 70 + "\n"
            f"SESSION SUMMARY\n"
            f"Status           : {status}\n"
            f"Waktu Selesai    : {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Durasi Sesi      : {str(duration).split('.')[0]}\n"
            f"Total Interaksi  : {self.turn_count} turn\n"
            + "=" * 70 + "\n"
        )
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(summary)
        except Exception:
            pass

    def __enter__(self) -> "SessionLogger":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        status = "Error Occurred" if exc_val else "Clean Exit"
        self.close(status=status)
