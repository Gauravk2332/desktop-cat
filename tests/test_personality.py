"""
tests/test_personality.py — Unit tests for behavior/personality.py

Tests trait get/set/modify with clamping, behavior mapping methods,
and personality persistence.
"""

import json
import os
import sys
import tempfile
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from behavior.personality import Personality, PERSONALITY_SCHEMA


class TestPersonalityInit(unittest.TestCase):
    """Test Personality initialization and defaults."""

    def test_default_traits_all_present(self):
        p = Personality(load_from_file=False)
        for name, info in PERSONALITY_SCHEMA.items():
            val = p.get_raw(name)
            self.assertEqual(val, info["default"],
                             f"{name} should start at {info['default']}, got {val}")

    def test_default_traits_normalized(self):
        p = Personality(load_from_file=False)
        for name, info in PERSONALITY_SCHEMA.items():
            val = p.get(name, normalized=True)
            expected = info["default"] / 10.0
            self.assertAlmostEqual(val, expected,
                                   msg=f"{name} normalized should be {expected}")

    def test_all_schema_keys_accepted(self):
        p = Personality(load_from_file=False)
        for name in PERSONALITY_SCHEMA:
            # Should not raise
            _ = p.get(name)
            _ = p.get(name, normalized=True)
            _ = p.get_raw(name)

    def test_unknown_trait_raises(self):
        p = Personality(load_from_file=False)
        with self.assertRaises(ValueError):
            p.modify("nonexistent", 1)
        with self.assertRaises(KeyError):
            p.get("nonexistent")


class TestPersonalityModify(unittest.TestCase):
    """Test trait modification with clamping."""

    def setUp(self):
        self.p = Personality(load_from_file=False)

    def test_modify_increases(self):
        self.p.modify("boldness", 3)
        self.assertEqual(self.p.get_raw("boldness"),
                         PERSONALITY_SCHEMA["boldness"]["default"] + 3)

    def test_modify_decreases(self):
        self.p.modify("boldness", -2)
        self.assertEqual(self.p.get_raw("boldness"),
                         PERSONALITY_SCHEMA["boldness"]["default"] - 2)

    def test_modify_clamps_above_10(self):
        self.p.modify("boldness", 20)
        self.assertEqual(self.p.get_raw("boldness"), 10)

    def test_modify_clamps_below_0(self):
        self.p.modify("boldness", -20)
        self.assertEqual(self.p.get_raw("boldness"), 0)

    def test_modify_all_traits(self):
        for name in PERSONALITY_SCHEMA:
            self.p.modify(name, 3)
            self.assertLessEqual(self.p.get_raw(name), 10)
            self.assertGreaterEqual(self.p.get_raw(name), 0)

    def test_modify_clamping_all_traits(self):
        for name in PERSONALITY_SCHEMA:
            self.p.modify(name, 100)
            self.assertEqual(self.p.get_raw(name), 10, f"{name} should clamp to 10")
            self.p.modify(name, -100)
            self.assertEqual(self.p.get_raw(name), 0, f"{name} should clamp to 0")


