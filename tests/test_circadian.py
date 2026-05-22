"""
tests/test_circadian.py — Unit tests for CircadianClock.

Tests:
- Phase transitions at all 7 boundary hours
- energy_multiplier sinusoidal shape (0.0-1.0, peak at noon)
- Clock jump tolerance (>300s gap triggers discontinuity flag)
- update advances internal hour correctly
- Phase change callbacks fire at transitions
"""

import sys
import os
import time
import math
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.circadian import CircadianClock


class TestPhaseBoundaries(unittest.TestCase):
    """Every boundary hour across all 7 phases."""

    def _assert_phase_at_hour(self, hour, expected_phase):
        clock = CircadianClock()
        clock.internal_hour = hour
        phase = clock._calculate_phase(hour)
        self.assertEqual(phase, expected_phase, f"hour={hour}")

    # ── DAWN: 5-7 ──
    def test_dawn_at_5(self):
        self._assert_phase_at_hour(5, "DAWN")

    def test_dawn_at_6(self):
        self._assert_phase_at_hour(6, "DAWN")

    def test_dawn_exit_at_7(self):
        """hour=7 is MORNING, not DAWN."""
        self._assert_phase_at_hour(7, "MORNING")

    # ── MORNING: 7-11 ──
    def test_morning_at_7(self):
        self._assert_phase_at_hour(7, "MORNING")

    def test_morning_at_10(self):
        self._assert_phase_at_hour(10, "MORNING")

    def test_morning_exit_at_11(self):
        self._assert_phase_at_hour(11, "MIDDAY")

    # ── MIDDAY: 11-14 ──
    def test_midday_at_11(self):
        self._assert_phase_at_hour(11, "MIDDAY")

    def test_midday_at_13(self):
        self._assert_phase_at_hour(13, "MIDDAY")

    def test_midday_exit_at_14(self):
        self._assert_phase_at_hour(14, "DUSK")

    # ── DUSK: 14-17 ──
    def test_dusk_at_14(self):
        self._assert_phase_at_hour(14, "DUSK")

    def test_dusk_at_16(self):
        self._assert_phase_at_hour(16, "DUSK")

    def test_dusk_exit_at_17(self):
        self._assert_phase_at_hour(17, "EVENING")

    # ── EVENING: 17-20 ──
    def test_evening_at_17(self):
        self._assert_phase_at_hour(17, "EVENING")

    def test_evening_at_19(self):
        self._assert_phase_at_hour(19, "EVENING")

    def test_evening_exit_at_20(self):
        self._assert_phase_at_hour(20, "NIGHT")

    # ── NIGHT: 20-23 ──
    def test_night_at_20(self):
        self._assert_phase_at_hour(20, "NIGHT")

    def test_night_at_22(self):
        self._assert_phase_at_hour(22, "NIGHT")

    def test_night_exit_at_23(self):
        self._assert_phase_at_hour(23, "DEEP_NIGHT")

    # ── DEEP_NIGHT: 23-5 ──
    def test_deep_night_at_23(self):
        self._assert_phase_at_hour(23, "DEEP_NIGHT")

    def test_deep_night_at_0(self):
        self._assert_phase_at_hour(0, "DEEP_NIGHT")

    def test_deep_night_at_3(self):
        self._assert_phase_at_hour(3, "DEEP_NIGHT")

    def test_deep_night_exit_at_5(self):
        self._assert_phase_at_hour(5, "DAWN")

    # ── All 24 hour boundaries ──
    def test_all_hours_map_to_some_phase(self):
        """Every integer hour 0-23 maps to exactly one of the 7 phases."""
        valid = set(CircadianClock.PHASES)
        for h in range(24):
            phase = CircadianClock._calculate_phase(h)
            self.assertIn(phase, valid, f"No phase for hour={h}")


