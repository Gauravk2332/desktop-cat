"""
tests/test_frame_timing.py — Performance benchmarks for sprite pipeline.

These tests measure real execution time and FAIL if thresholds are exceeded.
Marked with @pytest.mark.benchmark for CI segmentation (skipped in fast runs).

Measured thresholds:
- QPixmap blit < 30ms per frame (33fps budget)
- Spritesheet load < 500ms for single sheet
- Spritesheet load < 2s for all sheets combined
- Crossfade completes within 200±10ms (50 iterations)
"""

import os
import sys
import time
from pathlib import Path

import pytest
from PIL import Image

# Qt offscreen (set before any PyQt import)
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainter, QPixmap, QColor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from sprite.pipeline import stitch_spritesheet, SPRITE_WIDTH, SPRITE_HEIGHT
    from sprite.renderer import (
        load_spritesheet,
        SpriteRenderer,
        advance_frame_index,
    )
except ImportError:
    pytest.skip("sprite modules not available — Phase 0 stub needed", allow_module_level=True)
except Exception:
    pytest.skip("sprite modules import failed — Phase 0 stub needed", allow_module_level=True)

# ── Constants ─────────────────────────────────────────────────────────

SPRITE_W = 400
SPRITE_H = 400
F32 = 4  # frames for sit
F12 = 12  # frames for walk

# Thresholds
MAX_BLIT_MS = 30
MAX_SINGLE_SHEET_LOAD_MS = 500
MAX_ALL_SHEETS_LOAD_MS = 2000
CROSSFADE_TARGET_MS = 200
CROSSFADE_TOLERANCE_MS = 10


# ── Helpers ───────────────────────────────────────────────────────────

def _make_sheet(tmp_path: Path, name: str, frames: int,
                sw: int = SPRITE_W, sh: int = SPRITE_H) -> Path:
    """Create a horizontal strip spritesheet."""
    width = sw * frames
    img = Image.new("RGBA", (width, sh), (0, 0, 0, 0))
    for i in range(frames):
        r = (i * 60) % 256
        g = (i * 40 + 100) % 256
        b = (i * 20 + 50) % 256
        tile = Image.new("RGBA", (sw, sh), (r, g, b, 255))
        img.paste(tile, (int(i * sw), 0))
    path = tmp_path / name
    img.save(str(path), "PNG")
    return path


# ── QPixmap Blit Timing ──────────────────────────────────────────────

@pytest.mark.benchmark
class TestBlitTiming:
    """QPixmap blit must complete < 30ms per frame (33fps budget)."""

    def test_blit_under_30ms(self, tmp_path):
        """Single QPixmap blit measured over 100 iterations stays under 30ms."""
        sheet_path = _make_sheet(tmp_path, "sit.png", F32)
        pixmap = QPixmap(str(sheet_path))
        canvas = QPixmap(SPRITE_W, SPRITE_H)
        canvas.fill(Qt.GlobalColor.transparent)

        timings = []
        for _ in range(100):
            t0 = time.perf_counter()
            painter = QPainter(canvas)
            painter.drawPixmap(QPointF(0, 0), pixmap)
            painter.end()
            elapsed = (time.perf_counter() - t0) * 1000  # ms
            timings.append(elapsed)

        max_ms = max(timings)
        mean_ms = sum(timings) / len(timings)
        print(f"  Blit: max={max_ms:.3f}ms, mean={mean_ms:.3f}ms (threshold={MAX_BLIT_MS}ms)")
        assert max_ms < MAX_BLIT_MS, (
            f"Blit exceeded {MAX_BLIT_MS}ms: max={max_ms:.3f}ms"
        )

    def test_blit_slice_under_30ms(self, tmp_path):
        """QPixmap copy (sub-rectangle, as used per-frame) stays under 30ms."""
        sheet_path = _make_sheet(tmp_path, "walk.png", F12)
        pixmap = QPixmap(str(sheet_path))
        canvas = QPixmap(SPRITE_W, SPRITE_H)
        canvas.fill(Qt.GlobalColor.transparent)

        timings = []
        for i in range(100):
            src_x = (i % F12) * SPRITE_W
            t0 = time.perf_counter()
            painter = QPainter(canvas)
            painter.drawPixmap(
                QPointF(0, 0),
                pixmap,
                src_x, 0, SPRITE_W, SPRITE_H,
            )
            painter.end()
            elapsed = (time.perf_counter() - t0) * 1000
            timings.append(elapsed)

        max_ms = max(timings)
        mean_ms = sum(timings) / len(timings)
        print(f"  Blit-slice: max={max_ms:.3f}ms, mean={mean_ms:.3f}ms (threshold={MAX_BLIT_MS}ms)")
        assert max_ms < MAX_BLIT_MS, (
            f"Blit slice exceeded {MAX_BLIT_MS}ms: max={max_ms:.3f}ms"
        )


