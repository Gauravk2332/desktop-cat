"""
tests/test_engine_planner.py — Unit tests for behavior planner integration.

Tests:
  - _execute_planner_action maps each action correctly (12+ actions)
  - Planner runs in engine tick and produces output
  - Needs with circadian modulation (noon vs midnight)
  - Needs without circadian (NEEDS_ENABLED=False) fallback
  - Compatibility: planner doesn't interrupt chase/sleep with wrong action
"""

import os
import sys
import time
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState, default_cat_dict

# ── Qt bootstrap (headless) ─────────────────────────────────────────────
_app = None


def _get_app():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication(sys.argv[:1] if sys.argv else [])
    return _app


DEFAULT_W = 1920
DEFAULT_H = 1080


def _make_state(num_cats=1):
    state = CatState(screen_width=DEFAULT_W, screen_height=DEFAULT_H)
    while len(state.cats) < num_cats:
        state.cats.append(default_cat_dict(len(state.cats)))
    return state


def _make_mock_window():
    """Create a real QWidget that acts as a mock window.

    PyQt 6.11+ reject MagicMock even with __class__ override due to
    sip-based C-level type checks. Using a real QWidget avoids this.
    """
    from PyQt6.QtWidgets import QWidget
    from unittest.mock import MagicMock
    widget = QWidget()
    widget.update = MagicMock()
    widget.geometry = MagicMock(
        return_value=MagicMock(
            width=lambda: DEFAULT_W,
            height=lambda: DEFAULT_H,
        )
    )
    return widget


def _make_engine(num_cats=1):
    """Create a test Engine with mock window, timers stopped."""
    _get_app()
    from core.engine import Engine

    mock_window = _make_mock_window()
    state = _make_state(num_cats)
    engine = Engine(state, mock_window)

    # Stop timers to prevent interference
    if hasattr(engine, '_tick_timer') and engine._tick_timer:
        engine._tick_timer.stop()
    if hasattr(engine, '_idle_timer') and engine._idle_timer:
        engine._idle_timer.stop()
    if hasattr(engine, '_mouse_timer') and engine._mouse_timer:
        engine._mouse_timer.stop()

    return engine, state, mock_window


def _make_cat(x=500.0, y=700.0, state="SIT"):
    """Build a minimal cat dict matching engine expectations."""
    cat = default_cat_dict(0, 0, x, y)
    cat["state"] = state
    cat["energy"] = 80.0
    cat["hunger"] = 20.0
    cat["boredom"] = 0.0
    cat["purr_vibrate"] = 0.0
    cat["blinking"] = False
    cat["blink_timer"] = 0.0
    cat["reaction_type"] = None
    cat["reaction_timer"] = 0.0
    cat["eye_current"] = (0.0, 0.0)
    cat["speech_cooldown"] = 0.0
    cat["speech"] = {
        "text": None, "emoji": None, "timer": 0.0,
        "fading": False, "opacity": 0.0, "queue": [],
    }
    cat["deep_sleep"] = False
    cat["toy_active"] = False
    cat["toy_type"] = None
    cat["toy_target"] = None
    cat["toy_timer"] = 0.0
    cat["chase_timeout"] = 0.0
    cat["mouse_near"] = False
    cat["last_interaction"] = 0.0
    cat["walk_frame"] = 0
    cat["walk_accum"] = 0.0
    cat["walk_accel"] = 0.0
    cat["walk_pause"] = False
    cat["walk_duration"] = 0.0
    cat["walk_elapsed"] = 0.0
    cat["walk_vy"] = 0.0
    cat["wander_duration"] = 0.0
    cat["wander_elapsed"] = 0.0
    cat["wander_cooldown"] = 0.0
    cat["wander_vx"] = 0.0
    cat["wander_vy"] = 0.0
    cat["hut_index"] = 0
    cat["consecutive_pets"] = 0
    cat["tail_phase"] = 0.0
    cat["sleep_breath"] = 0.0
    cat["zzz_particles"] = []
    cat["hearts"] = []
    return cat


