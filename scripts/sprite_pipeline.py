#!/usr/bin/env python3
"""
scripts/sprite_pipeline.py — Sprite sheet stitcher for Desktop Cat.

Takes individual PNG frames (400×400) and stitches them into horizontal
strip spritesheets.  Generates a sprite manifest JSON.

Usage:
    python scripts/sprite_pipeline.py <frames_dir> [--dry-run] [--output-dir assets/sprites]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


FRAME_SIZE = (400, 400)

ANIMATION_SPECS: dict[str, dict] = {
    "sit_alert": {"frames": 4, "fps": 3, "type": "loop"},
    "sit_relaxed": {"frames": 4, "fps": 3, "type": "loop"},
    "loaf": {"frames": 4, "fps": 2, "type": "loop"},
    "walk": {"frames": 12, "fps": 12, "type": "loop"},
    "trot": {"frames": 8, "fps": 15, "type": "loop"},
    "sleep_curled": {"frames": 6, "fps": 0.5, "type": "loop"},
    "sleep_sprawl": {"frames": 6, "fps": 0.5, "type": "loop"},
    "groom": {"frames": 12, "fps": 4, "type": "loop"},
    "stretch": {"frames": 8, "fps": 2.5, "type": "one-shot"},
    "yawn": {"frames": 4, "fps": 1.5, "type": "one-shot"},
    "sit_to_walk": {"frames": 6, "fps": 12, "type": "transition"},
    "walk_to_sit": {"frames": 6, "fps": 12, "type": "transition"},
    "sit_to_lie": {"frames": 6, "fps": 12, "type": "transition"},
    "lie_to_sit": {"frames": 6, "fps": 12, "type": "transition"},
    "sit_to_groom": {"frames": 6, "fps": 12, "type": "transition"},
    "groom_to_sit": {"frames": 6, "fps": 12, "type": "transition"},
    "walk_turn": {"frames": 6, "fps": 12, "type": "one-shot"},
    "startle": {"frames": 3, "fps": 6, "type": "one-shot"},
}


def discover_frames(
    frames_dir: str, anim_name: str, expected: int
) -> list[str]:
    """Find frame PNGs for an animation.  Supports naming conventions:

        {anim_name}_000.png, {anim_name}_001.png, ...
        {anim_name}_0.png,  {anim_name}_1.png, ...
    """
    pattern_base = os.path.join(frames_dir, anim_name)
    frames: list[str] = []

    # Try zero-padded first (3 digits), then 2 digits, then plain
    for pad in (3, 2, 0):
        if pad > 0:
            names = [
                f"{pattern_base}_{str(i).zfill(pad)}.png"
                for i in range(expected)
            ]
        else:
            names = [
                f"{pattern_base}_{i}.png" for i in range(expected)
            ]
        if all(os.path.isfile(n) for n in names):
            return names

    # Fallback: glob for anything with the anim name
    import glob as glob_mod
    candidates = sorted(glob_mod.glob(os.path.join(frames_dir, f"{anim_name}_*.png")))
    if len(candidates) >= expected:
        return candidates[:expected]

    return frames


def validate_frame_size(image: Image.Image, expected: tuple[int, int]) -> list[str]:
    """Return list of issues (empty = valid)."""
    issues: list[str] = []
    if image.size != expected:
        issues.append(
            f"expected {expected[0]}×{expected[1]}, got {image.size[0]}×{image.size[1]}"
        )
    return issues


def stitch_frames(
    frame_paths: list[str],
    output_path: str,
    frame_size: tuple[int, int],
    dry_run: bool = False,
) -> Optional[str]:
    """Stitch frames into a horizontal spritesheet.  Returns output path or None."""
    num_frames = len(frame_paths)

    if dry_run:
        print(f"[DRY-RUN] Would stitch {num_frames} frames → {output_path}")
        return None

    sheet = Image.new("RGBA", (frame_size[0] * num_frames, frame_size[1]), (0, 0, 0, 0))

    for i, fp in enumerate(frame_paths):
        try:
            frame = Image.open(fp).convert("RGBA")
        except Exception as e:
            print(f"  ERROR: cannot open {fp}: {e}", file=sys.stderr)
            return None

        issues = validate_frame_size(frame, frame_size)
        if issues:
            for issue in issues:
                print(f"  VALIDATION: {fp}: {issue}", file=sys.stderr)
            return None

        sheet.paste(frame, (i * frame_size[0], 0), frame)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sheet.save(output_path, "PNG")
    print(f"  Wrote {output_path} ({sheet.size[0]}×{sheet.size[1]})")
    return output_path


def generate_placeholder_colors(anim_name: str, num_frames: int) -> list[Image.Image]:
    """Generate placeholder colored rectangles for dry-run/dev mode."""
    colors = {
        "sit": (0xE8, 0x9B, 0x5D),
        "walk": (0xC4, 0x7A, 0x3C),
        "sleep": (0x7C, 0x8E, 0x9E),
        "groom": (0xE8, 0xD5, 0x3F),
        "stretch": (0x8B, 0xC3, 0x4A),
        "startle": (0xF0, 0x80, 0x80),
        "turn": (0xCC, 0xD5, 0xDC),
    }
    base = colors.get(anim_name[:5], (0xCC, 0xCC, 0xCC))
    frames: list[Image.Image] = []
    for i in range(num_frames):
        shift = int((i / max(num_frames - 1, 1)) * 20 - 10)
        r = max(0, min(255, base[0] + shift))
        g = max(0, min(255, base[1] + shift))
        b = max(0, min(255, base[2] + shift))
        img = Image.new("RGBA", FRAME_SIZE, (r, g, b, 255))
        # Draw a simple silhouette center
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        cx, cy = FRAME_SIZE[0] // 2, FRAME_SIZE[1] // 2
        # Body ellipse
        draw.ellipse(
            [cx - 60, cy - 80, cx + 60, cy + 40],
            fill=(r - 20, g - 20, b - 20, 255),
        )
        # Head circle
        draw.ellipse(
            [cx - 30, cy - 120, cx + 30, cy - 60],
            fill=(r, g, b, 255),
        )
        # Ears
        draw.polygon(
            [(cx - 25, cy - 100), (cx - 35, cy - 130), (cx - 10, cy - 105)],
            fill=(r, g, b, 255),
        )
        draw.polygon(
            [(cx + 25, cy - 100), (cx + 35, cy - 130), (cx + 10, cy - 105)],
            fill=(r, g, b, 255),
        )
        # Tail (if walking animation)
        if "walk" in anim_name or "trot" in anim_name:
            tx = cx + 80 + int(math.sin(i * 0.8) * 15)
            ty = cy - 10
            draw.line(
                [cx + 60, cy - 20, tx, ty],
                fill=(r - 25, g - 25, b - 25, 255),
                width=8,
            )
        frames.append(img)
    return frames


def build_manifest(
    output_dir: str, sheet_map: dict[str, str], eye_rects: Optional[dict] = None
) -> dict:
    """Build the sprite manifest JSON."""
    manifest: dict = {
        "format_version": "1.0",
        "frame_size": list(FRAME_SIZE),
        "animations": {},
    }

    for anim_name, sheet_path in sheet_map.items():
        spec = ANIMATION_SPECS.get(anim_name, {"frames": 4, "fps": 8, "type": "loop"})
        entry: dict = {
            "path": os.path.relpath(sheet_path, output_dir) if sheet_path else f"{anim_name}.png",
            "frames": spec["frames"],
            "fps": spec.get("fps", 8),
            "type": spec.get("type", "loop"),
        }
        if eye_rects and anim_name in eye_rects:
            entry["eye_rects"] = eye_rects[anim_name]
        manifest["animations"][anim_name] = entry

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stitch animation frames into horizontal spritesheets."
    )
    parser.add_argument(
        "frames_dir",
        help="Directory containing individual PNG frames.",
    )
    parser.add_argument(
        "--output-dir",
        default="assets/sprites",
        help="Output directory for spritesheets (default: assets/sprites)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode: create placeholder colored rectangles instead of stitching.",
    )
    parser.add_argument(
        "--animations",
        nargs="*",
        default=list(ANIMATION_SPECS.keys()),
        help="Specific animations to process (default: all).",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Only regenerate manifest, skip stitching.",
    )
    args = parser.parse_args()

    if Image is None:
        print("ERROR: PIL (Pillow) is required.  Install with: pip install Pillow")
        sys.exit(1)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    import math as _math
    global math
    math = _math  # for placeholder drawing

    sheet_map: dict[str, str] = {}
    total_frames = 0
    errors = 0

    for anim_name in args.animations:
        spec = ANIMATION_SPECS.get(anim_name)
        if spec is None:
            print(f"WARNING: Unknown animation '{anim_name}', skipping.")
            continue

        expected_frames = spec["frames"]
        output_path = os.path.join(output_dir, f"{anim_name}.png")

        if args.manifest_only:
            # Check if sheet already exists
            if os.path.isfile(output_path):
                sheet_map[anim_name] = output_path
            continue

        if args.dry_run:
            print(f"[DRY-RUN] Building {anim_name} ({expected_frames} frames):")
            frames = generate_placeholder_colors(anim_name, expected_frames)
            result = stitch_frames(
                [""] * expected_frames,  # won't be opened in dry-run stub
                output_path,
                FRAME_SIZE,
                dry_run=True,
            )
            if result:
                sheet_map[anim_name] = result
                total_frames += expected_frames
            continue

        # Real mode: discover frames
        frame_paths = discover_frames(args.frames_dir, anim_name, expected_frames)

        if not frame_paths:
            print(
                f"  WARNING: Could not find {expected_frames} frames for "
                f"'{anim_name}' in {args.frames_dir}.  "
                f"Generating placeholder instead."
            )
            placeholders = generate_placeholder_colors(anim_name, expected_frames)
            frame_paths = []
            for i, ph in enumerate(placeholders):
                ph_path = os.path.join(output_dir, f"_placeholder_{anim_name}_{i}.png")
                ph.save(ph_path)
                frame_paths.append(ph_path)

        print(f"  Stitching {anim_name} ({len(frame_paths)} frames):")
        result = stitch_frames(frame_paths, output_path, FRAME_SIZE)
        if result:
            sheet_map[anim_name] = result
            total_frames += len(frame_paths)
        else:
            errors += 1

    # Write manifest
    manifest = build_manifest(output_dir, sheet_map)
    manifest_path = os.path.join(output_dir, "sprite_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written: {manifest_path}")
    print(f"Total frames processed: {total_frames}")
    if errors:
        print(f"Errors: {errors}", file=sys.stderr)
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