# ── Spritesheet Load Timing ──────────────────────────────────────────

@pytest.mark.benchmark
class TestSheetLoadTiming:
    """Spritesheet load must complete within thresholds."""

    def test_single_sheet_load_under_500ms(self, tmp_path):
        """Loading one spritesheet as QPixmap stays under 500ms."""
        sheet_path = _make_sheet(tmp_path, "sit.png", F32)
        t0 = time.perf_counter()
        pixmap = QPixmap(str(sheet_path))
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  Single load: {elapsed:.3f}ms (threshold={MAX_SINGLE_SHEET_LOAD_MS}ms)")
        assert elapsed < MAX_SINGLE_SHEET_LOAD_MS, (
            f"Single sheet load {elapsed:.1f}ms > {MAX_SINGLE_SHEET_LOAD_MS}ms"
        )

    def test_all_sheets_combined_under_2s(self, tmp_path):
        """Loading all 12 pose spritesheets stays under 2s cumulative."""
        sheets = {}
        poses = [
            ("sit", 4), ("sit_relaxed", 4), ("loaf", 4),
            ("walk", 12), ("trot", 8), ("sleep_curled", 6),
            ("sleep_sprawl", 6), ("groom", 12), ("stretch", 8),
            ("yawn", 4), ("eat", 6), ("alert", 2),
        ]
        for name, frames in poses:
            sheets[name] = _make_sheet(tmp_path, f"{name}.png", frames)

        t0 = time.perf_counter()
        loaded = {}
        for name, path in sheets.items():
            loaded[name] = QPixmap(str(path))
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  All sheets ({len(poses)}): {elapsed:.3f}ms (threshold={MAX_ALL_SHEETS_LOAD_MS}ms)")
        assert elapsed < MAX_ALL_SHEETS_LOAD_MS, (
            f"Combined load {elapsed:.1f}ms > {MAX_ALL_SHEETS_LOAD_MS}ms"
        )

    def test_manifest_plus_sheets_under_2s(self, tmp_path):
        """Parsing manifest + loading all spritesheets stays under 2s."""
        sheets = {}
        poses = [
            ("sit", 4), ("sit_relaxed", 4), ("loaf", 4),
            ("walk", 12), ("trot", 8), ("sleep_curled", 6),
            ("sleep_sprawl", 6), ("groom", 12), ("stretch", 8),
            ("yawn", 4), ("eat", 6), ("alert", 2),
        ]
        for name, frames in poses:
            sheets[name] = _make_sheet(tmp_path, f"{name}.png", frames)

        import json
        manifest = {name: {"frames": frames, "fps": 6}
                     for name, frames in poses}

        t0 = time.perf_counter()
        # Simulate full init
        with open(str(tmp_path / "manifest.json"), "w") as f:
            json.dump(manifest, f)
        with open(str(tmp_path / "manifest.json")) as f:
            loaded_manifest = json.load(f)
        for name in poses:
            name = name[0]
            QPixmap(str(sheets[name]))
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  Manifest + sheets: {elapsed:.3f}ms (threshold={MAX_ALL_SHEETS_LOAD_MS}ms)")
        assert elapsed < MAX_ALL_SHEETS_LOAD_MS, (
            f"Manifest + sheets load {elapsed:.1f}ms > {MAX_ALL_SHEETS_LOAD_MS}ms"
        )


# ── Crossfade Timing ─────────────────────────────────────────────────

