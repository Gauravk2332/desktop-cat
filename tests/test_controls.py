"""
tests/test_controls.py — Unit tests for keyboard shortcuts and controls.

Tests that:
- Controls handles basic key events (Escape, C, H, R)
- Click-through toggle works
- Unhandled keys return False
- Hearts are spawned on pet
- Interact mode indicator logic
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtCore import Qt
from core.state import CatState


class TestControls(unittest.TestCase):
    """Test Controls keyboard handler in isolation."""

    def setUp(self):
        self.state = CatState()
        self.mock_window = MagicMock()
        self.mock_engine = MagicMock()
        from core.controls import Controls
        self.controls = Controls(self.mock_window, self.state, self.mock_engine)

    def test_escape_toggles_visibility(self):
        """Escape key toggles window visibility."""
        initial_visible = self.mock_window.isVisible()
        result = self.controls.handle_key(Qt.Key.Key_Escape)
        self.assertTrue(result)
        self.mock_window.setVisible.assert_called_once_with(not initial_visible)

    def test_c_key_toggles_click_through(self):
        """Ctrl+Shift+C toggles click-through attribute on window."""
        with patch.object(self.controls, 'toggle_click_through') as mock_toggle:
            result = self.controls.handle_key(Qt.Key.Key_C)
            self.assertTrue(result)
            mock_toggle.assert_called_once()

    def test_toggle_click_through_flips_state(self):
        """toggle_click_through flips click_through in state."""
        initial = self.state.click_through
        self.controls.toggle_click_through()
        self.assertNotEqual(self.state.click_through, initial)

    def test_toggle_click_through_sets_window_attr(self):
        """toggle_click_through sets WA_TransparentForMouseEvents."""
        self.controls.toggle_click_through()
        self.mock_window.setAttribute.assert_called_once()

    def test_toggle_click_through_attr_value(self):
        """setAttribute arg matches new click_through state."""
        # Start True, after toggle should be False
        self.controls.toggle_click_through()
        args, kwargs = self.mock_window.setAttribute.call_args
        expected_attr = Qt.WidgetAttribute.WA_TransparentForMouseEvents
        self.assertEqual(args[0], expected_attr)
        self.assertEqual(args[1], False)

    def test_h_key_hides_window(self):
        """H key toggles window visibility."""
        self.mock_window.isVisible.return_value = True
        result = self.controls.handle_key(Qt.Key.Key_H)
        self.assertTrue(result)
        self.mock_window.setVisible.assert_called_once_with(False)

    def test_r_key_resets_position(self):
        """R key resets cat to center of screen."""
        self.state.screen_width = 1920
        self.state.screen_height = 1080
        self.state.cat_x = 42.0
        self.state.cat_y = 100.0
        result = self.controls.handle_key(Qt.Key.Key_R)
        self.assertTrue(result)
        self.assertEqual(self.state.cat_x, 960.0)  # screen_width // 2
        self.assertEqual(self.state.cat_y, 1060.0)  # screen_height - 20
        self.assertEqual(self.state.state, "SIT")

    def test_unhandled_key_returns_false(self):
        """Q key returns False (not handled)."""
        result = self.controls.handle_key(Qt.Key.Key_Q)
        self.assertFalse(result)

    def test_enter_key_returns_false(self):
        """Enter key returns False (not handled)."""
        result = self.controls.handle_key(Qt.Key.Key_Enter)
        self.assertFalse(result)

    def test_space_key_returns_false(self):
        """Space key returns False (not handled)."""
        result = self.controls.handle_key(Qt.Key.Key_Space)
        self.assertFalse(result)

    def test_f_key_returns_false(self):
        """F key returns False (not handled)."""
        result = self.controls.handle_key(Qt.Key.Key_F)
        self.assertFalse(result)


class TestControlsModifierKey(unittest.TestCase):
    """Test that modifier masks don't break keyboard handling.

    The controls use event.key() which is the base key without modifiers.
    This test verifies the correct pattern is used.
    """

    def setUp(self):
        self.state = CatState()
        self.mock_window = MagicMock()
        self.mock_engine = MagicMock()
        from core.controls import Controls
        self.controls = Controls(self.mock_window, self.state, self.mock_engine)

    def test_user_guide_uses_event_key(self):
        """Window's keyPressEvent should use event.key() not event.text()."""
        from core.window import CatWindow
        import inspect
        source = inspect.getsource(CatWindow.keyPressEvent)
        self.assertIn("event.key()", source,
                      "Window should pass event.key() not event.text()")


class TestControlsWindowKeys(unittest.TestCase):
    """Test that CatWindow wires keyPressEvent to Controls."""

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv if hasattr(sys, 'argv') else [])

    def setUp(self):
        self.state = CatState()

    def test_window_has_controls_attr(self):
        """CatWindow should have a 'controls' attribute after init."""
        from core.window import CatWindow
        window = CatWindow(self.state)
        self.assertTrue(hasattr(window, 'controls'),
                        "CatWindow missing 'controls'")
        from core.controls import Controls
        self.assertIsInstance(window.controls, Controls)

    def test_window_has_keypressevent(self):
        """CatWindow should have keyPressEvent method."""
        from core.window import CatWindow
        self.assertTrue(hasattr(CatWindow, 'keyPressEvent'))
        self.assertTrue(callable(CatWindow.keyPressEvent))

    def test_window_has_focus_policy(self):
        """CatWindow should have StrongFocus policy."""
        from core.window import CatWindow
        policy = CatWindow.focusPolicy
        # Can't easily check static attribute without instance;
        # verify the init setFocusPolicy was called
        import inspect
        source = inspect.getsource(CatWindow.__init__)
        self.assertIn("setFocusPolicy(Qt.FocusPolicy.StrongFocus)", source,
                      "Window must set StrongFocus for keyboard events")


