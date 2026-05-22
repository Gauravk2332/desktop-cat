"""
tests/test_state_machine.py — Unit tests for behavior/transitions.py

Tests state transitions without Qt display. Creates a mock state object
and runs the transition engine with controlled conditions.
"""

import sys
import os
import random
import unittest
from datetime import datetime
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState


class TestConfigSanity(unittest.TestCase):
    """Sanity checks on config values — catch math errors early."""

    def test_energy_thresholds_ordered(self):
        self.assertLess(config.HOME_ENERGY_THRESHOLD, config.HOME_NAP_MIN_ENERGY,
                        "Home energy threshold must be lower than nap min energy")

    def test_recharge_rate_positive(self):
        self.assertGreater(config.ENERGY_RECHARGE_SLEEP, 0)

    def test_drain_rates_non_negative(self):
        for name, val in [
            ("ENERGY_DRAIN_ACTIVE", config.ENERGY_DRAIN_ACTIVE),
            ("ENERGY_DRAIN_SIT", config.ENERGY_DRAIN_SIT),
            ("HUNGER_DRAIN", config.HUNGER_DRAIN),
            ("BOREDOM_INCREASE_SIT", config.BOREDOM_INCREASE_SIT),
        ]:
            self.assertGreaterEqual(val, 0, f"{name} should be >= 0")

    def test_walk_speed_sane(self):
        self.assertGreater(config.WALK_SPEED, 0)
        self.assertLess(config.WALK_SPEED, 500)  # shouldn't teleport

    def test_wander_duration_ordered(self):
        self.assertGreaterEqual(config.WANDER_DURATION_MAX, config.WANDER_DURATION_MIN)

    def test_wander_cooldown_sane(self):
        self.assertGreaterEqual(config.WANDER_COOLDOWN, 1.0)

    def test_home_padding_positive(self):
        self.assertGreater(config.HUT_PADDING_RIGHT, 0)
        self.assertGreater(config.HUT_PADDING_BOTTOM, 0)


