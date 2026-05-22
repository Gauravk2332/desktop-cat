"""behavior/contagion.py — Monitor user input rate, affect cat visual state.

The cat's tail swish rate and ear posture respond to the user's typing
intensity — contagious behavior that mirrors the user's energy.
"""

import time
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class ContagionMonitor:
    """Tracks user input rate and maps it to cat visual state modifiers.

    States:
        calm: Slow/no typing, low tail swish, normal ears
        agitated: Fast typing, rapid tail swish, airplane ears
    """

    def __init__(self, window_seconds: float = 5.0):
        self._input_window: List[Tuple[float, str]] = []
        self._window_seconds = window_seconds
        self._current_mood = "calm"  # "calm", "agitated"
        self._tail_swish_rate = 0.0  # swishes per second (target)
        self._current_tail_swish = 0.0  # smoothed value
        self._ears_airplane = False

    def record_input(self, input_type: str = "keyboard") -> None:
        """Record a user input event.

        Args:
            input_type: Type of input ("keyboard", "mouse", etc.).
        """
        now = time.monotonic()
        self._input_window.append((now, input_type))
        # Prune old events
        cutoff = now - self._window_seconds
        self._input_window = [(t, ty) for t, ty in self._input_window if t > cutoff]

    def update(self, dt: float) -> dict:
        """Update contagion state based on recent input rate.

        Args:
            dt: Delta time in seconds.

        Returns:
            Dict with visual modifiers:
                - tail_swish (float): target swish rate (0-4)
                - ears_airplane (bool): ears flattened
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds
        recent = [(t, ty) for t, ty in self._input_window if t > cutoff]

        input_rate = len(recent) / self._window_seconds  # events per second

        # Compute target swish rate
        target_swish = 0.0
        target_ears = False

        if input_rate > 10:  # Very fast typing
            target_swish = min(4.0, input_rate * 0.3)
            target_ears = True
        elif input_rate > 3:  # Moderate typing
            target_swish = min(2.0, input_rate * 0.2)
        # else: slow/absent, target stays 0.0

        # Smooth the tail swish value
        smoothing = 2.0  # blend factor (higher = faster response)
        self._current_tail_swish += (target_swish - self._current_tail_swish) * min(1.0, dt * smoothing)
        self._ears_airplane = target_ears

        # Update mood string
        self._current_mood = "agitated" if target_ears else "calm"

        return {
            "tail_swish": self._current_tail_swish,
            "ears_airplane": self._ears_airplane,
        }

    def reset(self) -> None:
        """Clear all input history and reset state."""
        self._input_window.clear()
        self._current_mood = "calm"
        self._tail_swish_rate = 0.0
        self._current_tail_swish = 0.0
        self._ears_airplane = False

    @property
    def mood(self) -> str:
        """Current contagion mood: 'calm' or 'agitated'."""
        return self._current_mood

    @property
    def input_rate(self) -> float:
        """Events per second in the current window."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        recent = [(t, ty) for t, ty in self._input_window if t > cutoff]
        return len(recent) / self._window_seconds if self._window_seconds > 0 else 0.0
