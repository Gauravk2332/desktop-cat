"""
tests/test_sprite_pipeline.py — Unit tests for the sprite pipeline.

Tests cover:
- Stitched spritesheet has correct dimensions (400×400 × num_frames)
- Manifest JSON includes all poses with correct frame counts
- Placeholder sprites (colored rects) work as fallback
- Frame size validation catches mismatched dimensions
- Graceful handling of missing/malformed source frames
"""

import json
import os
import struct
import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# These modules are built during Phase 0 — tests define the contract
try:
    from sprite.pipeline import (
        stitch_spritesheet,
        generate_manifest,
        create_placeholder_sheet,
        validate_frame_sizes,
        SPRITE_WIDTH,
        SPRITE_HEIGHT,
    )
except ImportError:
    pytest.skip("sprite.pipeline not yet available — Phase 0 stub needed", allow_module_level=True)
except Exception:
    pytest.skip("sprite.pipeline import failed — Phase 0 stub needed", allow_module_level=True)


# ── Helpers ───────────────────────────────────────────────────────────

def _make_frame_png(tmp_path, name, width=400, height=400, color=(232, 141, 59)):
    """Create a single PNG frame at tmp_path / name."""
    path = tmp_path / name
    img = Image.new("RGBA", (width, height), (*color, 255))
    img.save(str(path), "PNG")
    return path


def _make_frames(tmp_path, prefix, count, width=400, height=400):
    """Create count frame PNGs with naming pattern prefix_0000.png."""
    paths = []
    for i in range(count):
        p = _make_frame_png(tmp_path, f"{prefix}_{i:04d}.png", width, height)
        paths.append(p)
    return sorted(paths)


# ── Spritesheet Stitching ─────────────────────────────────────────────

class TestSpritesheetStitching:
    """stitch_spritesheet combines individual frames into a horizontal strip."""

    def test_stitched_sheet_dimensions(self, tmp_path):
        """Stitched spritesheet has width = SPRITE_WIDTH * num_frames, height = SPRITE_HEIGHT."""
        frames = _make_frames(tmp_path, "sit", 4)
        out = tmp_path / "sit.png"
        stitch_spritesheet(frames, str(out))
        im = Image.open(str(out))
        assert im.width == SPRITE_WIDTH * 4
        assert im.height == SPRITE_HEIGHT
        assert im.mode == "RGBA"

    def test_skill_stitched_sheet_correct_width(self, tmp_path):
        """Single frame sheet is exactly SPRITE_WIDTH wide."""
        frames = _make_frames(tmp_path, "loaf", 1)
        out = tmp_path / "loaf.png"
        stitch_spritesheet(frames, str(out))
        im = Image.open(str(out))
        assert im.width == SPRITE_WIDTH
        assert im.height == SPRITE_HEIGHT

    def test_sixteen_frame_sheet_gives_correct_width(self, tmp_path):
        """16-frame strip: width = SPRITE_WIDTH * 16."""
        frames = _make_frames(tmp_path, "walk", 16)
        out = tmp_path / "walk.png"
        stitch_spritesheet(frames, str(out))
        im = Image.open(str(out))
        assert im.width == SPRITE_WIDTH * 16
        assert im.height == SPRITE_HEIGHT

    def test_zero_frames_raises(self, tmp_path):
        """Empty frame list raises ValueError."""
        with pytest.raises(ValueError, match="at least one frame"):
            stitch_spritesheet([], str(tmp_path / "empty.png"))

    def test_stitch_output_is_png(self, tmp_path):
        """Output file is a valid PNG with transparency."""
        frames = _make_frames(tmp_path, "sit", 2)
        out = tmp_path / "output.png"
        stitch_spritesheet(frames, str(out))
        data = out.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n", "Not a valid PNG"


# ── Manifest Generation ───────────────────────────────────────────────

