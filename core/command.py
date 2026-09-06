"""
Command Handler Module for Project Anima.

Processes CLI system commands (e.g., /clear, /reset, /quit, /help)
separately from main orchestrator logic.
"""

import logging
from typing import Tuple, Optional
from core.orchestrator import Orchestrator

logger = logging.getLogger("anima.command")


class CommandHandler:
    """
    Handles parsing and dispatching CLI commands.
    """

    def __init__(self, orchestrator: Orchestrator) -> None:
        """
        Initialize CommandHandler with an injected Orchestrator instance.

        Args:
            orchestrator (Orchestrator): Central orchestrator instance.
        """
        self.orchestrator = orchestrator

    def handle(self, user_input: str) -> Tuple[bool, bool, Optional[str]]:
        """
        Check and execute CLI commands if match found.

        Args:
            user_input (str): Raw input string from the user.

        Returns:
            Tuple[bool, bool, Optional[str]]:
                - is_command (bool): True if input was a command, False otherwise.
                - should_exit (bool): True if application should terminate.
                - output_msg (Optional[str]): Feedback message to display to the user.
        """
        clean_input = user_input.strip().lower()

        # 1. Exit / Quit Commands
        if clean_input in ("exit", "quit", "q", "/exit", "/quit"):
            logger.info("Exit command issued by user.")
            return True, True, "Mematikan Project Anima CLI. Sampai jumpa!"

        # 2. Clear Short-Term & Chat History
        if clean_input == "/clear":
            self.orchestrator.clear_history()
            logger.info("Command /clear executed.")
            return True, False, "[+] History percakapan telah dibersihkan."

        # 3. Reset Entire Persistent Database
        if clean_input == "/reset":
            self.orchestrator.reset_database()
            logger.info("Command /reset executed.")
            return True, False, "[+] Entire database and persistent memory have been reset."

        # 4. Help Command
        if clean_input == "/help":
            help_text = (
                "[+] Available System Commands:\n"
                "    /clear - Clear short-term conversation history\n"
                "    /reset - Reset entire database & long-term memory\n"
                "    /help  - Show available commands\n"
                "    /quit  - Exit Project Anima (or 'exit', 'q')"
            )
            return True, False, help_text

        return False, False, None