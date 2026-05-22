"""
tests/test_sound.py — Unit tests for core/sound.py

Tests cover:
- SoundManager initialization and backend detection
- Path resolution
- Backend selection behavior
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
    """Test SoundManager initialization and backend detection."""

    def test_init_creates_self(self):
        from core.sound import SoundManager
        sm = SoundManager()
        self.assertIsNotNone(sm)
        self.assertTrue(hasattr(sm, '_can_winsound'))
        self.assertTrue(hasattr(sm, '_can_qse'))
        self.assertTrue(hasattr(sm, '_enabled'))

    def test_enabled_by_default(self):
        from core.sound import SoundManager
        sm = SoundManager()
        self.assertTrue(sm.enabled)

    def test_backend_flags_none(self):
        """When neither backend is available."""
        from core.sound import SoundManager
        sm = SoundManager()
        # Force both to False
        sm._can_winsound = False
        sm._can_qse = False
        self.assertFalse(sm._can_winsound)
        self.assertFalse(sm._can_qse)
        sm.play("test")  # Should not crash
        sm.start_loop("test")  # Should not crash

    def test_backend_flags_winsound_only(self):
        """When winsound is available but QSoundEffect is not."""
        with patch.dict('sys.modules', {'PyQt6.QtMultimedia': None}):
            from core.sound import SoundManager
            sm = SoundManager()
            sm._detect_backends()
            # On Linux, both will be False; on Windows, winsound=True, QSE=False
            # Just verify it doesn't crash and flags are bools
            self.assertIsInstance(sm._can_winsound, bool)
            self.assertIsInstance(sm._can_qse, bool)


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
        with patch.object(self.sm, '_play_winsound') as mock_play:
            self.sm.play("purr")
            mock_play.assert_not_called()

    def test_start_loop_does_nothing_when_disabled(self):
        self.sm.set_enabled(False)
        with patch.object(self.sm, '_start_loop_qse') as mock_loop:
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
        from core.sound import SOUNDS_DIR
        self.sounds_dir = SOUNDS_DIR

    def test_resolve_with_extension(self):
        path = self.sm._resolve_path("meow_short.wav")
        if os.path.exists(os.path.join(self.sounds_dir, "meow_short.wav")):
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith("meow_short.wav"))

    def test_resolve_without_extension(self):
        path = self.sm._resolve_path("purr")
        if os.path.exists(os.path.join(self.sounds_dir, "purr.wav")):
            self.assertIsNotNone(path)
            self.assertTrue(path.endswith("purr.wav"))

    def test_resolve_nonexistent(self):
        path = self.sm._resolve_path("nonexistent_sound_xyz123")
        self.assertIsNone(path)

    def test_resolve_returns_string(self):
        path = self.sm._resolve_path("footstep")
        if os.path.exists(os.path.join(self.sounds_dir, "footstep.wav")):
            self.assertIsInstance(path, str)


class TestSoundManagerPlay(unittest.TestCase):
    """Test play operations."""

    def setUp(self):
        from core.sound import SoundManager
        self.sm = SoundManager()

    def test_play_uses_winsound_when_available(self):
        """Should call _play_winsound when winsound is available."""
        self.sm._can_winsound = True
        self.sm._can_qse = False
        with patch.object(self.sm, '_play_winsound') as mock_pw:
            with patch.object(self.sm, '_resolve_path', return_value="/tmp/test.wav"):
                self.sm.play("test")
                mock_pw.assert_called_once_with("/tmp/test.wav")

    def test_play_uses_qse_when_winsound_unavailable(self):
        """Should call _play_qse when winsound is not available."""
        self.sm._can_winsound = False
        self.sm._can_qse = True
        with patch.object(self.sm, '_play_qse') as mock_qse:
            with patch.object(self.sm, '_resolve_path', return_value="/tmp/test.wav"):
                self.sm.play("test")
                mock_qse.assert_called_once_with("/tmp/test.wav")

    def test_play_does_nothing_no_backends(self):
        """Should do nothing when no backends available."""
        self.sm._can_winsound = False
        self.sm._can_qse = False
        with patch.object(self.sm, '_play_winsound') as mock_pw:
            with patch.object(self.sm, '_play_qse') as mock_qse:
                self.sm.play("test")
                mock_pw.assert_not_called()
                mock_qse.assert_not_called()

    def test_play_does_nothing_on_missing_path(self):
        self.sm._can_winsound = True
        with patch.object(self.sm, '_resolve_path', return_value=None):
            with patch.object(self.sm, '_play_winsound') as mock_pw:
                self.sm.play("test")
                mock_pw.assert_not_called()

    def test_play_winsound_called_with_path(self):
        """Direct test of _play_winsound (skipped on non-Windows)."""
        # Skip on Linux since winsound doesn't exist
        import sys
        if sys.platform != 'win32':
            self.skipTest("winsound only available on Windows")
        import winsound
        with patch('winsound.PlaySound') as mock_ps:
            self.sm._play_winsound("/tmp/test.wav")
            mock_ps.assert_called_once_with(
                "/tmp/test.wav",
                unittest.mock.ANY  # SND_ASYNC | SND_NODEFAULT
            )


class TestSoundManagerLoop(unittest.TestCase):
    """Test loop operations."""

    def setUp(self):
        from core.sound import SoundManager
        self.sm = SoundManager()

    def test_start_loop_uses_qse(self):
        """Should call _start_loop_qse when QSE is available."""
        self.sm._can_qse = True
        with patch.object(self.sm, '_start_loop_qse') as mock_loop:
            with patch.object(self.sm, '_resolve_path', return_value="/tmp/test.wav"):
                self.sm.start_loop("test")
                mock_loop.assert_called_once_with("/tmp/test.wav")

    def test_start_loop_does_nothing_when_qse_unavailable(self):
        """Should do nothing when QSoundEffect is not available."""
        self.sm._can_qse = False
        with patch.object(self.sm, '_start_loop_qse') as mock_loop:
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