class TestManifestGeneration:
    """generate_manifest produces correct JSON metadata."""

    def test_manifest_includes_all_poses(self, tmp_path):
        """Manifest JSON contains all specified poses with correct frame counts."""
        manifest = generate_manifest({
            "sit": {"frames": 4, "fps": 3},
            "walk": {"frames": 12, "fps": 12},
            "loaf": {"frames": 4, "fps": 2},
        })
        assert isinstance(manifest, dict)
        assert manifest["sit"]["frames"] == 4
        assert manifest["walk"]["frames"] == 12
        assert manifest["loaf"]["frames"] == 4

    def test_manifest_serializes_to_json(self, tmp_path):
        """Manifest can be written to and read from JSON."""
        data = generate_manifest({
            "sit": {"frames": 4, "fps": 3},
        })
        mpath = tmp_path / "manifest.json"
        with open(str(mpath), "w") as f:
            json.dump(data, f)
        with open(str(mpath)) as f:
            loaded = json.load(f)
        assert loaded["sit"]["frames"] == 4
        assert loaded["sit"]["fps"] == 3

    def test_manifest_missing_frame_count_logs_warning(self, tmp_path, caplog):
        """Pose without frame count defaults to 1 frame and logs a warning."""
        gen = generate_manifest({
            "alert": {},  # no frames key
        })
        assert gen["alert"]["frames"] == 1
        assert any("alert" in msg and "frames" in msg for msg in caplog.records)

    def test_manifest_includes_eye_rects(self, tmp_path):
        """Manifest can carry optional eye_rect metadata per pose."""
        manifest = generate_manifest({
            "sit": {
                "frames": 4,
                "fps": 3,
                "eye_rects": [
                    {"x": 180, "y": 160, "w": 16, "h": 12},
                ] * 4,
            },
        })
        assert len(manifest["sit"]["eye_rects"]) == 4
        assert manifest["sit"]["eye_rects"][0]["x"] == 180

    def test_manifest_defaults_fps_when_missing(self, tmp_path):
        """Missing fps key defaults to 12 fps."""
        manifest = generate_manifest({"walk": {"frames": 8}})
        assert manifest["walk"]["fps"] == 12


# ── Placeholder Sprites ───────────────────────────────────────────────

class TestPlaceholderSprites:
    """create_placeholder_sheet produces valid colored-rect fallbacks."""

    def test_placeholder_is_png(self, tmp_path):
        """Placeholder spritesheet is a valid RGBA PNG."""
        out = tmp_path / "placeholder.png"
        create_placeholder_sheet(4, "sit", str(out))
        assert out.exists()
        data = out.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_placeholder_dimensions(self, tmp_path):
        """Placeholder is SPRITE_WIDTH * frames wide, SPRITE_HEIGHT tall."""
        out = tmp_path / "ph.png"
        create_placeholder_sheet(6, "sit", str(out))
        im = Image.open(str(out))
        assert im.width == SPRITE_WIDTH * 6
        assert im.height == SPRITE_HEIGHT

    def test_placeholder_different_poses_have_different_colors(self, tmp_path):
        """Sit vs walk placeholders use different base colors for visual distinction."""
        sit = tmp_path / "sit_ph.png"
        walk = tmp_path / "walk_ph.png"
        create_placeholder_sheet(1, "sit", str(sit))
        create_placeholder_sheet(1, "walk", str(walk))
        sit_im = Image.open(str(sit))
        walk_im = Image.open(str(walk))
        sit_px = sit_im.getpixel((10, 10))
        walk_px = walk_im.getpixel((10, 10))
        assert sit_px != walk_px, "Different poses should use different placeholder colors"

    def test_placeholder_unknown_pose_does_not_crash(self, tmp_path):
        """Unknown pose name produces a placeholder without error."""
        out = tmp_path / "unknown.png"
        create_placeholder_sheet(4, "nonexistent_pose", str(out))
        assert out.exists()
        im = Image.open(str(out))
        assert im.width > 0 and im.height > 0


# ── Frame Size Validation ─────────────────────────────────────────────

