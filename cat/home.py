"""
cat/home.py — Draw the cat's bed/home cushion.

Pure draw functions. Uses SCREEN-relative coordinates.
Bed is always visible at the bottom-right of the screen.
"""

import math

from PyQt6.QtGui import QPainterPath, QColor, QFont

import config


def draw_bed(painter, state) -> None:
    """Draw the empty bed. Call FIRST as background in every state."""
    bx, by = _bed_center(state)
    _draw_cushion(painter, bx, by)


def draw_sleeping_cat(painter, state) -> None:
    """Draw curled cat sleeping on the bed + Z badge."""
    bx, by = _bed_center(state)
    _draw_curled_cat(painter, bx, by, state)
    _draw_z_badge(painter, bx, by, state)


def _bed_center(state) -> tuple[int, int]:
    """Return (bx, by) center of the bed in SCREEN coordinates."""
    bx = state.screen_width - config.HOME_BED_RX - config.HOME_PADDING_RIGHT
    by = state.screen_height - config.HOME_BED_RY - config.HOME_PADDING_BOTTOM
    return bx, by


def _draw_cushion(painter, bx: int, by: int) -> None:
    """Draw the oval donut cushion at (bx, by) center."""
    rx = config.HOME_BED_RX
    ry = config.HOME_BED_RY
    ir = config.HOME_BED_INNER

    # Shadow beneath
    sh = QPainterPath()
    sh.addEllipse(bx - rx + 2, by - ry + 2, rx * 2, ry * 2)
    painter.fillPath(sh, QColor(0, 0, 0, 20))

    # Outer cushion fill
    outer = QPainterPath()
    outer.addEllipse(bx - rx, by - ry, rx * 2, ry * 2)
    painter.fillPath(outer, config.C_BED_RIM)

    # Inner depression via OddEvenFill
    inner = QPainterPath()
    inner.addEllipse(bx - rx * ir, by - ry * ir, rx * 2 * ir, ry * 2 * ir)
    inner.addEllipse(bx - rx, by - ry, rx * 2, ry * 2)
    inner.setFillRule(inner.FillRule.OddEvenFill)
    painter.fillPath(inner, config.C_BED_INNER)

    # Top rim highlight (thin arc)
    hl = QPainterPath()
    hl.arcMoveTo(bx - rx, by - ry, rx * 2, ry * 2, -180)
    hl.arcTo(bx - rx, by - ry, rx * 2, ry * 2, -180, -140)
    hl.lineTo(bx - rx * ir + 2, by - ry * ir + 2)
    hl.arcTo(bx - rx * ir, by - ry * ir, rx * 2 * ir, ry * 2 * ir, 40, 140)
    hl.closeSubpath()
    painter.fillPath(hl, config.C_BED_ACCENT)


def _draw_curled_cat(painter, bx: int, by: int, state) -> None:
    """Draw curled cat sleeping on the bed."""
    breath = math.sin(state.sleep_breath * 2.0) * 0.008 + 1.0
    painter.save()
    painter.translate(bx, by)
    painter.scale(breath, breath)
    painter.translate(-bx, -by)

    # Curled oval body
    curl = QPainterPath()
    curl.addEllipse(bx - 12, by - 10, 24, 20)
    painter.fillPath(curl, config.C_BODY)

    # Belly
    belly = QPainterPath()
    belly.addEllipse(bx - 7, by - 7, 14, 12)
    painter.fillPath(belly, config.C_BELLY)

    # Ear tip poking up
    ear = QPainterPath()
    ear.moveTo(bx - 5, by - 10)
    ear.lineTo(bx - 2, by - 18)
    ear.lineTo(bx + 3, by - 12)
    ear.closeSubpath()
    painter.fillPath(ear, config.C_BODY)
    inner_ear = QPainterPath()
    inner_ear.addEllipse(bx - 1, by - 16, 4, 3)
    painter.fillPath(inner_ear, config.C_INNER_EAR)

    # Closed happy eye
    closed = QPainterPath()
    closed.moveTo(bx + 3, by - 4)
    closed.cubicTo(bx + 5, by - 6, bx + 8, by - 6, bx + 10, by - 4)
    painter.strokePath(closed, QColor(0x5C, 0x4A, 0x3D))

    # Nose
    nose = QPainterPath()
    nose.addEllipse(bx + 6, by - 2, 3, 2)
    painter.fillPath(nose, config.C_NOSE)

    painter.restore()


def _draw_z_badge(painter, bx: int, by: int, state) -> None:
    """Draw floating Z badge above the bed when sleeping."""
    bounce = math.sin(state.sleep_breath * 3.0) * 1.5
    zx = bx + 15
    zy = by - config.HOME_BED_RY - 4 + bounce

    painter.setPen(QColor(0xBB, 0xBB, 0xBB, 200))
    painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
    painter.drawText(int(zx), int(zy), "Z")
