"""core/controls.py — Keyboard shortcuts and interaction controls.

Handles keyboard shortcuts including multi-cat focus (Ctrl+1/2/3).
"""

import random
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

    def focus_cat(self, index: int) -> None:
        """Bring cat[index] to center of screen. Others follow with offset."""
        cats = self.state.cats
        if index >= len(cats):
            return

        target = cats[index]
        target_x = self.state.screen_width / 2.0

        # This cat walks to center
        target["x"] = target_x
        target["state"] = config.STATE_SIT
        target["facing"] = True

        # Other cats follow with offset
        for i, other in enumerate(cats):
            if i == index:
                continue
            other_x = target_x + random.uniform(-40, 40)
            other_x = max(50.0, min(other_x, float(self.state.screen_width - 50)))
            other["x"] = other_x
            other["state"] = config.STATE_SIT

    def handle_key(self, key, modifiers=Qt.KeyboardModifier.NoModifier) -> bool:
        """Handle a key press. Returns True if handled."""
        # ── Ctrl+1/2/3: Focus cat ──────────────────────────────────
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_1:
                self.focus_cat(0)
                return True
            elif key == Qt.Key.Key_2:
                self.focus_cat(1)
                return True
            elif key == Qt.Key.Key_3:
                self.focus_cat(2)
                return True

        # ── Ctrl+F: feed cycle ──────────────────────────────────────
        if key == Qt.Key.Key_F and (modifiers & Qt.KeyboardModifier.ControlModifier):
            self._feed_cycle()
            return True

        # ── Plain key shortcuts ─────────────────────────────────────
        if key == Qt.Key.Key_Escape or key == Qt.Key.Key_H:
            self.window.setVisible(not self.window.isVisible())
            return True
        elif key == Qt.Key.Key_C:
            self.toggle_click_through()
            return True
        elif key == Qt.Key.Key_R:
            # Reset cat 0 to center (backward compat)
            if self.state.cats:
                self.state.cats[0]["x"] = float(self.state.screen_width // 2)
                self.state.cats[0]["y"] = float(self.state.screen_height - 20)
                self.state.cats[0]["state"] = "SIT"
            return True
        return False

    def _feed_cycle(self):
        """Cycle through food options and feed cat 0 (backward compat)."""
        s = self.state
        if not s.cats:
            return
        cat = s.cats[0]

        foods = ["fish", "treat", "milk"]
        s.feed_cycle_index = (s.feed_cycle_index + 1) % 3
        food = foods[s.feed_cycle_index]

        reduction_mapping = {"fish": 40, "treat": 20, "milk": 25}
        reduction = reduction_mapping.get(food, config.FEED_HUNGER_REDUCTION)
        cat["hunger"] = max(0.0, cat["hunger"] - reduction)

        # Trigger happy speech via engine
        if cat.get("speech_cooldown", 0) <= 0:
            self.engine._trigger_speech("happy", cat_idx=0)
            cat["speech_cooldown"] = 3.0

        # Spawn hearts
        from core.navigation import _spawn_hearts
        _spawn_hearts(s, count=3)