class TestStateTransitions(unittest.TestCase):
    """Test state machine logic in behavior/transitions.py."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.cat_x = 500.0
        self.state.cat_y = 1060.0
        self.dt = 0.05  # one tick

    def _import_transitions(self):
        """Fresh import of transitions module (reload each test)."""
        if "behavior.transitions" in sys.modules:
            del sys.modules["behavior.transitions"]
        import behavior.transitions
        return behavior.transitions

    def _run_ticks(self, transitions, n=100):
        """Run N ticks to allow state machine to settle."""
        for _ in range(n):
            transitions.update(self.dt, self.state)

    def test_sit_to_sleep_low_energy(self):
        """SIT -> GO_HOME when energy drops below HOME_ENERGY_THRESHOLD (priority over field sleep)."""
        trans = self._import_transitions()
        self.state.energy = 35.0  # below HOME_ENERGY_THRESHOLD (40)
        trans.update(self.dt, self.state)
        # GO_HOME fires before SLEEP due to priority order
        self.assertEqual(self.state.state, config.STATE_GO_HOME)

    def test_sit_to_sleep_high_boredom(self):
        """SIT -> GO_HOME when boredom exceeds HOME_BOREDOM_THRESHOLD (priority over field sleep)."""
        trans = self._import_transitions()
        self.state.energy = 90.0
        self.state.boredom = config.HOME_BOREDOM_THRESHOLD + 1.0  # > 70
        trans.update(self.dt, self.state)
        # GO_HOME fires before SLEEP due to priority order
        self.assertEqual(self.state.state, config.STATE_GO_HOME)

    def test_sleep_to_sit_at_home(self):
        """SLEEP at home -> SIT when energy exceeds HOME_NAP_MIN_ENERGY."""
        trans = self._import_transitions()
        self.state.state = config.STATE_SLEEP
        self.state.at_home = True
        self.state.energy = config.HOME_NAP_MIN_ENERGY + 1.0
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)

    def test_sleep_to_sit_field(self):
        """SLEEP in field -> SIT when energy exceeds 85."""
        trans = self._import_transitions()
        self.state.state = config.STATE_SLEEP
        self.state.at_home = False
        self.state.energy = 86.0
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)

    def test_go_home_triggers_low_energy(self):
        """SIT -> GO_HOME when energy below HOME_ENERGY_THRESHOLD."""
        trans = self._import_transitions()
        self.state.energy = config.HOME_ENERGY_THRESHOLD - 1.0
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_GO_HOME)

    def test_sleep_linger_resets_at_home(self):
        """After home sleep, at_home should become False after linger expires."""
        trans = self._import_transitions()
        self.state.state = config.STATE_SLEEP
        self.state.at_home = True
        self.state.energy = 95.0
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)
        self.assertTrue(self.state.at_home)  # lingering
        self.assertGreater(self.state.home_linger, 0)

        # Run ticks until linger expires
        self.state.home_linger = 0.0  # force expire
        trans.update(self.dt, self.state)
        self.assertFalse(self.state.at_home)

    def test_wander_triggers_when_conditions_met(self):
        """SIT -> WANDER when cooldown is 0 and random roll succeeds."""
        trans = self._import_transitions()
        self.state.energy = 90.0
        self.state.boredom = 50.0
        self.state.wander_cooldown = 0.0
        self.state.wander_session_count = 0

        # Force wander chance high by patching datetime
        with patch("behavior.transitions._wander_chance_per_tick") as mock_chance:
            mock_chance.return_value = 1.0  # 100% chance
            trans.update(self.dt, self.state)

        # Should be in WANDER if not at home
        if not self.state.at_home:
            self.assertEqual(self.state.state, config.STATE_WANDER)

    def test_walk_sits_after_duration(self):
        """WALK -> SIT after walk_elapsed exceeds walk_duration + 0.5s."""
        trans = self._import_transitions()
        self.state.state = config.STATE_WALK
        self.state.walk_duration = 2.0
        self.state.walk_elapsed = 3.0  # over 2.0 + 0.5
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)

    def test_walk_sits_under_duration(self):
        """WALK stays WALK when walk_elapsed is within duration."""
        trans = self._import_transitions()
        self.state.state = config.STATE_WALK
        self.state.walk_duration = 3.0
        self.state.walk_elapsed = 2.0  # still under
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_WALK)

    def test_boredom_home_visit(self):
        """SIT -> GO_HOME when boredom high + cooldown expired."""
        trans = self._import_transitions()
        self.state.energy = 90.0
        self.state.boredom = config.HOME_BOREDOM_THRESHOLD + 1.0
        self.state.home_cooldown = 0.0
        self.state.at_home = False
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_GO_HOME)

    def test_field_sleep_not_at_home(self):
        """SLEEP in field stays asleep when energy below 85 (field threshold)."""
        trans = self._import_transitions()
        self.state.state = config.STATE_SLEEP
        self.state.at_home = False  # field sleep (not at home)
        self.state.energy = config.HOME_NAP_MIN_ENERGY + 1.0  # 61 < 85 field threshold
        trans.update(self.dt, self.state)
        # Field threshold is 85, energy 61 < 85, so stays asleep
        self.assertEqual(self.state.state, config.STATE_SLEEP,
                         "Should stay asleep if energy < 85 (field threshold)")

    def test_priority_energy_above_boredom(self):
        """Energy check should take priority over boredom check."""
        trans = self._import_transitions()
        self.state.energy = config.HOME_ENERGY_THRESHOLD - 1.0  # below threshold
        self.state.boredom = 0.0  # not bored
        trans.update(self.dt, self.state)
        self.assertEqual(self.state.state, config.STATE_GO_HOME,
                         "Energy should trigger GO_HOME even without boredom")


class TestNeedsSystem(unittest.TestCase):
    """Test behavior/needs.py — need drain and recharge."""

    def setUp(self):
        self.state = CatState()
        self.dt = 1.0  # 1 second for easy math

    def _import_needs(self):
        if "behavior.needs" in sys.modules:
            del sys.modules["behavior.needs"]
        import behavior.needs
        return behavior.needs

    def test_walk_drains_energy(self):
        """Walking drains ACTIVE rate."""
        needs = self._import_needs()
        self.state.state = config.STATE_WALK
        self.state.energy = 100.0
        needs.update(self.dt, self.state)
        self.assertLess(self.state.energy, 100.0)

    def test_sit_drains_slowly(self):
        """Sitting drains at SIT rate (slower)."""
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.energy = 100.0
        needs.update(self.dt, self.state)
        expected = 100.0 - config.ENERGY_DRAIN_SIT * 1.0
        self.assertAlmostEqual(self.state.energy, expected, places=4)

    def test_sleep_recharges(self):
        """Sleeping recharges energy."""
        needs = self._import_needs()
        self.state.state = config.STATE_SLEEP
        self.state.energy = 50.0
        needs.update(self.dt, self.state)
        self.assertGreater(self.state.energy, 50.0)

    def test_hunger_increases_over_time(self):
        """Hunger rises over time."""
        needs = self._import_needs()
        self.state.hunger = 20.0
        needs.update(self.dt, self.state)
        self.assertGreater(self.state.hunger, 20.0)

    def test_boredom_increases_when_sitting(self):
        """Boredom rises while sitting."""
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.boredom = 0.0
        needs.update(self.dt, self.state)
        self.assertGreater(self.state.boredom, 0.0)

    def test_boredom_stable_during_walk(self):
        """Boredom should not increase during WALK (cat is active)."""
        needs = self._import_needs()
        self.state.state = config.STATE_WALK
        self.state.boredom = 10.0
        before = self.state.boredom
        needs.update(self.dt, self.state)
        self.assertEqual(self.state.boredom, before,
                         "Boredom shouldn't change during WALK")

    def test_boredom_drops_during_sleep(self):
        """Boredom should drop during SLEEP."""
        needs = self._import_needs()
        self.state.state = config.STATE_SLEEP
        self.state.boredom = 50.0
        needs.update(5.0, self.state)  # 5 seconds
        self.assertLess(self.state.boredom, 50.0)

    def test_needs_clamped_upper(self):
        """Needs should be clamped to 100 max."""
        needs = self._import_needs()
        self.state.energy = 99.0
        self.state.state = config.STATE_SLEEP
        # Run many ticks to push energy past 100
        for _ in range(100):
            needs.update(1.0, self.state)
        self.assertLessEqual(self.state.energy, 100.0)

    def test_needs_clamped_lower(self):
        """Needs should be clamped to 0 min."""
        needs = self._import_needs()
        self.state.energy = 0.0
        self.state.state = config.STATE_WALK
        for _ in range(100):
            needs.update(1.0, self.state)
        self.assertGreaterEqual(self.state.energy, 0.0)


class TestNavigation(unittest.TestCase):
    """Test navigation math — walk, wander, go-home and API action processing."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.cat_x = 960.0
        self.state.cat_y = 1060.0

    def test_walk_moves_right(self):
        """Walking right increases cat_x."""
        from core import navigation
        self.state.state = config.STATE_WALK
        self.state.facing = True
        self.state.walk_duration = 2.0
        self.state.walk_elapsed = 0.5  # past acceleration phase
        self.state.walk_accel = 1.0
        before = self.state.cat_x
        navigation.update_walk(0.05, self.state)
        self.assertGreater(self.state.cat_x, before)

    def test_walk_moves_left(self):
        """Walking left decreases cat_x."""
        from core import navigation
        self.state.state = config.STATE_WALK
        self.state.facing = False
        self.state.walk_duration = 2.0
        self.state.walk_elapsed = 0.5  # past acceleration phase
        self.state.walk_accel = 1.0
        before = self.state.cat_x
        navigation.update_walk(0.05, self.state)
        self.assertLess(self.state.cat_x, before)

    def test_walk_stops_at_right_edge(self):
        """Walk should stop when reaching right screen edge."""
        from core import navigation
        self.state.state = config.STATE_WALK
        self.state.facing = True
        self.state.cat_x = float(self.state.screen_width - 80)
        self.state.walk_duration = 3.0
        navigation.update_walk(0.1, self.state)
        # Should have sat down and reversed
        self.assertEqual(self.state.state, config.STATE_SIT)

    def test_walk_stops_at_left_edge(self):
        """Walk should stop when reaching left screen edge."""
        from core import navigation
        self.state.state = config.STATE_WALK
        self.state.facing = False
        self.state.cat_x = 80.0
        self.state.walk_duration = 3.0
        navigation.update_walk(0.1, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)

    def test_wander_moves_then_times_out(self):
        """Wander should set state=SIT after duration expires."""
        from core import navigation
        self.state.state = config.STATE_WANDER
        self.state.wander_duration = 0.5
        self.state.wander_elapsed = 0.0
        pos_before = (self.state.cat_x, self.state.cat_y)
        # Run many ticks
        for _ in range(50):
            navigation.update_wander(0.05, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)
        self.assertGreater(self.state.wander_cooldown, 0)
        # Should have moved in some direction
        pos_after = (self.state.cat_x, self.state.cat_y)
        self.assertNotEqual(pos_before, pos_after, "Cat should have moved during wander")

    def test_wander_bounces_off_left_edge(self):
        """Wander should bounce off left edge (reverse vx)."""
        from core import navigation
        self.state.state = config.STATE_WANDER
        self.state.wander_vx = -1.0  # going left
        self.state.wander_vy = 0.0
        self.state.cat_x = 60.0  # near left edge (margin=60)
        self.state.cat_y = 100.0
        self.state.wander_duration = 3.0
        self.state.wander_elapsed = 0.0
        vx_before = self.state.wander_vx
        navigation.update_wander(0.05, self.state)
        # vx should be reversed
        self.assertGreater(self.state.wander_vx, 0, "wander_vx should reverse to positive")
        self.assertNotAlmostEqual(self.state.wander_vx, vx_before, delta=0.01)

    def test_wander_bounces_off_right_edge(self):
        """Wander should bounce off right edge (reverse vx)."""
        from core import navigation
        self.state.state = config.STATE_WANDER
        self.state.wander_vx = 1.0  # going right
        self.state.wander_vy = 0.0
        self.state.cat_x = float(self.state.screen_width - 61)  # near right edge
        self.state.cat_y = 100.0
        self.state.wander_duration = 3.0
        self.state.wander_elapsed = 0.0
        vx_before = self.state.wander_vx
        navigation.update_wander(0.05, self.state)
        self.assertLess(self.state.wander_vx, 0, "wander_vx should reverse to negative")

    def test_wander_bounces_off_top_edge(self):
        """Wander should bounce off top edge (reverse vy)."""
        from core import navigation
        self.state.state = config.STATE_WANDER
        self.state.wander_vx = 0.0
        self.state.wander_vy = -1.0  # going up
        y_min = int(self.state.screen_height * config.CAT_MIN_Y_FRACTION)
        self.state.cat_x = 500.0
        self.state.cat_y = float(y_min + 61)  # near top boundary
        self.state.wander_duration = 3.0
        self.state.wander_elapsed = 0.0
        vy_before = self.state.wander_vy
        navigation.update_wander(0.05, self.state)
        self.assertGreater(self.state.wander_vy, 0, "wander_vy should reverse to positive")

    def test_wander_bounces_off_bottom_edge(self):
        """Wander should bounce off bottom edge (cat_y clamped)."""
        from core import navigation
        self.state.state = config.STATE_WANDER
        self.state.wander_vx = 0.0
        self.state.wander_vy = 1.0  # going down
        self.state.wander_elapsed = 1.0  # skip first-tick init
        y_max = self.state.screen_height - config.CAT_BASELINE
        self.state.cat_x = 500.0
        self.state.cat_y = float(y_max - 1)
        self.state.wander_duration = 3.0
        vy_before = self.state.wander_vy
        # Run multiple ticks to ensure bounce (direction change may interfere)
        for _ in range(5):
            navigation.update_wander(0.05, self.state)
        self.assertLessEqual(self.state.cat_y, y_max,
                             "cat_y should not exceed y_max")

    def test_go_home_moves_toward_bed(self):
        """GO_HOME should move cat_x AND cat_y toward bed."""
        from core import navigation
        from cat.home import _hut_door_center
        hx, hy = _hut_door_center(self.state)
        # Place cat at bottom-left of screen (far from bed at bottom-right)
        self.state.cat_x = 100.0
        self.state.cat_y = float(self.state.screen_height - 20)
        self.state.state = config.STATE_GO_HOME
        before_x, before_y = self.state.cat_x, self.state.cat_y
        navigation.update_go_home(0.05, self.state)
        # Should move right AND up toward bed
        self.assertGreater(self.state.cat_x, before_x, "cat_x should increase (move right toward bed)")
        self.assertLess(self.state.cat_y, before_y, "cat_y should decrease (move up toward bed)")

    def test_go_home_arrives_at_hut(self):
        """GO_HOME should set SLEEP when approaching hut door center in 2D."""
        from core import navigation
        from cat.home import _hut_door_center
        hx, hy = _hut_door_center(self.state)
        self.state.state = config.STATE_GO_HOME
        # Close in both x and y
        self.state.cat_x = hx - 1.0
        self.state.cat_y = float(hy)  # y matches
        navigation.update_go_home(0.05, self.state)
        self.assertEqual(self.state.state, config.STATE_SLEEP)
        self.assertTrue(self.state.at_home)
        self.assertAlmostEqual(self.state.cat_x, hx, delta=2)
        self.assertAlmostEqual(self.state.cat_y, hy - 2, delta=2)

    def test_walk_accelerates_then_decelerates(self):
        """Walk accel curve should go up then down."""
        from core import navigation
        self.state.state = config.STATE_WALK
        self.state.facing = True
        self.state.walk_duration = 2.0
        accels = []
        for step in range(60):
            self.state.walk_elapsed = step * 0.05
            self.state.walk_accel = 0.0
            navigation.update_walk(0.001, self.state)  # tiny dt to not move much
            accels.append(self.state.walk_accel)
        # At start, accel should be low
        self.assertLess(accels[0], 0.5)
        # At middle, accel should be 1.0
        mid = len(accels) // 2
        self.assertAlmostEqual(accels[mid], 1.0, delta=0.3)
        # At end, accel should drop
        self.assertLess(accels[-1], accels[mid])

    def test_walk_frame_progresses(self):
        """Walk frame should increase during walk."""
        from core import navigation
        self.state.state = config.STATE_WALK
        self.state.facing = True
        self.state.walk_duration = 2.0
        frames = set()
        for _ in range(20):
            navigation.update_walk(0.05, self.state)
            frames.add(self.state.walk_frame)
        # Should have cycled through multiple frames
        self.assertGreater(len(frames), 1)

    def test_go_home_sets_correct_facing(self):
        """GO_HOME navigation should face toward hut."""
        from core import navigation
        from cat.home import _hut_door_center
        hx, hy = _hut_door_center(self.state)
        self.state.state = config.STATE_GO_HOME
        # Cat at left of bed
        self.state.cat_x = 100.0
        self.state.cat_y = float(hy)
        self.state.facing = False  # initially facing wrong way
        navigation.update_go_home(0.05, self.state)
        self.assertTrue(self.state.facing, "Cat should face right toward bed")


