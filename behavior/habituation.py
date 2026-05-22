"""
behavior/habituation.py — Interaction cooldown and response degradation.

Prevents the cat from responding endlessly to rapid repeated interactions.
Response sequence: full → ear flick → glance → ignore.

After ~5 rapid clicks the cat stops reacting entirely until the cooldown
decays. Cooldown decays naturally over time (one count per 4-5 minutes
of no interaction).
"""

import time

import config


# Response levels (0 = full, 3 = ignore)
RESPONSE_FULL = 0
RESPONSE_EAR_FLICK = 1
RESPONSE_GLANCE = 2
RESPONSE_IGNORE = 3

RESPONSE_LABELS = {
    RESPONSE_FULL: "full",
    RESPONSE_EAR_FLICK: "ear_flick",
    RESPONSE_GLANCE: "glance",
    RESPONSE_IGNORE: "ignore",
}


class HabituationModule:
    """Tracks interaction frequency per type and determines response level.

    Each interaction type (click, hover, pet, etc.) has its own counter
    and last-timestamp. Counters decay at ~1 per 4-5 minutes of no
    interaction.
    """

    def __init__(self):
        self._counters: dict[str, int] = {}
        self._last_times: dict[str, float] = {}
        self._decay_rate: float = config.HABITUATION_DECAY_RATE  # seconds per count

    def record_interaction(self, interaction_type: str) -> None:
        """Record an interaction of the given type."""
        self._counters[interaction_type] = self._counters.get(interaction_type, 0) + 1
        self._last_times[interaction_type] = time.monotonic()

    def get_response_level(self, interaction_type: str) -> int:
        """Return response level 0-3 for the given interaction type.

        0 = full response
        1 = ear flick only
        2 = glance only
        3 = ignore (no visible reaction)
        """
        counter = self._counters.get(interaction_type, 0)

        if counter <= 1:
            return RESPONSE_FULL
        elif counter == 2:
            return RESPONSE_EAR_FLICK
        elif counter == 3:
            return RESPONSE_EAR_FLICK
        elif counter == 4:
            return RESPONSE_GLANCE
        else:  # counter >= 5
            return RESPONSE_IGNORE

    def update(self, dt: float) -> None:
        """Decay all interaction counters over time.

        Call this once per frame/tick.
        Counters decay at approximately 1 count per decay_rate seconds
        of no interaction for that type.

        Args:
            dt: Delta time in seconds since last update.
        """
        now = time.monotonic()
        to_delete = []

        for typ in list(self._counters.keys()):
            last = self._last_times.get(typ, now)
            elapsed = now - last

            # Decay proportional to dt when no interaction occurred recently
            if elapsed >= self._decay_rate:
                # Full decay: reduce counter
                decay_count = int(elapsed / self._decay_rate)
                self._counters[typ] = max(0, self._counters[typ] - decay_count)
                # Update last time to reflect partial decay
                self._last_times[typ] = now

            # Clean up zero counters
            if self._counters[typ] <= 0:
                to_delete.append(typ)

        for typ in to_delete:
            del self._counters[typ]
            del self._last_times[typ]

    def get_counter(self, interaction_type: str) -> int:
        """Get the current counter value for a given interaction type."""
        return self._counters.get(interaction_type, 0)

    def get_all_counters(self) -> dict[str, int]:
        """Get all non-zero counters as a dict."""
        return dict(self._counters)

    def reset(self, interaction_type: str | None = None) -> None:
        """Reset counter(s) to zero.

        Args:
            interaction_type: If specified, reset only that type.
                              If None, reset all counters.
        """
        if interaction_type is None:
            self._counters.clear()
            self._last_times.clear()
        else:
            self._counters.pop(interaction_type, None)
            self._last_times.pop(interaction_type, None)

    def __repr__(self) -> str:
        active = {k: v for k, v in self._counters.items() if v > 0}
        return f"<HabituationModule active={len(active)} types={active}>"
