"""
Unit tests for core.llm_client module.
"""

import unittest
from unittest.mock import MagicMock, patch
from core.config import Config
from core.llm_client import (
    ChatResponse,
    OllamaClient,
    OllamaClientError,
    OllamaConnectionError,
    OllamaAPIError,
)


class TestLLMClient(unittest.TestCase):
    """Test suite for OllamaClient functionality and payload formatting."""

    def test_exception_hierarchy(self) -> None:
        """Test custom exception hierarchy."""
        self.assertTrue(issubclass(OllamaConnectionError, OllamaClientError))
        self.assertTrue(issubclass(OllamaAPIError, OllamaClientError))

    def test_context_manager(self) -> None:
        """Test OllamaClient context manager protocol."""
        config = Config()
        with OllamaClient(config=config) as client:
            self.assertIsInstance(client, OllamaClient)

    @patch("httpx.Client.post")
    def test_chat_payload_disables_thinking(self, mock_post: MagicMock) -> None:
        """Test that chat sends payload with think=False explicitly and returns ChatResponse."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Halo."},
            "eval_count": 5,
        }
        mock_post.return_value = mock_response

        config = Config()
        client = OllamaClient(config=config)
        messages = [{"role": "user", "content": "Halo Megumi"}]

        response = client.chat(messages=messages)
        self.assertIsInstance(response, ChatResponse)
        self.assertEqual(response.content, "Halo.")
        self.assertEqual(response.tool_calls, [])

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})

        # Verify thinking mode is hard-disabled in the request payload
        self.assertEqual(payload.get("think"), False)
        self.assertEqual(payload.get("model"), config.model_name)
        self.assertNotIn("tools", payload)
        client.close()

    @patch("httpx.Client.post")
    def test_chat_with_tools_and_tool_calls(self, mock_post: MagicMock) -> None:
        """Test that chat includes tools in payload and parses tool_calls in response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_current_time",
                            "arguments": {},
                        }
                    }
                ],
            },
            "eval_count": 8,
        }
        mock_post.return_value = mock_response

        client = OllamaClient(config=Config())
        tools = [{"type": "function", "function": {"name": "get_current_time"}}]
        messages = [{"role": "user", "content": "Jam berapa sekarang?"}]

        response = client.chat(messages=messages, tools=tools)
        self.assertIsInstance(response, ChatResponse)
        self.assertEqual(response.content, "")
        self.assertEqual(len(response.tool_calls), 1)
        self.assertEqual(response.tool_calls[0]["function"]["name"], "get_current_time")

        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        self.assertEqual(payload.get("tools"), tools)
        client.close()

    @patch("httpx.Client.post")
    def test_generate_backward_compatibility(self, mock_post: MagicMock) -> None:
        """Test that generate() returns string content for backward compatibility."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Ini hasil generate."},
            "eval_count": 10,
        }
        mock_post.return_value = mock_response

        client = OllamaClient(config=Config())
        result = client.generate(prompt="Jelaskan sesuatu")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "Ini hasil generate.")
        client.close()


if __name__ == "__main__":
    unittest.main()