class TestAPI(unittest.TestCase):
    """Test API action processing via standalone navigation.process_actions."""

    def setUp(self):
        self.state = CatState()

    def test_pet_resets_boredom(self):
        """Pet should reset boredom."""
        from core import navigation
        from core.api import action_queue
        self.state.boredom = 50.0
        action_queue.put("pet")
        navigation.process_actions(self.state)
        self.assertEqual(self.state.boredom, 0.0)

    def test_feed_reduces_hunger(self):
        """Feed should reduce hunger by 15."""
        from core import navigation
        from core.api import action_queue
        self.state.hunger = 50.0
        action_queue.put("feed")
        navigation.process_actions(self.state)
        self.assertEqual(self.state.hunger, 35.0)

    def test_wake_from_sleep(self):
        """Wake should transition SLEEP -> SIT and give energy."""
        from core import navigation
        from core.api import action_queue
        self.state.state = config.STATE_SLEEP
        self.state.energy = 30.0
        action_queue.put("wake")
        navigation.process_actions(self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)
        self.assertEqual(self.state.energy, 40.0)

    def test_consecutive_pets_trigger_purr(self):
        """5 consecutive pets should trigger purr and reset counter."""
        from core import navigation
        from core.api import action_queue
        for _ in range(5):
            action_queue.put("pet")
        navigation.process_actions(self.state)
        self.assertEqual(self.state.boredom, 0.0)
        self.assertEqual(self.state.consecutive_pets, 0)
        self.assertEqual(self.state.reaction_type, "purr")


