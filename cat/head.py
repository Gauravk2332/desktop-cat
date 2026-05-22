"""
cat/head.py — Head circle, ears, nose, and whiskers.
"""

import math
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QBrush

import config
from config import flip_x


def draw_head(painter: QPainter, cx: float, cy: float, state,
              head_y: float, scale: float = 1.0, coat_index: int = 0) -> None:
    """Draw the head circle."""
    coat = config.get_coat(coat_index)
    r = config.HEAD_R * scale
    path = QPainterPath()
    path.addEllipse(int(cx - r), int(head_y - r), int(r * 2), int(r * 2))
    painter.fillPath(path, coat.body)


def draw_ears(painter: QPainter, cx: float, cy: float, state,
              head_y: float, scale: float = 1.0, coat_index: int = 0) -> None:
    """Draw both ears with inner pink fill."""
    coat = config.get_coat(coat_index)
    ew = config.EAR_W * scale
    eh = config.EAR_H * scale
    eo = config.EAR_OFFSET * scale

    for side in (-1, 1):
        bx = int(cx + flip_x(side * eo, state.facing))
        tx = int(cx + flip_x(side * (eo + 4 * scale), state.facing))

        # Outer ear
        ear = QPainterPath()
        ear.moveTo(bx, int(head_y - 2 * scale))
        ear.lineTo(tx, int(head_y - eh - 2 * scale))
        ear.lineTo(int(cx + flip_x(side * (eo - 4 * scale), state.facing)),
                    int(head_y - 8 * scale))
        ear.closeSubpath()
        painter.fillPath(ear, coat.body)

        # Inner ear (pink)
        ibx = int(cx + flip_x(side * (eo - 1 * scale), state.facing))
        itx = int(cx + flip_x(side * (eo + 2 * scale), state.facing))
        inner = QPainterPath()
        inner.moveTo(ibx, int(head_y - 4 * scale))
        inner.lineTo(itx, int(head_y - eh + 2 * scale))
        inner.lineTo(int(cx + flip_x(side * (eo - 3 * scale), state.facing)),
                      int(head_y - 9 * scale))
        inner.closeSubpath()
        painter.fillPath(inner, coat.ear_inner)


def draw_nose(painter: QPainter, cx: float, head_y: float, state,
              coat_index: int = 0) -> None:
    """Tiny triangular nose."""
    coat = config.get_coat(coat_index)
    path = QPainterPath()
    path.moveTo(int(cx + flip_x(0, state.facing)), int(head_y + 6))
    path.lineTo(int(cx + flip_x(-3, state.facing)), int(head_y + 3))
    path.lineTo(int(cx + flip_x(3, state.facing)), int(head_y + 3))
    path.closeSubpath()
    painter.fillPath(path, coat.nose)


def draw_whiskers(painter: QPainter, cx: float, head_y: float, state,
                  coat_index: int = 0) -> None:
    """Three whiskers per side."""
    coat = config.get_coat(coat_index)
    for side in (-1, 1):
        for i, dy in enumerate((-1, 1, 3)):
            path = QPainterPath()
            sx = int(cx + flip_x(side * 6, state.facing))
            sy = int(head_y + 3 + dy)
            ex = int(cx + flip_x(side * (6 + config.WHISKER_LEN), state.facing))
            ey = int(sy + side * (2 + i * 2))
            path.moveTo(sx, sy)
            path.lineTo(ex, ey)
            painter.strokePath(path, QPen(coat.whisker, 1.2))
