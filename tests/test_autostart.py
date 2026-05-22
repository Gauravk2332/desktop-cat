"""
tests/test_autostart.py — Unit tests for launcher/autostart.py

Uses mock patches for winreg (Windows registry) to enable testing on any platform.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from launcher import autostart


class TestAutostartConstants(unittest.TestCase):
    """Verify constants and utility helpers."""

    def test_app_name_constant(self):
        self.assertEqual(autostart.APP_NAME, "DesktopCat")

    def test_reg_key_path_constant(self):
        self.assertEqual(autostart.REG_RUN_PATH,
                         r"Software\Microsoft\Windows\CurrentVersion\Run")

    def test_get_reg_key_with_mocked_winreg(self):
        """_get_reg_key should return (HKCU, REG_RUN_PATH)."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_winreg.HKEY_CURRENT_USER = "HKCU_MOCK"
            handle, path = autostart._get_reg_key()
            self.assertEqual(handle, "HKCU_MOCK")
            self.assertEqual(path, autostart.REG_RUN_PATH)


class TestIsRegistered(unittest.TestCase):
    """Test is_registered() with mocked winreg."""

    def test_registered_key_exists(self):
        """is_registered returns True when key+value exist."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            result = autostart.is_registered()

            self.assertTrue(result)
            mock_winreg.OpenKey.assert_called_once_with(
                mock_winreg.HKEY_CURRENT_USER,
                autostart.REG_RUN_PATH,
                0,
                mock_winreg.KEY_READ,
            )
            mock_winreg.QueryValueEx.assert_called_once_with(mock_key, "DesktopCat")

    def test_not_registered_file_not_found(self):
        """is_registered returns False when FileNotFoundError raised."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = FileNotFoundError

            result = autostart.is_registered()

            self.assertFalse(result)

    def test_not_registered_os_error(self):
        """is_registered returns False when OSError raised."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError

            result = autostart.is_registered()

            self.assertFalse(result)

    def test_not_registered_no_winreg(self):
        """is_registered returns False when winreg is None (non-Windows)."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.is_registered()
            self.assertFalse(result)


class TestRegister(unittest.TestCase):
    """Test register() with mocked winreg."""

    def test_register_with_default_path(self):
        """register() without exe_path uses sys.executable + -m launcher.autostart."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            result = autostart.register()

            self.assertTrue(result)
            expected_value = f'"{sys.executable}" -m launcher.autostart'
            mock_winreg.SetValueEx.assert_called_once_with(
                mock_key, "DesktopCat", 0, mock_winreg.REG_SZ, expected_value
            )

    def test_register_with_custom_path(self):
        """register() accepts a custom exe_path."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            custom = r"C:\Users\gk\AppData\Local\desktop-cat\desktop-cat.exe"
            result = autostart.register(custom)

            self.assertTrue(result)
            mock_winreg.SetValueEx.assert_called_once_with(
                mock_key, "DesktopCat", 0, mock_winreg.REG_SZ, custom,
            )

    def test_register_no_winreg(self):
        """register() returns False when winreg is None."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.register()
            self.assertFalse(result)

    def test_register_os_error(self):
        """register() returns False when OpenKey fails."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = OSError("Access denied")

            result = autostart.register()

            self.assertFalse(result)

    def test_register_uses_correct_key_path(self):
        """register() opens the Run key, not some other path."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            autostart.register()

            mock_winreg.OpenKey.assert_called_once_with(
                mock_winreg.HKEY_CURRENT_USER,
                autostart.REG_RUN_PATH,
                0,
                mock_winreg.KEY_SET_VALUE,
            )


class TestUnregister(unittest.TestCase):
    """Test unregister() with mocked winreg."""

    def test_unregister_success(self):
        """unregister() deletes the value and returns True."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            result = autostart.unregister()

            self.assertTrue(result)
            mock_winreg.DeleteValue.assert_called_once_with(mock_key, "DesktopCat")

    def test_unregister_not_found(self):
        """unregister() returns True (clean state) if value doesn't exist."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_winreg.OpenKey.side_effect = FileNotFoundError

            result = autostart.unregister()

            self.assertTrue(result)  # already clean

    def test_unregister_no_winreg(self):
        """unregister() returns False when winreg is None."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.unregister()
            self.assertFalse(result)

    def test_unregister_os_error(self):
        """unregister() returns False when deletion fails."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_winreg.OpenKey.return_value.__enter__.side_effect = OSError("Access denied")

            result = autostart.unregister()

            self.assertFalse(result)

    def test_unregister_uses_correct_key(self):
        """unregister() opens the Run key, not some other path."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            autostart.unregister()

            mock_winreg.OpenKey.assert_called_once_with(
                mock_winreg.HKEY_CURRENT_USER,
                autostart.REG_RUN_PATH,
                0,
                mock_winreg.KEY_SET_VALUE,
            )


