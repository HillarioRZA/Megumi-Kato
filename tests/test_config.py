"""
Unit tests for core.config module.
"""

import os
import unittest
from core.config import Config, get_config


class TestConfig(unittest.TestCase):
    """Test suite for application configuration management."""

    def test_default_config_fields(self) -> None:
        """Test that default Config instance has all required fields and types."""
        config = Config()
        self.assertIsInstance(config.ollama_base_url, str)
        self.assertIsInstance(config.model_name, str)
        self.assertIsInstance(config.num_ctx, int)
        self.assertIsInstance(config.num_predict_default, int)
        self.assertIsInstance(config.ollama_timeout, float)
        self.assertIsInstance(config.temperature, float)
        self.assertIsInstance(config.thinking_mode_default, bool)
        self.assertIsInstance(config.log_level, str)

        # Thinking mode must default to False
        self.assertFalse(config.thinking_mode_default)

    def test_get_config_singleton(self) -> None:
        """Test that get_config returns a singleton instance."""
        config1 = get_config()
        config2 = get_config()
        self.assertIs(config1, config2)

    def test_get_config_reload(self) -> None:
        """Test that get_config with reload=True creates a new instance."""
        config1 = get_config()
        config2 = get_config(reload=True)
        self.assertIsNot(config1, config2)


if __name__ == "__main__":
    unittest.main()