class TestExecutePlannerAction(unittest.TestCase):
    """Test _execute_planner_action maps each planner action correctly."""

    def setUp(self):
        self.engine, self.state, self._mock_window = _make_engine()
        self.cat = self.state.cats[0]
        # Replace cat with standard test cat
        self.cat.update(_make_cat(state="SIT"))

    def _execute(self, action, dt=0.05):
        self.engine._execute_planner_action(self.cat, action, dt)

    # ── sleep ──────────────────────────────────────────────────────────

    def test_sleep_from_sit(self):
        """sleep action from SIT transitions to SLEEP with deep sleep."""
        self.cat["state"] = "SIT"
        self._execute("sleep")
        self.assertEqual(self.cat["state"], "SLEEP")
        self.assertTrue(self.cat["deep_sleep"])

    def test_sleep_from_walk(self):
        """sleep action from WALK transitions to SLEEP."""
        self.cat["state"] = "WALK"
        self._execute("sleep")
        self.assertEqual(self.cat["state"], "SLEEP")
        self.assertTrue(self.cat["deep_sleep"])

    def test_sleep_does_not_interrupt_chase(self):
        """sleep action does not interrupt CHASE."""
        self.cat["state"] = "CHASE"
        self._execute("sleep")
        self.assertEqual(self.cat["state"], "CHASE")

    def test_sleep_does_not_interrupt_play(self):
        """sleep action does not interrupt PLAY."""
        self.cat["state"] = "PLAY"
        self._execute("sleep")
        self.assertEqual(self.cat["state"], "PLAY")

    def test_sleep_when_already_sleeping(self):
        """sleep action when already SLEEP is no-op (no error)."""
        self.cat["state"] = "SLEEP"
        self._execute("sleep")
        self.assertEqual(self.cat["state"], "SLEEP")

    # ── sit ────────────────────────────────────────────────────────────

    def test_sit_from_walk(self):
        """sit action from WALK transitions to SIT."""
        self.cat["state"] = "WALK"
        self._execute("sit")
        self.assertEqual(self.cat["state"], "SIT")

    def test_sit_from_wander(self):
        """sit action from WANDER transitions to SIT."""
        self.cat["state"] = "WANDER"
        self._execute("sit")
        self.assertEqual(self.cat["state"], "SIT")

    def test_sit_from_go_home(self):
        """sit action from GO_HOME transitions to SIT."""
        self.cat["state"] = "GO_HOME"
        self._execute("sit")
        self.assertEqual(self.cat["state"], "SIT")

    def test_sit_does_not_interrupt_chase(self):
        """sit action does not interrupt CHASE."""
        self.cat["state"] = "CHASE"
        self._execute("sit")
        self.assertEqual(self.cat["state"], "CHASE")

    def test_sit_does_not_interrupt_play(self):
        """sit action does not interrupt PLAY."""
        self.cat["state"] = "PLAY"
        self._execute("sit")
        self.assertEqual(self.cat["state"], "PLAY")

    def test_sit_does_not_wake_sleeping(self):
        """sit action does not wake a sleeping cat."""
        self.cat["state"] = "SLEEP"
        self._execute("sit")
        self.assertEqual(self.cat["state"], "SLEEP")

    # ── walk_to_food ───────────────────────────────────────────────────

    def test_walk_to_food_from_sit(self):
        """walk_to_food from SIT transitions to WALK with target near screen bottom."""
        self.cat["state"] = "SIT"
        self._execute("walk_to_food")
        self.assertEqual(self.cat["state"], "WALK")
        self.assertIsNotNone(self.cat.get("walk_target_x"))
        self.assertIsNotNone(self.cat.get("walk_target_y"))

    def test_walk_to_food_does_not_interrupt_chase(self):
        """walk_to_food does not interrupt CHASE."""
        self.cat["state"] = "CHASE"
        self._execute("walk_to_food")
        self.assertEqual(self.cat["state"], "CHASE")

    # ── play ───────────────────────────────────────────────────────────

    def test_play_from_sit(self):
        """play action from SIT transitions to PLAY with toy target."""
        self.cat["state"] = "SIT"
        self._execute("play")
        self.assertEqual(self.cat["state"], "PLAY")
        self.assertTrue(self.cat["toy_active"])
        self.assertEqual(self.cat["toy_type"], "ball")
        self.assertIsNotNone(self.cat["toy_target"])

    def test_play_does_not_interrupt_chase(self):
        """play action does not interrupt CHASE."""
        self.cat["state"] = "CHASE"
        self._execute("play")
        self.assertEqual(self.cat["state"], "CHASE")

    # ── greet ──────────────────────────────────────────────────────────

    def test_greet_sets_sit_purr(self):
        """greet action sets SIT, purr_vibrate, and doesn't crash."""
        self.cat["state"] = "SIT"
        self._execute("greet")
        self.assertEqual(self.cat["state"], "SIT")
        self.assertGreater(self.cat["purr_vibrate"], 0.0)

    def test_greet_from_play_blocked(self):
        """greet action blocked during PLAY."""
        self.cat["state"] = "PLAY"
        self._execute("greet")
        self.assertEqual(self.cat["state"], "PLAY")

    # ── window_watch ───────────────────────────────────────────────────

    def test_window_watch_sets_sit_west(self):
        """window_watch sets SIT and facing west (False)."""
        self.cat["state"] = "SIT"
        self.cat["facing"] = True
        self._execute("window_watch")
        self.assertEqual(self.cat["state"], "SIT")
        self.assertFalse(self.cat["facing"])

    def test_window_watch_blocked_during_chase(self):
        """window_watch blocked during CHASE."""
        self.cat["state"] = "CHASE"
        self._execute("window_watch")
        self.assertEqual(self.cat["state"], "CHASE")

    # ── patrol ─────────────────────────────────────────────────────────

    def test_patrol_from_sit(self):
        """patrol action from SIT transitions to WALK."""
        self.cat["state"] = "SIT"
        self._execute("patrol")
        self.assertEqual(self.cat["state"], "WALK")

    def test_patrol_blocked_during_chase(self):
        """patrol blocked during CHASE."""
        self.cat["state"] = "CHASE"
        self._execute("patrol")
        self.assertEqual(self.cat["state"], "CHASE")

    # ── micro-reactions ────────────────────────────────────────────────

    def test_groom_sets_reaction(self):
        """groom sets reaction_type and timer."""
        self.cat["state"] = "SIT"
        self._execute("groom")
        self.assertEqual(self.cat["reaction_type"], "groom")
        self.assertAlmostEqual(self.cat["reaction_timer"], 2.0, places=3)

    def test_ear_twitch_sets_reaction(self):
        """ear_twitch sets reaction_type and timer."""
        self._execute("ear_twitch")
        self.assertEqual(self.cat["reaction_type"], "ear_twitch")
        self.assertAlmostEqual(self.cat["reaction_timer"], 0.3, places=3)

    def test_slow_blink_triggers_blink(self):
        """slow_blink triggers blinking."""
        self.cat["blinking"] = False
        self._execute("slow_blink")
        self.assertTrue(self.cat["blinking"])

    def test_tail_twitch_sets_reaction(self):
        """tail_twitch sets reaction_type and timer."""
        self._execute("tail_twitch")
        self.assertEqual(self.cat["reaction_type"], "tail_twitch")
        self.assertAlmostEqual(self.cat["reaction_timer"], 0.5, places=3)

    def test_weight_shift_sets_reaction(self):
        """weight_shift sets reaction_type and timer."""
        self._execute("weight_shift")
        self.assertEqual(self.cat["reaction_type"], "weight_shift")
        self.assertAlmostEqual(self.cat["reaction_timer"], 0.4, places=3)

    def test_look_around_sets_reaction(self):
        """look_around sets reaction_type and timer."""
        self._execute("look_around")
        self.assertEqual(self.cat["reaction_type"], "look_around")
        self.assertAlmostEqual(self.cat["reaction_timer"], 0.6, places=3)

    def test_stare_sets_reaction(self):
        """stare sets reaction_type and timer."""
        self._execute("stare")
        self.assertEqual(self.cat["reaction_type"], "stare")
        self.assertAlmostEqual(self.cat["reaction_timer"], 1.0, places=3)

    def test_idle_is_noop(self):
        """idle action does nothing."""
        before_state = self.cat["state"]
        before_reaction = self.cat["reaction_type"]
        self._execute("idle")
        self.assertEqual(self.cat["state"], before_state)
        self.assertEqual(self.cat["reaction_type"], before_reaction)


