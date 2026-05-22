"""
core/renderer.py — Sprite-based rendering engine for Desktop Cat.

Provides SpriteRenderer which loads spritesheets, slices them into QPixmap
frames, and blits the current frame at the cat's position.  Includes drop
shadow, silhouette shadow layer, and crossfade transitions.  Falls back to
the old QPainter procedural cat when sprites are missing.
"""

import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import Qt, QRectF, QElapsedTimer, QPointF
from PyQt6.QtGui import (
    QPainter,
    QPixmap,
    QColor,
    QPainterPath,
)

import config


logger = logging.getLogger(__name__)


# ─── Easing ────────────────────────────────────────────────────────────


def ease_in_out_cubic(t: float) -> float:
    """InOutCubic easing function.  t in [0, 1], returns [0, 1]."""
    if t < 0.5:
        return 4.0 * t * t * t
    else:
        return 1.0 - pow(-2.0 * t + 2.0, 3.0) / 2.0


# ─── Crossfade State ───────────────────────────────────────────────────


class Crossfade:
    """Manages a single crossfade transition between two states."""

    __slots__ = ("active", "elapsed", "duration", "from_state", "to_state")

    def __init__(self) -> None:
        self.active = False
        self.elapsed = 0.0
        self.duration: float = config.CROSSFADE_MS / 1000.0
        self.from_state: Optional[str] = None
        self.to_state: Optional[str] = None

    def start(self, from_state: str, to_state: str) -> None:
        """Begin a crossfade transition."""
        self.active = True
        self.elapsed = 0.0
        self.from_state = from_state
        self.to_state = to_state

    def update(self, dt: float) -> Optional[str]:
        """Advance the crossfade.  Returns current animation state when done."""
        if not self.active or not self.to_state:
            return None
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            result = self.to_state
            self.to_state = None
            self.from_state = None
            return result
        return None

    @property
    def progress(self) -> float:
        """Normalized progress [0, 1]."""
        if not self.active or self.duration <= 0:
            return 1.0
        return min(self.elapsed / self.duration, 1.0)

    @property
    def eased(self) -> float:
        """Eased progress for opacity blending."""
        return ease_in_out_cubic(self.progress)


# ─── Animation State ───────────────────────────────────────────────────


class AnimationState:
    """Tracks the playback state of one animation loop."""

    __slots__ = ("current_frame", "elapsed", "fps_override")

    def __init__(self, fps_override: Optional[float] = None) -> None:
        self.current_frame = 0
        self.elapsed = 0.0
        self.fps_override: Optional[float] = fps_override

    def advance(self, dt: float, frame_count: int, anim_type: str) -> int:
        """Advance the animation by dt seconds.  Returns the current frame index."""
        if frame_count <= 0:
            return 0
        self.elapsed += dt
        # Determine frame duration in seconds
        fps = self.fps_override or 8.0
        frame_duration = 1.0 / fps if fps > 0 else 0.1
        frames_to_advance = int(self.elapsed / frame_duration)
        if frames_to_advance > 0:
            self.elapsed -= frames_to_advance * frame_duration
            if anim_type == "loop":
                self.current_frame = (self.current_frame + frames_to_advance) % frame_count
            elif anim_type in ("one-shot", "transition"):
                new_frame = self.current_frame + frames_to_advance
                if new_frame >= frame_count:
                    self.current_frame = frame_count - 1  # hold on last frame
                else:
                    self.current_frame = new_frame
        return self.current_frame


# ─── Sprite Loader ─────────────────────────────────────────────────────


