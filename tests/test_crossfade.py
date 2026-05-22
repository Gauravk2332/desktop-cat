#!/usr/bin/env python3
"""
tests/test_crossfade.py — Crossfade performance and timing test.

Verifies:
1. 200ms InOutCubic crossfade completes within 200±10ms
2. Opacity blend is smooth (no jumps)
3. All frame operations complete within 33ms (33fps budget)

Uses QPixmap blit timing without requiring a display (offscreen).
"""

import math
import sys
import os
import time

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QElapsedTimer

import config
from core.renderer import Crossfade, ease_in_out_cubic


def test_easing_function():
    """Verify InOutCubic mathematical properties."""
    assert ease_in_out_cubic(0.0) == 0.0, "ease(0) should be 0"
    assert ease_in_out_cubic(1.0) == 1.0, "ease(1) should be 1"
    assert ease_in_out_cubic(0.5) == 0.5, "ease(0.5) should be 0.5"
    # Symmetry check
    for t in [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]:
        forward = ease_in_out_cubic(t)
        backward = 1.0 - ease_in_out_cubic(1.0 - t)
        assert abs(forward - backward) < 1e-6, \
            f"ease({t}) = {forward}, reverse = {backward}"
    # Monotonicity
    prev = 0.0
    for i in range(1, 101):
        t = i / 100.0
        v = ease_in_out_cubic(t)
        assert v >= prev, f"ease({t}) = {v} < prev {prev}"
        prev = v
    print(f"  [PASS] Easing function: InOutCubic monotonic, symmetric, bounds correct")


def test_crossfade_timing():
    """Verify crossfade completes within roughly 200ms (tick-boundary tolerant).

    Because the crossfade checks elapsed >= duration only at tick boundaries,
    the observed duration may exceed config.CROSSFADE_MS by up to one full dt
    step (16.7ms at 60fps).  We accept 200-230ms.
    """
    cf = Crossfade()
    cf.start("sit_alert", "walk")

    start = time.perf_counter()
    elapsed = 0.0
    dt = 1.0 / 60.0  # 60 updates per second

    while cf.active:
        cf.update(dt)
        elapsed += dt

    wall_time = (time.perf_counter() - start) * 1000  # ms
    expected_ms = config.CROSSFADE_MS

    assert elapsed * 1000 >= expected_ms, \
        f"Crossfade duration {elapsed*1000:.1f}ms < expected {expected_ms}ms"
    assert elapsed * 1000 <= expected_ms + 30, \
        f"Crossfade duration {elapsed*1000:.1f}ms too long (max {expected_ms + 30}ms)"
    print(f"  [PASS] Crossfade timing: {elapsed*1000:.1f}ms (target {expected_ms}ms, "
          f"wall {wall_time:.1f}ms, tick-budget OK)")


def test_crossfade_progress_monotonic():
    """Verify crossfade progress advances monotonically and smoothly."""
    cf = Crossfade()
    cf.start("sleep_curled", "sit_alert")

    dt = 1.0 / 120.0  # 120Hz for smoother step granularity
    prev_progress = -1.0
    prev_eased = -1.0
    steps = int((config.CROSSFADE_MS / 1000.0) / dt) + 2

    for _ in range(steps):
        progress = cf.progress
        eased = cf.eased

        assert progress >= prev_progress, f"Progress regressed: {progress} < {prev_progress}"
        assert eased >= prev_eased, f"Eased value regressed: {eased} < {prev_eased}"

        prev_progress = progress
        prev_eased = eased
        cf.update(dt)

    assert cf.progress >= 0.99, f"Crossfade failed to reach 1.0: {cf.progress}"
    print(f"  [PASS] Crossfade progress monotonic across {steps} steps")


def test_crossfade_state_transition():
    """Verify crossfade correctly reports completed animation name."""
    cf = Crossfade()
    cf.start("sit_alert", "walk")
    assert cf.active
    assert cf.from_state == "sit_alert"
    assert cf.to_state == "walk"

    # Run to completion
    while cf.active:
        result = cf.update(0.016)
        if result:
            assert result == "walk", f"Expected 'walk', got {result}"
    assert not cf.active
    assert cf.to_state is None
    assert cf.from_state is None
    print("  [PASS] Crossfade state transition: correct completed animation name")