class TestEnergyMultiplier(unittest.TestCase):
    """Sinusoidal shape: [0, 1], peak at noon, trough at midnight."""

    def setUp(self):
        self.clock = CircadianClock()

    def test_range_never_exceeds_one(self):
        """All hours produce energy_multiplier in [0.0, 1.0]."""
        for hour in [x * 0.5 for x in range(0, 49)]:  # every 30 min
            self.clock.internal_hour = hour
            em = self.clock.energy_multiplier
            self.assertGreaterEqual(em, 0.0, f"hour={hour}")
            self.assertLessEqual(em, 1.0, f"hour={hour}")

    def test_peak_at_noon(self):
        """energy_multiplier is 1.0 at exactly noon."""
        self.clock.internal_hour = 12.0
        self.assertAlmostEqual(self.clock.energy_multiplier, 1.0, places=4)

    def test_trough_at_midnight(self):
        """energy_multiplier is 0.0 at exactly midnight."""
        self.clock.internal_hour = 0.0
        self.assertEqual(self.clock.energy_multiplier, 0.0)

    def test_symmetry_around_noon(self):
        """Same distance before/after noon gives same multiplier."""
        self.clock.internal_hour = 8.0
        v1 = self.clock.energy_multiplier
        self.clock.internal_hour = 16.0
        v2 = self.clock.energy_multiplier
        self.assertAlmostEqual(v1, v2, places=4)

    def test_monotonic_increasing_morning(self):
        """6 AM → noon should be monotonically increasing."""
        prev = -1.0
        for hour in [x * 0.25 for x in range(24, 49)]:  # 6.0 to 12.0
            self.clock.internal_hour = hour
            cur = self.clock.energy_multiplier
            self.assertGreaterEqual(cur, prev, f"Energy dropped at hour={hour}")
            prev = cur

    def test_monotonic_decreasing_afternoon(self):
        """Noon → 18 should be monotonically decreasing."""
        prev = float("inf")
        for hour in [x * 0.25 for x in range(48, 73)]:  # 12.0 to 18.0
            self.clock.internal_hour = hour
            cur = self.clock.energy_multiplier
            self.assertLessEqual(cur, prev, f"Energy rose at hour={hour}")
            prev = cur

    def test_formula_at_key_points(self):
        """Verify formula at known values."""
        self.clock.internal_hour = 6.0   # sin(0) = 0 → 0.5
        self.assertAlmostEqual(self.clock.energy_multiplier, 0.5, places=2)
        self.clock.internal_hour = 18.0  # sin(pi) = 0 → 0.5
        self.assertAlmostEqual(self.clock.energy_multiplier, 0.5, places=2)


class TestClockJumpTolerance(unittest.TestCase):
    """Detect discontinuities when real time gap > 300s.

    Uses mocked monotonic clock for precise threshold control.
    """

    def _make_clock(self, last_update_time):
        """Create a clock with a fake monotonic baseline."""
        clock = CircadianClock()
        # Patch last_update so we control real elapsed precisely
        clock.last_update = last_update_time
        return clock

    def test_normal_update_no_jump(self):
        """Small dt (1s) with matching real elapsed should not flag."""
        clock = self._make_clock(1000.0)
        with patch("core.circadian.time.monotonic", return_value=1001.0):
            clock.update(1.0)
        self.assertFalse(clock.clock_jump_detected)

    def test_small_deviation_no_jump(self):
        """A 10s real gap when dt=5s should not flag (delta=5 < 300)."""
        clock = self._make_clock(1000.0)
        with patch("core.circadian.time.monotonic", return_value=1015.0):
            clock.update(5.0)
        self.assertFalse(clock.clock_jump_detected)

    def test_large_gap_triggers_jump(self):
        """Real gap much larger than dt should flag discontinuity."""
        clock = self._make_clock(1000.0)
        with patch("core.circadian.time.monotonic", return_value=1500.0):
            clock.update(1.0)
        self.assertTrue(clock.clock_jump_detected)

    def test_jump_then_normal_update_resets(self):
        """After a jump, next normal update clears the flag."""
        clock = self._make_clock(1000.0)
        # First call: large gap
        with patch("core.circadian.time.monotonic", return_value=1500.0):
            clock.update(1.0)
        self.assertTrue(clock.clock_jump_detected)

        # Second call: normal gap
        with patch("core.circadian.time.monotonic", return_value=1501.0):
            clock.update(1.0)
        self.assertFalse(clock.clock_jump_detected)

    def test_at_threshold_no_jump(self):
        """Exactly at 300s delta should NOT flag (not > 300)."""
        clock = self._make_clock(1000.0)
        with patch("core.circadian.time.monotonic", return_value=1300.0):
            clock.update(0.0)
        self.assertFalse(clock.clock_jump_detected)

    def test_just_over_threshold_triggers(self):
        """301s delta should flag."""
        clock = self._make_clock(1000.0)
        with patch("core.circadian.time.monotonic", return_value=1301.0):
            clock.update(0.0)
        self.assertTrue(clock.clock_jump_detected)


