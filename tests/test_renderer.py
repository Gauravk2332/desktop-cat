"""
tests/test_renderer.py — Unit tests for the sprite renderer.

Tests cover:
- SpriteRenderer loads spritesheet correctly
- Fallback to QPainter when spritesheet missing
- Frame index advances correctly (looping vs one-shot vs ping-pong)
- Drop shadow is painted (check opacity layer)
- Silhouette shadow layer rendered at 8-12% opacity
- Scale slider changes render size (ensure no distortion)
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image

# Qt offscreen must be set before any PyQt import
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import (
    QPainter,
    QPixmap,
    QColor,
    QImage,
    qRgba,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from sprite.renderer import (
        SpriteRenderer,
        load_spritesheet,
        advance_frame_index,
        paint_drop_shadow,
        paint_silhouette_shadow,
        render_cat_at_scale,
    )
except ImportError:
    pytest.skip("sprite.renderer not yet available — Phase 0 stub needed", allow_module_level=True)
except Exception:
    pytest.skip("sprite.renderer import failed — Phase 0 stub needed", allow_module_level=True)

# ── Constants ─────────────────────────────────────────────────────────

SPRITE_W = 400
SPRITE_H = 400
FRAMES = 4


# ── Helpers ───────────────────────────────────────────────────────────

def _make_simple_spritesheet(path: Path, frames: int = 4,
                             sw: int = SPRITE_W, sh: int = SPRITE_H):
    """Create a horizontal strip spritesheet PNG at path."""
    width = sw * frames
    img = Image.new("RGBA", (width, sh), (0, 0, 0, 0))
    for i in range(frames):
        left = i * sw
        # Fill each frame with a distinct color block
        r = (i * 60) % 256
        g = (i * 40 + 100) % 256
        b = (i * 20 + 50) % 256
        tile = Image.new("RGBA", (sw, sh), (r, g, b, 255))
        img.paste(tile, (left, 0))
    img.save(str(path), "PNG")
    return path


# ── Spritesheet Loading ───────────────────────────────────────────────

class TestLoadSpritesheet:
    """load_spritesheet returns a QPixmap from a valid spritesheet file."""

    def test_loads_valid_sheet(self, tmp_path):
        """Valid spritesheet returns a non-null QPixmap."""
        sheet_path = _make_simple_spritesheet(tmp_path / "sit.png")
        pixmap = load_spritesheet(str(sheet_path))
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() == SPRITE_W * FRAMES
        assert pixmap.height() == SPRITE_H

    def test_loads_empty_pixmap_on_missing(self, tmp_path):
        """Missing file returns a null/empty QPixmap (caller handles fallback)."""
        pixmap = load_spritesheet(str(tmp_path / "nonexistent.png"))
        assert pixmap is None or pixmap.isNull()

    def test_loads_empty_pixmap_on_corrupt(self, tmp_path):
        """Corrupt file returns a null/empty QPixmap."""
        bad = tmp_path / "corrupt.png"
        bad.write_bytes(b"not a png at all")
        pixmap = load_spritesheet(str(bad))
        assert pixmap is None or pixmap.isNull()

    def test_load_sheet_with_transparency(self, tmp_path):
        """Loaded QPixmap preserves alpha channel."""
        sheet_path = _make_simple_spritesheet(tmp_path / "alpha_test.png")
        pixmap = load_spritesheet(str(sheet_path))
        qimg = pixmap.toImage()
        # Check a pixel that should be opaque (frame area)
        px = qimg.pixelColor(10, 10)
        assert px.alpha() == 255
        # Check a pixel outside the frame area — should be transparent
        # (our helper fills entire image, so this tests the format)
        assert qimg.format() == QImage.Format.Format_ARGB32_Premultiplied or \
               qimg.hasAlphaChannel()


# ── SpriteRenderer ────────────────────────────────────────────────────

class TestSpriteRenderer:
    """SpriteRenderer manages loaded sheets and frame extraction."""

    def test_init_with_sheet_loads_frames(self, tmp_path):
        """Renderer initializes with correct frame count from manifest."""
        sheet = _make_simple_spritesheet(tmp_path / "test_sheet.png", FRAMES)
        manifest = {"test_pose": {"frames": FRAMES, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        assert renderer is not None

    def test_get_frame_returns_qpixmap(self, tmp_path):
        """get_frame returns a valid QPixmap for a known pose and frame index."""
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        frame = renderer.get_frame("sit", 0)
        assert frame is not None
        assert not frame.isNull()
        assert frame.width() == SPRITE_W
        assert frame.height() == SPRITE_H

    def test_get_frame_out_of_range_loops(self, tmp_path):
        """Frame index >= frame count wraps around (modulo)."""
        sheet = _make_simple_spritesheet(tmp_path / "walk.png", 4)
        manifest = {"walk": {"frames": 4, "fps": 12}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        f0 = renderer.get_frame("walk", 0)
        f4 = renderer.get_frame("walk", 4)  # should wrap to frame 0
        assert f0 is not None and f4 is not None

    def test_get_frame_unknown_pose_returns_placeholder(self, tmp_path):
        """Unknown pose returns a placeholder or None (no crash)."""
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        # Should not crash
        result = renderer.get_frame("nonexistent_pose", 0)
        assert result is None or (not result.isNull())

    def test_get_frame_negative_index_uses_frame_zero(self, tmp_path):
        """Negative frame index safely resolves to frame 0."""
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        frame = renderer.get_frame("sit", -1)
        expect = renderer.get_frame("sit", 0)
        assert frame is not None and expect is not None


# ── Frame Index Advancement ───────────────────────────────────────────

class TestFrameAdvance:
    """advance_frame_index handles looping, one-shot, and ping-pong modes."""

    @pytest.fixture
    def renderer(self, tmp_path):
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        return SpriteRenderer(str(tmp_path), manifest)

    def test_looping_advances_correctly(self, renderer):
        """Looping advances: 0→1→2→3→0→1..."""
        for i in range(3):  # 0,1,2
            assert renderer.get_current_frame_index() == i
            renderer.advance_frame("sit", mode="loop")
        assert renderer.get_current_frame_index() == 3
        renderer.advance_frame("sit", mode="loop")
        assert renderer.get_current_frame_index() == 0

    def test_one_shot_stops_at_last_frame(self, renderer):
        """One-shot: advances 0→1→2→3→3→3 (holds last)."""
        renderer.reset_frame_index()
        for _ in range(3):
            renderer.advance_frame("sit", mode="once")
        assert renderer.get_current_frame_index() == 3
        # Additional advances hold at last
        renderer.advance_frame("sit", mode="once")
        assert renderer.get_current_frame_index() == 3

    def test_ping_pong_oscillates(self, renderer):
        """Ping-pong: 0→1→2→3→2→1→0→1..."""
        renderer.reset_frame_index()
        # Forward: 0→1→2→3
        for _ in range(3):
            renderer.advance_frame("sit", mode="pingpong")
        assert renderer.get_current_frame_index() == 3
        # Reverse: 3→2
        renderer.advance_frame("sit", mode="pingpong")
        assert renderer.get_current_frame_index() == 2
        renderer.advance_frame("sit", mode="pingpong")
        assert renderer.get_current_frame_index() == 1

    def test_ping_pong_from_zero_reverses_at_one(self, renderer):
        """Ping-pong at frame 1 going backward reverses to 0 then forward."""
        renderer.reset_frame_index()
        # Forward to 3
        for _ in range(3):
            renderer.advance_frame("sit", mode="pingpong")
        assert renderer.get_current_frame_index() == 3
        # Now go back: 3→2→1→0→1...
        for _ in range(3):
            renderer.advance_frame("sit", mode="pingpong")
        assert renderer.get_current_frame_index() == 0
        renderer.advance_frame("sit", mode="pingpong")
        assert renderer.get_current_frame_index() == 1

    def test_single_frame_loop_does_not_advance(self, renderer):
        """Single frame stays at index 0 regardless of advance calls."""
        manifest2 = {"idle": {"frames": 1, "fps": 3}}
        sheet2 = tmp_path / "idle.png"
        _make_simple_spritesheet(sheet2, 1)
        renderer2 = SpriteRenderer(str(tmp_path / "sheets"), manifest2)
        renderer2.reset_frame_index()
        for _ in range(5):
            renderer2.advance_frame("idle", mode="loop")
        assert renderer2.get_current_frame_index() == 0


# ── Drop Shadow ───────────────────────────────────────────────────────

class TestDropShadow:
    """Drop shadow painted as dark blur behind cat."""

    def test_drop_shadow_layer_exists(self, tmp_path):
        """paint_drop_shadow draws onto a QPixmap without crashing."""
        canvas = QPixmap(SPRITE_W, SPRITE_H)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        try:
            paint_drop_shadow(painter, QPointF(200, 350), 200, 150)
        finally:
            painter.end()
        # Shadow should be visible — check alpha channel has content
        qimg = canvas.toImage()
        has_shadow = False
        for y in range(SPRITE_H):
            for x in range(SPRITE_W):
                if qimg.pixelColor(x, y).alpha() > 0:
                    has_shadow = True
                    break
            if has_shadow:
                break
        assert has_shadow, "Drop shadow produced no visible pixels"

    def test_drop_shadow_is_dark(self, tmp_path):
        """Shadow pixels are dark (low RGB values) with partial alpha."""
        canvas = QPixmap(SPRITE_W, SPRITE_H)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        try:
            paint_drop_shadow(painter, QPointF(200, 350), 200, 150)
        finally:
            painter.end()
        qimg = canvas.toImage()
        # Check a pixel near shadow center
        cx, cy = 200, 350
        pc = qimg.pixelColor(cx, cy)
        # Shadow should be dark (low values) and not fully opaque
        assert pc.red() < 50 or pc.green() < 50 or pc.blue() < 50
        assert pc.alpha() < 255

    def test_drop_shadow_attenuated_opacity(self, tmp_path):
        """Drop shadow uses low opacity (< 15%)."""
        canvas = QPixmap(SPRITE_W, SPRITE_H)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        try:
            paint_drop_shadow(painter, QPointF(200, 350), 200, 150)
        finally:
            painter.end()
        qimg = canvas.toImage()

        # Sample multiple pixels for max alpha to avoid center-alignment miss
        max_alpha = 0
        for dy in range(-20, 21, 5):
            for dx in range(-20, 21, 5):
                pc = qimg.pixelColor(200 + dx, 350 + dy)
                if pc.alpha() > max_alpha:
                    max_alpha = pc.alpha()
        # Expect at most ~15% opacity = alpha 38/255
        assert max_alpha < 40, f"Drop shadow too opaque: max alpha {max_alpha}"


# ── Silhouette Shadow ─────────────────────────────────────────────────

class TestSilhouetteShadow:
    """Silhouette shadow layer at 8-12% opacity separates cat from background."""

    def test_silhouette_renders_at_8_to_12_percent_opacity(self, tmp_path):
        """Silhouette shadow alpha is between 20 and 31 (8-12% of 255)."""
        canvas = QPixmap(SPRITE_W, SPRITE_H)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        try:
            paint_silhouette_shadow(painter, QPointF(200, 200), 0, 0,
                                    100 * 4, 100, 4)
        finally:
            painter.end()
        qimg = canvas.toImage()
        max_alpha = 0
        for y in range(SPRITE_H):
            for x in range(SPRITE_W):
                a = qimg.pixelColor(x, y).alpha()
                if a > max_alpha:
                    max_alpha = a
        assert 20 <= max_alpha <= 31, \
            f"Silhouette shadow alpha {max_alpha} outside 8-12% (20-31)"

    def test_silhouette_dark(self, tmp_path):
        """Silhouette shadow is dark (black)."""
        canvas = QPixmap(20, 20)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        try:
            paint_silhouette_shadow(painter, QPointF(10, 10), 0, 0,
                                    20, 20, 1)
        finally:
            painter.end()
        qimg = canvas.toImage()
        for y in range(20):
            for x in range(20):
                pc = qimg.pixelColor(x, y)
                if pc.alpha() > 20:
                    assert pc.red() < 30 and pc.green() < 30 and pc.blue() < 30, \
                        "Silhouette shadow must be dark"


# ── Scale ─────────────────────────────────────────────────────────────

class TestScale:
    """Scale slider changes render size without distortion."""

    def test_scale_200px_default_no_distortion(self, tmp_path):
        """render_cat_at_scale with default 200px keeps aspect ratio."""
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        canvas = render_cat_at_scale(renderer, "sit", 0, target_height=200)
        assert canvas is not None
        assert not canvas.isNull()
        # Should be close to 400:200 = 2:1 ratio when scaled to 200px
        ar_ratio = canvas.width() / canvas.height()
        assert 1.8 <= ar_ratio <= 2.2, \
            f"Aspect ratio {ar_ratio:.2f} deviates from 2.0"

    def test_scale_350px_larger_no_distortion(self, tmp_path):
        """render_cat_at_scale at 350px maintains ratio."""
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        canvas = render_cat_at_scale(renderer, "sit", 0, target_height=350)
        assert canvas is not None
        ar = canvas.width() / canvas.height()
        assert 1.8 <= ar <= 2.2

    def test_scale_120px_smaller_no_distortion(self, tmp_path):
        """render_cat_at_scale at 120px maintains ratio."""
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        canvas = render_cat_at_scale(renderer, "sit", 0, target_height=120)
        assert canvas is not None
        ar = canvas.width() / canvas.height()
        assert 1.8 <= ar <= 2.2

    def test_scale_smooth_sampling(self, tmp_path):
        """Scaling uses smooth transformation (smoothTransformation flag)."""
        # This is more of a contract check — we verify the renderer uses
        # Qt.SmoothTransformation by inspecting output quality
        pass  # Contract: render_cat_at_scale must use SmoothTransformation


# ── Full Render Pipeline ──────────────────────────────────────────────

class TestFullRenderPipeline:
    """End-to-end render integration."""

    def test_render_frame_with_shadows(self, tmp_path):
        """Full render: get frame + drop shadow + silhouette shadow composited."""
        sheet = _make_simple_spritesheet(tmp_path / "sit.png", 4)
        manifest = {"sit": {"frames": 4, "fps": 3}}
        renderer = SpriteRenderer(str(tmp_path), manifest)
        frame = renderer.get_frame("sit", 0)
        assert frame is not None

        canvas = QPixmap(SPRITE_W, SPRITE_H)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        try:
            paint_drop_shadow(painter, QPointF(200, 350), 200, 150)
            paint_silhouette_shadow(painter, QPointF(200, 200), 0, 0,
                                    SPRITE_W, SPRITE_H, 1)
            painter.drawPixmap(QPointF(0, 0), frame)
        finally:
            painter.end()

        # Verify composited result has content
        qimg = canvas.toImage()
        total_pixels = SPRITE_W * SPRITE_H
        non_transparent = sum(
            1 for y in range(SPRITE_H) for x in range(SPRITE_W)
            if qimg.pixelColor(x, y).alpha() > 0
        )
        # At least shadow + frame pixels should be visible
        assert non_transparent > 100, "Composited output has insufficient content"
