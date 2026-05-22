"""
cat/stripes.py — Coat pattern (stripe) drawing for desktop-cat.

Pure draw functions. Stateless. Used by the draw pipeline.
Draws stripes/patches/markings on top of the body fill based on coat style.

Supported styles:
- "mackerel" — vertical curved stripes (orange tabby, gray tabby)
- "classic" — swirled/blotched stripes
- "tuxedo" — white chest/belly patch
- "patch" — irregular color patches (calico/tortie)
- "point" — dark extremities (Siamese)
- "solid" / "none" — no extra markings
"""

import math
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QColor
from PyQt6.QtCore import Qt

import config
from config import flip_x


def draw_coat_pattern(painter: QPainter, cx: float, cy: float, state,
                      coat_index: int) -> None:
    """Dispatch to the correct stripe/pattern drawing function based on coat style.

    Called after body fill but before head/legs in the draw pipeline.
    """
    coat = config.get_coat(coat_index)
    style = coat.stripe_style

    if style == "mackerel":
        draw_tabby_stripes(painter, cx, cy, state, coat)
    elif style == "classic":
        draw_classic_stripes(painter, cx, cy, state, coat)
    elif style == "tuxedo":
        draw_white_chest(painter, cx, cy, state, coat)
    elif style == "patch":
        # Calico/tortie patches — simplified
        pass
    elif style == "point":
        # Siamese point — simplified
        pass
    # "solid" / "none" = nothing extra

    # Forehead "M" marking (orange & gray tabbies)
    if coat.has_forehead_m and coat.stripe is not None:
        draw_forehead_m(painter, cx, cy, state, coat)

    # White chin/chest patch
    if coat.chin_chest is not None:
        draw_white_chin_chest(painter, cx, cy, state, coat)

    # Leg stripes (tabby styles only)
    if style in ("mackerel", "classic") and coat.stripe is not None:
        draw_leg_stripes(painter, cx, cy, state, coat)


def draw_tabby_stripes(painter: QPainter, cx: float, cy: float, state,
                       coat) -> None:
    """Draw 5-7 mackerel tabby stripes on the body.

    Stripes are short curved lines overlaid on the body ellipse.
    Drawn with semi-transparency for natural blending.
    """
    stripe_color = coat.stripe
    if stripe_color is None:
        return

    pen = QPen(QColor(stripe_color.red(), stripe_color.green(),
                       stripe_color.blue(), 200), 2.5,
               cap=Qt.PenCapStyle.RoundCap)

    # Body stripe positions relative to (cx, cy)
    # Structure: (x1, y1, x2, y2) — start to end of each stripe
    stripes = [
        (-4, -40, -4, -32),   # neck left
        (4, -40, 4, -32),     # neck right
        (-8, -34, -6, -22),   # left shoulder
        (8, -34, 6, -22),     # right shoulder
        (-12, -30, -10, -18), # left mid-body
        (12, -30, 10, -18),   # right mid-body
        (-14, -22, -12, -12), # left lower body
        (14, -22, 12, -12),   # right lower body
    ]

    for x1, y1, x2, y2 in stripes:
        path = QPainterPath()
        mx = int(cx + flip_x((x1 + x2) / 2 - 2, state.facing))
        my = int(cy + (y1 + y2) / 2)
        sx = int(cx + flip_x(x1, state.facing))
        sy = int(cy + y1)
        ex = int(cx + flip_x(x2, state.facing))
        ey = int(cy + y2)
        path.moveTo(sx, sy)
        path.cubicTo(mx, my - 1, mx + 4, my + 1, ex, ey)
        painter.strokePath(path, pen)


def draw_classic_stripes(painter: QPainter, cx: float, cy: float, state,
                         coat) -> None:
    """Draw swirled/blotched classic tabby stripes.

    Uses 3-4 concentric arc-like shapes on each side of the body.
    """
    stripe_color = coat.stripe
    if stripe_color is None:
        return

    pen = QPen(QColor(stripe_color.red(), stripe_color.green(),
                       stripe_color.blue(), 180), 2.5,
               cap=Qt.PenCapStyle.RoundCap)

    # Classic pattern: bulls-eye swirls on sides
    swirls = [
        # Left side: center at (-10, -28)
        (-10, -28, -14, -22, -8, -20),
        (-10, -28, -6, -34, -14, -32),
        # Right side: center at (10, -28)
        (10, -28, 14, -22, 8, -20),
        (10, -28, 6, -34, 14, -32),
    ]

    for cx_off, cy_off, sx_off, sy_off, ex_off, ey_off in swirls:
        path = QPainterPath()
        scx = int(cx + flip_x(cx_off, state.facing))
        scy = int(cy + cy_off)
        sx = int(cx + flip_x(sx_off, state.facing))
        sy = int(cy + sy_off)
        ex = int(cx + flip_x(ex_off, state.facing))
        ey = int(cy + ey_off)
        path.moveTo(sx, sy)
        path.cubicTo(scx - 2, scy - 4, scx + 2, scy + 4, ex, ey)
        painter.strokePath(path, pen)


