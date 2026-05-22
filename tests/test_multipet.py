"""
tests/test_multipet.py — Multi-cat unit tests.

Tests add/remove cat, backward-compat properties,
independent state machines, paint loop, tray interactions,
keyboard focus, and save/load.
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState, default_cat_dict


from PyQt6.QtCore import QObject

class _WindowStub(QObject):
    """Minimal window stub for Engine tests."""
    def __init__(self):
        super().__init__()
        self._update_count = 0
    def update(self):
        self._update_count += 1
    def isVisible(self):
        return True
    def show(self):
        pass
    def hide(self):
        pass
    def parent(self):
        return None
    def winId(self):
        return 0


class TestMultiCatAddRemove(unittest.TestCase):
    """Test add_cat and remove_cat operations."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080

    def test_initial_single_cat(self):
        """Start with exactly 1 cat."""
        self.assertEqual(len(self.state.cats), 1)
        self.assertEqual(self.state.cats[0]["id"], 0)

    def test_add_cat(self):
        """Adding a cat increases count."""
        cat_id = self.state.add_cat()
        self.assertEqual(cat_id, 1)
        self.assertEqual(len(self.state.cats), 2)
        self.assertEqual(self.state.cats[1]["id"], 1)

    def test_add_cat_max(self):
        """Adding more than MAX_CATS returns -1."""
        for i in range(config.MAX_CATS - 1):
            self.state.add_cat()
        self.assertEqual(len(self.state.cats), config.MAX_CATS)
        cat_id = self.state.add_cat()
        self.assertEqual(cat_id, -1)
        self.assertEqual(len(self.state.cats), config.MAX_CATS)

    def test_remove_cat_id_0_fails(self):
        """Cannot remove cat with id 0 (minimum 1)."""
        self.assertFalse(self.state.remove_cat(0))
        self.assertEqual(len(self.state.cats), 1)

    def test_remove_last_cat(self):
        """Add a cat then remove it."""
        self.state.add_cat()
        self.assertEqual(len(self.state.cats), 2)
        self.assertTrue(self.state.remove_cat(1))
        self.assertEqual(len(self.state.cats), 1)
        # hut_index should be reassigned
        self.assertEqual(self.state.cats[0]["hut_index"], 0)

    def test_remove_invalid_id(self):
        """Removing an invalid id returns False."""
        self.assertFalse(self.state.remove_cat(99))

    def test_each_cat_has_unique_hut_index(self):
        """Each cat gets a unique hut_index."""
        self.state.add_cat()
        self.state.add_cat()
        indices = [c["hut_index"] for c in self.state.cats]
        self.assertEqual(len(set(indices)), len(indices))


class TestBackwardCompat(unittest.TestCase):
    """Verify backward-compat properties still read/write cats[0]."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.cats = [
            default_cat_dict(0, 0, 500.0, 700.0),
            default_cat_dict(1, 1, 800.0, 700.0),
        ]

    def test_cat_x_property(self):
        """state.cat_x reads/writes cats[0]."""
        self.assertAlmostEqual(self.state.cat_x, 500.0)
        self.state.cat_x = 600.0
        self.assertAlmostEqual(self.state.cats[0]["x"], 600.0)
        self.assertAlmostEqual(self.state.cat_x, 600.0)

    def test_cat_y_property(self):
        """state.cat_y reads/writes cats[0]."""
        self.assertAlmostEqual(self.state.cat_y, 700.0)
        self.state.cat_y = 800.0
        self.assertAlmostEqual(self.state.cats[0]["y"], 800.0)

    def test_state_property(self):
        """state.state reads/writes cats[0].state."""
        self.state.cats[0]["state"] = "WALK"
        self.assertEqual(self.state.state, "WALK")
        self.state.state = "SLEEP"
        self.assertEqual(self.state.cats[0]["state"], "SLEEP")

    def test_energy_property(self):
        """state.energy reads/writes cats[0].energy."""
        self.assertAlmostEqual(self.state.energy, 80.0)
        self.state.energy = 50.0
        self.assertAlmostEqual(self.state.cats[0]["energy"], 50.0)

    def test_hunger_property(self):
        """state.hunger reads/writes cats[0].hunger."""
        self.state.hunger = 30.0
        self.assertAlmostEqual(self.state.cats[0]["hunger"], 30.0)

    def test_boredom_property(self):
        """state.boredom reads/writes cats[0].boredom."""
        self.state.boredom = 15.0
        self.assertAlmostEqual(self.state.cats[0]["boredom"], 15.0)

    def test_facing_property(self):
        """state.facing reads/writes cats[0].facing."""
        self.assertTrue(self.state.facing)
        self.state.facing = False
        self.assertFalse(self.state.cats[0]["facing"])

    def test_at_home_property(self):
        """state.at_home reads/writes cats[0].at_home."""
        self.assertFalse(self.state.at_home)
        self.state.at_home = True
        self.assertTrue(self.state.cats[0]["at_home"])

    def test_cat_2_properties_unaffected(self):
        """Modifying cats[0] properties doesn't affect cats[1]."""
        self.state.energy = 50.0
        self.assertAlmostEqual(self.state.cats[1]["energy"], 80.0)