class TestPlannerInEngineTick(unittest.TestCase):
    """Test that planner runs during engine tick and produces output."""

    def setUp(self):
        self.engine, self.state, self._mock_window = _make_engine()

    def test_planner_initialized_after_engine_init(self):
        """Engine has planner_initialized flag set to True."""
        self.assertTrue(self.engine._planner_initialized)

    def test_planner_is_behaviorplanner(self):
        """Engine planner is a BehaviorPlanner instance."""
        from behavior.planner import BehaviorPlanner
        self.assertIsInstance(self.engine._planner, BehaviorPlanner)

    def test_circadian_clock_exists(self):
        """Engine has circadian clock when CIRCADIAN_ENABLED."""
        from core.circadian import CircadianClock
        if config.CIRCADIAN_ENABLED:
            self.assertIsNotNone(self.engine._circadian)
            self.assertIsInstance(self.engine._circadian, CircadianClock)

    def test_tick_does_not_crash_with_planner(self):
        """Engine tick runs without error with planner active."""
        try:
            self.engine._on_tick()
        except Exception as e:
            self.fail(f"Engine tick raised {e}")

    def test_tick_produces_planner_output(self):
        """After a tick, planner has been called (check last_priority set)."""
        self.engine._planner._last_priority = None
        # Run a few ticks to let planner evaluate
        for _ in range(10):
            self.engine._on_tick()
        # Planner should have evaluated something
        self.assertIsNotNone(self.engine._planner._last_priority,
                             "Planner should have set _last_priority after tick(s)")