class SpriteLoader:
    """Loads and caches spritesheet pixmaps and slices."""

    def __init__(self, sprites_dir: str) -> None:
        self._sprites_dir = sprites_dir
        self._sheets: dict[str, QPixmap] = {}
        self._frames: dict[str, list[QPixmap]] = {}
        self._manifest: dict[str, Any] = {}
        self._loaded = False

    def load(self) -> bool:
        """Load all spritesheets from the manifest.  Returns True if any loaded."""
        manifest_path = os.path.join(self._sprites_dir, "sprite_manifest.json")
        if not os.path.isfile(manifest_path):
            logger.info("No sprite manifest found at %s", manifest_path)
            return False

        try:
            with open(manifest_path) as f:
                self._manifest = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load sprite manifest: %s", e)
            return False

        animations = self._manifest.get("animations", {})
        if not animations:
            return False

        loaded_any = False
        for anim_name, info in animations.items():
            rel_path = info.get("path", f"{anim_name}.png")
            full_path = os.path.join(self._sprites_dir, rel_path)
            if not os.path.isfile(full_path):
                logger.debug("Spritesheet not found: %s", full_path)
                continue
            pix = QPixmap(full_path)
            if pix.isNull():
                logger.warning("Failed to load spritesheet: %s", full_path)
                continue

            self._sheets[anim_name] = pix
            frame_count = info.get("frames", 1)
            frame_w = self._manifest.get("frame_size", [400, 400])[0]
            frame_h = self._manifest.get("frame_size", [400, 400])[1]
            slices: list[QPixmap] = []
            for i in range(frame_count):
                slice_pix = pix.copy(i * frame_w, 0, frame_w, frame_h)
                slices.append(slice_pix)
            self._frames[anim_name] = slices
            loaded_any = True

        if loaded_any:
            logger.info(
                "Loaded %d spritesheets from %s",
                len(self._frames),
                self._sprites_dir,
            )
        return loaded_any

    def get_frames(self, anim_name: str) -> list[QPixmap]:
        """Get cached frames.  Returns empty list if not loaded."""
        return self._frames.get(anim_name, [])

    def get_frame(self, anim_name: str, idx: int) -> Optional[QPixmap]:
        """Get a single cached frame.  Returns None if not found."""
        frames = self._frames.get(anim_name)
        if frames and 0 <= idx < len(frames):
            return frames[idx]
        return None

    @property
    def has_sprites(self) -> bool:
        return bool(self._frames)

    def get_anim_info(self, anim_name: str) -> dict[str, Any]:
        """Get manifest info for an animation.  Returns empty dict if not found."""
        return self._manifest.get("animations", {}).get(anim_name, {})


# ─── SpriteRenderer ────────────────────────────────────────────────────


