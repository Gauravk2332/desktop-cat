"""
core/window.py — Frameless full-screen transparent overlay.

One window covering the entire screen. Each cat has its own hut positioned
left-to-right from the right edge. Cats are drawn in order (z-order follows
cats list order — last cat in list is visually top).

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
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QFont

import config
from core.state import CatState, CatProxy
from cat import body as cat_body, tail, legs, head, eyes
from cat.stripes import draw_coat_pattern
from cat.home import (
    draw_hut_frame, draw_hut_front, draw_sleeping_cat,
    draw_cat_hearts, draw_speech_bubble_for_cat,
)
from core.controls import Controls


class CatWindow(QWidget):
    """Full-screen transparent overlay — the cats live here."""

    visibility_changed = pyqtSignal(bool)

    def showEvent(self, event):
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def __init__(self, state: CatState, engine=None):
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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._position_window()

        # Keyboard controls
        self.controls = Controls(self, state, engine)

    # ── DWM Border Fix (Windows 11) ────────────────────────────────────

    def _remove_dwm_border(self):
        """Remove forced border and rounded corners on Windows 11."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            dwmapi = ctypes.windll.dwmapi
            DWMWA_BORDER_COLOR = 34
            DWMWA_COLOR_NONE = 0xFFFFFFFE
            color = ctypes.c_uint32(DWMWA_COLOR_NONE)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR,
                ctypes.byref(color), ctypes.sizeof(color))
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_DONOTROUND = 1
            pref = ctypes.c_int(DWMWCP_DONOTROUND)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(pref), ctypes.sizeof(pref))
        except Exception as e:
            logging.warning("DWM border fix failed: %s", e)

    def _position_window(self):
        """Resize to full screen and set initial cat positions."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.state.screen_width = geo.width()
        self.state.screen_height = geo.height()
        self.setFixedSize(geo.width(), geo.height())
        self.move(0, 0)

    # ── Keyboard ─────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        """Handle key presses via the Controls delegate."""
        self.controls.handle_key(event.key(), event.modifiers())

    def _draw_interact_indicator(self, painter):
        """Draw subtle indicator bar when click-through is disabled."""
        w = self.state.screen_width
        bar_w = 120
        bar_h = 22
        bar_x = w // 2 - bar_w // 2
        bar_y = 4

        bar = QPainterPath()
        bar.addRoundedRect(bar_x, bar_y, bar_w, bar_h, 8, 8)
        painter.fillPath(bar, QColor(0, 0, 0, 100))

        painter.setPen(QColor(255, 255, 255, 200))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(bar_x, bar_y, bar_w, bar_h,
                         Qt.AlignmentFlag.AlignCenter, "🎯 Interact")

    # ── Draw pipeline ───────────────────────────────────────────────────

    def paintEvent(self, event):
        """Orchestrate the draw pipeline in fixed z-order.

        For each cat:
          1. Draw its hut frame (interior behind cat)
          2. Draw sleeping cat inside hut (if at home)
          3. Draw hut front (roof overlays cat)
          4. Draw the cat
          5. Draw hearts
          6. Draw speech bubble
        """
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw all huts (back layer — one hut per cat)
            for cat in self.state.cats:
                hut_idx = cat.get("hut_index", 0)
                try:
                    draw_hut_frame(painter, self.state, hut_idx)
                except Exception as e:
                    logging.debug("draw_hut_frame failed: %s", e)

            # Draw cats and their foreground elements
            for cat in self.state.cats:
                # Wrap cat dict in CatProxy for attribute access in draw funcs
                proxy = CatProxy(cat)
                cx = cat["x"]
                cy = cat["y"]
                hut_idx = cat.get("hut_index", 0)
                state_str = cat["state"]
                at_home = cat.get("at_home", False)
                facing = cat.get("facing", True)

                # Purr vibration offsets
                purr_vibrate = cat.get("purr_vibrate", 0.0)
                if purr_vibrate > 0:
                    vib = math.sin(time.monotonic() * 40) * purr_vibrate * 0.5
                    cx += vib
                    cy += vib

                # Deep sleep dimming
                if state_str == config.STATE_SLEEP and cat.get("deep_sleep"):
                    painter.setOpacity(0.6)

                # Draw sleeping cat inside hut if at home
                try:
                    if state_str == config.STATE_SLEEP and at_home:
                        draw_sleeping_cat(painter, self.state, hut_idx)
                except Exception as e:
                    logging.debug("draw_sleeping_cat failed: %s", e)

                # Draw hut front (roof, walls overlaying cat)
                try:
                    draw_hut_front(painter, self.state, hut_idx)
                except Exception as e:
                    logging.debug("draw_hut_front failed: %s", e)

                # Dispatch by state — pass proxy for drawing functions
                try:
                    if state_str == config.STATE_SLEEP:
                        if not at_home:
                            self._draw_sleep(painter, cx, cy, proxy)
                    elif state_str in (config.STATE_WALK, config.STATE_WANDER,
                                       config.STATE_CHASE, config.STATE_PLAY):
                        self._draw_walk(painter, cx, cy, proxy)
                    else:
                        self._draw_sit(painter, cx, cy, proxy)
                except Exception as e:
                    logging.debug("cat pose draw failed: %s", e)

                # Reset opacity
                painter.setOpacity(1.0)

                # Draw floating hearts (per cat)
                try:
                    draw_cat_hearts(painter, cat)
                except Exception as e:
                    logging.debug("draw_cat_hearts failed: %s", e)

                # Draw speech bubble (per cat)
                try:
                    draw_speech_bubble_for_cat(painter, cat, self.state)
                except Exception as e:
                    logging.debug("draw_speech_bubble failed: %s", e)

            # Draw interactive toy (shared)
            try:
                self._draw_toys(painter)
            except Exception as e:
                logging.debug("_draw_toys failed: %s", e)

            # Interact mode indicator
            try:
                if not self.state.click_through:
                    self._draw_interact_indicator(painter)
            except Exception as e:
                logging.debug("_draw_interact_indicator failed: %s", e)

            painter.end()
        except Exception as e:
            if config.DEBUG:
                logging.exception("desktop-cat paintEvent failed: %s", e)

    # ── SIT pose ───────────────────────────────────────────────────

    def _draw_sit(self, painter, cx, cy, wrapped):
        """Draw sitting cat using a CatProxy wrapper for attribute access."""
        try:
            from animation.breathe import breath_value
            _, bbob = breath_value(wrapped)

            coat_index = getattr(wrapped, 'coat', 0)
            head_y = int(cy - 55 + bbob)
            ear_scale = 1.15 if wrapped.mouse_near else 1.0

            cat_body.draw_shadow(painter, cx, cy, wrapped, coat_index)
            tail.draw_tail_sit(painter, cx, cy, wrapped, coat_index)
            cat_body.draw_body_sit(painter, cx, cy, wrapped, coat_index)
            legs.draw_paws(painter, cx, cy, wrapped, coat_index)
            # Draw coat pattern (stripes, tuxedo patch, etc.) over body
            draw_coat_pattern(painter, cx, cy, wrapped, coat_index)
            head.draw_head(painter, cx, cy, wrapped, head_y, 1.0, coat_index)
            head.draw_ears(painter, cx, cy, wrapped, head_y, ear_scale, coat_index)
            eyes.draw_eyes(painter, cx, cy, head_y, wrapped, coat_index)

            if wrapped.reaction_type == "meow":
                head.draw_nose(painter, cx, head_y, wrapped, coat_index)
                head.draw_whiskers(painter, cx, head_y, wrapped, coat_index)
            elif wrapped.reaction_type == "purr":
                eyes.draw_happy_eyes(painter, cx, head_y, wrapped, coat_index)
                head.draw_nose(painter, cx, head_y, wrapped, coat_index)
                head.draw_whiskers(painter, cx, head_y, wrapped, coat_index)
            else:
                head.draw_nose(painter, cx, head_y, wrapped, coat_index)
                head.draw_whiskers(painter, cx, head_y, wrapped, coat_index)
        except Exception as e:
            logging.debug("_draw_sit failed: %s", e)

    # ── WALK / WANDER pose ─────────────────────────────────────────

    def _draw_walk(self, painter, cx, cy, wrapped):
        """Draw walking cat using a CatProxy wrapper.

        Features:
        - 4-leg articulated gait
        - Body bob synchronized with gait (vertical oscillation ±2px)
        - Body tilt synchronized with gait (rotation ±2°)
        - Tail sway synchronized with gait
        - Coat pattern (stripes) drawn over body
        """
        try:
            from animation.breathe import breath_value
            _, bbob = breath_value(wrapped)

            coat_index = getattr(wrapped, 'coat', 0)
            walk_frame = getattr(wrapped, 'walk_frame', 0) % 8

            # Body bob and tilt from gait tables
            bob = legs.GAIT_BODY_BOB[walk_frame]
            tilt = legs.GAIT_BODY_TILT[walk_frame]

            head_y = int(cy - 52 + bbob + bob)

            # Shadow stays at ground level (no bob/tilt)
            cat_body.draw_shadow(painter, cx, cy, wrapped, coat_index)

            painter.save()
            painter.translate(0, bob)
            painter.rotate(tilt)

            tail.draw_tail_walk(painter, cx, cy, wrapped, coat_index)
            cat_body.draw_body_walk(painter, cx, cy, wrapped, coat_index)
            # Draw coat pattern over body before legs/head
            draw_coat_pattern(painter, cx, cy, wrapped, coat_index)
            legs.draw_legs_walk(painter, cx, cy, wrapped, coat_index)
            head.draw_head(painter, cx, cy, wrapped, head_y, 0.95, coat_index)
            head.draw_ears(painter, cx, cy, wrapped, head_y, 0.95, coat_index)
            eyes.draw_eyes(painter, cx, cy, head_y, wrapped, coat_index)
            head.draw_nose(painter, cx, head_y, wrapped, coat_index)
            head.draw_whiskers(painter, cx, head_y, wrapped, coat_index)

            painter.restore()
        except Exception as e:
            logging.debug("_draw_walk failed: %s", e)

    # ── FIELD SLEEP pose ──────────────────────────────────────────

    def _draw_sleep(self, painter, cx, cy, wrapped):
        """Draw field sleep cat using a CatProxy wrapper."""
        try:
            breath = math.sin(wrapped.sleep_breath) * 0.02 + 1.0
            painter.save()
            painter.translate(cx, cy)
            painter.scale(breath, breath)
            painter.translate(-cx, -cy)

            coat_index = getattr(wrapped, 'coat', 0)
            coat = config.get_coat(coat_index)

            base_r = 22 if not wrapped.deep_sleep else 16
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
            painter.fillPath(curl, coat.body)

            # Inner curl
            inner = QPainterPath()
            inner.addEllipse(
                int(cx - base_r * 0.5),
                int(base_y - base_r * 0.4),
                int(base_r * 1.0),
                int(base_r * 0.8),
            )
            painter.fillPath(inner, coat.belly)

            # Ear poking out
            facing = wrapped.facing
            ear = QPainterPath()
            ex = int(cx + config.flip_x(base_r * 0.85, facing))
            ey = int(base_y - base_r * 0.4)
            ear.moveTo(ex, ey)
            ear.lineTo(int(cx + config.flip_x(base_r * 1.15, facing)),
                        int(ey - 12))
            ear.lineTo(int(cx + config.flip_x(base_r * 0.6, facing)),
                        int(ey - 4))
            ear.closeSubpath()
            painter.fillPath(ear, coat.body)

            # Closed eye
            nlx = int(cx + config.flip_x(base_r * 0.2, facing))
            nly = int(base_y - base_r * 0.1)
            sleep_eye = QPainterPath()
            sleep_eye.moveTo(nlx - 3, nly)
            sleep_eye.cubicTo(nlx - 1, nly + 1, nlx + 1, nly + 1, nlx + 3, nly)
            painter.strokePath(sleep_eye, QPen(config.C_CLOSED_EYE, 1.5))

            # Nose
            n2 = QPainterPath()
            nlx2 = int(cx + config.flip_x(2, facing))
            nly2 = int(base_y - base_r * 0.1 + 2)
            n2.addEllipse(nlx2 - 1, nly2 - 1, 3, 2)
            painter.fillPath(n2, coat.nose)

            # Tail curled
            tail.draw_tail_sleep(painter, cx, cy, wrapped, base_r, base_y, coat_index)

            # Zzz particles
            for p in wrapped.zzz_particles:
                z = QPainterPath()
                zx = int(cx + config.flip_x(p[0], facing))
                zy = int(base_y - base_r + p[1] - 10)
                zsize = int(6 + p[3] * 2)
                z.addText(zx, zy, QFont("Arial", zsize), "z")
                painter.fillPath(z, config.C_ZZZ)

            painter.restore()
        except Exception as e:
            logging.debug("_draw_sleep failed: %s", e)

    # ── Toy drawing (laser dot / yarn ball) ──────────────────────

    def _draw_toys(self, painter):
        """Draw the laser pointer dot or yarn ball toy."""
        try:
            s = self.state
            if not s.toy_active or s.toy_target is None:
                return

            tx, ty = s.toy_target

            if s.toy_type == "laser":
                painter.setBrush(QColor(255, 60, 60, 220))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(tx - 3), int(ty - 3), 6, 6)
                painter.setBrush(QColor(255, 60, 60, 40))
                painter.drawEllipse(int(tx - 6), int(ty - 6), 12, 12)

            elif s.toy_type == "ball":
                alpha = 220
                painter.setBrush(QColor(255, 120, 180, alpha))
                painter.setPen(QPen(QColor(200, 80, 140, alpha), 1.5))
                painter.drawEllipse(int(tx - 8), int(ty - 8), 16, 16)
                painter.setBrush(QColor(255, 180, 210, 120))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(tx - 3), int(ty - 3), 6, 6)
        except Exception as e:
            logging.debug("_draw_toys failed: %s", e)
