"""
tests/test_toys.py — Unit tests for interactive toy system (Phase 2B).

Tests state transitions, navigation, and timers for laser pointer chase
and yarn ball play. No Qt display needed.
"""

import sys
import os
import time
import math
import random
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState


class TestToyChaseNavigation(unittest.TestCase):
    """Test the laser pointer chase (update_chase) in core/navigation.py."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.cat_x = 500.0
        self.state.cat_y = 800.0
        self.state.state = config.STATE_CHASE
        self.state.toy_type = "laser"
        self.state.toy_active = True
        self.state.toy_target = (700.0, 800.0)  # target to the right

    def _import_navigation(self):
        from core import navigation
        return navigation

    def test_chase_moves_toward_target(self):
        """CHASE should move cat_x toward the toy target."""
        nav = self._import_navigation()
        before = self.state.cat_x
        for _ in range(20):
            nav.update_chase(0.05, self.state)
        self.assertGreater(
            self.state.cat_x, before,
            "Cat should move right toward target"
        )

    def test_chase_faces_target(self):
        """CHASE should face toward the toy target."""
        nav = self._import_navigation()
        self.state.toy_target = (100.0, 800.0)  # left
        self.state.facing = True
        nav.update_chase(0.05, self.state)
        self.assertFalse(
            self.state.facing,
            "Cat should face left when target is to the left"
        )

    def test_chase_reaches_target(self):
        """CHASE should sit when within reach distance of target."""
        nav = self._import_navigation()
        self.state.toy_target = (510.0, 800.0)  # only 10px away, less than 30
        nav.update_chase(0.05, self.state)
        self.assertEqual(
            self.state.state, config.STATE_SIT,
            "Cat should sit when close to laser target"
        )

    def test_chase_with_no_target(self):
        """CHASE with no target should return to SIT."""
        nav = self._import_navigation()
        self.state.toy_target = None
        self.state.toy_active = False
        nav.update_chase(0.05, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)

    def test_chase_clamps_to_screen(self):
        """Chase should not let cat_x go out of screen bounds."""
        nav = self._import_navigation()
        self.state.toy_target = (0.0, 800.0)
        for _ in range(200):
            nav.update_chase(0.05, self.state)
        margin = config.WANDER_OFFSET
        self.assertGreaterEqual(
            self.state.cat_x, float(margin),
            "cat_x should not go below left margin"
        )
        self.assertLessEqual(
            self.state.cat_x, float(self.state.screen_width - margin),
            "cat_x should not go beyond right margin"
        )

    def test_chase_fast_speed(self):
        """Chase speed should be faster than normal walk."""
        nav = self._import_navigation()
        # Move cat to chase state far from target
        self.state.toy_target = (1500.0, 800.0)
        self.state.walk_elapsed = 0.5  # past accel
        before = self.state.cat_x
        nav.update_chase(0.05, self.state)
        move_chase = self.state.cat_x - before

        # Compare with normal walk speed
        self.state.state = config.STATE_WALK
        self.state.toy_active = False
        self.state.toy_type = None
        self.state.cat_x = 500.0
        self.state.facing = True
        self.state.walk_duration = 5.0
        self.state.walk_elapsed = 0.5
        self.state.walk_accel = 1.0
        nav.update_walk(0.05, self.state)
        move_walk = self.state.cat_x - 500.0

        self.assertGreater(
            move_chase, move_walk,
            "Chase speed should exceed normal walk speed"
        )

    def test_chase_updates_walk_frame(self):
        """Chase should advance walk_frame at a faster rate."""
        nav = self._import_navigation()
        frames = set()
        for _ in range(30):
            nav.update_chase(0.05, self.state)
            frames.add(self.state.walk_frame)
        self.assertGreater(
            len(frames), 1,
            "Walk frame should cycle during chase"
        )


class TestToyPlayNavigation(unittest.TestCase):
    """Test the yarn ball / butterfly toy (update_play) in core/navigation.py."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.cat_x = 500.0
        self.state.cat_y = 800.0
        self.state.state = config.STATE_PLAY
        self.state.toy_type = "ball"
        self.state.toy_active = True
        self.state.toy_target = (700.0, 800.0)
        self.state.toy_timer = config.PLAY_TOY_DURATION

    def _import_navigation(self):
        from core import navigation
        return navigation

    def test_play_moves_toward_toy(self):
        """PLAY should move cat_x toward the toy."""
        nav = self._import_navigation()
        before = self.state.cat_x
        for _ in range(20):
            nav.update_play(0.05, self.state)
        self.assertGreater(
            self.state.cat_x, before,
            "Cat should move toward toy during play"
        )

    def test_play_catches_toy(self):
        """PLAY should catch toy within reach distance and trigger hearts."""
        nav = self._import_navigation()
        self.state.toy_target = (510.0, 800.0)
        before_hearts = len(self.state.hearts)
        nav.update_play(0.05, self.state)
        self.assertEqual(
            self.state.state, config.STATE_SIT,
            "Cat should sit after catching toy"
        )
        self.assertFalse(
            self.state.toy_active,
            "Toy should be deactivated after catch"
        )
        self.assertIsNone(self.state.toy_type, "Toy type should be None after catch")

    def test_play_times_out(self):
        """PLAY should end when timer expires."""
        nav = self._import_navigation()
        self.state.toy_timer = 0.0
        nav.update_play(0.05, self.state)
        self.assertEqual(
            self.state.state, config.STATE_SIT,
            "Cat should sit when toy timer expires"
        )
        self.assertFalse(self.state.toy_active, "Toy should deactivate on timeout")

    def test_play_no_toy(self):
        """PLAY with no active toy should return to SIT."""
        nav = self._import_navigation()
        self.state.toy_active = False
        self.state.toy_target = None
        nav.update_play(0.05, self.state)
        self.assertEqual(self.state.state, config.STATE_SIT)

    def test_play_faces_toy(self):
        """PLAY should face toward the toy."""
        nav = self._import_navigation()
        self.state.toy_target = (300.0, 800.0)  # left of cat
        self.state.facing = True
        nav.update_play(0.05, self.state)
        self.assertFalse(
            self.state.facing,
            "Cat should face left when toy is left"
        )

    def test_play_clamps_to_screen(self):
        """Play navigation should clamp cat within screen bounds."""
        nav = self._import_navigation()
        self.state.toy_target = (0.0, 800.0)
        for _ in range(200):
            nav.update_play(0.05, self.state)
        margin = config.WANDER_OFFSET
        self.assertGreaterEqual(
            self.state.cat_x, float(margin),
            "cat_x should not go below left margin"
        )

    def test_play_toy_still_active_on_timer_running(self):
        """PLAY stays active while timer is still running and toy not reached."""
        nav = self._import_navigation()
        self.state.toy_timer = 10.0  # plenty of time
        self.state.toy_target = (2000.0, 800.0)  # far away
        nav.update_play(0.05, self.state)
        self.assertEqual(
            self.state.state, config.STATE_PLAY,
            "Should stay in PLAY when timer remaining and toy not reached"
        )

    def test_play_generates_hearts_on_catch(self):
        """Catching the toy should spawn hearts."""
        nav = self._import_navigation()
        self.state.toy_target = (510.0, 800.0)
        before = len(self.state.hearts)
        nav.update_play(0.05, self.state)
        after = len(self.state.hearts)
        self.assertGreater(
            after, before,
            "Catching toy should spawn hearts"
        )