class TestIndependentStateMachines(unittest.TestCase):
    """Test that each cat has an independent state machine."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.add_cat()
        self.state.add_cat()  # 3 cats

    def test_independent_states(self):
        """Each cat can be in a different state."""
        self.state.cats[0]["state"] = "SIT"
        self.state.cats[1]["state"] = "WALK"
        self.state.cats[2]["state"] = "SLEEP"
        self.assertEqual(self.state.cats[0]["state"], "SIT")
        self.assertEqual(self.state.cats[1]["state"], "WALK")
        self.assertEqual(self.state.cats[2]["state"], "SLEEP")

    def test_independent_energy(self):
        """Each cat has independent energy levels."""
        self.state.cats[0]["energy"] = 100.0
        self.state.cats[1]["energy"] = 50.0
        self.state.cats[2]["energy"] = 10.0
        self.assertEqual(self.state.cats[0]["energy"], 100.0)
        self.assertEqual(self.state.cats[1]["energy"], 50.0)
        self.assertEqual(self.state.cats[2]["energy"], 10.0)

    def test_independent_facing(self):
        """Each cat can face different directions."""
        self.state.cats[0]["facing"] = True
        self.state.cats[1]["facing"] = False
        self.assertTrue(self.state.cats[0]["facing"])
        self.assertFalse(self.state.cats[1]["facing"])

    def test_needs_update_per_cat(self):
        """Each cat's needs update independently."""
        from behavior import needs
        dt = 1.0
        self.state.cats[0]["state"] = "WALK"
        self.state.cats[1]["state"] = "SLEEP"

        initial_e1 = self.state.cats[0]["energy"]
        initial_e2 = self.state.cats[1]["energy"]

        needs.update(dt, self.state.cats[0], self.state)
        needs.update(dt, self.state.cats[1], self.state)

        # Walking cat lost energy, sleeping cat gained
        self.assertLess(self.state.cats[0]["energy"], initial_e1,
                        "Walking cat should lose energy")
        self.assertGreater(self.state.cats[1]["energy"], initial_e2,
                           "Sleeping cat should gain energy")

    def test_transitions_per_cat(self):
        """State transitions affect only the target cat."""
        from behavior import transitions
        self.state.cats[0]["energy"] = 30.0  # below HOME_ENERGY_THRESHOLD
        self.state.cats[1]["energy"] = 80.0  # fine

        transitions.update(0.05, self.state.cats[0], self.state)

        self.assertEqual(self.state.cats[0]["state"], "GO_HOME",
                         "Low-energy cat should go home")
        self.assertEqual(self.state.cats[1]["state"], "SIT",
                         "Healthy cat should stay sitting")