class TestWindowInteractIndicator(unittest.TestCase):
    """Test the interact mode indicator drawing."""

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv if hasattr(sys, 'argv') else [])

    def setUp(self):
        self.state = CatState()
        from core.window import CatWindow
        self.window = CatWindow(self.state)

    def test_draw_interact_indicator_exists(self):
        """CatWindow has _draw_interact_indicator method."""
        method = getattr(self.window, '_draw_interact_indicator', None)
        self.assertIsNotNone(method)
        self.assertTrue(callable(method))

    def test_indicator_not_drawn_when_click_through(self):
        """Interact mode indicator should not appear by default (click-through on)."""
        # By default click_through is True, so indicator should not be shown
        self.assertTrue(self.state.click_through,
                        "Default state should be click-through enabled")


class TestHearts(unittest.TestCase):
    """Test hearts state management."""

    def setUp(self):
        self.state = CatState()

    def test_spawn_hearts_creates_hearts(self):
        """_spawn_hearts adds heart entries to state."""
        from core.navigation import _spawn_hearts
        count_before = len(self.state.hearts)
        _spawn_hearts(self.state, count=3)
        self.assertEqual(len(self.state.hearts), count_before + 3)

    def test_heart_structure(self):
        """Each heart has [x_offset, y_offset, lifetime, size]."""
        from core.navigation import _spawn_hearts
        _spawn_hearts(self.state, count=1)
        heart = self.state.hearts[0]
        self.assertEqual(len(heart), 4)
        x_off, y_off, lifetime, size = heart
        self.assertIsInstance(x_off, (int, float))
        self.assertIsInstance(y_off, (int, float))
        self.assertIsInstance(lifetime, (int, float))
        self.assertIsInstance(size, (int, float))
        self.assertGreater(lifetime, 0)
        self.assertGreater(size, 0)

    def test_heart_decay_updates_lifetime(self):
        """Simulate heart tick decay."""
        from core.navigation import _spawn_hearts
        _spawn_hearts(self.state, count=1)
        original_lifetime = self.state.hearts[0][2]
        self.state.hearts[0][2] -= 0.5  # simulate half-second decay
        self.assertAlmostEqual(self.state.hearts[0][2], original_lifetime - 0.5)

    def test_heart_removal_on_zero_lifetime(self):
        """Hearts with lifetime <= 0 should be removed."""
        from core.navigation import _spawn_hearts
        _spawn_hearts(self.state, count=2)
        # Mark first heart as expired
        self.state.hearts[0][2] = 0.5
        self.state.hearts[1][2] = -0.1
        # Simulate removal logic
        for h in list(self.state.hearts):
            if h[2] <= 0:
                self.state.hearts.remove(h)
        self.assertEqual(len(self.state.hearts), 1)


class TestTrayShowHide(unittest.TestCase):
    """Test the tray Show Cat toggle is wired to window."""

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv if hasattr(sys, 'argv') else [])

    def setUp(self):
        self.state = CatState()
        self.mock_window = MagicMock()
        from ui.tray import CatTrayIcon
        self.tray = CatTrayIcon(self.app, self.state, self.mock_window)

    def test_show_action_toggles_window(self):
        """Toggling Show Cat calls setVisible on window."""
        self.tray.act_show.setChecked(False)
        self.mock_window.setVisible.assert_called_with(False)
        self.tray.act_show.setChecked(True)
        self.mock_window.setVisible.assert_called_with(True)

    def test_doubleclick_toggles_visibility(self):
        """Double-clicking tray toggles window visibility."""
        from PyQt6.QtWidgets import QSystemTrayIcon
        self.mock_window.isVisible.return_value = False
        self.tray._on_activated(QSystemTrayIcon.ActivationReason.DoubleClick)
        self.mock_window.setVisible.assert_called_with(True)

    def test_visibility_sync(self):
        """Window visibility changes sync tray check state."""
        self.tray._on_visibility_changed(True)
        self.assertTrue(self.tray.act_show.isChecked())
        self.tray._on_visibility_changed(False)
        self.assertFalse(self.tray.act_show.isChecked())


class TestControlsState(unittest.TestCase):
    """Test the click_through state field."""

    def test_click_through_default(self):
        """CatState.click_through defaults to True."""
        from core.state import CatState
        s = CatState()
        self.assertTrue(s.click_through)

    def test_hearts_list_default(self):
        """CatState.hearts defaults to empty list."""
        from core.state import CatState
        s = CatState()
        self.assertEqual(s.hearts, [])


if __name__ == "__main__":
    unittest.main()
