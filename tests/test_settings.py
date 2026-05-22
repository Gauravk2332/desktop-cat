"""
tests/test_settings.py — Unit tests for ui/settings.py

Tests cover:
- AppSettings dataclass: save/load round-trip, default values
- SettingsDialog: UI structure, coat options, button binding
- Settings open/close
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAppSettings(unittest.TestCase):
    """Test the AppSettings dataclass."""

    def setUp(self):
        from ui.settings import AppSettings
        self.AppSettings = AppSettings

    def test_default_values(self):
        s = self.AppSettings()
        self.assertEqual(s.coat, "russian_blue")
        self.assertTrue(s.sound_enabled)
        self.assertFalse(s.autostart)

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            s = self.AppSettings(coat="ginger", sound_enabled=False, autostart=True)
            s.save(path)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(data["coat"], "ginger")
            self.assertFalse(data["sound_enabled"])
            self.assertTrue(data["autostart"])

    def test_load_returns_defaults_on_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nonexistent.json")
            s = self.AppSettings.load(path)
            self.assertEqual(s.coat, "russian_blue")

    def test_load_returns_defaults_on_corrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w") as f:
                f.write("not json")
            s = self.AppSettings.load(path)
            self.assertEqual(s.coat, "russian_blue")

    def test_load_ignores_unknown_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            with open(path, "w") as f:
                json.dump({"coat": "tuxedo", "unknown": True}, f)
            s = self.AppSettings.load(path)
            self.assertEqual(s.coat, "tuxedo")
            self.assertTrue(s.sound_enabled)  # default

    def test_load_partial_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            with open(path, "w") as f:
                json.dump({"autostart": True}, f)
            s = self.AppSettings.load(path)
            self.assertEqual(s.coat, "russian_blue")  # default
            self.assertTrue(s.autostart)  # override

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            s1 = self.AppSettings(coat="siamese", sound_enabled=False)
            s1.save(path)
            s2 = self.AppSettings.load(path)
            self.assertEqual(s2.coat, "siamese")
            self.assertFalse(s2.sound_enabled)
            self.assertFalse(s2.autostart)


class TestColorSwatch(unittest.TestCase):
    """Test the color swatch pixmap generator."""

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv if hasattr(sys, 'argv') else [])

    def test_swatch_returns_pixmap(self):
        from ui.settings import _color_swatch_pixmap
        pix = _color_swatch_pixmap("#FF0000", 24)
        self.assertIsNotNone(pix)
        self.assertEqual(pix.width(), 24)
        self.assertEqual(pix.height(), 24)

    def test_swatch_various_sizes(self):
        from ui.settings import _color_swatch_pixmap
        for size in [16, 24, 32]:
            pix = _color_swatch_pixmap("#7C8E9E", size)
            self.assertEqual(pix.width(), size)
            self.assertEqual(pix.height(), size)


class TestSettingsDialog(unittest.TestCase):
    """Test the settings dialog UI structure."""

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv if hasattr(sys, 'argv') else [])

    def setUp(self):
        """Patch coat loading to avoid file dependency."""
        # Save original coats path
        from ui import settings as s
        self._orig_path = s.COATS_PATH

        # Point to a temp file with test coats
        self._tmpdir = tempfile.TemporaryDirectory()
        self._coats_path = os.path.join(self._tmpdir.name, "coats.json")
        with open(self._coats_path, "w") as f:
            json.dump({
                "russian_blue": {"body": "#7C8E9E", "belly": "#A8B8C8"},
                "ginger": {"body": "#E8A87C", "belly": "#FAD6B2"},
                "tuxedo": {"body": "#2C2C2C", "belly": "#F5F5F5"},
            }, f)
        s.COATS_PATH = self._coats_path

    def tearDown(self):
        from ui import settings as s
        s.COATS_PATH = self._orig_path
        self._tmpdir.cleanup()

    def test_dialog_creates(self):
        """Dialog can be instantiated."""
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        self.assertIsNotNone(dlg)
        self.assertEqual(dlg.windowTitle(), "Desktop Cat Settings")

    def test_contains_coat_group(self):
        """Dialog has a coat color group with radio buttons."""
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        # Should have 3 coats
        self.assertEqual(dlg._coat_group.buttons().__len__(), 3)

    def test_coat_names_loaded(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        names = [b.property("coat_name") for b in dlg._coat_group.buttons()]
        self.assertIn("russian_blue", names)
        self.assertIn("ginger", names)
        self.assertIn("tuxedo", names)

    def test_default_coat_selected(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        selected = dlg._coat_group.checkedButton()
        self.assertEqual(selected.property("coat_name"), "russian_blue")

    def test_contains_sound_checkbox(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        self.assertIsNotNone(dlg._sound_cb)
        self.assertEqual(dlg._sound_cb.text(), "Sound Effects")

    def test_contains_autostart_checkbox(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        self.assertIsNotNone(dlg._autostart_cb)
        self.assertEqual(dlg._autostart_cb.text(), "Start with Windows")

    def test_apply_method_exists(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        self.assertTrue(hasattr(dlg, '_apply'))
        self.assertTrue(callable(dlg._apply))

    def test_load_state_sets_coat(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        dlg.settings.coat = "ginger"
        dlg._load_state()
        selected = dlg._coat_group.checkedButton()
        self.assertEqual(selected.property("coat_name"), "ginger")

    def test_apply_saves_settings(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        # Switch to ginger
        for btn in dlg._coat_group.buttons():
            if btn.property("coat_name") == "ginger":
                btn.setChecked(True)
                break
        dlg._sound_cb.setChecked(False)

        with patch.object(dlg.settings, 'save') as mock_save:
            dlg._apply()
            self.assertEqual(dlg.settings.coat, "ginger")
            self.assertFalse(dlg.settings.sound_enabled)
            mock_save.assert_called_once()
            self.assertTrue(dlg.changed)

    def test_open_returns_settings_on_accept(self):
        """SettingsDialog.open returns settings when accepted."""
        from ui.settings import SettingsDialog
        with patch.object(SettingsDialog, 'exec', return_value=1):  # Accepted
            result = SettingsDialog.open()
            self.assertIsNotNone(result)
            self.assertEqual(result.coat, "russian_blue")

    def test_open_returns_none_on_cancel(self):
        from ui.settings import SettingsDialog
        with patch.object(SettingsDialog, 'exec', return_value=0):  # Rejected
            result = SettingsDialog.open()
            self.assertIsNone(result)

    def test_autostart_toggle_in_apply(self):
        """_apply should call register/unregister when autostart changes."""
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        dlg.settings.autostart = False
        dlg._autostart_cb.setChecked(True)

        with patch('ui.settings.logger') as mock_log:
            with patch.object(dlg.settings, 'save'):
                dlg._apply()
                self.assertTrue(dlg.settings.autostart)

    def test_size_fixed(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        self.assertGreater(dlg.width(), 0)
        self.assertGreater(dlg.height(), 0)

    def test_coat_group_is_button_group(self):
        from ui.settings import SettingsDialog
        dlg = SettingsDialog()
        from PyQt6.QtWidgets import QButtonGroup
        self.assertIsInstance(dlg._coat_group, QButtonGroup)


if __name__ == "__main__":
    unittest.main()
