"""
Command & Test Execution Logger for Project Anima.

Executes a command or test script in the terminal while streaming and recording
all terminal output into a timestamped, indexed log file: logs/[tanggal][waktu]-[n].txt.

Usage:
    python scripts/run_and_log.py python -m unittest discover tests
    python scripts/run_and_log.py python main.py
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Ensure backend root is in PYTHONPATH
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import get_config
from core.log_manager import get_next_log_file


def run_and_log() -> int:
    """Execute command from CLI arguments and record complete output to log file."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_and_log.py <command> [args...]")
        print("Example: python scripts/run_and_log.py python -m unittest discover tests")
        return 1

    config = get_config()
    cmd = sys.argv[1:]
    log_file_path, attempt_index = get_next_log_file(log_dir=config.log_dir, extension="txt")

    start_time = datetime.now()
    header = (
        "=" * 70 + "\n"
        f"PROJECT ANIMA — TERMINAL TEST EXECUTION LOG\n"
        f"Percobaan Ke : #{attempt_index}\n"
        f"Command      : {' '.join(cmd)}\n"
        f"Waktu Mulai  : {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"File Log     : {log_file_path.name}\n"
        + "=" * 70 + "\n\n"
    )

    print("=" * 70)
    print(f"[*] Menjalankan Test / Command dengan Logging Aktif")
    print(f"    Percobaan Ke : #{attempt_index}")
    print(f"    File Log     : {log_file_path}")
    print("=" * 70 + "\n")

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(header)
        log_file.flush()

        # Execute process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=str(PROJECT_ROOT),
        )

        for line in iter(process.stdout.readline, ""):
            sys.stdout.write(line)
            sys.stdout.flush()
            log_file.write(line)
            log_file.flush()

        process.stdout.close()
        return_code = process.wait()

        end_time = datetime.now()
        duration = end_time - start_time
        footer = (
            "\n" + "=" * 70 + "\n"
            f"EXECUTION COMPLETED\n"
            f"Exit Code    : {return_code}\n"
            f"Waktu Selesai: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Durasi       : {str(duration).split('.')[0]}\n"
            + "=" * 70 + "\n"
        )
        log_file.write(footer)

    print("\n" + "=" * 70)
    print(f"[+] Selesai! Hasil uji coba berhasil disimpan di:")
    print(f"    {log_file_path}")
    print("=" * 70)

    return return_code


if __name__ == "__main__":
    sys.exit(run_and_log())
