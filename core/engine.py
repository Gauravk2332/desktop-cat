"""
core/engine.py — Game loop and system orchestrator.

Owns the QTimer, the ordered list of systems, and the tick lifecycle.
Window is full-screen overlay — cat_x/cat_y are screen coords.
No window.move() calls — the window is static.
"""

import logging
import math
import random
import time
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime

logging.basicConfig(level=logging.WARNING)

from PyQt6.QtCore import QTimer, QElapsedTimer, QPointF
from PyQt6.QtGui import QScreen, QCursor
from PyQt6.QtWidgets import QApplication

import config
from core.state import CatState
import core.navigation as navigation
from core.sound import SoundManager


class Engine:
    """The heart of the cat's inner life."""

    def __init__(self, state: CatState, window):
        self.state = state
        self.window = window
        self.sound = SoundManager()
        self._prev_state = state.state
        self._prev_at_home = state.at_home
        self._footstep_counter = 0.0
        self.systems: OrderedDict[str, object] = OrderedDict()
        self._elapsed = QElapsedTimer()
        self._elapsed.start()

        # Internal timers
        self._tail_et = QElapsedTimer()
        self._tail_et.start()

        # Register core animation systems
        from animation import breathe
        self.register("breathe", breathe)

        # Register behavior systems
        from behavior import needs, transitions
        self.register("needs", needs)
        self.register("transitions", transitions)
        self._walk_et = QElapsedTimer()
        self._walk_et.start()
        self._walk_pause_et = QElapsedTimer()
        self._walk_pause_et.start()

        # Main tick timer
        self._tick_timer = QTimer(window)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start(config.TICK_MS)

        # Mouse polling (every 200ms is lightweight enough)
        self._mouse_timer = QTimer(window)
        self._mouse_timer.timeout.connect(self._check_mouse)
        self._mouse_timer.start(200)

        # System-wide idle detection (slow — ctypes call)
        self._idle_timer = QTimer(window)
        self._idle_timer.timeout.connect(self._poll_idle)
        self._idle_timer.start(5000)

        # Eye tracking — lazy init values
        self._eye_target = QPointF(0.0, 0.0)
        self._eye_current = QPointF(0.0, 0.0)
        self._prev_mouse_pos = QPointF(0.0, 0.0)

    def register(self, name: str, system) -> None:
        """Register a system with an update(dt, state) method."""
        self.systems[name] = system

    def load_state(self) -> None:
        """Restore persisted state (if any)."""
        try:
            with open(config.STATE_PATH) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return

        s = self.state
        s.energy = float(data.get("energy", 80.0))
        s.hunger = float(data.get("hunger", 20.0))
        s.boredom = float(data.get("boredom", 0.0))
        s.state = data.get("state", config.STATE_SIT)
        s.cat_x = float(data.get("x", s.cat_x))
        s.facing = bool(data.get("facing", True))

        try:
            saved_ts = datetime.fromisoformat(data["timestamp"])
            elapsed = (datetime.now() - saved_ts).total_seconds()
            if elapsed > 0:
                s.energy = max(0.0, s.energy - config.ENERGY_DRAIN_SIT * elapsed)
                s.hunger = min(100.0, s.hunger + config.HUNGER_DRAIN * elapsed)
        except (KeyError, ValueError):
            pass
        self._clamp_needs()

    def save_state(self) -> None:
        """Persist current state to disk."""
        s = self.state
        data = {
            "energy": s.energy, "hunger": s.hunger,
            "boredom": s.boredom, "state": s.state,
            "x": s.cat_x, "facing": s.facing,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            os.makedirs(config.STATE_DIR, exist_ok=True)
            with open(config.STATE_PATH, "w") as f:
                json.dump(data, f)
        except OSError:
            pass

    # ── Tick lifecycle ──────────────────────────────────────────────────

    def _on_tick(self):
        dt = self._elapsed.elapsed() / 1000.0
        self._elapsed.start()
        dt = min(dt, 0.1)

        try:
            # 1. Run registered systems (needs, transitions)
            for name, system in self.systems.items():
                system.update(dt, self.state)

            # 2. Sound system
            self._update_sounds(dt)

            # 3. Internal animation updates
            self._update_animations(dt)

            # 3. Process external action queue
            self._process_actions()

            # 4. Clamp needs
            self._clamp_needs()

            # 5. Persist
            self.state.save_accum += dt
            if self.state.save_accum >= config.SAVE_INTERVAL:
                self.state.save_accum = 0.0
                self.save_state()

            # 6. Repaint
            self.window.update()

        except Exception as e:
            logging.exception("desktop-cat engine tick failed: %s", e)

    # ── Sound system ───────────────────────────────────────────────────

    def _update_sounds(self, dt: float) -> None:
        """Handle sound playback based on state transitions."""
        s = self.state

        # Load current settings for mute state
        try:
            from ui.settings import AppSettings
            self.sound.set_enabled(AppSettings.load().sound_enabled)
        except ImportError:
            pass

        # State transition detection
        if s.state != self._prev_state:
            if s.state == config.STATE_SLEEP:
                if s.at_home:
                    self.sound.start_loop("purr")
                else:
                    self.sound.start_loop("sleep_breathing")
            elif self._prev_state == config.STATE_SLEEP:
                self.sound.stop_loop()
                self.sound.play("yawn")
            elif s.state in (config.STATE_WALK, config.STATE_WANDER):
                self.sound.play("footstep")
            elif s.state == config.STATE_GO_HOME:
                self.sound.play("meow_short")

        self._prev_state = s.state

        # At-home vs field sleep sound switch
        if s.state == config.STATE_SLEEP and s.at_home != self._prev_at_home:
            self.sound.stop_loop()
            if s.at_home:
                self.sound.start_loop("purr")
            else:
                self.sound.start_loop("sleep_breathing")

        self._prev_at_home = s.at_home

        # Footstep rhythm during walk/wander
        if s.state in (config.STATE_WALK, config.STATE_WANDER):
            self._footstep_counter += dt
            if self._footstep_counter >= 0.3:
                self._footstep_counter = 0.0
                suffix = "2" if s.walk_frame % 2 == 0 else ""
                self.sound.play(f"footstep{suffix}")

    def _update_animations(self, dt: float) -> None:
        s = self.state

        # Tail phase (slow sinusoidal)
        s.tail_phase = (self._tail_et.elapsed() / 1000.0) * math.pi * 0.5

        # Blink
        s.blink_timer += dt
        if s.blinking:
            if s.blink_timer > 0.15:
                s.blinking = False
                s.blink_timer = 0.0
                s.next_blink = random.uniform(
                    config.BLINK_INTERVAL_MIN, config.BLINK_INTERVAL_MAX
                )
        elif s.blink_timer > s.next_blink:
            s.blinking = True
            s.blink_timer = 0.0

        # Sleep breathing + Zzz
        if s.state == config.STATE_SLEEP:
            breath_speed = 2.0 if not s.deep_sleep else 0.8
            s.sleep_breath += dt * breath_speed
            if random.random() < 0.15:
                s.zzz_particles.append([random.uniform(-10, 10), 0.0, 1.0, 0.0])
            for p in list(s.zzz_particles):
                p[1] -= 10 * dt
                p[2] -= dt
                p[3] += dt
                if p[2] <= 0 or p[3] > 2.5:
                    s.zzz_particles.remove(p)

        # Purr decay
        if s.purr_vibrate > 0:
            s.purr_vibrate = max(0.0, s.purr_vibrate - dt * 4.0)

        # Reaction timer
        if s.reaction_timer > 0:
            s.reaction_timer -= dt
            if s.reaction_timer <= 0:
                s.reaction_type = None
                s.consecutive_pets = 0
        if s.reaction_type == "meow":
            s.mouth_open = math.sin(s.reaction_timer * 18) * 0.5 + 0.5

        # Eye tracking — smooth toward target
        tx = self._eye_current.x() + (self._eye_target.x() - self._eye_current.x()) * min(1.0, dt * 5)
        ty = self._eye_current.y() + (self._eye_target.y() - self._eye_current.y()) * min(1.0, dt * 5)
        self._eye_current = QPointF(tx, ty)
        s.eye_current = (float(self._eye_current.x()), float(self._eye_current.y()))

        # Navigation (delegated to pure functions)
        if s.state == config.STATE_GO_HOME:
            navigation.update_go_home(dt, s)

        if s.state == config.STATE_WALK:
            navigation.update_walk(dt, s)

        if s.state == config.STATE_WANDER:
            navigation.update_wander(dt, s)

    def _update_walk(self, dt: float) -> None:
        navigation.update_walk(dt, self.state)

    def _update_wander(self, dt: float) -> None:
        navigation.update_wander(dt, self.state)

    def _update_go_home(self, dt: float) -> None:
        navigation.update_go_home(dt, self.state)

    # ── Mouse tracking ──────────────────────────────────────────────

    def _check_mouse(self) -> None:
        s = self.state
        cursor = QCursor.pos()
        s.mouse_pos = (cursor.x(), cursor.y())

        cx = s.cat_x
        cy = s.cat_y
        dx = cursor.x() - cx
        dy = cursor.y() - cy
        dist = math.sqrt(dx * dx + dy * dy)

        s.mouse_near = dist < 150

        # Mouse moving detection (stored for blink reactivity)
        dx_move = cursor.x() - self._prev_mouse_pos.x()
        dy_move = cursor.y() - self._prev_mouse_pos.y()
        self._mouse_moving = abs(dx_move) > 2 or abs(dy_move) > 2
        self._prev_mouse_pos = QPointF(cursor)

        # Eye tracking
        if s.state != config.STATE_SLEEP:
            max_off = 2.0
            angle = math.atan2(dy, dx)
            factor = min(dist / 80.0, 1.0)
            self._eye_target = QPointF(
                math.cos(angle) * max_off * factor,
                math.sin(angle) * max_off * factor,
            )

        # Proximity reactions (only when not sleeping)
        if dist < 40 and s.state != config.STATE_SLEEP:
            if time.monotonic() - s.last_interaction > 1.0:
                s.last_interaction = time.monotonic()
                s.boredom = 0.0
                if s.consecutive_pets >= 5:
                    self._trigger_purr()
                    s.consecutive_pets = 0
                elif random.random() < 0.4:
                    self._trigger_purr()
                    self.sound.play("purr")
                    s.consecutive_pets += 1

        # Approach walk (mouse within 80px)
        if dist < 80 and s.state == config.STATE_SIT:
            if (time.monotonic() - s.last_interaction > 3.0 and
                random.random() < 0.01):
                s.facing = cursor.x() > cx
                s.state = config.STATE_WALK
                s.walk_duration = max(0.8, random.uniform(1.5, 3.0))
                s.walk_elapsed = 0.0
                s.walk_accel = 0.0
                s.walk_pause = False
                s.walk_frame = 0
                s.walk_accum = 0.0
                self._walk_et.start()

    def _process_actions(self) -> None:
        navigation.process_actions(self.state)

    def _trigger_purr(self) -> None:
        navigation.trigger_purr(self.state)

    def _clamp_needs(self) -> None:
        s = self.state
        s.energy = max(0.0, min(100.0, s.energy))
        s.hunger = max(0.0, min(100.0, s.hunger))
        s.boredom = max(0.0, min(100.0, s.boredom))

    # ── System idle detection ───────────────────────────────────────────

    def _poll_idle(self):
        """Check GetLastInputInfo for system-wide idle (Windows only)."""
        if sys.platform != "win32":
            return  # idle detection only supported on Windows

        try:
            import ctypes
            class _LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = _LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if user32.GetLastInputInfo(ctypes.byref(lii)):
                idle = (kernel32.GetTickCount() - lii.dwTime) / 1000.0
                if idle > config.IDLE_SLEEP_DELAY:
                    self.state.deep_sleep = True
                else:
                    self.state.deep_sleep = False
        except Exception as e:
            logging.warning("Idle detection failed: %s", e)
