"""behavior/social_referencing.py — Cat looks at user → object → back → chirp.

Simulates social referencing: the cat glances at the user, then at an
object, then back at the user, optionally ending with a chirp.
"""

import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SocialReferencing:
    """Manages social referencing sequences.

    Phases:
        0 = inactive
        1 = look_toward (head turn toward user)
        2 = look_object (look at nearby object)
        3 = look_back (look back at user)
        4 = chirp (optional end vocalization)
    """

    def __init__(self):
        self._cooldown = 0.0
        self._active = False
        self._phase = 0  # 0=none, 1=look_user, 2=look_object, 3=look_back, 4=chirp
        self._timer = 0.0
        self._cooldown_duration = 30.0
        self._trigger_chance = 0.005  # 0.5% per tick
        self._phase_duration = 0.5

    def update(self, dt: float, cat: dict, state, personality) -> Optional[str]:
        """Return action string if a social referencing sequence should happen.

        Args:
            dt: Delta time in seconds.
            cat: Cat state dict.
            state: Global state object.
            personality: Personality instance (optional).

        Returns:
            Action string or None if inactive/no trigger.
        """
        self._cooldown = max(0.0, self._cooldown - dt)

        if self._active:
            return self._advance_sequence(dt)

        # Trigger conditions
        curiosity = 0.5
        if personality is not None:
            try:
                curiosity = personality.get_raw("curiosity", normalized=True)
            except (AttributeError, TypeError):
                pass

        user_near = state.last_interaction < 10.0 if hasattr(state, 'last_interaction') else False
        user_near = user_near or cat.get("mouse_near", False)

        if (curiosity > 0.5 and user_near and self._cooldown <= 0
                and random.random() < self._trigger_chance):
            self._start_sequence()
            return "look_toward"

        return None

    def _start_sequence(self) -> None:
        """Begin a new social referencing sequence."""
        self._active = True
        self._phase = 1
        self._timer = self._phase_duration
        logger.debug("Social referencing sequence started")

    def _advance_sequence(self, dt: float) -> Optional[str]:
        """Advance through sequence phases. Returns current phase action."""
        self._timer -= dt
        if self._timer <= 0:
            self._phase += 1
            if self._phase >= 5:  # completed all phases
                self._active = False
                self._cooldown = self._cooldown_duration
                logger.debug("Social referencing sequence complete")
                return None

            phase_actions = {
                1: "look_toward",
                2: "look_object",
                3: "look_back",
                4: "chirp",
            }
            self._timer = self._phase_duration
            return phase_actions.get(self._phase)

        # Return the current phase's action while timer is running
        phase_actions = {
            1: "look_toward",
            2: "look_object",
            3: "look_back",
            4: "chirp",
        }
        return phase_actions.get(self._phase)

    def reset(self) -> None:
        """Reset social referencing state."""
        self._active = False
        self._phase = 0
        self._timer = 0.0
        self._cooldown = 0.0

    @property
    def is_active(self) -> bool:
        """Whether a social referencing sequence is in progress."""
        return self._active

    @property
    def cooldown_remaining(self) -> float:
        """Seconds remaining until next sequence can trigger."""
        return max(0.0, self._cooldown)
