"""
Mood Manager Module for Project Anima.

Handles mood score calculations, time decay towards neutral (50),
state labeling, and ambient prompt context generation.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from memory.repository import get_latest_mood_entry, insert_mood_event

logger = logging.getLogger("anima.memory.mood_manager")

MOOD_EVENT_DELTAS: Dict[str, int] = {
    "praised": 8,
    "nice_conversation": 5,
    "shared_something_personal": 3,
    "wrong_name_used": -10,
    "dismissed_or_ignored": -5,
}

DEFAULT_MOOD_SCORE: int = 50
DECAY_RATE_PER_HOUR: float = 1.0
MIN_SCORE: int = 0
MAX_SCORE: int = 100


class MoodManager:
    """
    Coordinates mood tracking, event application, time-decay adjustments,
    and system prompt formatting.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize MoodManager with database path.

        Args:
            db_path (str): Path to SQLite database file.
        """
        self.db_path = db_path

    def apply_event(self, event_type: str) -> int:
        """
        Apply a mood event trigger, adjust score, and record to database.

        Args:
            event_type (str): Key matching MOOD_EVENT_DELTAS dictionary.

        Returns:
            int: Updated mood score.
        """
        if event_type not in MOOD_EVENT_DELTAS:
            logger.warning(
                f"Unknown mood event type: '{event_type}'. Skipping adjustment."
            )
            return self.get_current_score()

        delta = MOOD_EVENT_DELTAS[event_type]
        current_score = self.get_current_score()
        new_score = max(MIN_SCORE, min(MAX_SCORE, current_score + delta))

        try:
            insert_mood_event(
                db_path=self.db_path,
                score=new_score,
                delta=delta,
                event_type=event_type,
            )
            logger.info(
                f"Applied mood event '{event_type}' (delta: {delta:+d}). New score: {new_score}"
            )
        except Exception as exc:
            logger.error(f"Failed to record mood event '{event_type}': {exc}")

        return new_score

    def get_current_score(self) -> int:
        """
        Retrieve current mood score with dynamic time decay towards neutral (50).

        Returns:
            int: Current calculated score rounded to integer.
        """
        entry = get_latest_mood_entry(self.db_path)
        if not entry:
            return DEFAULT_MOOD_SCORE

        last_score = entry.get("score", DEFAULT_MOOD_SCORE)
        raw_timestamp = entry.get("timestamp")

        if not raw_timestamp:
            return last_score

        try:
            # Handle SQLite CURRENT_TIMESTAMP string format (YYYY-MM-DD HH:MM:SS)
            if isinstance(raw_timestamp, str):
                last_time = datetime.strptime(raw_timestamp, "%Y-%m-%d %H:%M:%S")
            elif isinstance(raw_timestamp, datetime):
                last_time = raw_timestamp
            else:
                return last_score

            # SQLite CURRENT_TIMESTAMP disimpan dalam UTC
            hours_idle = (datetime.utcnow() - last_time).total_seconds() / 3600.0
            if hours_idle < 0:
                hours_idle = 0.0

            decay = hours_idle * DECAY_RATE_PER_HOUR

            if last_score > DEFAULT_MOOD_SCORE:
                current = max(float(DEFAULT_MOOD_SCORE), last_score - decay)
            else:
                current = min(float(DEFAULT_MOOD_SCORE), last_score + decay)

            return round(current)
        except Exception as exc:
            logger.error(f"Error calculating mood decay: {exc}")
            return last_score

    def get_state_label(self, score: Optional[int] = None) -> str:
        """
        Map mood score to descriptive state label.

        Args:
            score (Optional[int]): Mood score to map. If None, retrieves current score.

        Returns:
            str: State label ("very_warm", "warm", "neutral", "distant", "cold").
        """
        if score is None:
            score = self.get_current_score()

        if score >= 80:
            return "very_warm"
        if score >= 60:
            return "warm"
        if score >= 40:
            return "neutral"
        if score >= 20:
            return "distant"
        return "cold"

    def get_mood_context_prompt(self) -> str:
        """
        Generate ambient mood system prompt injection based on current state.

        Returns:
            str: Formatted system prompt or empty string if mood is neutral.
        """
        label = self.get_state_label()

        descriptions = {
            "very_warm": (
                "You're feeling a bit more open and willing to engage than usual, "
                "though still in your usual understated way."
            ),
            "warm": (
                "You're feeling a bit more open and willing to engage than usual, "
                "though still in your usual understated way."
            ),
            "neutral": "",
            "distant": (
                "You're feeling more withdrawn and short right now — responses "
                "come out more clipped than usual."
            ),
            "cold": (
                "You're feeling more withdrawn and short right now — responses "
                "come out more clipped than usual."
            ),
        }

        description = descriptions.get(label, "")
        if not description:
            return ""

        return f"[Current Mood: {label}] {description}"