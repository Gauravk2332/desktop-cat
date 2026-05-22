"""
cat/home.py — Draw the cat's hut (house).

Pure draw functions. Uses SCREEN-relative coordinates.
Huts are placed left-to-right from right edge.
Each cat (by hut_index) gets its own hut.

Drawing order in window.py:
  1. draw_hut_frame   (interior dark area — behind cat)
  2. draw_sleeping_cat (cat curled inside doorway)
  3. draw_hut_front    (roof, walls — overlays cat)
"""

import math

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainterPath, QColor, QFont, QPen

import config


def _hut_x(state, hut_index: int = 0) -> int:
    """Return x position of hut for given index (0 = rightmost)."""
    gap = config.MULTI_HUT_GAP
    total_w = config.HUT_WIDTH + gap
    return state.screen_width - config.HUT_PADDING_RIGHT - config.HUT_WIDTH - (hut_index * total_w)


def _hut_door_center(state, hut_index: int = 0) -> tuple[int, int]:
    """Return (hx, hy) center of the hut doorway in SCREEN coordinates.
    This is the GO_HOME target — cat sleeps here inside the hut."""
    hx = _hut_x(state, hut_index) + config.HUT_WIDTH // 2
    hy = state.screen_height - config.HUT_PADDING_BOTTOM - config.HUT_DOOR_FLOOR
    return hx, hy


def draw_hut_frame(painter, state, hut_index: int = 0) -> None:
    """Draw the hut interior + shadow. Call FIRST as background."""
    hx, hy = _hut_door_center(state, hut_index)
    _draw_hut_interior(painter, hx, hy)
    _draw_hut_shadow(painter, hx, hy)


def draw_hut_front(painter, state, hut_index: int = 0) -> None:
    """Draw the hut front (walls, roof, trim). Call LAST to overlay cat."""
    hx, hy = _hut_door_center(state, hut_index)
    _draw_hut_walls(painter, hx, hy)
    _draw_hut_roof(painter, hx, hy)
    _draw_hut_door_trim(painter, hx, hy)
    _draw_hut_doormat(painter, hx, hy)


def draw_sleeping_cat(painter, state, hut_index: int = 0) -> None:
    """Draw curled cat sleeping inside the hut + Z badge."""
    hx, hy = _hut_door_center(state, hut_index)
    _draw_curled_cat(painter, hx, hy, state)
    _draw_z_badge(painter, hx, hy, state)


# ── Drawing helpers (relative to door center hx, hy) ─────────────────


def _draw_hut_shadow(painter, hx: int, hy: int) -> None:
    """Soft shadow beneath the hut."""
    half_w = config.HUT_WIDTH // 2 + 4
    floor_bottom = hy + config.HUT_DOOR_H // 2 + config.HUT_DOOR_FLOOR
    sh = QPainterPath()
    sh.addRoundedRect(
        hx - half_w + 3, floor_bottom - 2,
        half_w * 2 - 6, 6, 3, 3
    )
    painter.fillPath(sh, QColor(0, 0, 0, 20))


def _draw_hut_interior(painter, hx: int, hy: int) -> None:
    """Dark interior visible through the door opening (behind cat)."""
    dw = config.HUT_DOOR_W
    dh = config.HUT_DOOR_H
    interior = QPainterPath()
    interior.addRoundedRect(
        hx - dw // 2, hy - dh // 2,
        dw, dh, 3, 3
    )
    painter.fillPath(interior, config.HUT_INTERIOR_COLOR)

    # Floor inside the doorway (slightly lighter)
    floor_h = 4
    floor_in = QPainterPath()
    floor_in.addRect(
        hx - dw // 2 + 1, hy + dh // 2 - floor_h,
        dw - 2, floor_h
    )
    painter.fillPath(floor_in, QColor(0x2A, 0x2A, 0x2A, 200))


