"""
Unit tests for core.orchestrator module.
"""

import unittest
from unittest.mock import MagicMock
from core.config import Config
from core.llm_client import ChatResponse, OllamaClient
from core.orchestrator import Orchestrator
from core.tool_dispatcher import ToolDispatcher
from personality.personality_builder import PersonalityBuilder


class TestOrchestrator(unittest.TestCase):
    """Test suite for Orchestrator routing, prompt injection, and history tracking."""

    def setUp(self) -> None:
        """Set up mock LLM client and personality builder."""
        self.mock_client = MagicMock(spec=OllamaClient)
        self.mock_client.chat.return_value = ChatResponse(content="Halo, Reza.", tool_calls=[])
        self.builder = PersonalityBuilder(
            char_file_path="personality/base_character.yaml",
            few_shot_file_path="personality/few_shot_examples.yaml",
        )
        self.config = Config()
        self.orchestrator = Orchestrator(
            llm_client=self.mock_client,
            personality_builder=self.builder,
            config=self.config,
        )

    def test_empty_input(self) -> None:
        """Test that empty or whitespace input returns empty string without calling LLM."""
        res = self.orchestrator.process_message("   ")
        self.assertEqual(res, "")
        self.mock_client.chat.assert_not_called()

    def test_message_flow_and_history(self) -> None:
        """Test full message routing and history accumulation."""
        reply = self.orchestrator.process_message("Halo Megumi!")
        self.assertEqual(reply, "Halo, Reza.")

        history = self.orchestrator.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], {"role": "user", "content": "Halo Megumi!"})
        self.assertEqual(history[1], {"role": "assistant", "content": "Halo, Reza."})

        # Test clear history
        self.orchestrator.clear_history()
        self.assertEqual(self.orchestrator.get_history(), [])

    def test_prompt_injection_to_llm(self) -> None:
        """Test that system prompt and few-shot turns are prepended when calling LLM."""
        self.orchestrator.process_message("Apa kabar?")
        self.mock_client.chat.assert_called_once()
        _, kwargs = self.mock_client.chat.call_args
        messages = kwargs.get("messages", [])

        # Check first message is system prompt
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Megumi", messages[0]["content"])

        # Check last message is current user input
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], "Apa kabar?")

    def test_tool_calling_loop_execution(self) -> None:
        """Test that orchestrator iterates tool-calling loop and resolves tool calls."""
        mock_dispatcher = MagicMock(spec=ToolDispatcher)
        mock_dispatcher.dispatch_all.return_value = [
            {"role": "tool", "content": "Wednesday, 03 September 2026", "name": "get_current_time"}
        ]

        # Iteration 1: model calls tool; Iteration 2: model answers with final content
        self.mock_client.chat.side_effect = [
            ChatResponse(
                content="",
                tool_calls=[{"function": {"name": "get_current_time", "arguments": {}}}],
            ),
            ChatResponse(
                content="Sekarang hari Rabu, 03 September 2026.",
                tool_calls=[],
            ),
        ]

        orch = Orchestrator(
            llm_client=self.mock_client,
            personality_builder=self.builder,
            tool_dispatcher=mock_dispatcher,
            config=self.config,
        )

        reply = orch.process_message("Jam berapa sekarang?")
        self.assertEqual(reply, "Sekarang hari Rabu, 03 September 2026.")
        self.assertEqual(self.mock_client.chat.call_count, 2)
        mock_dispatcher.dispatch_all.assert_called_once()

        # History should ONLY contain user and final assistant response (not intermediate tool messages)
        history = orch.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Sekarang hari Rabu, 03 September 2026.")

    def test_tool_calling_max_iterations(self) -> None:
        """Test that orchestrator breaks when max tool iterations is reached."""
        mock_dispatcher = MagicMock(spec=ToolDispatcher)
        mock_dispatcher.dispatch_all.return_value = [
            {"role": "tool", "content": "some result", "name": "dummy"}
        ]

        # Always returns tool call
        self.mock_client.chat.return_value = ChatResponse(
            content="sedang mencoba...",
            tool_calls=[{"function": {"name": "dummy", "arguments": {}}}],
        )

        orch = Orchestrator(
            llm_client=self.mock_client,
            personality_builder=self.builder,
            tool_dispatcher=mock_dispatcher,
            config=self.config,
        )

        reply = orch.process_message("test loop")
        self.assertEqual(self.mock_client.chat.call_count, 3)
        self.assertEqual(reply, "sedang mencoba...")


if __name__ == "__main__":
    unittest.main()