class TestHutCoordinates(unittest.TestCase):
    """Test hut door center coordinate calculations."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080

    def test_hut_door_center_bottom_right(self):
        """Hut door center should be at bottom-right of screen."""
        from cat.home import _hut_door_center
        hx, hy = _hut_door_center(self.state)
        # Bottom-right minus padding
        expected_x = self.state.screen_width - config.HUT_PADDING_RIGHT - config.HUT_WIDTH // 2
        expected_y = self.state.screen_height - config.HUT_PADDING_BOTTOM - config.HUT_DOOR_FLOOR
        self.assertAlmostEqual(hx, expected_x, delta=1)
        self.assertAlmostEqual(hy, expected_y, delta=1)

    def test_hut_door_center_scales_with_screen(self):
        """Hut door position should scale with screen size."""
        from cat.home import _hut_door_center
        self.state.screen_width = 1366
        self.state.screen_height = 768
        hx, hy = _hut_door_center(self.state)
        expected_x = 1366 - config.HUT_PADDING_RIGHT - config.HUT_WIDTH // 2
        expected_y = 768 - config.HUT_PADDING_BOTTOM - config.HUT_DOOR_FLOOR
        self.assertAlmostEqual(hx, expected_x, delta=1)
        self.assertAlmostEqual(hy, expected_y, delta=1)


if __name__ == "__main__":
    unittest.main()