def _draw_hut_walls(painter, hx: int, hy: int) -> None:
    """Front walls with door cutout (door hole)."""
    hw = config.HUT_WIDTH // 2           # 30
    dw = config.HUT_DOOR_W // 2          # 11
    dh = config.HUT_DOOR_H // 2          # 15
    ff = config.HUT_DOOR_FLOOR           # 6
    wall_top_y = hy - dh - 4             # wall above door

    floor_bottom = hy + dh + ff

    # Wall shape = full wall rect minus door opening
    wall = QPainterPath()
    wall.addRect(hx - hw, wall_top_y, hw * 2, floor_bottom - wall_top_y)

    # Door cutout (arch-topped)
    door = QPainterPath()
    door.moveTo(hx - dw, hy - dh)
    door.arcTo(hx - dw, hy - dh - 6, dw * 2, 12, 180, -180)
    door.lineTo(hx - dw, hy + dh)
    door.lineTo(hx + dw, hy + dh)
    door.closeSubpath()

    # Subtract door from wall
    wall = wall.subtracted(door)
    painter.fillPath(wall, config.HUT_WALL_COLOR)

    # Wall edge/grain lines (subtle verticals)
    for ox in [-hw + 6, hw - 6]:
        grain = QPainterPath()
        grain.moveTo(hx + ox, wall_top_y + 4)
        grain.lineTo(hx + ox, floor_bottom - 2)
        painter.strokePath(grain, QPen(QColor(0, 0, 0, 15), 1))


def _draw_hut_roof(painter, hx: int, hy: int) -> None:
    """Peaked triangular roof with overhang."""
    hw = config.HUT_WIDTH // 2            # 30
    over = config.HUT_ROOF_OVERHANG       # 6
    dh = config.HUT_DOOR_H // 2           # 15
    roof_peak_y = hy - dh - 4 - 16        # roof peak above wall top (~16px tall)
    eave_y = hy - dh - 4                  # eave line = top of wall

    roof = QPainterPath()
    roof.moveTo(hx, roof_peak_y)                    # peak
    roof.lineTo(hx - hw - over, eave_y)              # left eave
    roof.lineTo(hx + hw + over, eave_y)              # right eave
    roof.closeSubpath()
    painter.fillPath(roof, config.HUT_ROOF_COLOR)

    # Roof shaded side (right half — slightly darker for 3D look)
    shade = QPainterPath()
    shade.moveTo(hx, roof_peak_y)
    shade.lineTo(hx + hw + over, eave_y)
    shade.lineTo(hx, eave_y)
    shade.closeSubpath()
    painter.fillPath(shade, QColor(0, 0, 0, 25))

    # Roof trim (thin line along bottom of roof)
    trim = QPainterPath()
    trim.moveTo(hx - hw - over, eave_y)
    trim.lineTo(hx + hw + over, eave_y)
    painter.strokePath(trim, QPen(config.HUT_ACCENT_COLOR, 2))

    # Roof ridge line (peak decorative accent)
    ridge = QPainterPath()
    ridge.moveTo(hx, roof_peak_y)
    ridge.lineTo(hx, eave_y)
    painter.strokePath(ridge, QPen(QColor(0, 0, 0, 30), 1.5))


def _draw_hut_door_trim(painter, hx: int, hy: int) -> None:
    """Light trim/frame around the door opening."""
    dw = config.HUT_DOOR_W // 2
    dh = config.HUT_DOOR_H // 2

    # Arch trim on top of door
    arch = QPainterPath()
    arch.arcMoveTo(hx - dw - 2, hy - dh - 8, (dw + 2) * 2, 12, 180)
    arch.arcTo(hx - dw - 2, hy - dh - 8, (dw + 2) * 2, 12, 180, -180)

    # Side trims
    arch.moveTo(hx - dw - 2, hy - dh - 2)
    arch.lineTo(hx - dw - 2, hy + dh)
    arch.moveTo(hx + dw + 2, hy - dh - 2)
    arch.lineTo(hx + dw + 2, hy + dh)

    painter.strokePath(arch, QPen(config.HUT_ACCENT_COLOR, 2))


