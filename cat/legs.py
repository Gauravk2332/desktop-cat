"""
cat/legs.py — Paw and leg drawing for sit and walk poses.

4-leg gait: each leg has 2 segments (upper + lower) meeting at a knee/elbow.
The 8-frame gait cycles diagonal pairs (trot pattern).
"""

from PyQt6.QtGui import QPainter, QPainterPath, QPen
from PyQt6.QtCore import Qt

import config
from config import flip_x


# Gait frame data: each frame maps leg keys to (mid_x, mid_y, paw_x, paw_y)
# relative to the leg's base (shoulder/hip) position.
# Layout: frame -> {leg_key: (mid_dx, mid_dy, paw_dx, paw_dy)}
# Leg keys: "fl" = front-left, "fr" = front-right,
#           "bl" = back-left, "br" = back-right
GAIT_FRAMES_4LEG = {
    0: {"fl": (-2, -4, -8, -2), "fr": (-2, -4, -8, -2),
        "bl": (2, -4, 8, -2), "br": (2, -4, 8, -2)},
    1: {"fl": (-1, -6, -10, -4), "fr": (0, -2, -4, 0),
        "bl": (1, -6, 10, -4), "br": (0, -2, 4, 0)},
    2: {"fl": (0, -6, -8, -6), "fr": (2, -2, 0, 2),
        "bl": (0, -6, 8, -4), "br": (-2, -2, 0, 2)},
    3: {"fl": (2, -4, -4, -4), "fr": (0, -4, 4, 2),
        "bl": (-2, -4, 4, -2), "br": (0, -4, -4, 2)},
    4: {"fl": (-2, -4, -8, -2), "fr": (-2, -4, -8, -2),
        "bl": (2, -4, 8, -2), "br": (2, -4, 8, -2)},
    5: {"fl": (0, -2, -4, 0), "fr": (-1, -6, -10, -4),
        "bl": (0, -2, 4, 0), "br": (1, -6, 10, -4)},
    6: {"fl": (2, -2, 0, 2), "fr": (0, -6, -8, -6),
        "bl": (-2, -2, 0, 2), "br": (0, -6, 8, -4)},
    7: {"fl": (0, -4, 4, 2), "fr": (2, -4, -4, -4),
        "bl": (0, -4, -4, 2), "br": (-2, -4, 4, -2)},
}

GAIT_BODY_BOB = [0, -1, -2, -1, 0, 1, 2, 1]
GAIT_BODY_TILT = [-2, -1, 0, 1, 2, 1, 0, -1]
GAIT_TAIL_SWAY = [0, -2, -4, -2, 0, 2, 4, 2]


# ── Leg base positions (relative to body center cx, cy, before facing) ──
# Front shoulders: slightly forward and above body center
# Back hips: slightly behind and above body center
_LEG_BASES = {
    "fl": (-12, -12),  # front-left shoulder
    "fr": (12, -12),   # front-right shoulder
    "bl": (-16, -14),  # back-left hip
    "br": (16, -14),   # back-right hip
}


def draw_paws(painter: QPainter, cx: float, cy: float, state,
              coat_index: int = 0) -> None:
    """Two front paw ellipses at body base (sitting pose).

    Also draws tucked back paws for realistic sitting posture.
    Uses coat_index for paw pad colors.
    """
    coat = config.get_coat(coat_index)
    # Front paws (sit) — straight down from shoulders
    for side in (-1, 1):
        bx = int(cx + flip_x(side * 10, state.facing))
        by = int(cy - 5)
        # Upper leg segment
        leg_path = QPainterPath()
        leg_path.moveTo(bx, int(cy - 15))
        leg_path.lineTo(bx, by)
        painter.strokePath(leg_path, QPen(coat.body, 5,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        # Paw ellipse
        paw = QPainterPath()
        paw.addEllipse(bx - 5, by, 10, 7)
        painter.fillPath(paw, coat.paw_pads)

    # Back paws (sit) — folded, tucked under body
    for side in (-1, 1):
        bx = int(cx + flip_x(side * 14, state.facing))
        by = int(cy - 6)
        # Folded thigh — horizontal segment
        thigh = QPainterPath()
        thigh.moveTo(bx, int(cy - 18))
        thigh.lineTo(int(bx + flip_x(-4, state.facing)), by)
        painter.strokePath(thigh, QPen(coat.body, 4,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        # Tucked paw
        tucked = QPainterPath()
        tucked.addEllipse(int(bx + flip_x(-4, state.facing)) - 4, by, 8, 6)
        painter.fillPath(tucked, coat.paw_pads)


def draw_legs_walk(painter: QPainter, cx: float, cy: float, state,
                   coat_index: int = 0) -> None:
    """8-frame 4-leg articulated gait animation.

    Each leg is drawn as 2 segments (upper + lower) meeting at a joint.
    Uses diagonal-pair trot pattern for natural walking.
    """
    coat = config.get_coat(coat_index)
    frame = getattr(state, 'walk_frame', 0) % 8
    leg_data = GAIT_FRAMES_4LEG.get(frame, GAIT_FRAMES_4LEG[0])

    for leg_key in ("fl", "fr", "bl", "br"):
        base_dx, base_dy = _LEG_BASES[leg_key]
        mid_dx, mid_dy, paw_dx, paw_dy = leg_data[leg_key]

        # Base (shoulder/hip) in screen coords
        base_x = int(cx + flip_x(base_dx, state.facing))
        base_y = int(cy + base_dy)

        # Joint (knee/elbow) in screen coords, facing-aware
        joint_x = int(cx + flip_x(base_dx + mid_dx, state.facing))
        joint_y = int(cy + base_dy + mid_dy)

        # Paw in screen coords, facing-aware
        paw_x = int(cx + flip_x(base_dx + paw_dx, state.facing))
        paw_y = int(cy + base_dy + paw_dy)

        # Upper segment: base -> joint (thicker, 5px)
        upper = QPainterPath()
        upper.moveTo(base_x, base_y)
        upper.lineTo(joint_x, joint_y)
        painter.strokePath(upper, QPen(
            coat.body, 5,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        ))

        # Lower segment: joint -> paw (slightly thinner, 4px)
        lower = QPainterPath()
        lower.moveTo(joint_x, joint_y)
        lower.lineTo(paw_x, paw_y)
        painter.strokePath(lower, QPen(
            coat.body, 4,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        ))

        # Paw tip (small ellipse)
        paw_tip = QPainterPath()
        paw_tip.addEllipse(paw_x - 3, paw_y - 2, 6, 4)
        painter.fillPath(paw_tip, coat.paw_pads)