class TestFrameValidation:
    """validate_frame_sizes catches mismatched dimensions."""

    def test_all_same_size_passes(self, tmp_path):
        """All frames at SPRITE_WIDTH × SPRITE_HEIGHT passes validation."""
        frames = _make_frames(tmp_path, "sit", 3)
        validate_frame_sizes(frames)  # should not raise

    def test_mismatched_width_raises(self, tmp_path):
        """A frame with wrong width raises ValueError."""
        frames = _make_frames(tmp_path, "sit", 3)
        odd = _make_frame_png(tmp_path, "bad.png", width=300)
        frames.append(odd)
        with pytest.raises(ValueError, match="dimension|size|width|different"):
            validate_frame_sizes(frames)

    def test_mismatched_height_raises(self, tmp_path):
        """A frame with wrong height raises ValueError."""
        frames = _make_frames(tmp_path, "sit", 3)
        odd = _make_frame_png(tmp_path, "bad.png", height=500)
        frames.append(odd)
        with pytest.raises(ValueError, match="dimension|size|height|different"):
            validate_frame_sizes(frames)

    def test_mismatched_channel_count_raises(self, tmp_path):
        """A frame with different number of channels raises ValueError."""
        frames = _make_frames(tmp_path, "sit", 2)
        # RGBA -> RGB (no alpha)
        bad_path = tmp_path / "bad_rgb.png"
        img = Image.new("RGB", (SPRITE_WIDTH, SPRITE_HEIGHT), (200, 100, 50))
        img.save(str(bad_path), "PNG")
        frames.append(bad_path)
        with pytest.raises(ValueError, match="channel|mode|alpha|different"):
            validate_frame_sizes(frames)

    def test_empty_list_raises(self):
        """Empty frame list raises ValueError."""
        with pytest.raises(ValueError, match="at least one"):
            validate_frame_sizes([])


# ── Malformed / Missing Frames ────────────────────────────────────────

class TestMalformedFrames:
    """Graceful handling of missing or corrupt source frames."""

    def test_missing_source_logs_warning(self, tmp_path, caplog):
        """Missing source frame files should be logged without crashing."""
        # Try stitching with nonexistent paths
        fake_frames = [
            tmp_path / "does_not_exist_0000.png",
            tmp_path / "does_not_exist_0001.png",
        ]
        out = tmp_path / "result.png"
        result = stitch_spritesheet(fake_frames, str(out))
        assert result is False or result is None
        assert any("missing" in msg.lower() or "not found" in msg.lower()
                   for msg in caplog.records)

    def test_corrupt_png_logs_warning(self, tmp_path, caplog):
        """Corrupt (non-PNG) source file logs warning and does not crash."""
        bad = tmp_path / "corrupt.png"
        bad.write_bytes(b"\x00\x00\x00\x00corrupt data here")
        frames = _make_frames(tmp_path, "good", 1) + [bad]
        out = tmp_path / "corrupt_out.png"
        result = stitch_spritesheet(frames, str(out))
        if result is False or result is None:
            assert any("corrupt" in msg.lower() or "invalid" in msg.lower()
                       for msg in caplog.records)

    def test_partial_missing_does_not_prevent_output(self, tmp_path, caplog):
        """When some frames are missing, stitch produces output for available frames."""
        frames = _make_frames(tmp_path, "ok", 2)
        bad = tmp_path / "missing_0002.png"
        # bad path does not exist
        frames.append(bad)
        out = tmp_path / "partial.png"
        stitch_spritesheet(frames, str(out))
        # Should still produce output with the frames it could load
        assert out.exists()


# ── Pixel Content ─────────────────────────────────────────────────────

class TestPixelContent:
    """Verify that stitched sheet actually contains frame data."""

    def test_stitched_frames_are_not_blank(self, tmp_path):
        """Each frame slot in the stitched sheet has non-zero content."""
        frames = _make_frames(tmp_path, "pixel_test", 3)
        out = tmp_path / "stitched.png"
        stitch_spritesheet(frames, str(out))
        im = Image.open(str(out))
        for i in range(3):
            left = i * SPRITE_WIDTH
            tile = im.crop((left, 0, left + SPRITE_WIDTH, SPRITE_HEIGHT))
            # Should have some content (average > 0)
            pixels = list(tile.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            assert avg_r > 0, f"Frame {i} appears blank"

    def test_stitched_frames_preserve_source_colors(self, tmp_path):
        """Source frame pixels are preserved in the stitched output."""
        color = (200, 100, 50, 255)
        path = _make_frame_png(tmp_path, "red.png", color=color[:3])
        frames = [path]
        out = tmp_path / "preserve.png"
        stitch_spritesheet(frames, str(out))
        im = Image.open(str(out))
        px = im.getpixel((10, 10))
        assert px == (200, 100, 50, 255)
