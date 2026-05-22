"""
tests/test_sound.py — Unit tests for core/sound.py

Tests cover:
- SoundManager initialization and tier detection
- Path resolution
- Tier fallback behavior
- Enable/disable
- Play/stop-loop operations
- Cleanup
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSoundManagerInit(unittest.TestCase):
    """Test SoundManager initialization and tier detection."""

    def test_detect_tier_fallback_no_multimedia(self):
        """Should fall back when QSoundEffect is unavailable."""
        with patch.dict('sys.modules', {'PyQt6.QtMultimedia': None}):
            from core.sound import SoundManager
            sm = SoundManager()
            # Should be 0 (no backends available on headless Linux)
            self.assertIn(sm._tier, [0, 2])  # 0 for Linux, 2 for Windows

    def test_init_creates_self(self):
        from core.sound import SoundManager
        sm = SoundManager()
        self.assertIsNotNone(sm)
        self.assertTrue(hasattr(sm, '_tier'))
        self.assertTrue(hasattr(sm, '_enabled'))

    def test_enabled_by_default(self):
        from core.sound import SoundManager
        sm = SoundManager()
        self.assertTrue(sm.enabled)


class TestSoundManagerEnable(unittest.TestCase):
    """Test set_enabled and property."""

    def setUp(self):
        from core.sound import SoundManager
        self.sm = SoundManager()

    def test_set_enabled_false(self):
        self.sm.set_enabled(False)
        self.assertFalse(self.sm.enabled)

    def test_set_enabled_true(self):
        self.sm.set_enabled(False)
        self.sm.set_enabled(True)
        self.assertTrue(self.sm.enabled)

    def test_play_does_nothing_when_disabled(self):
        self.sm.set_enabled(False)
        with patch.object(self.sm, '_play_tier1') as mock_play:
            self.sm.play("purr")
            mock_play.assert_not_called()

    def test_start_loop_does_nothing_when_disabled(self):
        self.sm.set_enabled(False)
        with patch.object(self.sm, '_start_loop_tier1') as mock_loop:
            self.sm.start_loop("purr")
            mock_loop.assert_not_called()

    def test_stop_loop_does_nothing_when_disabled(self):
        self.sm.set_enabled(False)
        # Should not crash
        self.sm.stop_loop()


class TestSoundManagerPathResolution(unittest.TestCase):
    """Test sound file resolution."""

    def setUp(self):
        from core.sound import SoundManager
        self.sm = SoundManager()
        # Ensure sounds directory exists
        from core.sound import SOUNDS_DIR
        self.sounds_dir = SOUNDS_DIR

    def test_resolve_with_extension(self):
        """Should find file with .wav extension when given name with extension."""
        path = self.sm._resolve_path("meow_short.wav")
        if os.path.exists(os.path.join(self.sounds_dir, "meow_short.wav")):
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith("meow_short.wav"))

    def test_resolve_without_extension(self):
        """Should find file when given name without extension."""
        path = self.sm._resolve_path("purr")
        if os.path.exists(os.path.join(self.sounds_dir, "purr.wav")):
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith("purr.wav"))

    def test_resolve_nonexistent(self):
        """Should return None for missing sound."""
        path = self.sm._resolve_path("nonexistent_sound_xyz123")
        self.assertIsNone(path)

    def test_resolve_returns_string(self):
        path = self.sm._resolve_path("footstep")
        if os.path.exists(os.path.join(self.sounds_dir, "footstep.wav")):
            self.assertIsInstance(path, str)


class TestSoundManagerPlay(unittest.TestCase):
    """Test play operations with mocked tier 1."""

    def setUp(self):
        from core.sound import SoundManager
        self.sm = SoundManager()

    def test_play_calls_tier1_when_available(self):
        """Should call _play_tier1 when tier=1."""
        self.sm._tier = 1
        with patch.object(self.sm, '_play_tier1') as mock_play:
            with patch.object(self.sm, '_resolve_path', return_value="/tmp/test.wav"):
                self.sm.play("test")
                mock_play.assert_called_once_with("/tmp/test.wav")

    def test_play_calls_tier2_when_available(self):
        """Should call _play_tier2 when tier=2."""
        self.sm._tier = 2
        with patch.object(self.sm, '_play_tier2') as mock_play:
            with patch.object(self.sm, '_resolve_path', return_value="/tmp/test.wav"):
                self.sm.play("test")
                mock_play.assert_called_once_with("/tmp/test.wav")

    def test_play_does_nothing_on_tier_0(self):
        self.sm._tier = 0
        with patch.object(self.sm, '_play_tier1') as mock_play:
            self.sm.play("test")
            mock_play.assert_not_called()

    def test_play_does_nothing_on_missing_path(self):
        self.sm._tier = 1
        with patch.object(self.sm, '_resolve_path', return_value=None):
            with patch.object(self.sm, '_play_tier1') as mock_play:
                self.sm.play("test")
                mock_play.assert_not_called()


class TestSoundManagerLoop(unittest.TestCase):
    """Test loop operations."""

    def setUp(self):
        from core.sound import SoundManager
        self.sm = SoundManager()

    def test_start_loop_calls_tier1(self):
        self.sm._tier = 1
        with patch.object(self.sm, '_start_loop_tier1') as mock_loop:
            with patch.object(self.sm, '_resolve_path', return_value="/tmp/test.wav"):
                self.sm.start_loop("test")
                mock_loop.assert_called_once_with("/tmp/test.wav")

    def test_start_loop_does_nothing_tier_0(self):
        self.sm._tier = 0
        with patch.object(self.sm, '_start_loop_tier1') as mock_loop:
            self.sm.start_loop("test")
            mock_loop.assert_not_called()

    def test_cleanup(self):
        """Should not crash on cleanup."""
        self.sm.cleanup()

    def test_cleanup_calls_stop_loop(self):
        with patch.object(self.sm, 'stop_loop') as mock_stop:
            self.sm.cleanup()
            mock_stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
