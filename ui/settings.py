"""ui/settings.py — Skinned settings dialog for desktop-cat.

Provides:
- Coat color palette picker (radio buttons with color swatches)
- Sound on/off toggle
- Autostart on/off toggle (Windows registry)
- Minimal dark warm theme
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QRadioButton, QCheckBox, QPushButton, QGroupBox,
    QWidget, QButtonGroup, QApplication
)
from PyQt6.QtGui import QColor, QPixmap, QPainter, QFont
from PyQt6.QtCore import Qt, QSize

logger = logging.getLogger(__name__)

SETTINGS_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Nova", "desktop-cat"
)
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")

COATS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "coats.json"
)

DEFAULT_SETTINGS = {
    "coat": "russian_blue",
    "sound_enabled": True,
    "autostart": False,
}


@dataclass
class AppSettings:
    """Serializable application settings."""
    coat: str = "russian_blue"
    sound_enabled: bool = True
    autostart: bool = False

    def save(self, path: str = SETTINGS_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str = SETTINGS_PATH) -> "AppSettings":
        try:
            with open(path) as f:
                data = json.load(f)
            return cls(**{k: data.get(k, v) for k, v in DEFAULT_SETTINGS.items()})
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()


def _color_swatch_pixmap(color_hex: str, size: int = 24) -> QPixmap:
    """Generate a small colored square pixmap for radio button decoration."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor(color_hex)
    painter.setBrush(color)
    painter.setPen(QColor(0x80, 0x80, 0x80, 0x80))
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 3, 3)
    painter.end()
    return pix


class SettingsDialog(QDialog):
    """Settings dialog for desktop-cat. Dark warm theme, compact layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = AppSettings.load()
        self._coats = self._load_coats()
        self._changed = False

        self.setWindowTitle("Desktop Cat Settings")
        self.setFixedSize(420, 380)
        self._apply_theme()
        self._build_ui()
        self._load_state()

    def _apply_theme(self):
        """Dark warm theme."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2C2C2C;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #4A4A4A;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
                font-size: 13px;
                font-weight: bold;
                color: #D4A574;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QRadioButton {
                color: #D0D0D0;
                font-size: 12px;
                spacing: 8px;
                padding: 3px 0;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #666;
            }
            QRadioButton::indicator:checked {
                background-color: #D4A574;
                border-color: #D4A574;
            }
            QCheckBox {
                color: #D0D0D0;
                font-size: 12px;
                spacing: 8px;
                padding: 3px 0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #666;
            }
            QCheckBox::indicator:checked {
                background-color: #D4A574;
                border-color: #D4A574;
            }
            QPushButton {
                background-color: #4A4A4A;
                color: #E0E0E0;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
                border-color: #D4A574;
            }
            QPushButton:pressed {
                background-color: #3A3A3A;
            }
            QPushButton#applyBtn {
                background-color: #B87A4A;
                color: #1A1A1A;
                font-weight: bold;
                border: none;
            }
            QPushButton#applyBtn:hover {
                background-color: #D4A574;
            }
        """)

    def _load_coats(self) -> dict:
        """Load coat palettes from coats.json."""
        try:
            with open(COATS_PATH) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning("Failed to load coats.json: %s", e)
            return {}

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # ── Coat Color Group ──
        coat_group = QGroupBox("Coat Color")
        coat_layout = QVBoxLayout(coat_group)
        self._coat_group = QButtonGroup(self)

        for name, palette in self._coats.items():
            row = QHBoxLayout()
            row.setSpacing(10)

            # Color swatch
            swatch = QLabel()
            body_color = palette.get("body", "#888888")
            swatch.setPixmap(_color_swatch_pixmap(body_color, 20))
            swatch.setFixedSize(24, 24)
            row.addWidget(swatch)

            # Radio button
            display_name = name.replace("_", " ").title()
            rb = QRadioButton(display_name)
            rb.setProperty("coat_name", name)
            self._coat_group.addButton(rb)
            row.addWidget(rb)
            row.addStretch()
            coat_layout.addLayout(row)

        layout.addWidget(coat_group)

        # ── Options Group ──
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self._sound_cb = QCheckBox("Sound Effects")
        options_layout.addWidget(self._sound_cb)

        self._autostart_cb = QCheckBox("Start with Windows")
        options_layout.addWidget(self._autostart_cb)

        layout.addWidget(options_group)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("applyBtn")
        apply_btn.clicked.connect(self._apply)
        btn_row.addWidget(apply_btn)

        layout.addStretch()
        layout.addLayout(btn_row)

    def _load_state(self):
        """Populate UI from current settings."""
        # Coat selection
        for btn in self._coat_group.buttons():
            if btn.property("coat_name") == self.settings.coat:
                btn.setChecked(True)
                break
        if not self._coat_group.checkedButton():
            # Fallback: select first
            btns = self._coat_group.buttons()
            if btns:
                btns[0].setChecked(True)

        # Checkboxes
        self._sound_cb.setChecked(self.settings.sound_enabled)
        self._autostart_cb.setChecked(self._check_autostart_registered())

    def _check_autostart_registered(self) -> bool:
        """Check if currently registered for autostart."""
        try:
            from launcher.autostart import is_registered
            return is_registered()
        except ImportError:
            return self.settings.autostart

    def _apply(self):
        """Save settings and close."""
        selected = self._coat_group.checkedButton()
        if selected:
            self.settings.coat = selected.property("coat_name")

        self.settings.sound_enabled = self._sound_cb.isChecked()

        # Handle autostart change
        new_autostart = self._autostart_cb.isChecked()
        if new_autostart != self.settings.autostart:
            try:
                from launcher.autostart import register, unregister, is_registered
                currently = is_registered()
                if new_autostart and not currently:
                    register()
                elif not new_autostart and currently:
                    unregister()
            except ImportError:
                pass
        self.settings.autostart = new_autostart

        self.settings.save()
        self._changed = True
        self.accept()

    @property
    def changed(self) -> bool:
        return self._changed

    @property
    def selected_coat(self) -> str:
        return self.settings.coat

    @staticmethod
    def open(parent=None) -> Optional["AppSettings"]:
        """Open settings dialog and return updated settings, or None if cancelled."""
        dlg = SettingsDialog(parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.settings
        return None
