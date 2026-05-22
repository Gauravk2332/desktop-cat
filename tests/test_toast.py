"""tests/test_toast.py — Tests for Windows toast notifications."""

import sys
import unittest
from unittest.mock import patch

from core.toast import notify, set_notifications_enabled


class TestToast(unittest.TestCase):
    """Test that toast notifications are safe and controllable."""

    def test_notify_safe_noop_on_non_windows(self):
        """Notify should be a safe no-op on non-Windows platforms."""
        with patch("core.toast._notification_enabled", True):
            with patch.object(sys, "platform", "linux"):
                notify("Test Title", "Test Message")

    def test_notify_safe_noop_when_disabled(self):
        """Notify should be a no-op when notifications are disabled."""
        with patch("core.toast._notification_enabled", False):
            notify("Test Title", "Test Message")

    def test_set_notifications_enabled(self):
        """set_notifications_enabled should toggle the global flag."""
        import core.toast as toast_mod
        set_notifications_enabled(True)
        self.assertTrue(toast_mod._notification_enabled)

        set_notifications_enabled(False)
        self.assertFalse(toast_mod._notification_enabled)

        set_notifications_enabled(True)
        self.assertTrue(toast_mod._notification_enabled)

    @patch.object(sys, "platform", "win32")
    def test_notify_import_fail_safe(self):
        """Notify should handle ImportError gracefully on Windows."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("winrt"):
                raise ImportError("winrt not available")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("core.toast._notification_enabled", True):
                notify("Test", "Message")

    def test_notify_with_empty_strings(self):
        """Notify should handle empty title and message."""
        with patch("core.toast._notification_enabled", True):
            with patch.object(sys, "platform", "linux"):
                notify("", "")
