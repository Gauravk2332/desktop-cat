"""
tests/test_vocalizations.py — Unit tests for behavior/vocalizations.py

Tests cover:
- VocalizationState initialization and tracking
- Proximity event detection (owner returned, sudden approach, petting)
- Distress sound triggering (yowl at critical needs)
- Boredom meows
- Play excitement sounds (chirp/chatter)
- Idle vocalizations
- Priority resolution (higher-priority sound wins)
- Cooldown enforcement
"""

import os
import sys
import math
import time
import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config

# Fake screen dimensions for scaling
SCREEN_W = 1920
SCREEN_H = 1080


def _make_cat(override=None):
    """Helper to create a realistic cat state dict."""
    cat = {
        "id": 0,
        "x": 500.0,
        "y": 700.0,
        "state": "SIT",
        "energy": 80.0,
        "hunger": 20.0,
        "boredom": 0.0,
        "_screen_width": SCREEN_W,
    }
    if override:
        cat.update(override)
    return cat


def _make_state(cats=None):
    """Helper to create a minimal state object."""
    class FakeState:
        pass
    fs = FakeState()
    fs.cats = cats or [_make_cat()]
    fs.screen_width = SCREEN_W
    fs.screen_height = SCREEN_H
    fs._mouse_x = 500.0
    fs._mouse_y = 700.0
    return fs


class TestVocalizationState(unittest.TestCase):
    """Test VocalizationState initialization and tracking."""

    def test_init(self):
        from behavior.vocalizations import VocalizationState
        vs = VocalizationState()
        self.assertEqual(vs.last_sound_time, 0.0)
        self.assertEqual(vs.last_sound_name, "")
        self.assertEqual(len(vs.mouse_proximity), 0)
        self.assertEqual(len(vs.mouse_positions), 0)
        self.assertGreater(vs.idle_timer, 0)

    def test_record_proximity(self):
        from behavior.vocalizations import VocalizationState
        vs = VocalizationState()
        vs.record_proximity(500, 700, 500, 700, 100.0)
        self.assertEqual(len(vs.mouse_proximity), 1)
        self.assertEqual(len(vs.mouse_positions), 1)
        self.assertEqual(len(vs.mouse_timestamps), 1)
        # Distance 0 (mouse on cat)
        self.assertEqual(vs.mouse_proximity[0], 0.0)

    def test_record_proximity_far(self):
        from behavior.vocalizations import VocalizationState
        vs = VocalizationState()
        vs.record_proximity(0, 0, 1000, 1000, 100.0)
        d = vs.mouse_proximity[0]
        self.assertAlmostEqual(d, math.hypot(1000, 1000))

    def test_record_proximity_respects_maxlen(self):
        from behavior.vocalizations import VocalizationState, PROXIMITY_HISTORY_LEN, MOUSE_POS_HISTORY_LEN
        vs = VocalizationState()
        for i in range(PROXIMITY_HISTORY_LEN + 5):
            vs.record_proximity(0, 0, 100, 100, float(i))
        self.assertEqual(len(vs.mouse_proximity), PROXIMITY_HISTORY_LEN)
        self.assertEqual(len(vs.mouse_positions), MOUSE_POS_HISTORY_LEN)


