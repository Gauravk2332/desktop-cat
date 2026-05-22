"""core/controls.py — Keyboard shortcuts and interaction controls."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

import config


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

    def handle_key(self, key, modifiers=Qt.KeyboardModifier.NoModifier) -> bool:
        """Handle a key press. Returns True if handled."""
        # ── Ctrl+F: feed cycle ──────────────────────────────────────
        if key == Qt.Key.Key_F and (modifiers & Qt.KeyboardModifier.ControlModifier):
            self._feed_cycle()
            return True

        # ── Plain key shortcuts ─────────────────────────────────────
        if key == Qt.Key.Key_Escape:
            self.window.setVisible(not self.window.isVisible())
            return True
        elif key == Qt.Key.Key_C:
            # Ctrl+Shift+C: toggle click-through (plain C was the original)
            self.toggle_click_through()
            return True
        elif key == Qt.Key.Key_H:
            self.window.setVisible(not self.window.isVisible())
            return True
        elif key == Qt.Key.Key_R:
            self.state.cat_x = float(self.state.screen_width // 2)
            self.state.cat_y = float(self.state.screen_height - 20)
            self.state.state = "SIT"
            return True
        return False

    def _feed_cycle(self):
        """Cycle through food options and feed the cat."""
        s = self.state
        foods = ["fish", "treat", "milk"]
        s.feed_cycle_index = (s.feed_cycle_index + 1) % 3
        food = foods[s.feed_cycle_index]

        reduction_mapping = {"fish": 40, "treat": 20, "milk": 25}
        reduction = reduction_mapping.get(food, config.FEED_HUNGER_REDUCTION)
        s.hunger = max(0.0, s.hunger - reduction)

        # Trigger happy speech via engine
        if s.speech_cooldown <= 0:
            self.engine._trigger_speech("happy")
            s.speech_cooldown = 3.0

        # Spawn hearts
        from core.navigation import _spawn_hearts
        _spawn_hearts(s, count=3)
