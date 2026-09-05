"""
Main Terminal CLI Entry Point for Project Anima (Phase 2).

Provides an interactive command-line interface to interact with Project Anima core,
demonstrating Ollama LLM integration, logging, personality prompt injection, and history management.
"""

import sys
import logging

# Ensure UTF-8 stdout/stderr on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


from core.config import get_config
from core.llm_client import OllamaClient, OllamaConnectionError, OllamaAPIError
from core.log_manager import SessionLogger
from core.orchestrator import Orchestrator
from core.tool_dispatcher import ToolDispatcher
from personality.personality_builder import PersonalityBuilder
from memory.manager import MemoryManager
from core.time_cache import TimeCache


def main() -> None:
    """Run the main CLI interactive loop for Project Anima with automated session logging, memory & tools."""
    config = get_config()
    session_logger = SessionLogger(log_dir=config.log_dir, log_level_name=config.log_level)

    logger = logging.getLogger("anima.main")
    logger.info(
        f"Starting Project Anima — Phase 4 (Percobaan #{session_logger.attempt_index}, Log: {session_logger.log_file_path.name})"
    )

    # Initialize client, memory manager, personality builder, tool dispatcher, and orchestrator
    llm_client = OllamaClient(config=config)
    memory_manager = MemoryManager(db_path=config.db_path)
    tool_dispatcher = ToolDispatcher(memory_manager=memory_manager)
    personality_builder = PersonalityBuilder(
        char_file_path="personality/base_character.yaml",
        few_shot_file_path="personality/few_shot_examples.yaml",
    )
    time_cache = TimeCache(refresh_interval_minutes=30)
    orchestrator = Orchestrator(
        llm_client=llm_client,
        personality_builder=personality_builder,
        memory_manager=memory_manager,
        time_cache=time_cache,
        tool_dispatcher=tool_dispatcher,
        config=config,
    )

    restored_msgs = len(orchestrator.history)

    print("=" * 60)
    print("      PROJECT ANIMA — AI Companion Backend (Phase 4)")
    print("=" * 60)
    print(f"Base URL        : {config.ollama_base_url}")
    print(f"Model           : {config.model_name}")
    print(f"Context Window  : {config.num_ctx} tokens")
    print(f"Default Tokens  : {config.num_predict_default} tokens")
    print(f"Memory Database : {config.db_path}")
    print(f"Restored Memory : {restored_msgs} messages ({restored_msgs // 2} turns)")
    print(f"Tools Enabled   : Yes (get_current_time, web_search, save_memory, recall_memory)")
    print(f"Temperature     : {config.temperature}")
    print(f"Session Log     : {session_logger.log_file_path.name} (Percobaan #{session_logger.attempt_index})")
    print("-" * 60)

    # Health check for Ollama connection
    print("\n[+] Checking connection to Ollama server...")
    if not llm_client.check_connection():
        print(f"\n[!] WARNING: Could not connect to Ollama at {config.ollama_base_url}.")
        print(f"    Please ensure Ollama is running and model '{config.model_name}' is pulled.")
        print(f"    Command to run Ollama: ollama run {config.model_name}\n")


    print("\n[+] System ready! Commands available:")
    print("    - Type your message to chat.")
    print("    - Type '/clear' to clear history.")
    print("    - Type 'exit', 'quit', or 'q' to stop.")
    print("-" * 60 + "\n")

    try:
        while True:
            try:
                user_input = input("Anda > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nMematikan Project Anima CLI. Sampai jumpa!")
                break

            if not user_input:
                continue

            # Command handling
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nMematikan Project Anima CLI. Sampai jumpa!")
                break

            if user_input.lower() == "/clear":
                orchestrator.clear_history()
                print("[+] History percakapan telah dibersihkan.\n")
                continue

            print("[*] Processing message...")

            try:
                response = orchestrator.process_message(
                    user_input=user_input,
                )
                print(f"\nMegumi > {response}\n")
                session_logger.record_turn(user_input=user_input, assistant_response=response)
            except OllamaConnectionError as e:
                print(f"\n[!] Error Koneksi Ollama: {e}")
                print("    Pastikan server Ollama sudah dinyalakan.\n")
            except OllamaAPIError as e:
                print(f"\n[!] Error API Ollama: {e}\n")
            except Exception as e:
                logger.exception("An unexpected error occurred during processing.")
                print(f"\n[!] System Error: {e}\n")

    finally:
        session_logger.close(status="Session Ended Normally")
        llm_client.close()


if __name__ == "__main__":
    main()
