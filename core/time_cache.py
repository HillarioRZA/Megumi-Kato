"""
Time Cache Module for Project Anima.

Maintains an approximate, periodically-refreshed snapshot of the current
time in the background, so the orchestrator can inject time awareness
into context without a tool-call round-trip for every request.
"""

import logging
import threading
from typing import Optional

from tools.time_tools import execute_get_current_time

logger = logging.getLogger("anima.time_cache")


class TimeCache:
    """
    Background-refreshed cache of the current time string.

    Attributes:
        refresh_interval_seconds (int): How often the cache refreshes.
    """

    def __init__(self, refresh_interval_minutes: int = 30) -> None:
        """
        Initialize TimeCache and start the background refresh loop.

        Args:
            refresh_interval_minutes (int): Refresh interval in minutes.
        """
        self.refresh_interval_seconds = refresh_interval_minutes * 60
        self._cached_value: str = execute_get_current_time()
        self._timer: Optional[threading.Timer] = None
        self._start_background_refresh()
        logger.info(f"TimeCache initialized [Refresh: {refresh_interval_minutes} min]")

    def _refresh(self) -> None:
        """Refresh the cached time value and reschedule the next refresh."""
        try:
            self._cached_value = execute_get_current_time()
            logger.debug(f"TimeCache refreshed: {self._cached_value}")
        except Exception as exc:
            logger.error(f"TimeCache refresh failed: {exc}")
        finally:
            self._start_background_refresh()

    def _start_background_refresh(self) -> None:
        """Schedule the next background refresh using a daemon timer thread."""
        self._timer = threading.Timer(self.refresh_interval_seconds, self._refresh)
        self._timer.daemon = True
        self._timer.start()

    def get_cached(self) -> str:
        """
        Return the current cached (approximate) time string.

        Returns:
            str: Last-refreshed time string, may be up to
                `refresh_interval_seconds` old.
        """
        return self._cached_value

    def stop(self) -> None:
        """Cancel the background refresh loop (call on app shutdown)."""
        if self._timer:
            self._timer.cancel()