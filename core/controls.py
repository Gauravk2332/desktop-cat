"""core/controls.py — Keyboard shortcuts and interaction controls."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget


class Controls:
    """Handles keyboard shortcuts for the cat overlay."""

    def __init__(self, window: QWidget, state, engine):
        self.window = window
        self.state = state
        self.engine = engine

    def toggle_click_through(self):
        """Toggle whether mouse events pass through the overlay."""
        self.state.click_through = not self.state.click_through
        self.window.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            self.state.click_through
        )

    def handle_key(self, key) -> bool:
        """Handle a key press. Returns True if handled."""
        if key == Qt.Key.Key_Escape:
            # Show/hide toggle
            self.window.setVisible(not self.window.isVisible())
            return True
        elif key == Qt.Key.Key_C:
            # Ctrl+Shift+C: toggle click-through
            self.toggle_click_through()
            return True
        elif key == Qt.Key.Key_H:
            # H: toggle cat visibility
            self.window.setVisible(not self.window.isVisible())
            return True
        elif key == Qt.Key.Key_R:
            # R: reset cat position
            self.state.cat_x = float(self.state.screen_width // 2)
            self.state.cat_y = float(self.state.screen_height - 20)
            self.state.state = "SIT"
            return True
        return False