class TestToggle(unittest.TestCase):
    """Test toggle() behavior."""

    def test_toggle_registers_when_not_registered(self):
        """toggle() should register when currently not registered, return True."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            # First call (is_registered): key missing -> FileNotFoundError
            # Second call (register): succeeds
            mock_winreg.OpenKey.side_effect = [
                FileNotFoundError,  # is_registered
                mock_key,           # register -> OpenKey succeeds
            ]
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            result = autostart.toggle()

            self.assertTrue(result)  # now registered
            mock_winreg.SetValueEx.assert_called_once()

    def test_toggle_unregisters_when_registered(self):
        """toggle() should unregister when currently registered, return False."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
            # QueryValueEx succeeds -> is_registered = True

            result = autostart.toggle()

            self.assertFalse(result)  # now unregistered
            mock_winreg.DeleteValue.assert_called_once_with(mock_key, "DesktopCat")

    def test_toggle_calls_is_registered_first(self):
        """toggle() should call is_registered() and then act."""
        with patch("launcher.autostart.winreg") as mock_winreg:
            mock_key = MagicMock()
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

            autostart.toggle()

            # Should call QueryValueEx first (is_registered check)
            mock_winreg.QueryValueEx.assert_called_once_with(mock_key, "DesktopCat")

    def test_toggle_no_winreg_returns_true(self):
        """toggle() with no winreg: is_registered=False, register fails, returns False."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.toggle()
            self.assertFalse(result)


class TestModuleStructure(unittest.TestCase):
    """Verify module interface matches expected API."""

    def test_module_has_expected_functions(self):
        """autostart module must expose register, unregister, is_registered, toggle."""
        self.assertTrue(hasattr(autostart, "register"))
        self.assertTrue(hasattr(autostart, "unregister"))
        self.assertTrue(hasattr(autostart, "is_registered"))
        self.assertTrue(hasattr(autostart, "toggle"))

    def test_register_returns_bool(self):
        """register() should return bool."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.register()
            self.assertIsInstance(result, bool)

    def test_unregister_returns_bool(self):
        """unregister() should return bool."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.unregister()
            self.assertIsInstance(result, bool)

    def test_is_registered_returns_bool(self):
        """is_registered() should return bool."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.is_registered()
            self.assertIsInstance(result, bool)

    def test_toggle_returns_bool(self):
        """toggle() should return bool."""
        with patch("launcher.autostart.winreg", None):
            result = autostart.toggle()
            self.assertIsInstance(result, bool)


class TestWinregNone(unittest.TestCase):
    """Test that autostart module works safely on non-Windows (winreg=None)."""

    @classmethod
    def setUpClass(cls):
        # Ensure we're testing with winreg=None
        cls._orig_winreg = autostart.winreg
        autostart.winreg = None

    @classmethod
    def tearDownClass(cls):
        autostart.winreg = cls._orig_winreg

    def test_is_registered_returns_false(self):
        self.assertFalse(autostart.is_registered())

    def test_register_returns_false(self):
        self.assertFalse(autostart.register())

    def test_unregister_returns_false(self):
        self.assertFalse(autostart.unregister())

    def test_toggle_returns_false(self):
        self.assertFalse(autostart.toggle())


if __name__ == "__main__":
    unittest.main()
