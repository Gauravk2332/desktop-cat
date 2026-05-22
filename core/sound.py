"""core/sound.py — Sound system for desktop-cat.

Tiered playback:
  1. QSoundEffect (lowest latency, loopable) — preferred on Windows
  2. winsound.PlaySound() — built-in, no deps
  3. Silent no-op fallback

All WAV assets live in assets/sounds/*.wav
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")


class SoundManager:
    """Plays WAV sound effects with automatic tiered fallback.

    Usage:
        sm = SoundManager()
        sm.play("purr")           # fire-and-forget
        sm.start_loop("purr")     # start looping
        sm.stop_loop()            # stop current loop
        sm.set_enabled(False)     # mute all
    """

    def __init__(self):
        self._enabled = True
        self._tier = self._detect_best_tier()
        self._player = None  # QSoundEffect instance (tier 1)
        self._active_shots: list = []  # keep one-shot effects alive until finish
        logger.info("SoundManager initialized (tier=%d)", self._tier)

    # ── Tier Detection ────────────────────────────────────────

    @staticmethod
    def _detect_best_tier() -> int:
        """Detect best available audio backend. Returns 1, 2, or 0 (silent)."""
        # Tier 1: QSoundEffect
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl
            # Quick smoke test
            _ = QSoundEffect.__new__
            logger.debug("QSoundEffect available (tier 1)")
            return 1
        except (ImportError, TypeError):
            pass

        # Tier 2: winsound (Windows built-in)
        try:
            import winsound
            _ = winsound.PlaySound
            logger.debug("winsound available (tier 2)")
            return 2
        except (ImportError, AttributeError):
            pass

        logger.warning("No audio backend found — sound disabled")
        return 0

    # ── Public API ────────────────────────────────────────────

    def set_enabled(self, enabled: bool):
        """Enable or disable all sound playback."""
        self._enabled = enabled
        if not enabled:
            self.stop_loop()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def play(self, name: str):
        """Play a sound effect once. Fire-and-forget.

        Args:
            name: Sound name (e.g. 'purr', 'meow_short', 'footstep')
                  — without .wav extension.
        """
        if not self._enabled or self._tier == 0:
            return

        path = self._resolve_path(name)
        if path is None:
            return

        if self._tier == 1:
            self._play_tier1(path)
        elif self._tier == 2:
            self._play_tier2(path)

    def start_loop(self, name: str):
        """Start looping a sound. Stops any current loop first."""
        self.stop_loop()

        if not self._enabled or self._tier == 0:
            return

        path = self._resolve_path(name)
        if path is None:
            return

        if self._tier == 1:
            self._start_loop_tier1(path)

    def stop_loop(self):
        """Stop any currently looping sound."""
        if self._tier == 1 and self._player is not None:
            try:
                self._player.stop()
                self._player = None
            except RuntimeError:
                self._player = None

    # ── Path Resolution ───────────────────────────────────────

    def _resolve_path(self, name: str) -> Optional[str]:
        """Find WAV file for given sound name."""
        # Try with extension first
        path = os.path.join(SOUNDS_DIR, name)
        if os.path.exists(path):
            return path
        path = os.path.join(SOUNDS_DIR, f"{name}.wav")
        if os.path.exists(path):
            return path
        logger.warning("Sound not found: %s", name)
        return None

    # ── Tier 1: QSoundEffect ─────────────────────────────────

    def _play_tier1(self, path: str):
        """Play via QSoundEffect (fire-and-forget).

        Keeps a reference to the effect until playback completes to
        prevent Python GC from collecting it before Qt can play.
        """
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            effect.setVolume(0.7)
            effect.playingChanged.connect(lambda: self._on_shot_finished(effect))
            effect.play()
            self._active_shots.append(effect)
        except Exception as e:
            logger.warning("QSoundEffect play failed: %s", e)

    def _on_shot_finished(self, effect) -> None:
        """Remove finished one-shot effects from the keep-alive list."""
        try:
            if not effect.isPlaying() and effect in self._active_shots:
                self._active_shots.remove(effect)
        except (RuntimeError, ValueError):
            pass

    def _start_loop_tier1(self, path: str):
        """Start looping via QSoundEffect."""
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            effect.setVolume(0.5)
            effect.setLoopCount(-1)  # Infinite
            effect.play()
            self._player = effect
        except Exception as e:
            logger.warning("QSoundEffect loop failed: %s", e)

    # ── Tier 2: winsound ─────────────────────────────────────

    def _play_tier2(self, path: str):
        """Play via winsound.PlaySound (async, no-stop)."""
        try:
            import winsound
            winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception as e:
            logger.warning("winsound play failed: %s", e)

    # ── Cleanup ───────────────────────────────────────────────

    def cleanup(self):
        """Stop any active sound playback and release resources."""
        self.stop_loop()
        self._active_shots.clear()
        logger.debug("SoundManager cleaned up")
