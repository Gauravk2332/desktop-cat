"""
cat/body.py — Body silhouette, belly, and shadow drawing.

Pure draw functions. Stateless. Used by the draw pipeline.
"""

import math
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush

import config
from config import flip_x


def draw_shadow(painter: QPainter, cx: float, cy: float, state) -> None:
    """Soft ellipse shadow beneath the cat."""
    path = QPainterPath()
    path.addEllipse(int(cx - 18), int(cy - 6), 36, 10)
    painter.fillPath(path, QColor(0, 0, 0, 30))


def draw_body_sit(painter: QPainter, cx: float, cy: float, state) -> None:
    """Sitting body — pill-like rounded shape."""
    dx = flip_x(0, state.facing)

    body = QPainterPath()
    body.moveTo(int(cx + dx), int(cy - 5))
    body.cubicTo(
        int(cx + flip_x(18, state.facing)), int(cy - 5),
        int(cx + flip_x(22, state.facing)), int(cy - 15),
        int(cx + flip_x(22, state.facing)), int(cy - 25),
    )
    body.cubicTo(
        int(cx + flip_x(22, state.facing)), int(cy - 38),
        int(cx + flip_x(15, state.facing)), int(cy - 44),
        int(cx + dx), int(cy - 44),
    )
    body.cubicTo(
        int(cx + flip_x(-15, state.facing)), int(cy - 44),
        int(cx + flip_x(-22, state.facing)), int(cy - 38),
        int(cx + flip_x(-22, state.facing)), int(cy - 25),
    )
    body.cubicTo(
        int(cx + flip_x(-22, state.facing)), int(cy - 15),
        int(cx + flip_x(-18, state.facing)), int(cy - 5),
        int(cx + dx), int(cy - 5),
    )
    painter.fillPath(body, config.C_BODY)

    # Belly highlight
    belly = QPainterPath()
    belly.addEllipse(
        int(cx + flip_x(-6, state.facing)),
        int(cy - 32),
        12, 20,
    )
    painter.fillPath(belly, config.C_BELLY)


def draw_body_walk(painter: QPainter, cx: float, cy: float, state) -> None:
    """Walking body — slightly elongated."""
    dx = flip_x(0, state.facing)

    body = QPainterPath()
    body.moveTo(int(cx + dx), int(cy - 5))
    body.cubicTo(
        int(cx + flip_x(20, state.facing)), int(cy - 5),
        int(cx + flip_x(24, state.facing)), int(cy - 15),
        int(cx + flip_x(24, state.facing)), int(cy - 25),
    )
    body.cubicTo(
        int(cx + flip_x(24, state.facing)), int(cy - 38),
        int(cx + flip_x(16, state.facing)), int(cy - 44),
        int(cx + dx), int(cy - 44),
    )
    body.cubicTo(
        int(cx + flip_x(-16, state.facing)), int(cy - 44),
        int(cx + flip_x(-24, state.facing)), int(cy - 38),
        int(cx + flip_x(-24, state.facing)), int(cy - 25),
    )
    body.cubicTo(
        int(cx + flip_x(-24, state.facing)), int(cy - 15),
        int(cx + flip_x(-20, state.facing)), int(cy - 5),
        int(cx + dx), int(cy - 5),
    )
    painter.fillPath(body, config.C_BODY)

    # Belly
    belly = QPainterPath()
    belly.addEllipse(
        int(cx + flip_x(-6, state.facing)),
        int(cy - 30),
        12, 20,
    )
    painter.fillPath(belly, config.C_BELLY)
