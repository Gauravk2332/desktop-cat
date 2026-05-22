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
from core.state import CatState, SPEECH_MOODS
import core.navigation as navigation
from core.sound import SoundManager
from core.navigation import _spawn_hearts


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

        # Speech state transition tracking
        self._prev_speech_state = state.state
        self._prev_hunger = state.hunger
        self._speech_proximity_triggered = False

        # System-wide idle detection (slow — ctypes call)
        self._idle_timer = QTimer(window)
        self._idle_timer.timeout.connect(self._poll_idle)
        self._idle_timer.start(5000)

        # Eye tracking — lazy init values
        self._eye_target = QPointF(0.0, 0.0)
        self._eye_current = QPointF(0.0, 0.0)
        self._prev_mouse_pos = QPointF(0.0, 0.0)

        # Toy system state
        self._toy_spawn_timer: float = 0.0
        self._mouse_still_timer: float = 0.0
        self._prev_mouse_pos_ts: tuple = (0.0, 0.0)

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
        s = self.state

        try:
            # 1. Run registered systems (needs, transitions)
            for name, system in self.systems.items():
                system.update(dt, self.state)

            # 2. Sound system
            self._update_sounds(dt)

            # 3. Internal animation updates
            self._update_animations(dt)

            # 3. Process external action queue (pet/feed/wake actions)
            self._prev_hunger = s.hunger
            self._process_actions()

            # 3a. Speech trigger on feed action (hunger dropped)
            if s.hunger < self._prev_hunger - 1.0 and s.speech_cooldown <= 0:
                self._trigger_speech("happy")
                s.speech_cooldown = 5.0

            # 3b. Speech bubble tick
            self._update_speech(dt)

            # 3c. Toy system (yarn ball spawning, chase timeout)
            self._update_toys(dt)

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
            elif s.state in (config.STATE_WALK, config.STATE_WANDER, config.STATE_CHASE, config.STATE_PLAY):
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

        # Footstep rhythm during walk/wander/chase/play
        if s.state in (config.STATE_WALK, config.STATE_WANDER, config.STATE_CHASE, config.STATE_PLAY):
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

        # Hearts decay (on-pet animation)
        for h in list(s.hearts):
            h[2] -= dt  # lifetime
            h[1] -= 40 * dt  # float upward
            if h[2] <= 0:
                s.hearts.remove(h)

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

        if s.state == config.STATE_CHASE:
            navigation.update_chase(dt, s)

        if s.state == config.STATE_PLAY:
            navigation.update_play(dt, s)

    def _update_walk(self, dt: float) -> None:
        navigation.update_walk(dt, self.state)

    def _update_wander(self, dt: float) -> None:
        navigation.update_wander(dt, self.state)

    def _update_go_home(self, dt: float) -> None:
        navigation.update_go_home(dt, self.state)

    # ── Speech bubble system ────────────────────────────────────────

    def _trigger_speech(self, mood: str) -> None:
        """Queue or display a speech bubble for the given mood/pool.
        Handles priority-based interruption vs queuing.
        """
        s = self.state
        mood_data = SPEECH_MOODS.get(mood)
        if not mood_data:
            return

        text = random.choice(mood_data["texts"])
        emoji = mood_data["emoji"]

        new_priority = config.MOOD_PRIORITY.get(mood, 1)
        speech = s.speech

        if speech["text"] is None:
            # Nothing showing — display immediately
            speech["text"] = text
            speech["emoji"] = emoji
            speech["timer"] = config.SPEECH_DISPLAY
            speech["fading"] = False
            speech["opacity"] = 0.0  # fade in
        else:
            # Determine current mood priority
            current_mood = None
            for m, md in SPEECH_MOODS.items():
                if md["emoji"] == speech.get("emoji"):
                    current_mood = m
                    break
            current_priority = config.MOOD_PRIORITY.get(current_mood, 1)

            if new_priority >= current_priority:
                # Higher/same priority — queue
                if len(speech["queue"]) < config.SPEECH_QUEUE_MAX:
                    speech["queue"].append({
                        "text": text, "emoji": emoji,
                        "duration": config.SPEECH_DISPLAY
                    })
            # else: lower priority — drop

    def _update_speech(self, dt: float) -> None:
        """Tick the speech bubble system each frame."""
        s = self.state
        speech = s.speech

        # Advance cooldown
        if s.speech_cooldown > 0:
            s.speech_cooldown -= dt
            if s.speech_cooldown < 0:
                s.speech_cooldown = 0.0

        # Idle timer
        if s.state != config.STATE_SLEEP:
            s.speech_idle_timer += dt
        else:
            s.speech_idle_timer = 0.0

        # Periodic idle bubble check
        if (s.speech_idle_timer > config.SPEECH_IDLE_THRESHOLD
                and s.speech_cooldown <= 0
                and speech["text"] is None):
            self._trigger_speech("long-idle")
            s.speech_cooldown = config.SPEECH_IDLE_COOLDOWN

        # State transition check
        if s.state != self._prev_speech_state:
            self._prev_speech_state = s.state
            mood_map = {
                config.STATE_SIT: "bored",
                config.STATE_WALK: "playful",
                config.STATE_WANDER: "playful",
                config.STATE_CHASE: "playful",
                config.STATE_PLAY: "playful",
                config.STATE_SLEEP: "sleepy",
                config.STATE_GO_HOME: "sleepy",
            }
            mood = mood_map.get(s.state)
            if mood and s.speech_cooldown <= 0:
                self._trigger_speech(mood)
                s.speech_cooldown = 3.0

        # No active speech — drain queue
        if speech["text"] is None and speech["queue"]:
            next_msg = speech["queue"].pop(0)
            speech["text"] = next_msg["text"]
            speech["emoji"] = next_msg["emoji"]
            speech["timer"] = next_msg["duration"] + config.SPEECH_FADE_IN
            speech["fading"] = False
            speech["opacity"] = 0.0

        # Active speech lifecycle
        if speech["text"] is not None:
            speech["timer"] -= dt

            # Fade-in phase (first SPEECH_FADE_IN seconds)
            if not speech["fading"] and speech["opacity"] < 1.0:
                speech["opacity"] = min(1.0, speech["opacity"] + dt / config.SPEECH_FADE_IN)

            # Enter fade-out when timer drops to SPEECH_FADE_OUT
            if speech["timer"] <= config.SPEECH_FADE_OUT and not speech["fading"]:
                speech["fading"] = True

            # Fade-out phase
            if speech["fading"] and speech["opacity"] > 0.0:
                speech["opacity"] = max(0.0, speech["opacity"] - dt / config.SPEECH_FADE_OUT)

            # Fully done
            if speech["timer"] <= 0 and speech["opacity"] <= 0:
                speech["text"] = None
                speech["emoji"] = None
                speech["timer"] = 0.0
                speech["fading"] = False
                speech["opacity"] = 0.0

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
        if dist < 40 and s.state not in (config.STATE_SLEEP, config.STATE_CHASE, config.STATE_PLAY):
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
                # Spawn hearts on pet
                _spawn_hearts(s)
                # Speech: happy on pet
                if s.speech_cooldown <= 0:
                    self._trigger_speech("happy")
                    s.speech_cooldown = config.SPEECH_PROXIMITY_COOLDOWN

        # Proximity speech trigger (mouse nearby, not close enough to pet)
        if (dist < config.SPEECH_PROXIMITY_RADIUS and dist >= 40
                and s.state not in (config.STATE_SLEEP, config.STATE_CHASE, config.STATE_PLAY)
                and s.speech["text"] is None
                and s.speech_cooldown <= 0):
            self._trigger_speech("alert")
            s.speech_cooldown = config.SPEECH_PROXIMITY_COOLDOWN

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

        # ── Laser pointer chase (interact mode, click-through OFF) ──
        if not s.click_through and dist < 300 and s.state in (config.STATE_SIT,):
            if self._mouse_moving:
                # Start chasing the cursor
                s.toy_target = (cursor.x(), cursor.y())
                s.toy_active = True
                s.toy_type = "laser"
                s.chase_timeout = config.CHASE_TIMEOUT
                s.state = config.STATE_CHASE

        # ── Chase timeout (mouse stopped) ──
        if s.state == config.STATE_CHASE:
            # Update toy_target to current cursor position
            s.toy_target = (cursor.x(), cursor.y())

        # ── Check if cat caught the toy (yarn ball reach) ──
        if s.state == config.STATE_PLAY and s.toy_active:
            tx, ty = s.toy_target
            td = math.hypot(tx - s.cat_x, ty - s.cat_y)
            if td <= config.PLAY_TOY_REACH_DISTANCE:
                # Caught it!
                _spawn_hearts(s, count=5)
                s.state = config.STATE_SIT
                s.toy_active = False
                s.toy_type = None
                s.toy_target = None
                try:
                    self.sound.play("footstep")
                except Exception:
                    pass

    def _process_actions(self) -> None:
        navigation.process_actions(self.state)

    def _trigger_purr(self) -> None:
        navigation.trigger_purr(self.state)

    def _clamp_needs(self) -> None:
        s = self.state
        s.energy = max(0.0, min(100.0, s.energy))
        s.hunger = max(0.0, min(100.0, s.hunger))
        s.boredom = max(0.0, min(100.0, s.boredom))

    # ── Toy system ─────────────────────────────────────────────────────

    def _update_toys(self, dt: float) -> None:
        """Handle yarn ball spawning and chase timeout.
        Called every tick from _on_tick.
        """
        s = self.state

        # Only spawn toys when click-through is OFF (interact mode)
        if s.click_through:
            self._toy_spawn_timer = 0.0
            return

        # Don't spawn while chase/play is already active or cat is sleeping
        if s.state in (config.STATE_CHASE, config.STATE_PLAY, config.STATE_SLEEP):
            return

        # Yarn ball / butterfly toy spawning
        self._toy_spawn_timer += dt
        if self._toy_spawn_timer >= config.PLAY_TOY_INTERVAL and s.state == config.STATE_SIT:
            self._toy_spawn_timer = 0.0

            # Spawn toy near mouse position
            mx, my = s.mouse_pos
            import random as _random
            tx = mx + _random.uniform(-60, 60)
            ty = my + _random.uniform(-40, 40)

            # Clamp to screen
            margin = 50
            tx = max(float(margin), min(tx, float(s.screen_width - margin)))
            y_min = s.screen_height * config.CAT_MIN_Y_FRACTION
            y_max = s.screen_height - config.CAT_BASELINE
            ty = max(float(y_min), min(ty, float(y_max)))

            s.toy_target = (tx, ty)
            s.toy_active = True
            s.toy_type = "ball"
            s.toy_timer = config.PLAY_TOY_DURATION

            # Check if cat is within 100px of toy → start playing
            tdx = tx - s.cat_x
            tdy = ty - s.cat_y
            tdist = math.hypot(tdx, tdy)
            if tdist <= 100.0:
                s.state = config.STATE_PLAY

        # Chase timeout: when mouse hasn't moved, stop chasing
        if s.state == config.STATE_CHASE:
            if not self._mouse_moving:
                s.chase_timeout -= dt
                if s.chase_timeout <= 0:
                    s.state = config.STATE_SIT
                    s.toy_active = False
                    s.toy_type = None
                    s.toy_target = None
            else:
                s.chase_timeout = config.CHASE_TIMEOUT

        # Yarn ball timer expiration
        if s.state == config.STATE_PLAY:
            s.toy_timer -= dt
            if s.toy_timer <= 0:
                s.state = config.STATE_SIT
                s.toy_active = False
                s.toy_type = None

        # Advance toy drift (slow float for yarn ball)
        if s.toy_active and s.toy_type == "ball" and s.toy_target is not None:
            tx, ty = s.toy_target
            tx += math.sin(time.monotonic() * 0.5) * 5 * dt
            ty += math.cos(time.monotonic() * 0.7) * 3 * dt
            # Clamp
            margin = 50
            tx = max(float(margin), min(tx, float(s.screen_width - margin)))
            y_min = s.screen_height * config.CAT_MIN_Y_FRACTION
            y_max = s.screen_height - config.CAT_BASELINE
            ty = max(float(y_min), min(ty, float(y_max)))
            s.toy_target = (tx, ty)

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
