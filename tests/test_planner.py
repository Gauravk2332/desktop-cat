"""
tests/test_planner.py — Tests for behavior/planner.py
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from behavior.planner import BehaviorPlanner


class FakeState:
    """Minimal state stub for planner tests."""
    pass


def _make_cat(**kwargs):
    cat = {
        "energy": 80.0,
        "hunger": 20.0,
        "boredom": 20.0,
        "state": "SIT",
        "user_nearby": False,
        "pet_timer": 0.0,
        "x": 500.0,
        "y": 700.0,
        "facing": True,
    }
    cat.update(kwargs)
    return cat


class TestPlannerChain(unittest.TestCase):
    """Test the 5-layer priority chain."""

    def setUp(self):
        self.planner = BehaviorPlanner()
        self.state = FakeState()

    def test_emergency_energy_critical(self):
        """Layer 1: Emergency sleep when energy < 5."""
        cat = _make_cat(energy=4.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state)
        self.assertEqual(action, "sleep", f"Expected sleep, got {action}")
        self.assertEqual(priority, 1, "Emergency should be priority 1")

    def test_emergency_not_triggered_normal(self):
        """Normal energy should NOT trigger emergency."""
        cat = _make_cat(energy=50.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state)
        self.assertNotEqual(action, "sleep",
                            f"Should not emergency sleep at energy 50, got {action}")

    def test_hunger_above_threshold_triggers_hungerwalk(self):
        """Layer 4: Hunger > 60 at dawn triggers walk_to_food."""
        circadian = MagicMock()
        circadian.internal_hour = 6.0  # dawn

        cat = _make_cat(hunger=70.0, boredom=10.0, energy=80.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state,
                                                        circadian=circadian)
        self.assertEqual(action, "walk_to_food",
                         f"Expected walk_to_food at hunger=70 dawn, got {action}")

    def test_boredom_triggers_play(self):
        """Layer 4: Boredom > 60 triggers play."""
        cat = _make_cat(hunger=20.0, boredom=80.0, energy=80.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state)
        self.assertEqual(action, "play",
                         f"Expected play at boredom=80, got {action}")

    def test_low_energy_triggers_sleep(self):
        """Layer 4: Energy < 40 triggers sleep."""
        cat = _make_cat(energy=30.0, hunger=20.0, boredom=30.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state)
        self.assertEqual(action, "sleep",
                         f"Expected sleep at energy=30, got {action}")

    def test_happy_idle(self):
        """Layer 5: Satisfied needs produce idle action."""
        cat = _make_cat(energy=80.0, hunger=20.0, boredom=20.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state)
        self.assertTrue(action in ("sit", "ear_twitch", "slow_blink", "tail_twitch",
                                    "weight_shift", "look_around", "stare",
                                    "window_watch"),
                        f"Expected idle action, got {action}")
        self.assertTrue(priority >= 5, f"Idle should be priority >= 5, got {priority}")

    def test_interaction_triggers_greet(self):
        """Layer 3: User nearby + pet_timer triggers greet."""
        cat = _make_cat(energy=80.0, user_nearby=True, pet_timer=1.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state)
        self.assertEqual(action, "greet",
                         f"Expected greet from interaction, got {action}")
        self.assertEqual(priority, 3)

    def test_is_cat_busy_no_sequence(self):
        """Cat not busy when no sequence running."""
        cat = _make_cat()
        busy = self.planner.is_cat_busy(cat)
        self.assertFalse(busy)

    def test_handle_interaction_sets_timer(self):
        """handle_interaction should set pet_timer and user_nearby."""
        cat = _make_cat()
        self.planner.handle_interaction("click", cat, self.state)
        self.assertGreater(cat["pet_timer"], 0)
        self.assertTrue(cat["user_nearby"])

    def test_reset_clears_state(self):
        """Reset should clear planner state."""
        cat = _make_cat(energy=4.0)
        self.planner.update(0.05, cat, self.state)
        self.planner.reset()
        self.assertEqual(self.planner.get_current_sequence_name(), "")
        self.assertFalse(self.planner.sequence_runner.running)

    def test_needs_enabled_flag(self):
        """When NEEDS_ENABLED=False, planner skips need check."""
        with patch.object(config, "NEEDS_ENABLED", False):
            planner = BehaviorPlanner()
            # With needs disabled, hunger should not trigger anything
            circadian = MagicMock()
            circadian.internal_hour = 6.0
            cat = _make_cat(hunger=70.0, boredom=10.0, energy=80.0)
            action, is_seq, priority = planner.update(0.05, cat, self.state,
                                                       circadian=circadian)
            # Should fall through to idle
            self.assertEqual(priority, 6,
                             f"With needs disabled, should be idle priority 6, got {priority}")


class TestHungerNeeds(unittest.TestCase):
    """Test the hunger-driven behavior specifically.
    
    This is a Lens-verified exit criterion: hunger=80+dawn → HungerWalk,
    not GroomSession.
    """

    def setUp(self):
        self.planner = BehaviorPlanner()
        self.state = FakeState()

    def test_hunger_at_dawn_triggers_food_walk(self):
        """hunger > 60 at dawn → walk_to_food (not groom/sleep/play)."""
        circadian = MagicMock()
        circadian.internal_hour = 5.5  # dawn

        cat = _make_cat(hunger=80.0, boredom=30.0, energy=70.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state,
                                                        circadian=circadian)
        self.assertEqual(action, "walk_to_food",
                         f"Hunger=80 at dawn should produce 'walk_to_food', got {action}")

    def test_hunger_at_midday_no_trigger(self):
        """hunger > 60 outside dawn/dusk should not trigger walk_to_food."""
        circadian = MagicMock()
        circadian.internal_hour = 13.0  # midday

        cat = _make_cat(hunger=80.0, boredom=30.0, energy=70.0)
        action, is_seq, priority = self.planner.update(0.05, cat, self.state,
                                                        circadian=circadian)
        self.assertNotEqual(action, "walk_to_food",
                            f"Hunger=80 at hour 13 should not trigger food walk, got {action}")


if __name__ == "__main__":
    unittest.main()
