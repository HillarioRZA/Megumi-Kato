"""
Unit tests for personality.personality_builder module.
"""

import unittest
from personality.personality_builder import PersonalityBuilder, FALLBACK_SYSTEM_PROMPT


class TestPersonalityBuilder(unittest.TestCase):
    """Test suite for PersonalityBuilder and YAML loading."""

    def test_load_and_prompt_assembly(self) -> None:
        """Test loading valid character YAML files and assembling system prompt."""
        builder = PersonalityBuilder(
            char_file_path="personality/base_character.yaml",
            few_shot_file_path="personality/few_shot_examples.yaml",
        )
        prompt = builder.get_system_prompt()

        self.assertIn("Megumi", prompt)
        self.assertIn("Reza", prompt)
        self.assertIn("[Identity Rules — follow strictly]", prompt)
        self.assertIn("[Core Traits]", prompt)
        self.assertIn("[Speaking Style]", prompt)
        self.assertIn("[Emotional Depth]", prompt)
        self.assertIn("[Mood Behavior]", prompt)
        self.assertIn("[Hard Rules — never violate]", prompt)

    def test_few_shot_turns_generation(self) -> None:
        """Test few-shot turn messages generation."""
        builder = PersonalityBuilder(
            char_file_path="personality/base_character.yaml",
            few_shot_file_path="personality/few_shot_examples.yaml",
        )
        turns = builder.get_few_shot_messages(limit=6)

        self.assertEqual(len(turns), 6)
        self.assertEqual(turns[0]["role"], "user")
        self.assertEqual(turns[1]["role"], "assistant")
        self.assertEqual(turns[0]["content"], "Megumi?")
        self.assertIn("Yeah, I'm here", turns[1]["content"])

    def test_fallback_resilience(self) -> None:
        """Test graceful fallback when configuration files are missing."""
        builder = PersonalityBuilder(
            char_file_path="non_existent_file.yaml",
            few_shot_file_path="non_existent_file.yaml",
        )
        prompt = builder.get_system_prompt()
        self.assertEqual(prompt, FALLBACK_SYSTEM_PROMPT)

        turns = builder.get_few_shot_messages()
        self.assertEqual(turns, [])


if __name__ == "__main__":
    unittest.main()
