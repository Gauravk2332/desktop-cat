"""
cat/legs.py — Paw and leg drawing for sit and walk poses.
"""

from PyQt6.QtGui import QPainter, QPainterPath, QPen
from PyQt6.QtCore import Qt

import config
from config import flip_x


def draw_paws(painter: QPainter, cx: float, cy: float, state) -> None:
    """Two front paw ellipses at body base."""
    for side in (-1, 1):
        path = QPainterPath()
        path.addEllipse(
            int(cx + flip_x(side * 10, state.facing)) - 5,
            int(cy - 5),
            10, 7,
        )
        painter.fillPath(path, config.C_BODY)


def draw_legs_walk(painter: QPainter, cx: float, cy: float, state) -> None:
    """4-frame alternating leg animation for walking."""
    # leg_frames: (left_offset, right_offset) relative to foot position
    leg_frames = [(-4, 4), (-1, 1), (4, -4), (1, -1)]
    leg1_s, leg2_s = leg_frames[state.walk_frame]

    # Left leg
    path = QPainterPath()
    path.moveTo(int(cx + flip_x(-10, state.facing)), int(cy - 5))
    path.lineTo(int(cx + flip_x(-10 + leg1_s, state.facing)), int(cy + 3))
    painter.strokePath(path, QPen(
        config.C_BODY, 5,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
    ))

    # Right leg
    path = QPainterPath()
    path.moveTo(int(cx + flip_x(6, state.facing)), int(cy - 5))
    path.lineTo(int(cx + flip_x(6 + leg2_s, state.facing)), int(cy + 3))
    painter.strokePath(path, QPen(
        config.C_BODY, 5,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
    ))
