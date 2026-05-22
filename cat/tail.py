"""
cat/tail.py — Tail drawing (sit swish, walk up, sleep curl).
"""

import math
from PyQt6.QtGui import QPainter, QPainterPath, QPen
from PyQt6.QtCore import Qt

import config
from config import flip_x


def draw_tail_sit(painter: QPainter, cx: float, cy: float, state,
                  coat_index: int = 0) -> None:
    """Sitting tail with sinusoidal swish."""
    coat = config.get_coat(coat_index)
    phase = state.tail_phase
    ts = math.sin(phase) * 12
    bx = int(cx + flip_x(-16, state.facing))
    by = int(cy - 25)

    path = QPainterPath()
    path.moveTo(bx, by)
    mx = int(bx + flip_x(-15, state.facing))
    my = int(by + ts - 25)
    ex = int(bx + flip_x(-25, state.facing))
    ey = int(my - 15 + math.sin(phase * 0.7) * 5)
    path.cubicTo(
        int(bx + flip_x(-8, state.facing)), int(by - 10),
        mx, my,
        ex, ey,
    )
    painter.strokePath(path, QPen(
        coat.body, 5,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
    ))


def draw_tail_walk(painter: QPainter, cx: float, cy: float, state,
                   coat_index: int = 0) -> None:
    """Walking tail — held up, sinusoidal sway synchronized with gait."""
    coat = config.get_coat(coat_index)
    walk_frame = getattr(state, 'walk_frame', 0)
    # Sinusoidal tail sway synchronized with gait
    sway = math.sin(walk_frame * 0.785) * 6

    tx = int(cx + flip_x(-14, state.facing))
    ty = int(cy - 28)

    # Tail tip sways horizontally with gait
    tip_sway_x = int(cx + flip_x(-10, state.facing)) + int(flip_x(sway, state.facing))

    path = QPainterPath()
    path.moveTo(tx, ty)
    path.cubicTo(
        int(tx + flip_x(-12, state.facing)), int(ty - 15),
        int(tx + flip_x(-6, state.facing)), int(ty - 35),
        tip_sway_x, int(ty - 45),
    )
    painter.strokePath(path, QPen(
        coat.body, 4,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
    ))


def draw_tail_sleep(painter: QPainter, cx: float, cy: float, state,
                    base_r: float, base_y: float, coat_index: int = 0) -> None:
    """Curled-around tail for sleep pose."""
    coat = config.get_coat(coat_index)
    path = QPainterPath()
    tc_x = int(cx - base_r)
    tc_y = int(base_y)
    path.moveTo(tc_x, tc_y)
    path.cubicTo(
        tc_x - 15, int(tc_y - 20),
        tc_x + 10, int(tc_y - 35),
        int(cx + flip_x(8, state.facing)), int(base_y - 15),
    )
    painter.strokePath(path, QPen(
        coat.body, 4,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
    ))
