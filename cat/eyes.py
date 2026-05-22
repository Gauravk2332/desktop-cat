"""
cat/eyes.py — Eye drawing with blink, pupil tracking, and happy-eyes arcs.
"""

import math
from PyQt6.QtGui import QPainter, QPainterPath, QPen

import config
from config import flip_x


def draw_eyes(painter: QPainter, cx: float, cy: float, head_y: float,
              state) -> None:
    """Main eye drawing — handles blink vs. open eyes with pupil tracking."""
    if state.blinking:
        _draw_blink_eyes(painter, cx, head_y, state)
    else:
        _draw_open_eyes(painter, cx, head_y, state)


def _draw_blink_eyes(painter: QPainter, cx: float, head_y: float,
                     state) -> None:
    """Closed eyes drawn as upward arcs."""
    for side in (-1, 1):
        ex = int(cx + flip_x(side * 6, state.facing))
        ey = int(head_y)
        path = QPainterPath()
        path.moveTo(ex - 4, ey)
        path.cubicTo(ex - 2, ey + 2, ex + 2, ey + 2, ex + 4, ey)
        painter.strokePath(path, QPen(config.C_CLOSED_EYE, 2))


def _draw_open_eyes(painter: QPainter, cx: float, head_y: float,
                    state) -> None:
    """Open eyes with sclera, pupil, and mouse tracking."""
    for side in (-1, 1):
        ex = int(cx + flip_x(side * 6, state.facing))
        ey = int(head_y)

        # Sclera (white)
        sc = QPainterPath()
        sc.addEllipse(ex - config.EYE_R, ey - config.EYE_R,
                       config.EYE_R * 2, config.EYE_R * 2)
        painter.fillPath(sc, config.C_EYE_WHITE)

        # Pupil with tracking offset
        px, py = state.eye_current
        if not state.facing:
            px = -px
        pp = QPainterPath()
        pp.addEllipse(
            int(ex + px - config.PUPIL_R),
            int(ey + py - config.PUPIL_R * 1.2),
            int(config.PUPIL_R * 2),
            int(config.PUPIL_R * 2.4),
        )
        painter.fillPath(pp, config.C_PUPIL)


def draw_happy_eyes(painter: QPainter, cx: float, head_y: float,
                    state) -> None:
    """Happy closed-eye arcs (inverted U shape)."""
    for side in (-1, 1):
        ex = int(cx + flip_x(side * 6, state.facing))
        ey = int(head_y)
        path = QPainterPath()
        path.moveTo(ex - 3, ey)
        path.cubicTo(ex - 2, ey - 2, ex + 2, ey - 2, ex + 3, ey)
        painter.strokePath(path, QPen(config.C_PUPIL, 2))
