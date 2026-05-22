"""core/sound.py — Sound system for desktop-cat.

Tiered playback:
  1. QSoundEffect (lowest latency, loopable) — for looping sounds
  2. winsound.PlaySound() — for one-shot sounds (native Windows, always works)
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

    On Windows, one-shot sounds use winsound (native, reliable).
    Looping sounds use QSoundEffect when available.

    Usage:
        sm = SoundManager()
        sm.play("purr")           # fire-and-forget
        sm.start_loop("purr")     # start looping
        sm.stop_loop()            # stop current loop
        sm.set_enabled(False)     # mute all
    """

    def __init__(self):
        self._enabled = True
        self._can_winsound = False
        self._can_qse = False
        self._detect_backends()
        self._player = None  # QSoundEffect instance for looping
        self._active_shots: list = []  # keep one-shot QSE effects alive
        logger.info("SoundManager: winsound=%s qsoundeffect=%s",
                     self._can_winsound, self._can_qse)

    # ── Backend Detection ──────────────────────────────────────

    def _detect_backends(self) -> None:
        """Detect available audio backends."""
        # winsound (always available on Windows)
        try:
            import winsound
            _ = winsound.PlaySound
            self._can_winsound = True
            logger.debug("winsound available")
        except (ImportError, AttributeError):
            self._can_winsound = False

        # QSoundEffect (requires PyQt6.QtMultimedia)
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl
            _ = QSoundEffect.__new__
            self._can_qse = True
            logger.debug("QSoundEffect available")
        except (ImportError, TypeError):
            self._can_qse = False

        if not self._can_winsound and not self._can_qse:
            logger.warning("No audio backend found — sound disabled")

    # ── Public API ─────────────────────────────────────────────

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
        if not self._enabled:
            return

        path = self._resolve_path(name)
        if path is None:
            return

        # Prefer winsound on Windows (always reliable)
        if self._can_winsound:
            self._play_winsound(path)
        elif self._can_qse:
            self._play_qse(path)

    def start_loop(self, name: str):
        """Start looping a sound. Stops any current loop first."""
        self.stop_loop()

        if not self._enabled:
            return

        path = self._resolve_path(name)
        if path is None:
            return

        # Looping only works with QSoundEffect
        if self._can_qse:
            self._start_loop_qse(path)

    def stop_loop(self):
        """Stop any currently looping sound."""
        if self._player is not None:
            try:
                self._player.stop()
            except RuntimeError:
                pass
            self._player = None

    # ── Path Resolution ───────────────────────────────────────

    def _resolve_path(self, name: str) -> Optional[str]:
        """Find WAV file for given sound name."""
        path = os.path.join(SOUNDS_DIR, name)
        if os.path.exists(path):
            return path
        path = os.path.join(SOUNDS_DIR, f"{name}.wav")
        if os.path.exists(path):
            return path
        logger.warning("Sound not found: %s", name)
        return None

    # ── winsound (one-shot, native Windows) ───────────────────

    def _play_winsound(self, path: str):
        """Play via winsound.PlaySound (async, no-stop)."""
        try:
            import winsound
            winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception as e:
            logger.warning("winsound play failed: %s", e)

    # ── QSoundEffect (one-shot + loop) ────────────────────────

    def _play_qse(self, path: str):
        """Play via QSoundEffect (fire-and-forget, keep-alive list)."""
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

    def _start_loop_qse(self, path: str):
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

    def _on_shot_finished(self, effect) -> None:
        """Remove finished one-shot effects from the keep-alive list."""
        try:
            if not effect.isPlaying() and effect in self._active_shots:
                self._active_shots.remove(effect)
        except (RuntimeError, ValueError):
            pass

    # ── Cleanup ───────────────────────────────────────────────

    def cleanup(self):
        """Stop any active sound playback and release resources."""
        self.stop_loop()
        self._active_shots.clear()
        logger.debug("SoundManager cleaned up")