def draw_forehead_m(painter: QPainter, cx: float, cy: float, state,
                    coat) -> None:
    """Draw the 'M' marking on the forehead (orange & gray tabbies).

    3 strokes: left upstroke, center V, right upstroke.
    Located above the eyes on the head circle.
    """
    stripe_color = coat.stripe
    if stripe_color is None:
        return

    head_y = int(cy - 52)

    pen = QPen(QColor(stripe_color.red(), stripe_color.green(),
                       stripe_color.blue(), 200), 1.5,
               cap=Qt.PenCapStyle.RoundCap)

    # Left upstroke
    p1 = QPainterPath()
    p1.moveTo(int(cx + flip_x(-6, state.facing)), int(head_y - 8))
    p1.cubicTo(int(cx + flip_x(-4, state.facing)), int(head_y - 12),
                int(cx + flip_x(-2, state.facing)), int(head_y - 12),
                int(cx), int(head_y - 10))
    painter.strokePath(p1, pen)

    # Right upstroke
    p2 = QPainterPath()
    p2.moveTo(int(cx + flip_x(6, state.facing)), int(head_y - 8))
    p2.cubicTo(int(cx + flip_x(4, state.facing)), int(head_y - 12),
                int(cx + flip_x(2, state.facing)), int(head_y - 12),
                int(cx), int(head_y - 10))
    painter.strokePath(p2, pen)

    # Center V
    p3 = QPainterPath()
    p3.moveTo(int(cx + flip_x(-3, state.facing)), int(head_y - 11))
    p3.cubicTo(int(cx + flip_x(-2, state.facing)), int(head_y - 10),
                int(cx + flip_x(2, state.facing)), int(head_y - 10),
                int(cx + flip_x(3, state.facing)), int(head_y - 11))
    painter.strokePath(p3, pen)

    # Cheek stripes (2 short horizontal lines per side)
    for side in (-1, 1):
        for dy in (-2, 0):
            cheek = QPainterPath()
            cheek.moveTo(int(cx + flip_x(side * 8, state.facing)),
                          int(head_y + dy))
            cheek.lineTo(int(cx + flip_x(side * 12, state.facing)),
                          int(head_y + dy + 1))
            painter.strokePath(cheek, pen)


def draw_white_chin_chest(painter: QPainter, cx: float, cy: float, state,
                           coat) -> None:
    """Draw white chin and upper chest patch."""
    if coat.chin_chest is None:
        return

    head_y = int(cy - 52)
    chin_color = coat.chin_chest

    # Chin patch — small ellipse under jaw
    chin = QPainterPath()
    chin.addEllipse(int(cx + flip_x(-4, state.facing)), int(head_y + 3), 8, 5)
    painter.fillPath(chin, chin_color)

    # Chest patch — larger ellipse below chin
    chest = QPainterPath()
    chest.addEllipse(int(cx + flip_x(-6, state.facing)), int(head_y + 5), 12, 8)
    painter.fillPath(chest, chin_color)


def draw_leg_stripes(painter: QPainter, cx: float, cy: float, state,
                     coat) -> None:
    """Draw 1-2 horizontal stripe marks on each leg upper segment."""
    stripe_color = coat.stripe
    if stripe_color is None:
        return

    pen = QPen(QColor(stripe_color.red(), stripe_color.green(),
                       stripe_color.blue(), 180), 1.5,
               cap=Qt.PenCapStyle.RoundCap)

    # Leg stripe positions: (base_dx, base_dy, length_dx) per leg
    leg_stripes = [
        (-12, -6, 6),   # FL upper: (-15, -6) -> (-9, -6)
        (9, -6, 6),     # FR upper: (9, -6) -> (15, -6)
        (-19, -8, 6),   # BL upper: (-19, -8) -> (-13, -8)
        (13, -8, 6),    # BR upper: (13, -8) -> (19, -8)
    ]

    for base_dx, base_dy, length in leg_stripes:
        stripe = QPainterPath()
        sx = int(cx + flip_x(base_dx, state.facing))
        sy = int(cy + base_dy)
        ex = int(cx + flip_x(base_dx + length * (1 if base_dx >= 0 else -1), state.facing))
        ey = int(cy + base_dy)
        stripe.moveTo(sx, sy)
        stripe.lineTo(ex, ey)
        painter.strokePath(stripe, pen)