class TestPersonalityBehaviorMapping(unittest.TestCase):
    """Test behavior mapping methods return sane values from traits."""

    def setUp(self):
        self.p = Personality(load_from_file=False)

    def test_reaction_delay_bold_vs_shy(self):
        bold = Personality(load_from_file=False)
        bold.modify("boldness", 5)  # bold = 10
        shy = Personality(load_from_file=False)
        shy.modify("boldness", -5)  # bold = 0

        bold_delay = bold.get_reaction_delay()
        shy_delay = shy.get_reaction_delay()
        self.assertLess(bold_delay, shy_delay,
                        "Bold cat should have shorter reaction delay")

    def test_reaction_delay_in_range(self):
        delay = self.p.get_reaction_delay()
        self.assertGreaterEqual(delay, 0.5)
        self.assertLessEqual(delay, 2.5)

    def test_behavior_bias_returns_all_keys(self):
        bias = self.p.get_behavior_bias()
        expected_keys = {"walk", "sleep", "play", "greet",
                         "investigate", "flee", "follow_mouse"}
        self.assertSetEqual(set(bias.keys()), expected_keys)
        for k, v in bias.items():
            self.assertGreaterEqual(v, 0.0, f"{k} weight should be >= 0")

    def test_behavior_bias_all_positive(self):
        for name in PERSONALITY_SCHEMA:
            p = Personality(load_from_file=False)
            p.modify(name, 10)  # Max this trait
            bias = p.get_behavior_bias()
            for k, v in bias.items():
                self.assertGreaterEqual(v, 0.0, f"{k} weight negative with max {name}")

    def test_play_chance_range(self):
        for _ in range(100):
            chance = Personality(load_from_file=False).get_play_chance()
            self.assertGreaterEqual(chance, 0.0)
            self.assertLessEqual(chance, 1.0)

    def test_sleep_threshold_range(self):
        p = Personality(load_from_file=False)
        thresh = p.get_sleep_threshold()
        self.assertGreaterEqual(thresh, 30.0)
        self.assertLessEqual(thresh, 70.0)

    def test_wake_threshold_range(self):
        p = Personality(load_from_file=False)
        thresh = p.get_wake_threshold()
        self.assertGreaterEqual(thresh, 60.0)
        self.assertLessEqual(thresh, 90.0)

    def test_wake_higher_than_sleep(self):
        p = Personality(load_from_file=False)
        self.assertGreater(p.get_wake_threshold(), p.get_sleep_threshold())

    def test_lazy_affects_thresholds(self):
        lazy_max = Personality(load_from_file=False)
        lazy_max.modify("laziness", 7)  # max lazy
        lazy_min = Personality(load_from_file=False)
        lazy_min.modify("laziness", -3)  # min lazy
        self.assertGreater(lazy_max.get_sleep_threshold(), lazy_min.get_sleep_threshold(),
                           "Lazy cat should have higher sleep threshold")
        self.assertGreater(lazy_max.get_wake_threshold(), lazy_min.get_wake_threshold(),
                           "Lazy cat should have higher wake threshold")

    def test_approach_chance_range(self):
        for _ in range(100):
            chance = Personality(load_from_file=False).get_approach_chance()
            self.assertGreaterEqual(chance, 0.0)
            self.assertLessEqual(chance, 1.0)


class TestPersonalityPersistence(unittest.TestCase):
    """Test save/load of personality traits to disk."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_file = config.PERSONALITY_FILE
        config.PERSONALITY_FILE = os.path.join(self.tmpdir, "personality.json")

    def tearDown(self):
        config.PERSONALITY_FILE = self.orig_file

    def test_save_creates_file(self):
        p = Personality(load_from_file=True)
        p.modify("boldness", 2)
        self.assertTrue(os.path.exists(config.PERSONALITY_FILE),
                        "Personality file should exist after save")

    def test_save_and_load_roundtrip(self):
        p1 = Personality(load_from_file=True)
        p1.modify("boldness", 3)
        p1.modify("playfulness", -2)
        p1.modify("laziness", 5)

        # Load a new instance — should read the file we just saved
        p2 = Personality(load_from_file=True)
        self.assertEqual(p2.get_raw("boldness"), PERSONALITY_SCHEMA["boldness"]["default"] + 3)
        self.assertEqual(p2.get_raw("playfulness"), PERSONALITY_SCHEMA["playfulness"]["default"] - 2)
        self.assertEqual(p2.get_raw("laziness"), PERSONALITY_SCHEMA["laziness"]["default"] + 5)

    def test_persistence_multiple_cats(self):
        p1 = Personality(cat_index=0, load_from_file=True)
        p2 = Personality(cat_index=1, load_from_file=True)
        p1.modify("boldness", 4)  # cat 0: bold=9
        p2.modify("boldness", -3)  # cat 1: bold=2

        p1_reload = Personality(cat_index=0, load_from_file=True)
        p2_reload = Personality(cat_index=1, load_from_file=True)
        self.assertEqual(p1_reload.get_raw("boldness"), 9)
        self.assertEqual(p2_reload.get_raw("boldness"), 2)

    def test_missing_file_uses_defaults(self):
        if os.path.exists(config.PERSONALITY_FILE):
            os.remove(config.PERSONALITY_FILE)
        p = Personality(load_from_file=True)
        for name, info in PERSONALITY_SCHEMA.items():
            self.assertEqual(p.get_raw(name), info["default"])

    def test_corrupted_file_uses_defaults(self):
        with open(config.PERSONALITY_FILE, "w") as f:
            f.write("not valid json {{{")
        p = Personality(load_from_file=True)
        for name, info in PERSONALITY_SCHEMA.items():
            self.assertEqual(p.get_raw(name), info["default"])


class TestPersonalityRepr(unittest.TestCase):
    """Test __repr__ output."""

    def test_repr_includes_traits(self):
        p = Personality(load_from_file=False)
        r = repr(p)
        self.assertIn("Personality", r)
        for name in PERSONALITY_SCHEMA:
            self.assertIn(name, r)


if __name__ == "__main__":
    unittest.main()