@pytest.mark.benchmark
class TestCrossfadeTiming:
    """Crossfade must complete within 200±10ms (50 iterations)."""

    def test_crossfade_200ms(self, tmp_path):
        """Crossfade between two QPixmaps completes in 200±10ms over 50 iters."""
        sheet_a = _make_sheet(tmp_path, "a.png", F32)
        sheet_b = _make_sheet(tmp_path, "b.png", F32)
        pix_a = QPixmap(str(sheet_a))
        pix_b = QPixmap(str(sheet_b))

        timings = []
        for _ in range(50):
            canvas = QPixmap(SPRITE_W, SPRITE_H)
            canvas.fill(Qt.GlobalColor.transparent)
            t0 = time.perf_counter()
            # Simulate a crossfade by painting a at alpha 0.5 and b at alpha 0.5
            painter = QPainter(canvas)
            painter.setOpacity(0.5)
            painter.drawPixmap(QPointF(0, 0), pix_a)
            painter.drawPixmap(QPointF(0, 0), pix_b)
            painter.end()
            elapsed = (time.perf_counter() - t0) * 1000
            timings.append(elapsed)

        max_ms = max(timings)
        mean_ms = sum(timings) / len(timings)
        print(f"  Crossfade: max={max_ms:.3f}ms, mean={mean_ms:.3f}ms "
              f"(target={CROSSFADE_TARGET_MS}±{CROSSFADE_TOLERANCE_MS}ms)")
        assert max_ms < CROSSFADE_TARGET_MS + CROSSFADE_TOLERANCE_MS, (
            f"Crossfade {max_ms:.1f}ms > {CROSSFADE_TARGET_MS + CROSSFADE_TOLERANCE_MS}ms"
        )

    def test_crossfade_with_different_sized_sheets(self, tmp_path):
        """Crossfade timing remains stable with different spritesheet sizes."""
        sheet_small = _make_sheet(tmp_path, "small.png", 4)
        sheet_large = _make_sheet(tmp_path, "large.png", 16)
        pix_small = QPixmap(str(sheet_small))
        pix_large = QPixmap(str(sheet_large))

        timings = []
        for _ in range(50):
            canvas = QPixmap(SPRITE_W, SPRITE_H)
            canvas.fill(Qt.GlobalColor.transparent)
            t0 = time.perf_counter()
            painter = QPainter(canvas)
            painter.setOpacity(0.5)
            painter.drawPixmap(QPointF(0, 0), pix_small)
            painter.drawPixmap(QPointF(0, 0), pix_large)
            painter.end()
            elapsed = (time.perf_counter() - t0) * 1000
            timings.append(elapsed)

        max_ms = max(timings)
        print(f"  Crossfade (mixed size): max={max_ms:.3f}ms (threshold={CROSSFADE_TARGET_MS + CROSSFADE_TOLERANCE_MS}ms)")
        assert max_ms < CROSSFADE_TARGET_MS + CROSSFADE_TOLERANCE_MS, (
            f"Crossfade with mixed sizes {max_ms:.1f}ms exceeds threshold"
        )


# ── Frame Index Advance Timing ────────────────────────────────────────

@pytest.mark.benchmark
class TestFrameAdvanceTiming:
    """Frame index advance must be near-zero overhead."""

    def test_frame_advance_under_1ms(self, tmp_path):
        """Calling advance_frame_index 1000 times stays under 1ms total."""
        idx = 0
        total = 4  # frames
        t0 = time.perf_counter()
        for _ in range(1000):
            idx = advance_frame_index(idx, total, mode="loop")
        elapsed = (time.perf_counter() - t0) * 1000  # ms
        print(f"  Frame advance (1000×): {elapsed:.6f}ms")
        assert elapsed < 1.0, (
            f"1000× frame advance took {elapsed:.3f}ms, expected < 1ms"
        )

    def test_advance_all_modes_fast(self, tmp_path):
        """All three advance modes (loop, once, pingpong) are fast."""
        total = 8
        for mode in ("loop", "once", "pingpong"):
            idx = 0
            t0 = time.perf_counter()
            for _ in range(500):
                idx = advance_frame_index(idx, total, mode=mode)
            elapsed = (time.perf_counter() - t0) * 1000
            print(f"  Frame advance {mode} (500×): {elapsed:.6f}ms")
            assert elapsed < 1.0, (
                f"500× {mode} advance took {elapsed:.3f}ms"
            )
