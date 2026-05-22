"""
core/window.py — Frameless full-screen transparent overlay.

One window covering the entire screen. Bed drawn at fixed bottom-right
position. Cat drawn at its current screen coordinates.
WA_TransparentForMouseEvents so it's click-through.
"""

import logging
import math
import sys
import time

# Guarded ctypes import for Windows DWM border fix
if sys.platform == "win32":
    import ctypes

logging.basicConfig(level=logging.WARNING)

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QFont

import config
from core.state import CatState
from cat import body, tail, legs, head, eyes
from cat.home import draw_hut_frame, draw_hut_front, draw_sleeping_cat


class CatWindow(QWidget):
    """Full-screen transparent overlay — the cat lives here."""

    def __init__(self, state: CatState):
        super().__init__()
        self.state = state
        self.setWindowTitle("Cat")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self._position_window()

    # ── DWM Border Fix (Windows 11) ────────────────────────────────────

    def _remove_dwm_border(self):
        """Remove forced border and rounded corners on Windows 11.
        Safe no-op on non-Windows platforms."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            dwmapi = ctypes.windll.dwmapi
            # Remove forced border
            DWMWA_BORDER_COLOR = 34
            DWMWA_COLOR_NONE = 0xFFFFFFFE
            color = ctypes.c_uint32(DWMWA_COLOR_NONE)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR,
                ctypes.byref(color), ctypes.sizeof(color))
            # Disable rounded corners
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_DONOTROUND = 1
            pref = ctypes.c_int(DWMWCP_DONOTROUND)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(pref), ctypes.sizeof(pref))
        except Exception as e:
            logging.warning("DWM border fix failed: %s", e)

    def _position_window(self):
        """Resize to full screen and set initial cat position."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.state.screen_width = geo.width()
        self.state.screen_height = geo.height()
        self.setFixedSize(geo.width(), geo.height())
        self.move(0, 0)

        # Cat starts at bottom-center of screen
        self.state.cat_x = float(geo.width() // 2)
        self.state.cat_y = float(geo.height() - config.CAT_BASELINE)

    # ── Draw pipeline ───────────────────────────────────────────────────

    def paintEvent(self, event):
        """Orchestrate the draw pipeline in fixed z-order."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Cat screen center
            cx = self.state.cat_x
            cy = self.state.cat_y

            # Purr vibration offsets
            if self.state.purr_vibrate > 0:
                vib = math.sin(time.monotonic() * 40) * self.state.purr_vibrate * 0.5
                cx += vib
                cy += vib

            # Deep sleep dimming
            if self.state.state == config.STATE_SLEEP and self.state.deep_sleep:
                painter.setOpacity(0.6)

            # 1. Draw hut base + interior (always, replaces old bed)
            draw_hut_frame(painter, self.state)

            # 2. Draw cat inside hut if sleeping at home
            if self.state.state == config.STATE_SLEEP and self.state.at_home:
                draw_sleeping_cat(painter, self.state)

            # 3. Draw hut front (roof, walls overlaying cat)
            draw_hut_front(painter, self.state)

            # Dispatch by state (field sleep, walk, sit)
            if self.state.state == config.STATE_SLEEP:
                if not self.state.at_home:
                    # Field sleep — drawn by window
                    self._draw_sleep(painter, cx, cy)
            elif self.state.state == config.STATE_WALK or self.state.state == config.STATE_WANDER:
                self._draw_walk(painter, cx, cy)
            else:  # STATE_SIT
                self._draw_sit(painter, cx, cy)

            painter.end()
        except Exception as e:
            if config.DEBUG:
                logging.exception("desktop-cat paintEvent failed: %s", e)

    # ── SIT pose ───────────────────────────────────────────────────

    def _draw_sit(self, painter, cx, cy):
        from animation.breathe import breath_value
        _, bbob = breath_value(self.state)

        head_y = int(cy - 55 + bbob)
        ear_scale = 1.15 if self.state.mouse_near else 1.0

        body.draw_shadow(painter, cx, cy, self.state)
        tail.draw_tail_sit(painter, cx, cy, self.state)
        body.draw_body_sit(painter, cx, cy, self.state)
        legs.draw_paws(painter, cx, cy, self.state)
        head.draw_head(painter, cx, cy, self.state, head_y)
        head.draw_ears(painter, cx, cy, self.state, head_y, ear_scale)
        eyes.draw_eyes(painter, cx, cy, head_y, self.state)

        if self.state.reaction_type == "meow":
            head.draw_nose(painter, cx, head_y, self.state)
            head.draw_whiskers(painter, cx, head_y, self.state)
        elif self.state.reaction_type == "purr":
            eyes.draw_happy_eyes(painter, cx, head_y, self.state)
            head.draw_nose(painter, cx, head_y, self.state)
            head.draw_whiskers(painter, cx, head_y, self.state)
        else:
            head.draw_nose(painter, cx, head_y, self.state)
            head.draw_whiskers(painter, cx, head_y, self.state)

    # ── WALK / WANDER pose ─────────────────────────────────────────

    def _draw_walk(self, painter, cx, cy):
        from animation.breathe import breath_value
        _, bbob = breath_value(self.state)
        head_y = int(cy - 52 + bbob)

        body.draw_shadow(painter, cx, cy, self.state)
        tail.draw_tail_walk(painter, cx, cy, self.state)
        body.draw_body_walk(painter, cx, cy, self.state)
        legs.draw_legs_walk(painter, cx, cy, self.state)
        head.draw_head(painter, cx, cy, self.state, head_y, 0.95)
        head.draw_ears(painter, cx, cy, self.state, head_y, 0.95)
        eyes.draw_eyes(painter, cx, cy, head_y, self.state)
        head.draw_nose(painter, cx, head_y, self.state)
        head.draw_whiskers(painter, cx, head_y, self.state)

    # ── FIELD SLEEP pose (cat sleeps anywhere on screen) ───────────

    def _draw_sleep(self, painter, cx, cy):
        breath = math.sin(self.state.sleep_breath) * 0.02 + 1.0
        painter.save()
        painter.translate(cx, cy)
        painter.scale(breath, breath)
        painter.translate(-cx, -cy)

        base_r = 22 if not self.state.deep_sleep else 16
        base_y = int(cy - 10)

        # Shadow
        sh = QPainterPath()
        sh.addEllipse(int(cx - base_r + 2), int(base_y + 2),
                       int(base_r * 2 - 4), 10)
        painter.fillPath(sh, QColor(0, 0, 0, 25))

        # Curled body
        curl = QPainterPath()
        curl.addEllipse(int(cx - base_r), int(base_y - base_r),
                        int(base_r * 2), int(base_r * 2))
        painter.fillPath(curl, config.C_BODY)

        # Inner curl (belly)
        inner = QPainterPath()
        inner.addEllipse(
            int(cx - base_r * 0.5),
            int(base_y - base_r * 0.4),
            int(base_r * 1.0),
            int(base_r * 0.8),
        )
        painter.fillPath(inner, config.C_BELLY)

        # Ear poking out
        ear = QPainterPath()
        ex = int(cx + config.flip_x(base_r * 0.85, self.state.facing))
        ey = int(base_y - base_r * 0.4)
        ear.moveTo(ex, ey)
        ear.lineTo(int(cx + config.flip_x(base_r * 1.15, self.state.facing)),
                    int(ey - 12))
        ear.lineTo(int(cx + config.flip_x(base_r * 0.6, self.state.facing)),
                    int(ey - 4))
        ear.closeSubpath()
        painter.fillPath(ear, config.C_BODY)

        # Closed eye
        nlx = int(cx + config.flip_x(base_r * 0.2, self.state.facing))
        nly = int(base_y - base_r * 0.1)
        sleep_eye = QPainterPath()
        sleep_eye.moveTo(nlx - 3, nly)
        sleep_eye.cubicTo(nlx - 1, nly + 1, nlx + 1, nly + 1, nlx + 3, nly)
        painter.strokePath(sleep_eye, QPen(config.C_CLOSED_EYE, 1.5))

        # Nose dot
        n2 = QPainterPath()
        nlx2 = int(cx + config.flip_x(2, self.state.facing))
        nly2 = int(base_y - base_r * 0.1 + 2)
        n2.addEllipse(nlx2 - 1, nly2 - 1, 3, 2)
        painter.fillPath(n2, config.C_NOSE)

        # Tail curled around
        tail.draw_tail_sleep(painter, cx, cy, self.state, base_r, base_y)

        # Zzz particles
        for p in self.state.zzz_particles:
            z = QPainterPath()
            zx = int(cx + config.flip_x(p[0], self.state.facing))
            zy = int(base_y - base_r + p[1] - 10)
            zsize = int(6 + p[3] * 2)
            z.addText(zx, zy, QFont("Arial", zsize), "z")
            painter.fillPath(z, config.C_ZZZ)

        painter.restore()