class TestUpdateAdvancesHour(unittest.TestCase):
    """update() correctly advances internal_hour at 1:1 real time."""

    def setUp(self):
        self.clock = CircadianClock()
        self.clock.internal_hour = 0.0  # start at midnight for clean math
        self.clock.last_update = time.monotonic()

    def test_one_second_advance(self):
        """1 second advances internal_hour by 1/3600."""
        self.clock.update(1.0)
        self.assertAlmostEqual(self.clock.internal_hour, 1.0 / 3600.0, places=6)

    def test_one_hour_advance(self):
        """3600 seconds advances internal_hour by 1.0 hour."""
        self.clock.update(3600.0)
        self.assertAlmostEqual(self.clock.internal_hour, 1.0, places=4)

    def test_24h_wraparound(self):
        """86400 seconds wraps around from 0 to 0."""
        self.clock.update(86400.0)
        self.assertAlmostEqual(self.clock.internal_hour, 0.0, places=4)

    def test_partial_hour(self):
        """1800 seconds = 0.5 hours."""
        self.clock.update(1800.0)
        self.assertAlmostEqual(self.clock.internal_hour, 0.5, places=4)

    def test_multiple_updates_accumulate(self):
        """Multiple calls accumulate correctly."""
        self.clock.update(1800.0)  # 0.5h
        self.clock.update(900.0)   # 0.25h
        self.clock.update(900.0)   # 0.25h
        self.assertAlmostEqual(self.clock.internal_hour, 1.0, places=4)

    def test_update_returns_energy_multiplier(self):
        """update() should return the current energy_multiplier."""
        self.clock.internal_hour = 12.0
        result = self.clock.update(0.0)
        self.assertAlmostEqual(result, 1.0, places=4)


class TestPhaseChangeCallbacks(unittest.TestCase):
    """Callbacks fire correctly on phase transitions."""

    def test_callback_fires_on_transition(self):
        """Callback fires with (new_phase, old_phase) when phase changes."""
        clock = CircadianClock()
        clock.internal_hour = 6.5  # DAWN

        fired = []
        clock.on_phase_change(lambda new_p, old_p: fired.append((new_p, old_p)))

        # Advance to 7.0 (DAWN → MORNING boundary)
        clock.update(1800.0)  # 30 min
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0], ("MORNING", "DAWN"))

    def test_multiple_callbacks(self):
        """Multiple registered callbacks all fire."""
        clock = CircadianClock()
        clock.internal_hour = 6.5  # DAWN

        fired = []
        clock.on_phase_change(lambda n, o: fired.append(("cb1", n, o)))
        clock.on_phase_change(lambda n, o: fired.append(("cb2", n, o)))

        clock.update(1800.0)  # → MORNING
        self.assertEqual(len(fired), 2)

    def test_callback_not_fired_within_phase(self):
        """No callback when staying in same phase."""
        clock = CircadianClock()
        clock.internal_hour = 8.0  # MORNING

        fired = []
        clock.on_phase_change(lambda n, o: fired.append((n, o)))

        clock.update(360.0)  # 6 min, still MORNING
        self.assertEqual(len(fired), 0)

    def test_multiple_transitions(self):
        """Callbacks fire on each distinct transition."""
        clock = CircadianClock()
        clock.internal_hour = 6.5  # DAWN

        transitions = []
        clock.on_phase_change(lambda n, o: transitions.append((n, o)))

        # DAWN → MORNING at 7
        clock.update(1800.0)
        self.assertEqual(len(transitions), 1)

        # MORNING → MIDDAY at 11
        clock.update(14400.0)  # 4 more hours
        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[1], ("MIDDAY", "MORNING"))

    def test_callback_receives_old_phase(self):
        """Callback's old_phase parameter has the previous phase."""
        clock = CircadianClock()
        clock.internal_hour = 6.999  # just before MORNING

        result = {}

        def cb(new_p, old_p):
            result["new"] = new_p
            result["old"] = old_p

        clock.on_phase_change(cb)
        clock.update(10.0)  # crosses into 7 → MORNING
        self.assertEqual(result.get("old"), "DAWN")
        self.assertEqual(result.get("new"), "MORNING")

    def test_deep_night_to_dawn_transition(self):
        """DEEP_NIGHT → DAWN at hour 5 fires callback."""
        clock = CircadianClock()
        clock.internal_hour = 4.5  # DEEP_NIGHT

        fired = []
        clock.on_phase_change(lambda n, o: fired.append((n, o)))
        clock.update(1800.0)  # 0.5h → 5.0 → DAWN
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0], ("DAWN", "DEEP_NIGHT"))


if __name__ == "__main__":
    unittest.main()