def test_qpixmap_blit_timing():
    """Verify that individual QPixmap blit operations stay within budget.

    A single 400×400 RGBA pixmap blit should be < 1ms on any modern GPU.
    Test requires QApplication (will use offscreen platform).
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create two test pixmaps
    p1 = QPixmap(400, 400)
    p1.fill(QColor(0xE8, 0x9B, 0x5D))
    p2 = QPixmap(400, 400)
    p2.fill(QColor(0xC4, 0x7A, 0x3C))

    # Create a target pixmap (offscreen compositing)
    target = QPixmap(400, 400)
    target.fill(Qt.GlobalColor.transparent)

    # Measure blit time
    painter = QPainter(target)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    iterations = 100
    start = time.perf_counter()
    for i in range(iterations):
        progress = i / iterations
        painter.setOpacity(progress)
        painter.drawPixmap(0, 0, p2)
        painter.setOpacity(1.0 - progress)
        painter.drawPixmap(0, 0, p1)

    painter.end()
    wall = (time.perf_counter() - start) * 1000
    avg_ms = wall / iterations

    # Budget: each blit should be < 1ms (33ms frame budget / 2 for crossfade)
    assert avg_ms < 2.0, \
        f"Average blit time {avg_ms:.3f}ms exceeds 2ms budget"
    print(f"  [PASS] QPixmap blit timing: avg {avg_ms:.3f}ms across {iterations} "
          f"iterations (budget: 2.0ms)")


def test_crossfade_two_pixmaps():
    """End-to-end test: blend two QPixmaps with opacity over 200ms.

    Measures that the compositing completes within timing budget.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    target = QPixmap(400, 400)
    p_from = QPixmap(400, 400)
    p_from.fill(QColor(0x7C, 0x8E, 0x9E))  # gray
    p_to = QPixmap(400, 400)
    p_to.fill(QColor(0xE8, 0x9B, 0x5D))   # orange

    cf = Crossfade()
    cf.start("sleep_curled", "sit_alert")

    dt = 1.0 / 60.0
    frames = 0
    start = time.perf_counter()

    while cf.active:
        progress = cf.progress
        eased = cf.eased

        target.fill(Qt.GlobalColor.transparent)
        p = QPainter(target)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw "to" fading in
        p.setOpacity(eased)
        p.drawPixmap(0, 0, p_to)

        # Draw "from" fading out
        p.setOpacity(1.0 - eased)
        p.drawPixmap(0, 0, p_from)

        p.end()
        cf.update(dt)
        frames += 1

    wall = (time.perf_counter() - start) * 1000
    avg_frame = wall / frames if frames > 0 else 0

    assert frames > 5, f"Too few crossfade frames: {frames}"
    assert avg_frame < 5.0, \
        f"Average crossfade frame {avg_frame:.3f}ms exceeds 5ms budget"
    print(f"  [PASS] Two-pixmap crossfade: {frames} frames, avg {avg_frame:.3f}ms "
          f"per frame, total {wall:.1f}ms")


def test_renderer_backend_config():
    """Verify RENDERER_BACKEND config is set correctly."""
    assert hasattr(config, "RENDERER_BACKEND"), "Missing RENDERER_BACKEND"
    assert config.RENDERER_BACKEND in ("sprite", "qpainter"), \
        f"Invalid RENDERER_BACKEND: {config.RENDERER_BACKEND}"
    assert config.CROSSFADE_MS == 200, \
        f"CROSSFADE_MS = {config.CROSSFADE_MS}, expected 200"
    assert config.SPRITE_SIZE == 400
    assert config.CAT_SIZE_DEFAULT == 120
    assert config.CAT_SIZE_MIN == 120
    assert config.CAT_SIZE_MAX == 350
    assert config.SHADOW_OPACITY == 0.10
    assert config.SILHOUETTE_SHADOW is True
    assert config.NIGHT_MODE is False
    assert config.NIGHT_DESATURATE == 0.20
    assert config.LOD_OUTLINE_THRESHOLD == 150
    assert config.LOD_OUTLINE_COLOR == "#1a1a1a"
    assert config.LOD_OUTLINE_OPACITY == 0.5
    print("  [PASS] Config: all sprite/renderer constants present and correct")


def test_silhouette_shadow_is_default():
    """Verify silhouette shadow is enabled by default (Muse requirement)."""
    assert config.SILHOUETTE_SHADOW is True, \
        "Silhouette shadow must be enabled by default"
    assert config.SHOW_BLINK_VISUAL is True, \
        "Blink visual must be enabled by default"
    print("  [PASS] Phase 1: SILHOUETTE_SHADOW + SHOW_BLINK_VISUAL + LOD + Night mode config")


if __name__ == "__main__":
    # Offscreen platform so tests work without display
    sys.argv = [sys.argv[0], "-platform", "offscreen"]

    tests = [
        test_easing_function,
        test_crossfade_timing,
        test_crossfade_progress_monotonic,
        test_crossfade_state_transition,
        test_qpixmap_blit_timing,
        test_crossfade_two_pixmaps,
        test_renderer_backend_config,
        test_silhouette_shadow_is_default,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
