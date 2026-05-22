"""
core/circadian.py — Single authoritative clock driving ALL time-dependent behavior.

7 phases: DAWN, MORNING, MIDDAY, DUSK, EVENING, NIGHT, DEEP_NIGHT
Energy curve: sinusoidal, peak at noon, trough at midnight
Clock jump tolerance: if real_elapsed diverges from passed dt by >300s, discontinuity
"""

import math
import time
from datetime import datetime

import config


class CircadianClock:
    """Drives circadian rhythm — no time acceleration, 1:1 real time."""

    PHASES = ["DAWN", "MORNING", "MIDDAY", "DUSK", "EVENING", "NIGHT", "DEEP_NIGHT"]

    def __init__(self):
        now = datetime.now()
        self._internal_hour = now.hour + now.minute / 60.0 + now.second / 3600.0
        self.current_phase = self._calculate_phase(self._internal_hour)
        self.last_update = time.monotonic()
        self.phase_change_callbacks = []
        self.clock_jump_detected = False

    @property
    def internal_hour(self):
        """Current internal hour (0.0-24.0 synchronized to current_phase)."""
        return self._internal_hour

    @internal_hour.setter
    def internal_hour(self, value):
        """Set hour and keep current_phase in sync."""
        self._internal_hour = value % 24.0
        self.current_phase = self._calculate_phase(self._internal_hour)

    def update(self, dt):
        """Advance clock by dt seconds (1:1 real time).

        Args:
            dt: Time delta in seconds since last update.

        Returns:
            float: Current energy multiplier (0.0-1.0).
        """
        real_now = time.monotonic()
        real_elapsed = real_now - self.last_update
        self.last_update = real_now

        # Clock jump detection — real wall time far exceeds expected dt
        # (system was suspended/sleeping; don't catch intentional fast dt)
        self.clock_jump_detected = (real_elapsed - dt) > config.CLOCK_JUMP_THRESHOLD

        # Advance internal hour by dt seconds (dt / 3600 = hours)
        self._internal_hour = (self._internal_hour + dt / 3600.0) % 24.0

        # Phase transition detection
        new_phase = self._calculate_phase(self.internal_hour)
        if new_phase != self.current_phase:
            old_phase = self.current_phase
            self.current_phase = new_phase
            for cb in self.phase_change_callbacks:
                cb(new_phase, old_phase)

        return self.energy_multiplier

    @property
    def energy_multiplier(self):
        """Sinusoidal energy curve.

        Formula: 0.5 + 0.5 * sin((hour - 6) * pi / 12)
        Clamped to [0.0, 1.0].
        Peak (1.0) at noon, trough (0.0) at midnight.
        """
        val = 0.5 + 0.5 * math.sin((self._internal_hour - 6) * math.pi / 12)
        return max(0.0, min(1.0, val))

    @staticmethod
    def _calculate_phase(hour):
        """Map a 0-24 hour value to a phase string."""
        if 5 <= hour < 7:
            return "DAWN"
        elif 7 <= hour < 11:
            return "MORNING"
        elif 11 <= hour < 14:
            return "MIDDAY"
        elif 14 <= hour < 17:
            return "DUSK"
        elif 17 <= hour < 20:
            return "EVENING"
        elif 20 <= hour < 23:
            return "NIGHT"
        else:  # 23-24 and 0-5
            return "DEEP_NIGHT"

    def on_phase_change(self, callback):
        """Register a callback(new_phase, old_phase) for phase transitions."""
        self.phase_change_callbacks.append(callback)