def _draw_hut_doormat(painter, hx: int, hy: int) -> None:
    """Small welcome doormat at the entrance threshold."""
    dw = config.HUT_DOOR_W // 2
    dh = config.HUT_DOOR_H // 2
    ff = config.HUT_DOOR_FLOOR
    floor_bottom = hy + dh + ff

    # Doormat at the threshold
    mat_w = dw * 1.2
    mat = QPainterPath()
    mat.addRoundedRect(
        hx - mat_w // 2, floor_bottom - ff,
        mat_w, ff - 1, 2, 2
    )
    painter.fillPath(mat, QColor(0xC4, 0x9A, 0x6C))

    # Doormat lines (welcome stripes)
    for i in range(3):
        stripe_y = floor_bottom - ff + 2 + i * 1.5
        s = QPainterPath()
        s.moveTo(hx - mat_w // 2 + 3, stripe_y)
        s.lineTo(hx + mat_w // 2 - 3, stripe_y)
        painter.strokePath(s, QPen(QColor(0, 0, 0, 12), 1))


def _draw_curled_cat(painter, hx: int, hy: int, state) -> None:
    """Draw curled cat sleeping inside the hut doorway."""
    breath = math.sin(state.sleep_breath * 2.0) * 0.008 + 1.0
    painter.save()
    painter.translate(hx, hy)
    painter.scale(breath, breath)
    painter.translate(-hx, -hy)

    # Curled oval body
    curl = QPainterPath()
    curl.addEllipse(hx - 12, hy - 10, 24, 20)
    painter.fillPath(curl, config.C_BODY)

    # Belly
    belly = QPainterPath()
    belly.addEllipse(hx - 7, hy - 7, 14, 12)
    painter.fillPath(belly, config.C_BELLY)

    # Ear tip poking up
    ear = QPainterPath()
    ear.moveTo(hx - 5, hy - 10)
    ear.lineTo(hx - 2, hy - 18)
    ear.lineTo(hx + 3, hy - 12)
    ear.closeSubpath()
    painter.fillPath(ear, config.C_BODY)
    inner_ear = QPainterPath()
    inner_ear.addEllipse(hx - 1, hy - 16, 4, 3)
    painter.fillPath(inner_ear, config.C_INNER_EAR)

    # Closed happy eye
    closed = QPainterPath()
    closed.moveTo(hx + 3, hy - 4)
    closed.cubicTo(hx + 5, hy - 6, hx + 8, hy - 6, hx + 10, hy - 4)
    painter.strokePath(closed, QPen(QColor(0x5C, 0x4A, 0x3D), 1.5))

    # Nose
    nose = QPainterPath()
    nose.addEllipse(hx + 6, hy - 2, 3, 2)
    painter.fillPath(nose, config.C_NOSE)

    painter.restore()


def draw_hearts(painter, state) -> None:
    """Draw floating hearts above all cats."""
    _draw_cat_hearts(painter, state, is_shared=False)


def draw_cat_hearts(painter, cat) -> None:
    """Draw floating hearts for a single cat dict."""
    for h in list(cat.get("hearts", [])):
        x_offset, y_offset, lifetime, size = h
        if lifetime <= 0:
            continue

        cx = cat["x"] + x_offset
        cy = cat["y"] + y_offset
        heart_size = size
        alpha = min(255, int(lifetime * 255))

        color = QColor(0xFF, 0x60, 0x80, alpha)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)

        # Simple heart: two overlapping circles + triangle
        r = heart_size * 0.5
        # Left lobe
        painter.drawEllipse(int(cx - r * 1.1), int(cy - r * 0.8), int(r * 1.4), int(r * 1.4))
        # Right lobe
        painter.drawEllipse(int(cx - r * 0.3), int(cy - r * 0.8), int(r * 1.4), int(r * 1.4))
        # Triangle pointing down
        heart_path = QPainterPath()
        heart_path.moveTo(cx - r * 1.2, cy - r * 0.1)
        heart_path.lineTo(cx + r * 1.2, cy - r * 0.1)
        heart_path.lineTo(cx, cy + r * 0.6)
        heart_path.closeSubpath()
        painter.drawPath(heart_path)


def _draw_cat_hearts(painter, state, is_shared=False):
    """Backward compat wrapper — draws hearts from cats[0]."""
    if state.cats:
        draw_cat_hearts(painter, state.cats[0])


_SPEECH_BUBBLE_COLOR = QColor(42, 42, 42, 200)
_SPEECH_TEXT_COLOR = QColor(224, 224, 224)
_SPEECH_DIVIDER_COLOR = QPen(QColor(60, 60, 60, 200), 1)


def draw_speech_bubble(painter, state, cat_x: float, cat_y: float,
                        facing_right: bool) -> None:
    """Draw speech bubble above cat with emoji + text.
    Uses state.speech dict. No-op when speech.text is None.
    """
    s = state.speech
    if s["text"] is None:
        return

    from PyQt6.QtCore import QPointF, QRectF
    from PyQt6.QtGui import QPainterPath, QFont, QPolygonF

    painter.save()
    painter.setOpacity(s["opacity"])

    bubble_w = config.SPEECH_BUBBLE_W
    top_h = config.SPEECH_CELL_TOP_H
    bot_h = config.SPEECH_CELL_BOT_H
    total_h = top_h + bot_h

    # Position: above cat head
    bx = int(cat_x - bubble_w // 2)
    by = int(cat_y - total_h - config.SPEECH_ABOVE_GAP)

    # Flip below cat if near top of screen
    flipped = False
    if by < 5:
        by = int(cat_y + config.SPEECH_BELOW_GAP)
        flipped = True

    # Clamp to screen edges
    bx = max(5, min(bx, state.screen_width - bubble_w - 5))

    # Bubble background
    bg = QPainterPath()
    bg.addRoundedRect(bx, by, bubble_w, total_h, 4, 4)
    painter.fillPath(bg, _SPEECH_BUBBLE_COLOR)

    # Divider line
    painter.setPen(_SPEECH_DIVIDER_COLOR)
    painter.drawLine(bx + 4, by + top_h, bx + bubble_w - 4, by + top_h)

    # Emoji (top cell)
    if s["emoji"] is not None:
        painter.setPen(_SPEECH_TEXT_COLOR)
        painter.setFont(QFont("Segoe UI", 12))
        emoji_rect = QRectF(bx, by, bubble_w, top_h)
        painter.drawText(emoji_rect, Qt.AlignmentFlag.AlignCenter, s["emoji"])

    # Text (bottom cell)
    if s["text"]:
        painter.setPen(_SPEECH_TEXT_COLOR)
        painter.setFont(QFont("Segoe UI", 10))
        text_rect = QRectF(bx, by + top_h, bubble_w, bot_h)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, s["text"])

    # Tail triangle
    tail_center_x = bx + bubble_w // 2
    tail_top_y = by + total_h
    tail_bottom_y = tail_top_y + 8

    if flipped:
        tail_pts = QPolygonF([
            QPointF(tail_center_x, tail_top_y),
            QPointF(tail_center_x - 5, tail_bottom_y),
            QPointF(tail_center_x + 5, tail_bottom_y),
        ])
    else:
        tail_pts = QPolygonF([
            QPointF(tail_center_x, tail_bottom_y),
            QPointF(tail_center_x - 5, tail_top_y),
            QPointF(tail_center_x + 5, tail_top_y),
        ])

    painter.setBrush(_SPEECH_BUBBLE_COLOR)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(tail_pts)

    painter.restore()


def draw_speech_bubble_for_cat(painter, cat, state) -> None:
    """Draw speech bubble for a cat dict, using its speech sub-dict."""
    speech = cat.get("speech", {})
    if speech.get("text") is None:
        return
    # Temporarily patch state.speech so the legacy draw function works
    original = state.speech
    state.speech = speech
    draw_speech_bubble(painter, state, cat["x"], cat["y"], cat.get("facing", True))
    state.speech = original


def _draw_z_badge(painter, hx: int, hy: int, state) -> None:
    """Draw floating Z badge above the hut roof when sleeping."""
    dh = config.HUT_DOOR_H // 2
    roof_peak_y = hy - dh - 4 - 16
    bounce = math.sin(state.sleep_breath * 3.0) * 1.5
    zx = hx + 15
    zy = roof_peak_y - 8 + bounce

    painter.setPen(config.C_ZZZ)
    painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
    painter.drawText(int(zx), int(zy), "Z")
