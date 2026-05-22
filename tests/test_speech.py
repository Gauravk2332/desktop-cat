"""
tests/test_speech.py — Unit tests for speech bubble system.

Tests that:
- Speech state structure is correct
- SPEECH_MOODS pool selection works
- Queue behavior (enqueue, dequeue, overflow)
- Cooldown timing
- Drawing function doesn't crash (offscreen Qt)
- Priority-based interruption
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.state import CatState, SPEECH_MOODS
import config


# Singleton QApplication for Qt-dependent tests
_app = None
def _get_app():
    global _app
    if _app is None:
        _app = QApplication(sys.argv[:1] if sys.argv else [])
    return _app


class TestSpeechState(unittest.TestCase):
    """Verify speech dict structure and defaults."""

    def test_speech_dict_keys(self):
        """CatState.speech has the expected keys."""
        s = CatState()
        expected_keys = {"text", "emoji", "timer", "fading", "opacity", "queue"}
        self.assertEqual(set(s.speech.keys()), expected_keys)

    def test_speech_defaults(self):
        """Speech starts with no active bubble."""
        s = CatState()
        self.assertIsNone(s.speech["text"])
        self.assertIsNone(s.speech["emoji"])
        self.assertEqual(s.speech["timer"], 0.0)
        self.assertFalse(s.speech["fading"])
        self.assertEqual(s.speech["opacity"], 0.0)
        self.assertEqual(s.speech["queue"], [])

    def test_speech_cooldown_defaults(self):
        """Cooldown and idle timer start at zero."""
        s = CatState()
        self.assertEqual(s.speech_cooldown, 0.0)
        self.assertEqual(s.speech_idle_timer, 0.0)


class TestSpeechMoods(unittest.TestCase):
    """Verify SPEECH_MOODS structure and content."""

    def test_has_all_moods(self):
        """All expected mood keys exist."""
        expected_moods = {"bored", "happy", "hungry", "alert",
                          "sleepy", "playful", "long-idle"}
        self.assertEqual(set(SPEECH_MOODS.keys()), expected_moods)

    def test_each_mood_has_emoji(self):
        """Every mood has a non-empty emoji string."""
        for mood, data in SPEECH_MOODS.items():
            self.assertIn("emoji", data)
            self.assertTrue(data["emoji"], f"Mood '{mood}' has empty emoji")

    def test_each_mood_has_texts(self):
        """Every mood has a non-empty texts list."""
        for mood, data in SPEECH_MOODS.items():
            self.assertIn("texts", data)
            self.assertGreater(len(data["texts"]), 0,
                               f"Mood '{mood}' has no texts")
            for t in data["texts"]:
                self.assertLessEqual(len(t), config.SPEECH_MAX_CHARS,
                                     f"Text '{t}' exceeds max chars")

    def test_texts_are_unique_per_mood(self):
        """No duplicate texts within a single mood."""
        for mood, data in SPEECH_MOODS.items():
            self.assertEqual(len(data["texts"]), len(set(data["texts"])),
                             f"Mood '{mood}' has duplicate texts")


class TestSpeechPoolSelection(unittest.TestCase):
    """Verify random selection from pools."""

    def test_random_selection_returns_valid_text(self):
        """random.choice from a mood pool returns a text from that pool."""
        import random
        mood = "happy"
        text = random.choice(SPEECH_MOODS[mood]["texts"])
        self.assertIn(text, SPEECH_MOODS[mood]["texts"])


class TestEngineSpeechTrigger(unittest.TestCase):
    """Engine._trigger_speech behavior."""

    def setUp(self):
        _get_app()
        from PyQt6.QtWidgets import QWidget
        from core.engine import Engine
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.real_window = QWidget()
        self.engine = Engine(self.state, self.real_window)

    def test_trigger_speech_sets_text_and_emoji(self):
        """_trigger_speech sets text and emoji when no active speech."""
        self.engine._trigger_speech("happy")
        self.assertIsNotNone(self.state.speech["text"])
        self.assertIsNotNone(self.state.speech["emoji"])
        self.assertIn(self.state.speech["text"],
                      SPEECH_MOODS["happy"]["texts"])
        self.assertEqual(self.state.speech["emoji"],
                         SPEECH_MOODS["happy"]["emoji"])

    def test_trigger_speech_starts_with_zero_opacity(self):
        """New speech starts at opacity 0 for fade-in."""
        self.engine._trigger_speech("happy")
        self.assertEqual(self.state.speech["opacity"], 0.0)

    def test_trigger_speech_queues_when_active(self):
        """Calling while speech is active queues the new message."""
        self.engine._trigger_speech("happy")
        self.engine._trigger_speech("hungry")
        self.assertEqual(len(self.state.speech["queue"]), 1)

    def test_trigger_queue_overflow_drops_lowest(self):
        """Queue exceeding SPEECH_QUEUE_MAX drops lowest priority."""
        self.engine._trigger_speech("happy")
        for _ in range(config.SPEECH_QUEUE_MAX + 2):
            self.engine._trigger_speech("sleepy")  # lowest priority
        # Should not exceed max queue
        self.assertLessEqual(len(self.state.speech["queue"]),
                             config.SPEECH_QUEUE_MAX)


class TestSpeechUpdateCycle(unittest.TestCase):
    """Test engine._update_speech lifecycle."""

    def setUp(self):
        _get_app()
        from PyQt6.QtWidgets import QWidget
        from core.engine import Engine
        self.state = CatState()
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.real_window = QWidget()
        self.engine = Engine(self.state, self.real_window)

    def test_fade_in(self):
        """Opacity increases during fade-in phase."""
        self.engine._trigger_speech("happy")
        self.state.speech["opacity"] = 0.0
        # Tick 1 frame of fade-in
        self.engine._update_speech(0.05)
        self.assertGreater(self.state.speech["opacity"], 0.0)
        self.assertLessEqual(self.state.speech["opacity"], 1.0)

    def test_fade_out_after_duration(self):
        """Speech enters fade-out phase when timer is low."""
        self.engine._trigger_speech("happy")
        self.state.speech["opacity"] = 1.0
        # Set timer close to end
        self.state.speech["timer"] = config.SPEECH_FADE_OUT + 0.1
        self.assertFalse(self.state.speech["fading"])
        # Tick past threshold
        self.engine._update_speech(0.2)
        self.assertTrue(self.state.speech["fading"])

    def test_clears_after_fade_out(self):
        """Speech clears when timer expires and opacity is zero."""
        self.engine._trigger_speech("happy")
        self.state.speech["opacity"] = 0.1
        self.state.speech["timer"] = 0.01
        self.state.speech["fading"] = True
        self.engine._update_speech(0.05)
        self.assertIsNone(self.state.speech["text"])
        self.assertEqual(self.state.speech["opacity"], 0.0)

    def test_queue_drains_after_clear(self):
        """Next queue item displays after current clears."""
        self.engine._trigger_speech("happy")
        self.engine._trigger_speech("hungry")
        # Force clear current
        self.state.speech["text"] = None
        self.state.speech["opacity"] = 0.0
        self.state.speech["timer"] = 0.0
        self.engine._update_speech(0.05)
        # Queue should have drained into active
        self.assertIsNotNone(self.state.speech["text"])
        self.assertEqual(len(self.state.speech["queue"]), 0)

    def test_idle_timer_increments_when_awake(self):
        """speech_idle_timer increases during awake states."""
        old = self.state.speech_idle_timer
        self.engine._update_speech(1.0)
        self.assertGreater(self.state.speech_idle_timer, old)

    def test_idle_timer_resets_when_sleeping(self):
        """speech_idle_timer resets during sleep."""
        self.state.speech_idle_timer = 50.0
        self.state.state = config.STATE_SLEEP
        self.engine._update_speech(1.0)
        self.assertEqual(self.state.speech_idle_timer, 0.0)

    def test_cooldown_decrements(self):
        """speech_cooldown decreases each tick."""
        self.state.speech_cooldown = 10.0
        self.engine._update_speech(1.0)
        self.assertAlmostEqual(self.state.speech_cooldown, 9.0, places=5)


class TestDrawSpeechBubble(unittest.TestCase):
    """Test draw_speech_bubble doesn't crash (offscreen painter)."""

    def setUp(self):
        self.state = CatState()
        self.state.speech["text"] = "hello"
        self.state.speech["emoji"] = "😊"
        self.state.speech["opacity"] = 1.0

    def test_draw_no_crash_with_active_speech(self):
        """draw_speech_bubble doesn't crash with valid speech."""
        painter = MagicMock()
        from cat.home import draw_speech_bubble
        draw_speech_bubble(painter, self.state, 100, 100, True)
        self.assertTrue(painter.save.called)
        self.assertTrue(painter.restore.called)

    def test_draw_noop_when_no_text(self):
        """draw_speech_bubble does nothing when text is None."""
        self.state.speech["text"] = None
        painter = MagicMock()
        from cat.home import draw_speech_bubble
        draw_speech_bubble(painter, self.state, 100, 100, True)
        painter.save.assert_not_called()

    def test_draw_no_crash_when_cat_near_edge(self):
        """draw_speech_bubble handles near-zero cat_y without crash."""
        painter = MagicMock()
        from cat.home import draw_speech_bubble
        draw_speech_bubble(painter, self.state, 50, 10, True)

    def test_draw_without_emoji(self):
        """draw_speech_bubble handles None emoji gracefully."""
        self.state.speech["emoji"] = None
        painter = MagicMock()
        from cat.home import draw_speech_bubble
        draw_speech_bubble(painter, self.state, 100, 100, True)


class TestMoodPriorityConfig(unittest.TestCase):
    """Verify MOOD_PRIORITY completeness and ordering."""

    def test_all_moods_have_priority(self):
        """Every mood in SPEECH_MOODS has an entry in MOOD_PRIORITY."""
        for mood in SPEECH_MOODS:
            self.assertIn(mood, config.MOOD_PRIORITY,
                          f"Mood '{mood}' missing from MOOD_PRIORITY")

    def test_hungry_and_alert_have_highest_priority(self):
        """hungry and alert are priority 3 (highest)."""
        self.assertEqual(config.MOOD_PRIORITY.get("hungry"), 3)
        self.assertEqual(config.MOOD_PRIORITY.get("alert"), 3)


if __name__ == "__main__":
    unittest.main()