class SpriteRenderer:
    """Main rendering engine that draws the cat using sprites.

    Coordinates sprite selection, animation playback, crossfade transitions,
    shadow layers, and graceful fallback to procedural QPainter drawing.
    """

    def __init__(self, sprites_dir: str = "") -> None:
        self._sprites_dir = sprites_dir or os.path.join(
            os.path.dirname(__file__), "..", "assets", "sprites"
        )
        self._loader = SpriteLoader(self._sprites_dir)
        self._crossfade = Crossfade()
        self._anim_states: dict[str, AnimationState] = {}
        self._previous_state: Optional[str] = None
        self._current_anim: Optional[str] = None
        self._fallback_active = True  # starts in fallback until loaded

        # Shadow precomputed
        self._shadow_pix: Optional[QPixmap] = None
        self._silhouette_pix: Optional[QPixmap] = None

        # Cached scaled pixmaps (keyed by anim_name + scale_factor)
        self._scaled_cache: dict[tuple[str, float], list[QPixmap]] = {}

        # Attempt to load sprites
        if self._loader.load():
            self._fallback_active = False
            logger.info("Sprite renderer active, fallback disabled.")
        else:
            logger.info("No sprites found — using QPainter fallback.")

    # ─── Properties ──────────────────────────────────────────────────

    @property
    def using_sprites(self) -> bool:
        return not self._fallback_active

    @property
    def using_fallback(self) -> bool:
        return self._fallback_active

    # ─── Drawing ─────────────────────────────────────────────────────

    def draw(
        self,
        cat: Any,
        painter: QPainter,
        dt: float,
        draw_fallback_fn: Optional[callable] = None,
    ) -> None:
        """Draw the cat at its current position.

        Args:
            cat: Cat object (dict-like with x, y, facing, state, coat keys).
            painter: Active QPainter.
            dt: Delta time in seconds.
            draw_fallback_fn: Callable(cat, painter) for legacy QPainter drawing.
        """
        if self._fallback_active:
            if draw_fallback_fn:
                draw_fallback_fn(cat, painter)
            return

        cx = float(getattr(cat, "x", cat.get("x", 500.0)))
        cy = float(getattr(cat, "y", cat.get("y", 700.0)))
        state_str = getattr(cat, "state", cat.get("state", "SIT"))
        facing = bool(getattr(cat, "facing", cat.get("facing", True)))
        coat_index = int(getattr(cat, "coat", cat.get("coat", 0)))

        # Map cat state to animation name
        anim_name = self._state_to_anim(state_str, cat)

        # Detect state transition → trigger crossfade
        if anim_name != self._current_anim:
            if self._current_anim is not None and anim_name is not None:
                if not self._crossfade.active:
                    self._crossfade.start(self._current_anim, anim_name)
            self._current_anim = anim_name

        # Advance crossfade
        completed_anim = self._crossfade.update(dt)
        if completed_anim:
            self._current_anim = completed_anim

        # Advance animation state
        anim_info = self._loader.get_anim_info(anim_name or "")
        if anim_name:
            frame_count = anim_info.get("frames", 1)
            anim_type = anim_info.get("type", "loop")
            fps = anim_info.get("fps", 8)
            state = self._get_anim_state(anim_name)
            state.fps_override = fps
            frame_idx = state.advance(dt, frame_count, anim_type)
        else:
            frame_idx = 0

        # Get sprite scale
        scale = config.CAT_SIZE_DEFAULT / config.SPRITE_SIZE

        # Draw shadow layer first
        self._draw_shadow(painter, cx, cy, scale)

        # Draw silhouette shadow (separates from busy backgrounds)
        if config.SILHOUETTE_SHADOW:
            self._draw_silhouette(painter, cx, cy, scale, cat, draw_fallback_fn, anim_name, frame_idx)

        # Determine which pixmap to draw
        if self._crossfade.active and self._crossfade.from_state:
            self._draw_crossfade(
                painter, cx, cy, scale, facing,
                cat, draw_fallback_fn,
                self._crossfade.from_state,
                anim_name or "",
                frame_idx,
            )
        else:
            pix = self._get_scaled_frame(anim_name or "", frame_idx, scale)
            if pix is not None and not pix.isNull():
                self._blit(painter, pix, cx, cy, facing, scale)
            elif draw_fallback_fn and self._current_anim:
                # Fallback per-frame
                draw_fallback_fn(cat, painter)

    # ─── Crossfade drawing ───────────────────────────────────────────

    def _draw_crossfade(
        self,
        painter: QPainter,
        cx: float, cy: float, scale: float, facing: bool,
        cat: Any,
        draw_fallback_fn: Optional[callable],
        from_anim: str,
        to_anim: str,
        to_frame_idx: int,
    ) -> None:
        """Blend between two sprites using opacity."""
        progress = self._crossfade.eased  # 0→1

        # Draw "to" pixmap fading in
        to_pix = self._get_scaled_frame(to_anim, to_frame_idx, scale)
        if to_pix is not None and not to_pix.isNull():
            painter.save()
            painter.setOpacity(progress)
            self._blit(painter, to_pix, cx, cy, facing, scale)
            painter.restore()
        elif draw_fallback_fn:
            draw_fallback_fn(cat, painter)
            return

        # Draw "from" pixmap fading out (same frame index)
        from_frame = self._get_anim_state(from_anim).current_frame
        from_pix = self._get_scaled_frame(from_anim, from_frame, scale)
        if from_pix is not None and not from_pix.isNull():
            painter.save()
            painter.setOpacity(1.0 - progress)
            self._blit(painter, from_pix, cx, cy, facing, scale)
            painter.restore()

    # ─── Shadow drawing ──────────────────────────────────────────────

    def _draw_shadow(self, painter: QPainter, cx: float, cy: float, scale: float) -> None:
        """Draw the drop shadow ellipse below the cat."""
        shadow_w = int(36 * scale)
        shadow_h = int(10 * scale)

        if self._shadow_pix is None or self._shadow_pix.size().width() != shadow_w:
            self._shadow_pix = self._make_shadow_pixmap(shadow_w, shadow_h)

        opacity = config.SHADOW_OPACITY
        painter.save()
        painter.setOpacity(opacity)
        painter.drawPixmap(
            int(cx - shadow_w // 2),
            int(cy - shadow_h // 2 + 4 * scale),
            self._shadow_pix,
        )
        painter.restore()

    def _make_shadow_pixmap(self, w: int, h: int) -> QPixmap:
        """Create a soft shadow ellipse pixmap."""
        from PyQt6.QtGui import QPixmap, QPainter as QP, QPainterPath, QColor
        pix = QPixmap(w, h)
        pix.fill(Qt.GlobalColor.transparent)
        p = QP(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, w, h)
        p.fillPath(path, QColor(0, 0, 0, 60))
        p.end()
        return pix

    def _draw_silhouette(
        self,
        painter: QPainter,
        cx: float, cy: float, scale: float,
        cat: Any,
        draw_fallback_fn: Optional[callable],
        anim_name: Optional[str],
        frame_idx: int,
    ) -> None:
        """Draw a dark silhouette blur behind the cat to separate from busy backgrounds."""
        if not anim_name:
            return
        pix = self._get_scaled_frame(anim_name, frame_idx, scale)
        if pix is None or pix.isNull():
            return

        # Create a dark, blurred version
        sil_w = pix.width()
        sil_h = pix.height()
        key = ("_silhouette", frame_idx, scale)
        if key not in self._scaled_cache:
            sil = QPixmap(pix.size())
            sil.fill(Qt.GlobalColor.transparent)
            sp = QPainter(sil)
            sp.setRenderHint(QPainter.RenderHint.Antialiasing)
            # Draw dark version at low opacity
            sp.setOpacity(0.12)
            sp.drawPixmap(0, 0, pix)
            sp.end()
            self._scaled_cache[key] = [sil]

        painter.save()
        painter.setOpacity(0.10)
        offset_x = int(-3 * scale)
        offset_y = int(2 * scale)
        painter.drawPixmap(
            int(cx - sil_w // 2 + offset_x),
            int(cy - sil_h // 2 + offset_y),
            self._scaled_cache[key][0],
        )
        painter.restore()

    # ─── Blit helper ─────────────────────────────────────────────────

    def _blit(
        self, painter: QPainter, pix: QPixmap,
        cx: float, cy: float, facing: bool, scale: float,
    ) -> None:
        """Blit a sprite pixmap at the cat position, handling facing direction."""
        pw = pix.width()
        ph = pix.height()

        if not facing:
            # Flip horizontally
            painter.save()
            painter.translate(int(cx), int(cy - ph // 2))
            painter.scale(-1.0, 1.0)
            painter.drawPixmap(
                -pw // 2, 0, pix,
            )
            painter.restore()
        else:
            painter.drawPixmap(
                int(cx - pw // 2),
                int(cy - ph // 2),
                pix,
            )

    # ─── State → Animation mapping ───────────────────────────────────

    def _state_to_anim(self, state_str: str, cat: Any) -> str:
        """Map CatState string to spritesheet animation name."""
        mapping = {
            config.STATE_SIT: "sit_alert",
            config.STATE_WALK: "walk",
            config.STATE_WANDER: "walk",
            config.STATE_CHASE: "trot",
            config.STATE_PLAY: "trot",
            config.STATE_SLEEP: "sleep_curled",
            config.STATE_GO_HOME: "walk",
        }
        return mapping.get(state_str, "sit_alert")

    # ─── Animation state management ──────────────────────────────────

    def _get_anim_state(self, anim_name: str) -> AnimationState:
        """Get (or create) the AnimationState for the given animation name."""
        if anim_name not in self._anim_states:
            self._anim_states[anim_name] = AnimationState()
        return self._anim_states[anim_name]

    def _get_scaled_frame(
        self, anim_name: str, frame_idx: int, scale: float,
    ) -> Optional[QPixmap]:
        """Get a cached scaled sprite frame.

        Returns None if the frame is not available.
        """
        cache_key = (anim_name, round(scale, 3))
        if cache_key in self._scaled_cache:
            frames = self._scaled_cache[cache_key]
            if 0 <= frame_idx < len(frames):
                return frames[frame_idx]

        # Load and scale
        raw = self._loader.get_frame(anim_name, frame_idx)
        if raw is None:
            return None

        new_w = max(1, int(raw.width() * scale))
        new_h = max(1, int(raw.height() * scale))

        scaled = raw.scaled(
            new_w, new_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Build cache list for this anim+scale
        frames_list = self._scaled_cache.get(cache_key, [])
        while len(frames_list) <= frame_idx:
            # Fill missing frames
            raw_fill = self._loader.get_frame(anim_name, len(frames_list))
            if raw_fill is None:
                fill = QPixmap(new_w, new_h)
                fill.fill(Qt.GlobalColor.transparent)
            else:
                fill = raw_fill.scaled(
                    new_w, new_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            frames_list.append(fill)
        self._scaled_cache[cache_key] = frames_list

        return frames_list[frame_idx]

    # ─── Reset ───────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset all animation and crossfade state."""
        self._anim_states.clear()
        self._scaled_cache.clear()
        self._crossfade = Crossfade()
        self._current_anim = None
        self._previous_state = None

    def reload(self) -> bool:
        """Reload sprites from disk.  Returns True if sprites loaded."""
        self.reset()
        self._loader = SpriteLoader(self._sprites_dir)
        loaded = self._loader.load()
        self._fallback_active = not loaded
        return loaded