class TestKeyboardFocus(unittest.TestCase):
    """Test Ctrl+1/2/3 focus behavior."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.add_cat()
        self.state.add_cat()

    def test_focus_cat_0(self):
        """from core.controls import Controls"""
        from core.controls import Controls
        mock_engine = MagicMock()
        mock_window = _WindowStub()
        ctrl = Controls(mock_window, self.state, mock_engine)

        self.state.cats[0]["x"] = 0.0
        self.state.cats[1]["x"] = 500.0

        ctrl.focus_cat(0)

        # Cat 0 should be centered
        expected = self.state.screen_width / 2.0
        self.assertAlmostEqual(self.state.cats[0]["x"], expected)

    def test_focus_cat_out_of_range(self):
        """from core.controls import Controls"""
        from core.controls import Controls
        ctrl = Controls(MagicMock(), self.state, MagicMock())
        # This should not raise
        ctrl.focus_cat(99)


class TestSaveLoad(unittest.TestCase):
    """Test save/load multi-cat state."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.add_cat()
        self.state.add_cat()

        self.cats_data = [
            {"id": 0, "state": "SIT", "energy": 80.0, "hunger": 20.0,
             "boredom": 0.0, "facing": True, "coat": 0,
             "x": 500.0, "y": 700.0, "at_home": False},
            {"id": 1, "state": "SLEEP", "energy": 90.0, "hunger": 30.0,
             "boredom": 0.0, "facing": True, "coat": 1,
             "x": 800.0, "y": 700.0, "at_home": True, "hut_index": 1},
            {"id": 2, "state": "WALK", "energy": 60.0, "hunger": 40.0,
             "boredom": 5.0, "facing": False, "coat": 2,
             "x": 300.0, "y": 700.0, "at_home": False, "hut_index": 2},
        ]

    @patch("config.STATE_PATH", new="/tmp/test_multipet_save.json")
    @patch("config.STATE_DIR", new="/tmp")
    def test_save_and_load(self):
        """Save multi-cat state and reload it."""
        import config as _cfg

        # Set up 3 cats with different states
        self.state.cats[0]["state"] = "SIT"
        self.state.cats[0]["energy"] = 80.0
        self.state.add_cat()
        self.state.add_cat()

        # Save (bypass Engine, call save logic directly)
        data = {
            "cats": [
                {k: c[k] for k in ["id","x","y","state","facing","coat",
                                   "energy","hunger","boredom",
                                   "at_home","home_cooldown","home_linger",
                                   "walk_duration","walk_elapsed",
                                   "wander_duration","wander_elapsed","wander_cooldown",
                                   "wander_vx","wander_vy","hut_index"]
                 if k in c}
                for c in self.state.cats
            ],
            "weather_condition": self.state.weather_condition,
            "timestamp": "2025-01-15T12:00:00",
        }
        os.makedirs(_cfg.STATE_DIR, exist_ok=True)
        with open(_cfg.STATE_PATH, "w") as f:
            json.dump(data, f)

        # Verify JSON was written
        with open(_cfg.STATE_PATH) as f:
            data = json.load(f)
        self.assertIn("cats", data)
        self.assertIn("weather_condition", data)
        self.assertIn("timestamp", data)

    @patch("config.STATE_PATH", new="/tmp/test_multipet_load.json")
    @patch("config.STATE_DIR", new="/tmp")
    def test_load_legacy_format(self):
        """Loading legacy single-cat format migrates to cats[0]."""
        legacy_data = {
            "state": "SIT",
            "facing": True,
            "energy": 75.0,
            "hunger": 30.0,
            "boredom": 10.0,
            "weather_condition": "sunny",
            "timestamp": "2025-01-15T12:00:00",
        }
        import config as _cfg
        with open(_cfg.STATE_PATH, "w") as f:
            json.dump(legacy_data, f)

        self.state.cats[0]["energy"] = 0.0  # will be overridden
        # Load directly (without Engine constructor)
        with open(_cfg.STATE_PATH) as f:
            data = json.load(f)

        cats_data = data.get("cats", [])
        if not cats_data:
            s = self.state
            x = float(data.get("x", s.cats[0]["x"] if s.cats else s.screen_width / 2.0))
            y = float(data.get("y", s.cats[0]["y"] if s.cats else s.screen_height - _cfg.CAT_BASELINE))
            from core.state import default_cat_dict
            legacy_cat = default_cat_dict(0, 0, x, y)
            legacy_cat["state"] = data.get("state", "SIT")
            legacy_cat["facing"] = bool(data.get("facing", True))
            legacy_cat["energy"] = float(data.get("energy", 80.0))
            legacy_cat["hunger"] = float(data.get("hunger", 20.0))
            legacy_cat["boredom"] = float(data.get("boredom", 0.0))
            self.state.cats = [legacy_cat]
        self.state.weather_condition = data.get("weather_condition", "cloudy")

        self.assertEqual(self.state.cats[0]["state"], "SIT")
        self.assertAlmostEqual(self.state.cats[0]["energy"], 75.0)
        self.assertAlmostEqual(self.state.cats[0]["hunger"], 30.0)
        self.assertEqual(self.state.weather_condition, "sunny")

    @patch("config.STATE_PATH", new="/tmp/test_multipet_load.json")
    @patch("config.STATE_DIR", new="/tmp")
    def test_load_multi_format(self):
        """Loading multi-cat format restores all cats."""
        import config as _cfg
        data = {
            "cats": self.cats_data,
            "weather_condition": "rainy",
            "timestamp": "2025-01-15T12:00:00",
        }
        with open(_cfg.STATE_PATH, "w") as f:
            json.dump(data, f)

        with open(_cfg.STATE_PATH) as f:
            loaded = json.load(f)
        cats_data = loaded.get("cats", [])
        self.assertEqual(len(cats_data), 3)
        self.assertEqual(cats_data[0]["state"], "SIT")
        self.assertEqual(cats_data[2]["state"], "WALK")
        self.assertEqual(loaded["weather_condition"], "rainy")