class TestProximityEvents(unittest.TestCase):
    """Test proximity event detection."""

    def setUp(self):
        from behavior.vocalizations import VocalizationState, _detect_proximity_events
        self.VocalizationState = VocalizationState
        self._detect = _detect_proximity_events

    def test_no_events_with_no_history(self):
        vs = self.VocalizationState()
        result = self._detect(vs, 500, 700, SCREEN_W)
        self.assertFalse(result["owner_returned"])
        self.assertFalse(result["sudden_approach"])
        self.assertFalse(result["petting"])
        self.assertEqual(result["current_distance"], 9999.0)

    def test_far_away_no_return(self):
        vs = self.VocalizationState()
        # Populate history with far distances
        far_d = 600  # > FAR_THRESHOLD (400)
        for i in range(10):
            vs.record_proximity(500, 700, 500 + far_d, 700, float(i))
        result = self._detect(vs, 500, 700, SCREEN_W)
        self.assertFalse(result["owner_returned"])
        self.assertFalse(result["petting"])

    def test_owner_returned_detected(self):
        vs = self.VocalizationState()
        vs.greeting_cooldown = 0.0  # Ensure greeting is allowed
        # Start with far distances
        for i in range(10):
            vs.record_proximity(500, 700, 500 + 500, 700, float(i))
        # Then record near position
        vs.record_proximity(500, 700, 500 + 50, 700, 99.0)
        result = self._detect(vs, 500, 700, SCREEN_W)
        self.assertTrue(result["owner_returned"])

    def test_owner_returned_blocked_by_greeting_cooldown(self):
        vs = self.VocalizationState()
        vs.greeting_cooldown = 30.0  # Still on cooldown
        for i in range(10):
            vs.record_proximity(500, 700, 1500, 700, float(i))
        vs.record_proximity(500, 700, 500 + 50, 700, 99.0)
        result = self._detect(vs, 500, 700, SCREEN_W)
        self.assertFalse(result["owner_returned"])

    def test_sudden_approach_detected(self):
        """Fast mouse movement toward cat should trigger sudden_approach."""
        from behavior.vocalizations import SUDDEN_SPEED
        vs = self.VocalizationState()
        # Start far, then jump near very fast
        vs.mouse_positions.append((1000, 700))
        vs.mouse_timestamps.append(0.0)
        vs.mouse_positions.append((550, 700))
        vs.mouse_timestamps.append(0.25)  # Fast: 450px in 0.25s = 1800px/s
        vs.mouse_proximity.append(750)  # Approx dist from cat
        vs.mouse_proximity.append(50)   # Close now
        result = self._detect(vs, 500, 700, SCREEN_W)
        self.assertTrue(result["sudden_approach"])

    def test_sudden_approach_not_for_slow_movement(self):
        vs = self.VocalizationState()
        vs.mouse_positions.append((600, 700))
        vs.mouse_timestamps.append(0.0)
        vs.mouse_positions.append((550, 700))
        vs.mouse_timestamps.append(2.0)  # 50px in 2s = 25px/s
        vs.mouse_proximity.append(100)
        vs.mouse_proximity.append(50)
        result = self._detect(vs, 500, 700, SCREEN_W)
        self.assertFalse(result["sudden_approach"])

    def test_petting_detected(self):
        vs = self.VocalizationState()
        # pet_threshold is PET_DISTANCE = 60
        vs.mouse_proximity.append(200)
        vs.mouse_proximity.append(30)  # Within pet range
        result = self._detect(vs, 500, 700, SCREEN_W)
        self.assertTrue(result["petting"])


class TestDistressSounds(unittest.TestCase):
    """Test distress sound triggers."""

    def setUp(self):
        from behavior.vocalizations import VocalizationState, _check_distress
        self.VocalizationState = VocalizationState
        self._check = _check_distress

    def test_yowl_at_critical_hunger(self):
        vs = self.VocalizationState()
        cat = _make_cat({"hunger": 95.0, "energy": 80.0})
        result = self._check(vs, cat, time.monotonic())
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "yowl")
        self.assertEqual(result.tier, 0)  # TIER_DISTRESS

    def test_yowl_at_critical_energy(self):
        vs = self.VocalizationState()
        cat = _make_cat({"hunger": 20.0, "energy": 10.0})
        result = self._check(vs, cat, time.monotonic())
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "yowl")

    def test_no_yowl_when_sleeping(self):
        vs = self.VocalizationState()
        cat = _make_cat({"hunger": 95.0, "state": "SLEEP"})
        result = self._check(vs, cat, time.monotonic())
        self.assertIsNone(result)

    def test_meow_long_at_moderate_hunger(self):
        vs = self.VocalizationState()
        cat = _make_cat({"hunger": 75.0})
        result = self._check(vs, cat, time.monotonic())
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "meow_long")
        self.assertEqual(result.tier, 1)  # TIER_URGENT

    def test_no_sound_at_low_hunger(self):
        vs = self.VocalizationState()
        cat = _make_cat({"hunger": 30.0})
        result = self._check(vs, cat, time.monotonic())
        self.assertIsNone(result)

    def test_yowl_cooldown_respected(self):
        vs = self.VocalizationState()
        now = time.monotonic()
        vs.cooldowns["yowl"] = now - 10.0  # Only 10s ago (needs 180s)
        cat = _make_cat({"hunger": 95.0})
        result = self._check(vs, cat, now)
        # Should get meow_long (fallback tier)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "meow_long")


class TestBoredomSounds(unittest.TestCase):
    """Test boredom sound triggers."""

    def setUp(self):
        from behavior.vocalizations import VocalizationState, _check_boredom
        self.VocalizationState = VocalizationState
        self._check = _check_boredom

    def test_meow_long_at_high_boredom(self):
        vs = self.VocalizationState()
        cat = _make_cat({"boredom": 85.0, "state": "SIT"})
        result = self._check(vs, cat, time.monotonic(), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "meow_long")
        self.assertEqual(result.tier, 1)  # TIER_URGENT

    def test_no_boredom_noise_when_sleeping(self):
        vs = self.VocalizationState()
        cat = _make_cat({"boredom": 90.0, "state": "SLEEP"})
        result = self._check(vs, cat, time.monotonic(), {})
        self.assertIsNone(result)

    def test_meow_short_at_medium_boredom(self):
        vs = self.VocalizationState()
        cat = _make_cat({"boredom": 65.0, "state": "SIT"})
        with patch('behavior.vocalizations.random.random', return_value=0.1):
            result = self._check(vs, cat, time.monotonic(), {})
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "meow_short")