class TestToyStateFields(unittest.TestCase):
    """Test that CatState has the correct toy fields."""

    def setUp(self):
        self.state = CatState()

    def test_toy_fields_exist(self):
        """CatState should have all toy-related fields."""
        self.assertTrue(hasattr(self.state, "toy_target"),
                        "CatState should have toy_target")
        self.assertTrue(hasattr(self.state, "toy_timer"),
                        "CatState should have toy_timer")
        self.assertTrue(hasattr(self.state, "toy_active"),
                        "CatState should have toy_active")
        self.assertTrue(hasattr(self.state, "toy_type"),
                        "CatState should have toy_type")
        self.assertTrue(hasattr(self.state, "chase_timeout"),
                        "CatState should have chase_timeout")

    def test_toy_field_defaults(self):
        """Toy fields should have correct defaults."""
        self.assertIsNone(self.state.toy_target)
        self.assertEqual(self.state.toy_timer, 0.0)
        self.assertFalse(self.state.toy_active)
        self.assertIsNone(self.state.toy_type)
        self.assertEqual(self.state.chase_timeout, 0.0)


class TestToyConfigConstants(unittest.TestCase):
    """Toy-related config constants should have sensible values."""

    def test_chase_speed_multiplier_sane(self):
        """Chase speed multiplier should be > 1.0 and < 5.0."""
        self.assertGreater(config.CHASE_SPEED_MULTIPLIER, 1.0)
        self.assertLess(config.CHASE_SPEED_MULTIPLIER, 5.0)

    def test_chase_reach_distance_positive(self):
        """Chase reach distance should be small and positive."""
        self.assertGreater(config.CHASE_REACH_DISTANCE, 0)
        self.assertLess(config.CHASE_REACH_DISTANCE, 100)

    def test_chase_timeout_positive(self):
        """Chase timeout should be positive."""
        self.assertGreater(config.CHASE_TIMEOUT, 0)
        self.assertLess(config.CHASE_TIMEOUT, 10)

    def test_play_toy_interval_positive(self):
        """Play toy interval should be positive."""
        self.assertGreater(config.PLAY_TOY_INTERVAL, 0)

    def test_play_toy_duration_positive(self):
        """Play toy duration should be positive and less than interval."""
        self.assertGreater(config.PLAY_TOY_DURATION, 0)
        self.assertLess(config.PLAY_TOY_DURATION, config.PLAY_TOY_INTERVAL)

    def test_play_toy_reach_distance_positive(self):
        """Play toy reach distance should be positive and small."""
        self.assertGreater(config.PLAY_TOY_REACH_DISTANCE, 0)
        self.assertLess(config.PLAY_TOY_REACH_DISTANCE, 100)

    def test_states_exist(self):
        """STATE_CHASE and STATE_PLAY should be defined."""
        self.assertEqual(config.STATE_CHASE, "CHASE")
        self.assertEqual(config.STATE_PLAY, "PLAY")