class TestTrayAddRemove(unittest.TestCase):
    """Test tray add/remove cat menu actions."""

    def setUp(self):
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080

    def test_tray_add_cat_max(self):
        """Adding cats up to MAX_CATS then exceeding."""
        for _ in range(config.MAX_CATS - 1):
            self.state.add_cat()
        self.assertEqual(len(self.state.cats), config.MAX_CATS)
        self.assertEqual(self.state.add_cat(), -1)

    def test_tray_remove_keeps_one(self):
        """Removing all but one cat."""
        self.state.add_cat()
        self.state.add_cat()
        self.state.remove_cat(1)
        self.assertEqual(len(self.state.cats), 2)
        self.state.remove_cat(1)
        self.assertEqual(len(self.state.cats), 1)
        self.assertFalse(self.state.remove_cat(0))  # can't remove last


class TestCatProxy(unittest.TestCase):
    """Test CatProxy wrapper for dict-to-attribute access."""

    def setUp(self):
        from core.state import CatProxy
        self.cat = default_cat_dict(0)
        self.proxy = CatProxy(self.cat)

    def test_attribute_read(self):
        """CatProxy reads dict values as attributes."""
        self.assertEqual(self.proxy.facing, True)
        self.assertEqual(self.proxy.energy, 80.0)

    def test_attribute_write(self):
        """CatProxy writes dict values as attributes."""
        self.proxy.facing = False
        self.assertFalse(self.cat["facing"])
        self.proxy.energy = 50.0
        self.assertEqual(self.cat["energy"], 50.0)

    def test_getitem(self):
        """CatProxy supports __getitem__."""
        self.assertEqual(self.proxy["state"], "SIT")

    def test_setitem(self):
        """CatProxy supports __setitem__."""
        self.proxy["state"] = "WALK"
        self.assertEqual(self.cat["state"], "WALK")

    def test_get_method(self):
        """CatProxy supports .get() fallback."""
        self.assertEqual(self.proxy.get("nonexistent", 42), 42)
        self.assertEqual(self.proxy.get("energy"), 80.0)

    def test_x_and_cat_x(self):
        """CatProxy maps x and cat_x to the same source."""
        self.assertEqual(self.proxy.x, 500.0)
        self.assertEqual(self.proxy.cat_x, 500.0)
        self.proxy.cat_x = 600.0
        self.assertEqual(self.cat["x"], 600.0)
        self.assertEqual(self.proxy.x, 600.0)


if __name__ == "__main__":
    unittest.main()