class TestPlayExcitement(unittest.TestCase):
    """Test play excitement sounds."""

    def setUp(self):
        from behavior.vocalizations import VocalizationState, _check_play_excitement
        self.VocalizationState = VocalizationState
        self._check = _check_play_excitement

    def test_chirp_during_chase(self):
        vs = self.VocalizationState()
        cat = _make_cat({"state": "CHASE"})
        with patch('behavior.vocalizations.random.random', return_value=0.2):
            result = self._check(vs, cat, time.monotonic(), {})
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "chirp")

    def test_no_chirp_during_sit(self):
        vs = self.VocalizationState()
        cat = _make_cat({"state": "SIT"})
        result = self._check(vs, cat, time.monotonic(), {})
        self.assertIsNone(result)


class TestPriorityResolution(unittest.TestCase):
    """Test that the VocalizationSystem correctly resolves priority."""

    def setUp(self):
        from behavior.vocalizations import VocalizationSystem
        self.system = VocalizationSystem(_make_state())

    def test_distress_beats_urgent(self):
        """Distress (tier 0) should beat urgent (tier 1)."""
        cat = _make_cat({"hunger": 95.0, "boredom": 85.0})
        result = self.system.update(0.1, cat, _make_state())
        self.assertIsNotNone(result)
        # Distress (yowl) should win over boredom meow
        self.assertEqual(result.name, "yowl")

    def test_urgent_beats_interact(self):
        """Urgent (tier 1) should beat interact (tier 2)."""
        from behavior.vocalizations import VocalizationState
        vs = self.system.get_vocal_state(0)
        vs.greeting_cooldown = 0.0
        vs.cooldowns["meow_long"] = 0.0  # Ensure not on cooldown

        # Cat is very hungry (urgent) and mouse just came near (interact)
        cat = _make_cat({"hunger": 85.0, "state": "SIT", "x": 500, "y": 700})
        state = _make_state([cat])
        state._mouse_x = 520  # Close to cat
        state._mouse_y = 700

        # Seed history so owner_returned fires
        for i in range(10):
            vs.mouse_proximity.append(600)
        vs.mouse_positions.append((1100, 700))
        vs.mouse_timestamps.append(0.0)
        vs.mouse_positions.append((520, 700))
        vs.mouse_timestamps.append(1.0)
        vs.mouse_proximity.append(600)
        vs.mouse_proximity.append(20)

        result = self.system.update(0.1, cat, state)
        # Should return something, most likely meow_long (hunger is urgent, tier 1)
        # which outranks trill (interact, tier 2)
        if result:
            self.assertIn(result.tier, [0, 1])  # distress or urgent

    def test_no_sound_on_healthy_cat(self):
        """A healthy, content cat should return None most of the time."""
        cat = _make_cat({"hunger": 30.0, "boredom": 10.0, "energy": 80.0})
        state = _make_state([cat])
        state._mouse_x = 1000  # Far
        state._mouse_y = 700

        # Multiple updates should rarely produce sounds
        results = []
        for _ in range(100):
            result = self.system.update(0.1, cat, state)
            if result:
                results.append(result.name)

        # Most runs should have 0 or very few sounds (healthy, content cat)
        self.assertLess(len(results), 30)  # generous upper bound


class TestCooldownEnforcement(unittest.TestCase):
    """Test that sound cooldowns are properly enforced."""

    def setUp(self):
        from behavior.vocalizations import VocalizationSystem
        self.system = VocalizationSystem(_make_state())

    def test_same_sound_not_replayed_within_cooldown(self):
        """After playing a sound, it should not replay until cooldown expires."""
        cat = _make_cat({"hunger": 95.0})
        state = _make_state([cat])

        # First call should trigger yowl
        r1 = self.system.update(0.1, cat, state)
        self.assertIsNotNone(r1)
        sound_name = r1.name

        # Check cooldown is set
        vs = self.system.get_vocal_state(0)
        self.assertIn(sound_name, vs.cooldowns)
        last_played = vs.cooldowns[sound_name]
        self.assertGreater(last_played, 0)

        # Second call immediately after should NOT play the same sound
        # (the check functions check their own cooldowns)
        r2 = self.system.update(0.1, cat, state)
        # Either no sound or a different sound
        if r2:
            self.assertNotEqual(r2.name, sound_name)


class TestVocalizationSystemInit(unittest.TestCase):
    """Test VocalizationSystem initialization."""

    def test_init_with_one_cat(self):
        from behavior.vocalizations import VocalizationSystem
        vsys = VocalizationSystem(_make_state())
        self.assertEqual(len(vsys._vocal_states), 1)

    def test_init_with_three_cats(self):
        from behavior.vocalizations import VocalizationSystem
        state = _make_state([_make_cat({"id": 0}), _make_cat({"id": 1}), _make_cat({"id": 2})])
        vsys = VocalizationSystem(state)
        self.assertEqual(len(vsys._vocal_states), 3)


if __name__ == "__main__":
    unittest.main()