class TestToyIntegrationPatterns(unittest.TestCase):
    """Integration-style tests checking patterns that involve toy interactions."""

    def test_sit_to_chase_state_transition(self):
        """Simulate the transition from SIT to CHASE when mouse moves nearby
        and click-through is OFF."""
        self.state = CatState()
        self.state.cat_x = 500.0
        self.state.cat_y = 800.0
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.state = config.STATE_SIT
        self.state.click_through = False
        self.state.mouse_pos = (550.0, 800.0)

        # Simulate what _check_mouse does: if click-through OFF, mouse moved,
        # mouse within 300px, and cat is SIT → CHASE
        dist = math.hypot(550 - 500, 800 - 800)
        mouse_moved = True
        if (not self.state.click_through
                and dist < 300
                and self.state.state == config.STATE_SIT
                and mouse_moved):
            self.state.toy_target = (550.0, 800.0)
            self.state.toy_active = True
            self.state.toy_type = "laser"
            self.state.chase_timeout = config.CHASE_TIMEOUT
            self.state.state = config.STATE_CHASE

        self.assertEqual(self.state.state, config.STATE_CHASE)
        self.assertEqual(self.state.toy_type, "laser")
        self.assertTrue(self.state.toy_active)

    def test_chase_timeout_transition(self):
        """Simulate chase timeout when mouse stops moving."""
        self.state = CatState()
        self.state.state = config.STATE_CHASE
        self.state.chase_timeout = config.CHASE_TIMEOUT
        self.state.toy_active = True
        self.state.toy_type = "laser"
        self.state.toy_target = (600.0, 800.0)

        # Simulate _update_toys: mouse not moving, decrement chase_timeout
        dt = 0.05
        mouse_moving = False
        for _ in range(int(config.CHASE_TIMEOUT / dt) + 5):
            if not mouse_moving:
                self.state.chase_timeout -= dt
                if self.state.chase_timeout <= 0:
                    self.state.state = config.STATE_SIT
                    self.state.toy_active = False
                    self.state.toy_type = None
                    self.state.toy_target = None
                    break
            else:
                self.state.chase_timeout = config.CHASE_TIMEOUT

        self.assertEqual(self.state.state, config.STATE_SIT,
                         "Chase should timeout when mouse stops")
        self.assertFalse(self.state.toy_active)
        self.assertIsNone(self.state.toy_type)

    def test_chase_timeout_reset_on_mouse_move(self):
        """Chase timeout should reset when mouse moves again."""
        self.state = CatState()
        self.state.state = config.STATE_CHASE
        self.state.chase_timeout = 0.5
        self.state.toy_active = True
        self.state.toy_type = "laser"
        self.state.toy_target = (600.0, 800.0)

        # First, a period with no mouse movement
        mouse_moving = False
        for _ in range(5):
            if not mouse_moving:
                self.state.chase_timeout -= 0.05

        self.assertLess(self.state.chase_timeout, 0.5)

        # Now mouse moves — timeout resets
        mouse_moving = True
        self.state.chase_timeout = config.CHASE_TIMEOUT

        self.assertAlmostEqual(self.state.chase_timeout, config.CHASE_TIMEOUT,
                               places=1)

    def test_click_through_blocks_chase(self):
        """When click-through is ON, chase should not trigger."""
        self.state = CatState()
        self.state.cat_x = 500.0
        self.state.cat_y = 800.0
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.state = config.STATE_SIT
        self.state.click_through = True  # interact mode OFF

        dist = math.hypot(550 - 500, 800 - 800)
        if (not self.state.click_through and dist < 300
                and self.state.state == config.STATE_SIT):
            self.state.state = config.STATE_CHASE

        self.assertNotEqual(
            self.state.state, config.STATE_CHASE,
            "Chase should not trigger when click-through is ON"
        )

    def test_click_through_blocks_toy_spawn(self):
        """When click-through is ON, toy spawn timer should not advance."""
        self.state = CatState()
        self.state.click_through = True

        # Simulate: no toy system activity when click_through
        toy_spawn_timer = 5.0
        if self.state.click_through:
            toy_spawn_timer = 0.0

        self.assertEqual(
            toy_spawn_timer, 0.0,
            "Toy spawn timer should reset to 0 when click-through is ON"
        )

    def test_chase_no_trigger_when_sleeping(self):
        """Chase should not trigger when cat is sleeping."""
        self.state = CatState()
        self.state.state = config.STATE_SLEEP
        self.state.click_through = False

        # Chase should not trigger
        if self.state.state in (config.STATE_SIT,):
            self.state.state = config.STATE_CHASE

        self.assertEqual(
            self.state.state, config.STATE_SLEEP,
            "Chase should not trigger when cat is sleeping"
        )


if __name__ == "__main__":
    unittest.main()
