"""
tests/test_habituation.py — Unit tests for behavior/habituation.py

Tests interaction counters, response levels, decay over time,
and full reset functionality.
"""

import os
import sys
import time
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from behavior.habituation import (
    HabituationModule,
    RESPONSE_FULL,
    RESPONSE_EAR_FLICK,
    RESPONSE_GLANCE,
    RESPONSE_IGNORE,
    RESPONSE_LABELS,
)


class TestHabituationCounter(unittest.TestCase):
    """Test basic counter mechanics."""

    def setUp(self):
        self.h = HabituationModule()

    def test_initial_counter_zero(self):
        self.assertEqual(self.h.get_counter("click"), 0)

    def test_record_increments_counter(self):
        self.h.record_interaction("click")
        self.assertEqual(self.h.get_counter("click"), 1)

    def test_multiple_records(self):
        for _ in range(5):
            self.h.record_interaction("click")
        self.assertEqual(self.h.get_counter("click"), 5)

    def test_separate_types_independent(self):
        self.h.record_interaction("click")
        self.h.record_interaction("hover")
        self.h.record_interaction("click")
        self.assertEqual(self.h.get_counter("click"), 2)
        self.assertEqual(self.h.get_counter("hover"), 1)
        self.assertEqual(self.h.get_counter("pet"), 0)

    def test_get_all_counters(self):
        self.h.record_interaction("click")
        self.h.record_interaction("hover")
        counters = self.h.get_all_counters()
        self.assertEqual(counters, {"click": 1, "hover": 1})


class TestHabituationResponseLevels(unittest.TestCase):
    """Test response level progression with increasing counters."""

    def setUp(self):
        self.h = HabituationModule()

    def test_zero_interactions_no_record(self):
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_FULL)

    def test_one_interaction_full_response(self):
        self.h.record_interaction("click")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_FULL)

    def test_two_interactions_ear_flick(self):
        self.h.record_interaction("click")
        self.h.record_interaction("click")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_EAR_FLICK)

    def test_three_interactions_ear_flick(self):
        for _ in range(3):
            self.h.record_interaction("click")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_EAR_FLICK)

    def test_four_interactions_glance(self):
        for _ in range(4):
            self.h.record_interaction("click")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_GLANCE)

    def test_five_rapid_clicks_ignore(self):
        """5 rapid clicks → ignore level."""
        for _ in range(5):
            self.h.record_interaction("click")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_IGNORE)

    def test_many_clicks_ignore(self):
        """More than 5 clicks → still ignore."""
        for _ in range(20):
            self.h.record_interaction("click")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_IGNORE)

    def test_separate_types_have_separate_levels(self):
        """One type maxed out should not affect another."""
        for _ in range(5):
            self.h.record_interaction("click")
        self.h.record_interaction("pet")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_IGNORE)
        self.assertEqual(self.h.get_response_level("pet"), RESPONSE_FULL)


class TestHabituationDecay(unittest.TestCase):
    """Test counter decay over time."""

    def setUp(self):
        self.h = HabituationModule()

    def _pretend_time_passed(self, seconds: float):
        """Simulate time passing by manipulating last_times directly."""
        for typ in list(self.h._last_times.keys()):
            self.h._last_times[typ] = time.monotonic() - seconds

    def test_decay_reduces_counter(self):
        self.h.record_interaction("click")
        self.h.record_interaction("click")
        self.h.record_interaction("click")  # counter = 3
        self._pretend_time_passed(480)  # 8 minutes
        self.h.update(30.0)  # dt doesn't matter much, elapsed since last does
        self.assertLess(self.h.get_counter("click"), 3,
                        "Counter should have decayed")

    def test_decay_single_count(self):
        """After decay_rate seconds, counter should drop by at least 1."""
        self.h.record_interaction("click")
        self.h.record_interaction("click")  # counter = 2
        self._pretend_time_passed(300)  # 5 minutes (> 240s decay rate)
        self.h.update(1.0)
        self.assertLessEqual(self.h.get_counter("click"), 1)

    def test_decay_multiple_counts(self):
        """After several decay periods, counter should drop more."""
        self.h.record_interaction("click")
        self.h.record_interaction("click")
        self.h.record_interaction("click")
        self.h.record_interaction("click")
        self.h.record_interaction("click")  # counter = 5
        self._pretend_time_passed(1200)  # 20 minutes = ~5 decay periods
        self.h.update(1.0)
        self.assertLessEqual(self.h.get_counter("click"), 2)

    def test_decay_to_zero(self):
        """After enough time, counter should reach zero."""
        self.h.record_interaction("click")
        self._pretend_time_passed(3600)  # 1 hour
        self.h.update(1.0)
        self.assertEqual(self.h.get_counter("click"), 0)

    def test_decay_cleans_up_zero_counters(self):
        """Zero counters should be removed from tracking."""
        self.h.record_interaction("click")
        self._pretend_time_passed(3600)
        self.h.update(1.0)
        self.assertEqual(len(self.h.get_all_counters()), 0)

    def test_decay_recovers_response_level(self):
        """After decay, the response level should improve."""
        for _ in range(5):
            self.h.record_interaction("click")
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_IGNORE)

        # Wait long enough
        self._pretend_time_passed(1200)  # 20 min
        self.h.update(1.0)

        # Should have recovered to some response
        self.assertLess(self.h.get_response_level("click"), RESPONSE_IGNORE)

    def test_recent_interaction_prevents_decay(self):
        """If interaction just happened, update should not decay."""
        self.h.record_interaction("click")
        self.h.update(1.0)  # dt=1s, but last interaction was just now
        self.assertEqual(self.h.get_counter("click"), 1)


class TestHabituationReset(unittest.TestCase):
    """Test reset functionality."""

    def setUp(self):
        self.h = HabituationModule()
        for _ in range(5):
            self.h.record_interaction("click")
        self.h.record_interaction("hover")

    def test_reset_single_type(self):
        self.h.reset("click")
        self.assertEqual(self.h.get_counter("click"), 0)
        self.assertEqual(self.h.get_counter("hover"), 1)

    def test_reset_all(self):
        self.h.reset()
        self.assertEqual(len(self.h.get_all_counters()), 0)
        self.assertEqual(self.h.get_response_level("click"), RESPONSE_FULL)

    def test_reset_nonexistent_type(self):
        self.h.reset("nonexistent")
        self.assertEqual(self.h.get_counter("click"), 5)


class TestHabituationConvenience(unittest.TestCase):
    """Test helper methods."""

    def setUp(self):
        self.h = HabituationModule()

    def test_repr_includes_active_counters(self):
        self.h.record_interaction("click")
        r = repr(self.h)
        self.assertIn("HabituationModule", r)
        self.assertIn("click", r)

    def test_empty_repr(self):
        r = repr(self.h)
        self.assertIn("0", r)  # 0 active types
        self.assertIn("{}", r)

    def test_response_labels_all_defined(self):
        for level in (RESPONSE_FULL, RESPONSE_EAR_FLICK,
                      RESPONSE_GLANCE, RESPONSE_IGNORE):
            self.assertIn(level, RESPONSE_LABELS)
            self.assertIsInstance(RESPONSE_LABELS[level], str)


if __name__ == "__main__":
    unittest.main()
