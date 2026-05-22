"""
core/engine.py — Game loop and system orchestrator.

Owns the QTimer, the ordered list of systems, and the tick lifecycle.
Window is full-screen overlay — cat_x/cat_y are screen coords.
No window.move() calls — the window is static.
"""

import math
import random
import time
import json
import os
from collections import OrderedDict
from datetime import datetime

from PyQt6.QtCore import QTimer, QElapsedTimer, QPointF
from PyQt6.QtGui import QScreen, QCursor
from PyQt6.QtWidgets import QApplication

import config
from core.state import CatState
from core.api import action_queue


class Engine:
    """The heart of the cat's inner life."""

    def __init__(self, state: CatState, window):
        self.state = state
        self.window = window
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

            # 2. Internal animation updates
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

        except Exception:
            pass

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

        # Go-home navigation
        if s.state == config.STATE_GO_HOME:
            self._update_go_home(dt)

        # Walk navigation (for STATE_WALK)
        if s.state == config.STATE_WALK:
            self._update_walk(dt)

        # Wander navigation (for STATE_WANDER)
        if s.state == config.STATE_WANDER:
            self._update_wander(dt)

    # ── Walk navigation (standard walk) ─────────────────────────────

    def _update_walk(self, dt: float) -> None:
        s = self.state
        if s.walk_pause:
            if self._walk_pause_et.elapsed() / 1000.0 > random.uniform(1.0, 2.0):
                s.walk_pause = False
            return

        s.walk_elapsed += dt
        total = s.walk_duration
        elapsed = s.walk_elapsed

        if elapsed < config.WALK_ACCEL_TIME:
            s.walk_accel = elapsed / config.WALK_ACCEL_TIME
        elif elapsed > total - config.WALK_ACCEL_TIME:
            rem = total - elapsed
            s.walk_accel = max(0.0, rem / config.WALK_ACCEL_TIME)
        else:
            s.walk_accel = 1.0

        speed = config.WALK_SPEED * s.walk_accel * dt
        geo_screen = self.state.screen_width

        if s.facing:
            s.walk_accum += speed
            whole = math.floor(s.walk_accum)
            s.cat_x += whole
            s.walk_accum -= whole
            if s.cat_x + 80 >= geo_screen:  # don't go off right edge
                s.cat_x = float(geo_screen - 80)
                s.state = config.STATE_SIT
                s.facing = False
                return
        else:
            s.walk_accum += speed
            whole = math.floor(s.walk_accum)
            s.cat_x -= whole
            s.walk_accum -= whole
            if s.cat_x - 80 <= 0:  # don't go off left edge
                s.cat_x = 80.0
                s.state = config.STATE_SIT
                s.facing = True
                return

        s.walk_frame = int((s.walk_elapsed * 6.5) % 4)

    # ── Wander navigation (exploratory walks) ───────────────────────

    def _update_wander(self, dt: float) -> None:
        s = self.state

        # Count this wander leg
        s.wander_elapsed += dt

        # Random direction reversal (so cat doesn't just go one way)
        if random.random() < config.WANDER_TURN_CHANCE:
            s.facing = not s.facing

        # Check if wander timer expired
        if s.wander_elapsed >= s.wander_duration:
            s.state = config.STATE_SIT
            s.wander_session_count += 1
            s.wander_cooldown = config.WANDER_COOLDOWN
            return

        # Walk movement in facing direction
        speed = config.WALK_SPEED * dt * 1.0
        margin = config.WANDER_OFFSET

        if s.facing:
            s.cat_x += speed
            if s.cat_x + margin >= s.screen_width:
                s.cat_x = float(s.screen_width - margin)
                s.facing = False  # bounce off right wall
        else:
            s.cat_x -= speed
            if s.cat_x - margin <= 0:
                s.cat_x = float(margin)
                s.facing = True   # bounce off left wall

        # Walk frame animation
        s.walk_accum = (s.walk_accum + speed) % 1.0
        s.walk_frame = int((s.wander_elapsed * 6.5) % 4)

    # ── Go-home navigation ───────────────────────────────────────────

    def _update_go_home(self, dt: float) -> None:
        s = self.state
        from cat.home import _bed_center
        bed_x, bed_y = _bed_center(s)
        remaining = bed_x - s.cat_x

        if remaining <= config.HOME_TOLERANCE:
            # Arrived at home
            s.cat_x = bed_x
            s.at_home = True
            s.state = config.STATE_SLEEP
            s.sleep_breath = 0.0
            s.zzz_particles = []
            s.walk_elapsed = 0.0
            return

        # Accelerate toward home, decelerate near arrival
        speed = config.WALK_SPEED * dt * 1.2
        if remaining < speed * 5:
            speed = remaining / 5.0  # ease in

        s.cat_x += speed
        s.walk_elapsed += dt
        s.walk_frame = int((s.walk_elapsed * 6.5) % 4)

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

        # Mouse moving detection
        dx_move = cursor.x() - self._prev_mouse_pos.x()
        dy_move = cursor.y() - self._prev_mouse_pos.y()
        mouse_moving = abs(dx_move) > 2 or abs(dy_move) > 2
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
                    s.consecutive_pets += 1

        # Approach walk (mouse within 80px)
        if dist < 80 and s.state == config.STATE_SIT:
            if random.random() < 0.03:
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
        s = self.state
        while not action_queue.empty():
            try:
                action = action_queue.get_nowait()
            except Exception:
                break
            s.last_interaction = time.monotonic()
            s.boredom = 0.0
            if action == "pet":
                s.consecutive_pets += 1
                if s.consecutive_pets >= 5:
                    self._trigger_purr()
                    s.consecutive_pets = 0
                elif s.state == config.STATE_SLEEP:
                    s.reaction_type = "meow"
                    s.reaction_timer = 0.8
                else:
                    s.reaction_type = random.choice(["purr", "meow"])
                    s.reaction_timer = 2.0 if s.reaction_type == "purr" else 0.8
            elif action == "feed":
                s.hunger = max(0.0, s.hunger - 15.0)
            elif action == "wake":
                if s.state == config.STATE_SLEEP:
                    s.state = config.STATE_SIT
                    s.energy = min(100.0, s.energy + 10.0)
                    s.deep_sleep = False

    def _trigger_purr(self) -> None:
        s = self.state
        s.reaction_type = "purr"
        s.reaction_timer = 1.5
        s.purr_vibrate = 1.0

    def _clamp_needs(self) -> None:
        s = self.state
        s.energy = max(0.0, min(100.0, s.energy))
        s.hunger = max(0.0, min(100.0, s.hunger))
        s.boredom = max(0.0, min(100.0, s.boredom))

    # ── System idle detection ───────────────────────────────────────────

    def _poll_idle(self):
        """Check GetLastInputInfo for system-wide idle."""
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
        except Exception:
            pass
