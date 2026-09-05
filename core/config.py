"""
Centralized Configuration Module for Project Anima.

Provides environment variable loading, default fallbacks, and typed settings access.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()


@dataclass
class Config:
    """
    Central configuration class for Ollama client and orchestrator settings.

    Attributes:
        ollama_base_url (str): Base URL of the Ollama API server.
        model_name (str): Name of the Ollama model to use.
        num_ctx (int): Maximum context window size for the LLM.
        num_predict_default (int): Maximum tokens for generated responses.
        ollama_timeout (float): HTTP request timeout in seconds for Ollama API calls.
        temperature (float): Sampling temperature for generation.
        thinking_mode_default (bool): Default thinking mode state (permanently False for direct inference).
        log_level (str): Logging level for the application.
        log_dir (str): Directory where session logs are stored.
        db_path (str): SQLite database path for persistent memory.
        short_term_memory_limit (int): Maximum messages in RAM sliding window history.
    """

    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    model_name: str = field(
        default_factory=lambda: os.getenv("MODEL_NAME", "qwen3.5:4b")
    )
    num_ctx: int = field(
        default_factory=lambda: int(os.getenv("NUM_CTX", "8192"))
    )
    num_predict_default: int = field(
        default_factory=lambda: int(os.getenv("NUM_PREDICT_DEFAULT", "512"))
    )
    ollama_timeout: float = field(
        default_factory=lambda: float(os.getenv("OLLAMA_TIMEOUT", "300.0"))
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.8"))
    )
    thinking_mode_default: bool = field(
        default_factory=lambda: os.getenv("THINKING_MODE_DEFAULT", "False").lower() in ("true", "1", "yes")
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )
    log_dir: str = field(
        default_factory=lambda: os.getenv("LOG_DIR", "logs")
    )
    db_path: str = field(
        default_factory=lambda: os.getenv("DB_PATH", "memory/anima_memory.db")
    )
    short_term_memory_limit: int = field(
        default_factory=lambda: int(os.getenv("SHORT_TERM_MEMORY_LIMIT", "16"))
    )


# Singleton instance cached
_global_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Retrieve or initialize the global Config singleton.

    Args:
        reload (bool): If True, reloads environment variables and returns a new Config instance.

    Returns:
        Config: The application configuration instance.
    """
    global _global_config
    if _global_config is None or reload:
        if reload:
            load_dotenv(override=True)
        _global_config = Config()
    return _global_config