class TestNeedsWithCircadian(unittest.TestCase):
    """Test needs.py circadian modulation works correctly."""

    def setUp(self):
        self.state = _make_state()
        self.cat = self.state.cats[0]
        self.cat["state"] = "SIT"
        self.cat["energy"] = 80.0
        self.cat["hunger"] = 20.0

    def _run_needs(self, ticks=100, circadian_multiplier=1.0):
        """Run needs.update for N ticks."""
        import behavior.needs as needs
        dt = 0.05
        for _ in range(ticks):
            needs.update(dt, self.cat, self.state,
                         circadian_energy_multiplier=circadian_multiplier)

    def test_high_circadian_drains_energy_faster(self):
        """Higher circadian multiplier drains energy faster than lower."""
        # Simulate noon (high energy multiplier ~1.0)
        self.cat["energy"] = 80.0
        self._run_needs(ticks=200, circadian_multiplier=1.0)
        energy_noon = self.cat["energy"]

        # Simulate midnight (low energy multiplier ~0.1)
        self.cat["energy"] = 80.0
        self._run_needs(ticks=200, circadian_multiplier=0.1)
        energy_midnight = self.cat["energy"]

        # Energy should drain faster at noon (higher multiplier)
        self.assertGreater(energy_midnight, energy_noon,
                          "Energy should drain slower at night (midnight)")

    def test_hunger_differs_by_circadian(self):
        """Hunger rate differs based on circadian modulation."""
        self.cat["hunger"] = 20.0
        self._run_needs(ticks=200, circadian_multiplier=0.5)
        hunger_night = self.cat["hunger"]

        self.cat["hunger"] = 20.0
        self._run_needs(ticks=200, circadian_multiplier=1.0)
        hunger_day = self.cat["hunger"]

        # Hunger should differ by circadian modulation
        self.assertNotEqual(hunger_night, hunger_day,
                           "Hunger should differ based on circadian modulation")

    def test_needs_without_circadian_fallback(self):
        """Needs work without circadian multiplier (default 1.0)."""
        import behavior.needs as needs
        dt = 0.05
        for _ in range(100):
            needs.update(dt, self.cat, self.state)
        # Energy should have drained from SIT
        self.assertLess(self.cat["energy"], 80.0,
                       "Energy should drain from SIT without circadian")
        self.assertGreater(self.cat["hunger"], 20.0,
                          "Hunger should increase without circadian")


class TestPlannerCompatibility(unittest.TestCase):
    """Test planner doesn't interrupt chase/sleep with wrong actions."""

    def setUp(self):
        self.engine, self.state, self._mock_window = _make_engine()

    def test_chase_not_interrupted_by_any_action(self):
        """CHASE is never interrupted by any planner action."""
        for state_name in ("CHASE", "PLAY"):
            for action in ("sit", "play", "walk_to_food", "greet",
                           "window_watch", "patrol", "groom", "stare",
                           "look_around", "tail_twitch", "weight_shift"):
                cat = self.state.cats[0]
                cat.update(_make_cat(state=state_name))
                self.engine._execute_planner_action(cat, action, 0.05)
                self.assertEqual(cat["state"], state_name,
                                f"{state_name} should not be interrupted by {action}")

    def test_sleep_not_interrupted(self):
        """Sleeping cat is not woken by planner actions."""
        for action in ("sit", "play", "walk_to_food", "greet",
                       "window_watch", "patrol", "groom", "stare",
                       "look_around", "tail_twitch", "weight_shift"):
            cat = self.state.cats[0]
            cat.update(_make_cat(state="SLEEP"))
            self.engine._execute_planner_action(cat, action, 0.05)
            self.assertEqual(cat["state"], "SLEEP",
                            f"SLEEP should not be interrupted by {action}")


class TestNeedsFunctionalityToggle(unittest.TestCase):
    """Test behavior when NEEDS_ENABLED is False."""

    def test_planner_works_without_needs(self):
        """Planner runs even when NEEDS_ENABLED=False (idle behaviors)."""
        from behavior.planner import BehaviorPlanner
        planner = BehaviorPlanner()
        cat = _make_cat(state="SIT")
        cat["energy"] = 80.0
        cat["hunger"] = 20.0
        cat["boredom"] = 0.0
        state = _make_state()
        state.mouse_pos = (0.0, 0.0)

        with patch.object(config, 'NEEDS_ENABLED', False):
            result = planner.update(0.05, cat, state)
            action, is_seq, priority = result
            # Without needs, planner returns idle/sit/micro-behaviors
            self.assertIn(action, ("idle", "sit", "ear_twitch", "slow_blink",
                                   "tail_twitch", "weight_shift", "look_around",
                                   "stare"),
                         f"Planner should return idle or micro-action, got {action}")


if __name__ == "__main__":
    unittest.main()
