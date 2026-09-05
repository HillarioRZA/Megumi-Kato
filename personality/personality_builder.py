"""
Personality Builder Module for Project Anima.

Loads YAML personality definitions and few-shot conversation examples,
building a structured System Prompt and conversation turn examples for the LLM.
"""

import os
import logging
from typing import Any, Dict, List, Optional
import yaml

logger = logging.getLogger("anima.personality")

FALLBACK_SYSTEM_PROMPT = (
    "You are Megumi, a local AI companion. Speak casually in Indonesian and English."
)


class PersonalityBuilder:
    """
    Constructs system prompts from config-driven YAML files for AI character Megumi.

    Attributes:
        char_file_path (str): Path to base character YAML configuration.
        few_shot_file_path (str): Path to few-shot conversation examples YAML configuration.
    """

    def __init__(
        self,
        char_file_path: str = "personality/base_character.yaml",
        few_shot_file_path: str = "personality/few_shot_examples.yaml",
    ) -> None:
        """
        Initialize PersonalityBuilder and load character configuration files.

        Args:
            char_file_path (str): Path to base_character.yaml file.
            few_shot_file_path (str): Path to few_shot_examples.yaml file.
        """
        self.char_file_path = char_file_path
        self.few_shot_file_path = few_shot_file_path
        self.char_data: Dict[str, Any] = {}
        self.few_shot_data: List[Dict[str, Any]] = []
        self._load_success = False

        self._load_yaml_configs()

    def _load_yaml_configs(self) -> None:
        """Load and parse base character and few-shot YAML files safely."""
        try:
            if not os.path.exists(self.char_file_path):
                raise FileNotFoundError(f"Character file not found: {self.char_file_path}")
            if not os.path.exists(self.few_shot_file_path):
                raise FileNotFoundError(f"Few-shot file not found: {self.few_shot_file_path}")

            with open(self.char_file_path, "r", encoding="utf-8") as f:
                self.char_data = yaml.safe_load(f) or {}

            with open(self.few_shot_file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self.few_shot_data = data.get("examples", [])

            self._load_success = True
            logger.info("Successfully loaded personality YAML configuration files.")
        except Exception as exc:
            logger.error(
                f"Failed to load personality YAML files ({self.char_file_path}, {self.few_shot_file_path}): {exc}. "
                "Using fallback default personality."
            )
            self._load_success = False

    def _build_core_prompt(self) -> str:
        """
        Build core persona instructions matching base_character.yaml schema.

        Returns:
            str: Formatted core character system prompt segment.
        """
        if not self._load_success or not self.char_data:
            return FALLBACK_SYSTEM_PROMPT

        name = self.char_data.get("character_name", "Megumi")
        user_name = self.char_data.get("user_name", "Reza")

        identity_rules = self.char_data.get("identity_rules", [])
        core_traits = self.char_data.get("core_traits", [])
        speaking_style = self.char_data.get("speaking_style", [])
        hard_rules = self.char_data.get("hard_rules", [])
        emotional_depth = str(self.char_data.get("emotional_depth", "")).strip()
        mood_behavior = str(self.char_data.get("mood_behavior", "")).strip()

        def fmt_list(items: List[str]) -> str:
            return "\n".join(f"- {i}" for i in items)

        core_prompt = (
            f"You are {name}, a local AI companion.\n"
            f"User's name: {user_name}.\n\n"
            f"[Identity Rules — follow strictly]\n{fmt_list(identity_rules)}\n\n"
            f"[Core Traits]\n{fmt_list(core_traits)}\n\n"
            f"[Speaking Style]\n{fmt_list(speaking_style)}\n\n"
            f"[Emotional Depth]\n{emotional_depth}\n\n"
            f"[Mood Behavior]\n{mood_behavior}\n\n"
            f"[Hard Rules — never violate]\n{fmt_list(hard_rules)}"
        )
        return core_prompt

    def _build_few_shot_prompt(self) -> str:
        """
        Build formatted conversation examples from few-shot data (legacy text block fallback).

        Returns:
            str: Formatted few-shot dialogue prompt segment.
        """
        if not self._load_success or not self.few_shot_data:
            return ""

        user_name = self.char_data.get("user_name", "User")
        name = self.char_data.get("character_name", "Megumi")

        lines = ["[Few-Shot Conversation Examples]"]
        for idx, item in enumerate(self.few_shot_data, 1):
            scenario = item.get("scenario", "")
            user_msg = item.get("user", "")
            anima_msg = (
                item.get("megumi", "")
                or item.get("assistant", "")
                or item.get("anima", "")
                or item.get("Megumi Kato", "")
            )

            lines.append(f"Example {idx} (Scenario: {scenario}):")
            lines.append(f"{user_name}: \"{user_msg}\"")
            lines.append(f"{name}: \"{anima_msg}\"\n")

        return "\n".join(lines).strip()

    def get_few_shot_messages(self, limit: Optional[int] = 6) -> List[Dict[str, str]]:
        """
        Build few-shot examples as actual conversation turns (role-based),
        instead of a flattened text block. This is more reliable for small
        models than describing examples in prose.

        Args:
            limit (Optional[int]): Max number of message turns (default 6 = 3 dialogue turns).
                Pass None to return all turns.

        Returns:
            List[Dict[str, str]]: Alternating user/assistant turns, ready to
            be prepended to the conversation history sent to the LLM.
        """
        if not self._load_success or not self.few_shot_data:
            return []

        turns: List[Dict[str, str]] = []
        for item in self.few_shot_data:
            user_msg = item.get("user", "")
            assistant_msg = (
                item.get("megumi", "")
                or item.get("assistant", "")
                or item.get("anima", "")
                or item.get("Megumi Kato", "")
            )
            if user_msg and assistant_msg:
                turns.append({"role": "user", "content": user_msg})
                turns.append({"role": "assistant", "content": assistant_msg})
                if limit and len(turns) >= limit:
                    break
        return turns


    def get_system_prompt(self) -> str:
        """
        Assemble and return the complete System Prompt string.

        Returns:
            str: System Prompt containing core traits and rules.
        """
        if not self._load_success:
            return FALLBACK_SYSTEM_PROMPT
        return self._build_core_prompt()
