"""conftest.py — Force offscreen Qt platform + shared fixtures for sprite tests."""

import os
import time
from pathlib import Path

import pytest
from PIL import Image

# Must be set before any PyQt imports
if "DISPLAY" not in os.environ and "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

# ── Constants ─────────────────────────────────────────────────────────

SPRITE_WIDTH = 400
SPRITE_HEIGHT = 400


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def placeholder_spritesheet(tmp_path):
    """
    Create a temporary horizontal strip spritesheet PNG for testing.

    Usage: sheet_path = placeholder_spritesheet(dims=(400, 400), frames=4)
    Returns a tuple of (path_to_sheet, frame_width, frame_height, frame_count).

    Each frame is a distinct solid color for visual debugging.
    """
    def _make(dims=(SPRITE_WIDTH, SPRITE_HEIGHT), frames=4):
        sw, sh = dims
        total_width = sw * frames
        img = Image.new("RGBA", (total_width, sh), (0, 0, 0, 0))
        for i in range(frames):
            left = i * sw
            r = (i * 55 + 30) % 256
            g = (i * 35 + 120) % 256
            b = (i * 25 + 60) % 256
            tile = Image.new("RGBA", (sw, sh), (r, g, b, 255))
            img.paste(tile, (left, 0))
        path = tmp_path / f"spritesheet_{frames}f.png"
        img.save(str(path), "PNG")
        return str(path), sw, sh, frames
    return _make


@pytest.fixture
def mock_cat_state():
    """
    Return a minimal CatState-like dict for render tests.

    This models what the engine pushes each tick: pose, frame index,
    position, facing direction, and scale.
    """
    def _make(**overrides):
        state = {
            "pose": "sit",
            "frame_index": 0,
            "x": 500.0,
            "y": 400.0,
            "facing": True,       # True = right, False = left
            "target_height": 200,  # scaled height in px
            "animation_mode": "loop",  # loop | once | pingpong
            "blinking": False,
            "eye_current": (0.0, 0.0),
        }
        state.update(overrides)
        return state
    return _make


@pytest.fixture
def frame_timing_benchmark():
    """
    Measure execution time of a callable and return detailed stats.

    Usage:
        stats = frame_timing_benchmark(func, iterations=100)
        print(f"mean={stats['mean_ms']:.3f}ms max={stats['max_ms']:.3f}ms")
    """
    def _run(func, iterations=100, *args, **kwargs):
        timings = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            func(*args, **kwargs)
            elapsed = (time.perf_counter() - t0) * 1000  # ms
            timings.append(elapsed)
        return {
            "mean_ms": sum(timings) / len(timings),
            "max_ms": max(timings),
            "min_ms": min(timings),
            "iterations": iterations,
            "timings": timings,
        }
    return _run

# ── QApplication fixture (for engine tests that need real widgets) ──

@pytest.fixture(scope="session")
def qapp():
    """Return a singleton QApplication instance for the test session."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

# ── QApplication singleton (must exist before any QWidget creation) ──

def _ensure_qapp():
    """Ensure a QApplication exists before any engine test."""
    from PyQt6.QtWidgets import QApplication
    if QApplication.instance() is None:
        QApplication([])

_ensure_qapp()
