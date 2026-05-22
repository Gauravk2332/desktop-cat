"""
core/engine.py — Game loop and system orchestrator.

Owns the QTimer, the ordered list of systems, and the tick lifecycle.
Multi-cat: iterates over state.cats for per-cat updates.
Window is full-screen overlay — cat positions are screen coords.
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
from core.state import CatState, SPEECH_MOODS, default_cat_dict
import core.navigation as navigation
from core.sound import SoundManager
from core.navigation import _spawn_hearts
from core.toast import notify
from behavior.vocalizations import VocalizationSystem


def _per_cat_fields():
    """List of per-cat field names to save/load."""
    return [
        "id", "x", "y", "state", "facing", "coat",
        "energy", "hunger", "boredom",
        "at_home", "home_cooldown", "home_linger",
        "walk_duration", "walk_elapsed",
        "wander_duration", "wander_elapsed", "wander_cooldown",
        "wander_vx", "wander_vy", "hut_index",
    ]


class Engine:
    """The heart of the cat's inner life."""

    def __init__(self, state: CatState, window):
        self.state = state
        self.window = window
        self.sound = SoundManager()
        self._sound_enabled = True

        # Per-cat previous-state tracking
        self._prev_cat_states: list[str] = [s["state"] for s in state.cats]
        self._prev_cat_at_home: list[bool] = [s.get("at_home", False) for s in state.cats]
        self._prev_hunger: list[float] = [s.get("hunger", 20.0) for s in state.cats]

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

        # Register weather system
        from core import weather
        self.register("weather", weather)
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

        # Vocalization system
        self._vocalization = VocalizationSystem(state)
        state._mouse_x = 0.0
        state._mouse_y = 0.0

        # Speech state transition tracking
        self._prev_speech_states: list[str] = [s["state"] for s in state.cats]
        self._prev_hunger_vals: list[float] = [s.get("hunger", 20.0) for s in state.cats]
        self._speech_proximity_triggered = False

        # System-wide idle detection
        self._idle_timer = QTimer(window)
        self._idle_timer.timeout.connect(self._poll_idle)
        self._idle_timer.start(5000)

        # Eye tracking
        self._eye_target = QPointF(0.0, 0.0)
        self._eye_current = QPointF(0.0, 0.0)
        self._prev_mouse_pos = QPointF(0.0, 0.0)

        # Toy system state
        self._toy_spawn_timer: float = 0.0
        self._mouse_still_timer: float = 0.0
        self._prev_mouse_pos_ts: tuple = (0.0, 0.0)

        # Toast notification cooldown
        self._toast_cooldowns: dict[str, float] = {}
        self._boredom_notify_timer: float = 0.0

        # Save original cat count for migration detection
        self._init_cat_count = len(state.cats)

    def _send_toast(self, kind: str, title: str, message: str, cooldown: float = 1800.0) -> None:
        """Send a toast notification if the cooldown for this kind has elapsed."""
        now = time.monotonic()
        last = self._toast_cooldowns.get(kind, 0.0)
        if now - last >= cooldown:
            notify(title, message)
            self._toast_cooldowns[kind] = now

    def register(self, name: str, system) -> None:
        """Register a system with an update(dt, cat, state) method."""
        self.systems[name] = system

    # ── Save/Load ──────────────────────────────────────────────────────

    def save_state(self) -> None:
        """Persist current multi-cat state to disk."""
        s = self.state
        data = {
            "cats": [
                {
                    k: cat[k]
                    for k in _per_cat_fields()
                    if k in cat
                }
                for cat in s.cats
            ],
            "weather_condition": s.weather_condition,
            "weather_raw": getattr(self, '_weather_raw', None),
            "timestamp": datetime.now().isoformat(),
        }
        try:
            os.makedirs(config.STATE_DIR, exist_ok=True)
            with open(config.STATE_PATH, "w") as f:
                json.dump(data, f, default=str)
        except OSError:
            pass

    def load_state(self) -> None:
        """Restore persisted multi-cat state (if any). Handles legacy migration."""
        try:
            with open(config.STATE_PATH) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return

        s = self.state
        cats_data = data.get("cats", [])

        if not cats_data:
            # Legacy single-cat state — migrate
            x = float(data.get("x", s.cats[0]["x"] if s.cats else s.screen_width / 2.0))
            y = float(data.get("y", s.cats[0]["y"] if s.cats else s.screen_height - config.CAT_BASELINE))
            legacy_cat = default_cat_dict(0, 0, x, y)
            legacy_cat["state"] = data.get("state", "SIT")
            legacy_cat["facing"] = bool(data.get("facing", True))
            legacy_cat["energy"] = float(data.get("energy", 80.0))
            legacy_cat["hunger"] = float(data.get("hunger", 20.0))
            legacy_cat["boredom"] = float(data.get("boredom", 0.0))
            s.cats = [legacy_cat]
        else:
            # Restore from multi-cat format
            restored = []
            for cd in cats_data:
                cat = default_cat_dict(
                    cd.get("id", len(restored)),
                    cd.get("coat", 0),
                    float(cd.get("x", 500.0)),
                    float(cd.get("y", 700.0)),
                )
                cat.update(cd)
                restored.append(cat)
            s.cats = restored if restored else [default_cat_dict(0)]

        # Restore shared state
        s.weather_condition = data.get("weather_condition", "cloudy")

        # Apply time-offset decay for all cats
        try:
            saved_ts = datetime.fromisoformat(data["timestamp"])
            elapsed = (datetime.now() - saved_ts).total_seconds()
            if elapsed > 0:
                for cat in s.cats:
                    cat["energy"] = max(0.0, cat["energy"] - config.ENERGY_DRAIN_SIT * elapsed)
                    cat["hunger"] = min(100.0, cat["hunger"] + config.HUNGER_DRAIN * elapsed)
        except (KeyError, ValueError):
            pass

        self._clamp_needs()

    # ── Tick lifecycle ──────────────────────────────────────────────────

    def _on_tick(self):
        dt = self._elapsed.elapsed() / 1000.0
        self._elapsed.start()
        dt = min(dt, 0.1)
        s = self.state

        try:
            # 1. Run per-cat systems (needs, transitions)
            for cat in s.cats:
                for name, system in self.systems.items():
                    if name in ("needs", "transitions"):
                        system.update(dt, cat, self.state)

            # 1b. Breathe (per cat)
            try:
                from animation import breathe
                for cat in s.cats:
                    breathe.update(dt, cat)
            except ImportError:
                pass

            # 2. Weather system (shared — once per tick)
            try:
                from core import weather
                weather.update(dt, self.state)
            except ImportError:
                pass

            # 3. Sound system (per cat, focused on cat[0] for now)
            self._update_sounds(dt)

            # 4. Internal animation updates (per cat)
            self._update_animations(dt)

            # 5. Process external actions (pet/feed/wake on cat[0])
            self._prev_hunger_vals = [c.get("hunger", 20.0) for c in s.cats]
            self._process_actions()

            # 5a. Speech on feed (per cat)
            for i, cat in enumerate(s.cats):
                prev_h = self._prev_hunger_vals[i] if i < len(self._prev_hunger_vals) else 20.0
                if cat.get("hunger", 20.0) < prev_h - 1.0 and cat.get("speech_cooldown", 0) <= 0:
                    self._trigger_speech("happy", cat_idx=i)
                    cat["speech_cooldown"] = 5.0

            # 6. Speech bubble tick (per cat)
            for i, cat in enumerate(s.cats):
                self._update_speech(dt, cat_idx=i)

            # 7. Toy system (shared — uses state-level toy tracking)
            self._update_toys(dt)

            # 8. Toast notifications (per cat)
            self._update_notifications(dt)

            # 9. Clamp needs (per cat)
            self._clamp_needs()

            # 10. Persist
            self.state.save_accum += dt
            if self.state.save_accum >= config.SAVE_INTERVAL:
                self.state.save_accum = 0.0
                self.save_state()

            # 11. Repaint
            self.window.update()

        except Exception as e:
            logging.exception("desktop-cat engine tick failed: %s", e)

    # ── Sound system ───────────────────────────────────────────────────

    def _update_sounds(self, dt: float) -> None:
        """Handle all sound playback: loops + behavioral vocalizations.

        Two concerns:
          1. Loop management: purr (while sleeping at home), sleep_breathing (field sleep)
          2. Behavioral vocalizations: meows, trills, chirps, hisses via VocalizationSystem

        Now iterates ALL cats for behavioral sounds. Loop sounds still cat[0] only.
        """
        s = self.state
        if not s.cats:
            return

        self.sound.set_enabled(self._sound_enabled)

        # ── Loop management for cat[0] ──────────────────────────────
        cat0 = s.cats[0]
        prev_state0 = self._prev_cat_states[0] if self._prev_cat_states else cat0["state"]

        # Sleep loop transitions
        if cat0["state"] != prev_state0:
            if cat0["state"] == config.STATE_SLEEP:
                if cat0.get("at_home"):
                    self.sound.start_loop("purr")
                else:
                    self.sound.start_loop("sleep_breathing")
                self._send_toast("sleep", "💤 Sleepy", "Cat is sleeping")
            elif prev_state0 == config.STATE_SLEEP:
                self.sound.stop_loop()
                self.sound.play("yawn")
            elif cat0["state"] == config.STATE_GO_HOME:
                self.sound.play("meow_short")

        # At-home vs field sleep switch
        prev_at_home = self._prev_cat_at_home[0] if self._prev_cat_at_home else cat0.get("at_home", False)
        if cat0["state"] == config.STATE_SLEEP and cat0.get("at_home") != prev_at_home:
            self.sound.stop_loop()
            if cat0.get("at_home"):
                self.sound.start_loop("purr")
            else:
                self.sound.start_loop("sleep_breathing")

        # Update prev cat[0] tracking
        while len(self._prev_cat_states) < len(s.cats):
            self._prev_cat_states.append(cat0["state"])
        while len(self._prev_cat_at_home) < len(s.cats):
            self._prev_cat_at_home.append(cat0.get("at_home", False))
        self._prev_cat_states[0] = cat0["state"]
        self._prev_cat_at_home[0] = cat0.get("at_home", False)

        # ── Footstep rhythm (all moving cats) ────────────────────────
        for i, cat in enumerate(s.cats):
            if cat["state"] in (config.STATE_WALK, config.STATE_WANDER,
                                config.STATE_CHASE, config.STATE_PLAY):
                if cat.get("_footstep_counter", 0.0) >= 0.3:
                    cat["_footstep_counter"] = 0.0
                    suffix = "2" if cat.get("walk_frame", 0) % 2 == 0 else ""
                    self.sound.play(f"footstep{suffix}")
                else:
                    cat["_footstep_counter"] = cat.get("_footstep_counter", 0.0) + dt

        # ── Behavioral vocalizations (all cats) ─────────────────────
        for i, cat in enumerate(s.cats):
            winner = self._vocalization.update(dt, cat, s)
            if winner is not None:
                # Check cooldown map for this sound
                self.sound.play(winner.name)

    # ── Toast notifications ──────────────────────────────────────────

    def _update_notifications(self, dt: float) -> None:
        """Check conditions and send toast notifications with cooldown."""
        s = self.state
        if not s.cats:
            return

        for cat in s.cats:
            if cat.get("energy", 80.0) < 15.0 and cat["state"] != config.STATE_SLEEP:
                self._send_toast("low_energy", "🥱 Tired", "Cat needs rest")

        # Boredom-based "miss you" for cat[0]
        cat0 = s.cats[0]
        if cat0["state"] != config.STATE_SLEEP:
            self._boredom_notify_timer += dt
            if self._boredom_notify_timer >= 300.0:
                self._send_toast("miss_you", "👋 Miss you!", "Cat hasn't seen you in a while")
                self._boredom_notify_timer = 0.0
        else:
            self._boredom_notify_timer = 0.0

    def _update_animations(self, dt: float) -> None:
        s = self.state

        for cat in s.cats:
            # Tail phase
            if self._tail_et.isValid():
                cat["tail_phase"] = (self._tail_et.elapsed() / 1000.0) * math.pi * 0.5

            # Blink
            cat["blink_timer"] = cat.get("blink_timer", 0.0) + dt
            if cat.get("blinking"):
                if cat["blink_timer"] > 0.15:
                    cat["blinking"] = False
                    cat["blink_timer"] = 0.0
                    cat["next_blink"] = random.uniform(
                        config.BLINK_INTERVAL_MIN, config.BLINK_INTERVAL_MAX
                    )
            elif cat["blink_timer"] > cat.get("next_blink", 2.0):
                cat["blinking"] = True
                cat["blink_timer"] = 0.0

            # Sleep breathing + Zzz
            if cat["state"] == config.STATE_SLEEP:
                breath_speed = 2.0 if not cat.get("deep_sleep") else 0.8
                cat["sleep_breath"] = cat.get("sleep_breath", 0.0) + dt * breath_speed
                zzz = cat.get("zzz_particles", [])
                if random.random() < 0.15:
                    zzz.append([random.uniform(-10, 10), 0.0, 1.0, 0.0])
                for p in list(zzz):
                    p[1] -= 10 * dt
                    p[2] -= dt
                    p[3] += dt
                    if p[2] <= 0 or p[3] > 2.5:
                        zzz.remove(p)
                cat["zzz_particles"] = zzz

            # Purr decay
            if cat.get("purr_vibrate", 0.0) > 0:
                cat["purr_vibrate"] = max(0.0, cat["purr_vibrate"] - dt * 4.0)

            # Hearts decay
            hearts = cat.get("hearts", [])
            for h in list(hearts):
                h[2] -= dt
                h[1] -= 40 * dt
                if h[2] <= 0:
                    hearts.remove(h)
            cat["hearts"] = hearts

            # Reaction timer
            if cat.get("reaction_timer", 0.0) > 0:
                cat["reaction_timer"] = cat["reaction_timer"] - dt
                if cat["reaction_timer"] <= 0:
                    cat["reaction_type"] = None
                    cat["consecutive_pets"] = 0
            if cat.get("reaction_type") == "meow":
                cat["mouth_open"] = math.sin(cat["reaction_timer"] * 18) * 0.5 + 0.5

            # Eye tracking — use shared mouse position
            if cat["state"] != config.STATE_SLEEP:
                mx, my = s.mouse_pos
                dx = mx - cat.get("x", 500.0)
                dy = my - cat.get("y", 700.0)
                max_off = 2.0
                angle = math.atan2(dy, dx)
                dist = math.hypot(dx, dy)
                factor = min(dist / 80.0, 1.0)
                target = (
                    math.cos(angle) * max_off * factor,
                    math.sin(angle) * max_off * factor,
                )
                cur = cat.get("eye_current", (0.0, 0.0))
                cat["eye_current"] = (
                    cur[0] + (target[0] - cur[0]) * min(1.0, dt * 5),
                    cur[1] + (target[1] - cur[1]) * min(1.0, dt * 5),
                )

            # Navigation (delegated)
            if cat["state"] == config.STATE_GO_HOME:
                navigation.update_go_home(dt, cat, s)

            if cat["state"] == config.STATE_WALK:
                navigation.update_walk(dt, cat, s)

            if cat["state"] == config.STATE_WANDER:
                navigation.update_wander(dt, cat, s)

            if cat["state"] == config.STATE_CHASE:
                navigation.update_chase(dt, cat, s)

            if cat["state"] == config.STATE_PLAY:
                navigation.update_play(dt, cat, s)

    # ── Speech bubble system ────────────────────────────────────────

    def _trigger_speech(self, mood: str, cat_idx: int = 0) -> None:
        """Queue or display a speech bubble for the given mood/pool on a specific cat."""
        s = self.state
        if cat_idx >= len(s.cats):
            return
        cat = s.cats[cat_idx]

        mood_data = SPEECH_MOODS.get(mood)
        if not mood_data:
            return

        text = random.choice(mood_data["texts"])
        emoji = mood_data["emoji"]

        new_priority = config.MOOD_PRIORITY.get(mood, 1)
        speech = cat.get("speech", {
            "text": None, "emoji": None, "timer": 0.0,
            "fading": False, "opacity": 0.0, "queue": [],
        })

        if speech["text"] is None:
            speech["text"] = text
            speech["emoji"] = emoji
            speech["timer"] = config.SPEECH_DISPLAY
            speech["fading"] = False
            speech["opacity"] = 0.0
        else:
            current_mood = None
            for m, md in SPEECH_MOODS.items():
                if md["emoji"] == speech.get("emoji"):
                    current_mood = m
                    break
            current_priority = config.MOOD_PRIORITY.get(current_mood, 1)
            if new_priority >= current_priority:
                if len(speech["queue"]) < config.SPEECH_QUEUE_MAX:
                    speech["queue"].append({
                        "text": text, "emoji": emoji,
                        "duration": config.SPEECH_DISPLAY
                    })

        cat["speech"] = speech

    def _update_speech(self, dt: float, cat_idx: int = 0) -> None:
        """Tick the speech bubble system for a specific cat."""
        s = self.state
        if cat_idx >= len(s.cats):
            return
        cat = s.cats[cat_idx]
        speech = cat.get("speech", {
            "text": None, "emoji": None, "timer": 0.0,
            "fading": False, "opacity": 0.0, "queue": [],
        })

        # Advance cooldown
        if cat.get("speech_cooldown", 0) > 0:
            cat["speech_cooldown"] = cat["speech_cooldown"] - dt
            if cat["speech_cooldown"] < 0:
                cat["speech_cooldown"] = 0.0

        # Idle timer
        if cat["state"] != config.STATE_SLEEP:
            cat["speech_idle_timer"] = cat.get("speech_idle_timer", 0.0) + dt
        else:
            cat["speech_idle_timer"] = 0.0

        # Periodic idle bubble
        if (cat.get("speech_idle_timer", 0.0) > config.SPEECH_IDLE_THRESHOLD
                and cat.get("speech_cooldown", 0) <= 0
                and speech["text"] is None):
            self._trigger_speech("long-idle", cat_idx)
            cat["speech_cooldown"] = config.SPEECH_IDLE_COOLDOWN

        # State transition check
        while len(self._prev_speech_states) <= cat_idx:
            self._prev_speech_states.append(cat["state"])
        prev_state = self._prev_speech_states[cat_idx]

        if cat["state"] != prev_state:
            self._prev_speech_states[cat_idx] = cat["state"]
            mood_map = {
                config.STATE_SIT: "bored",
                config.STATE_WALK: "playful",
                config.STATE_WANDER: "playful",
                config.STATE_CHASE: "playful",
                config.STATE_PLAY: "playful",
                config.STATE_SLEEP: "sleepy",
                config.STATE_GO_HOME: "sleepy",
            }
            mood = mood_map.get(cat["state"])
            if mood and cat.get("speech_cooldown", 0) <= 0:
                self._trigger_speech(mood, cat_idx)
                cat["speech_cooldown"] = 3.0

        # Drain queue
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
            if not speech["fading"] and speech["opacity"] < 1.0:
                speech["opacity"] = min(1.0, speech["opacity"] + dt / config.SPEECH_FADE_IN)
            if speech["timer"] <= config.SPEECH_FADE_OUT and not speech["fading"]:
                speech["fading"] = True
            if speech["fading"] and speech["opacity"] > 0.0:
                speech["opacity"] = max(0.0, speech["opacity"] - dt / config.SPEECH_FADE_OUT)
            if speech["timer"] <= 0 and speech["opacity"] <= 0:
                speech["text"] = None
                speech["emoji"] = None
                speech["timer"] = 0.0
                speech["fading"] = False
                speech["opacity"] = 0.0

        cat["speech"] = speech

    # ── Mouse tracking ──────────────────────────────────────────────

    def _check_mouse(self) -> None:
        s = self.state
        cursor = QCursor.pos()
        s.mouse_pos = (cursor.x(), cursor.y())
        s._mouse_x = cursor.x()
        s._mouse_y = cursor.y()

        # Mouse moving detection
        dx_move = cursor.x() - self._prev_mouse_pos.x()
        dy_move = cursor.y() - self._prev_mouse_pos.y()
        self._mouse_moving = abs(dx_move) > 2 or abs(dy_move) > 2
        self._prev_mouse_pos = QPointF(cursor)

        # Check proximity for all cats
        closest_cat = None
        closest_dist = 9999.0

        for cat in s.cats:
            cx = cat.get("x", 500.0)
            cy = cat.get("y", 700.0)
            dx = cursor.x() - cx
            dy = cursor.y() - cy
            dist = math.hypot(dx, dy)

            # Update per-cat mouse_near
            cat["mouse_near"] = dist < 150

            # Eye tracking (non-sleeping cats only)
            if cat["state"] != config.STATE_SLEEP:
                max_off = 2.0
                angle = math.atan2(dy, dx)
                factor = min(dist / 80.0, 1.0)
                target = (
                    math.cos(angle) * max_off * factor,
                    math.sin(angle) * max_off * factor,
                )
                cat["eye_target"] = target

            # Track closest non-sleeping cat for pet detection
            if dist < closest_dist and cat["state"] not in (
                config.STATE_SLEEP, config.STATE_CHASE, config.STATE_PLAY
            ):
                closest_dist = dist
                closest_cat = cat

        # Proximity reactions (only closest non-sleeping cat)
        if closest_cat is not None and closest_dist < 40:
            now = time.monotonic()
            last = closest_cat.get("last_interaction", 0.0)
            if now - last > 1.0:
                closest_cat["last_interaction"] = now
                closest_cat["boredom"] = 0.0
                consec = closest_cat.get("consecutive_pets", 0)
                if consec >= 5:
                    navigation.trigger_purr(closest_cat, s)
                    closest_cat["consecutive_pets"] = 0
                elif random.random() < 0.4:
                    navigation.trigger_purr(closest_cat, s)
                    try:
                        self.sound.play("purr")
                    except Exception:
                        pass
                    closest_cat["consecutive_pets"] = consec + 1
                navigation._spawn_hearts_for_cat(closest_cat)
                if closest_cat.get("speech_cooldown", 0) <= 0:
                    self._trigger_speech("happy",
                        cat_idx=s.cats.index(closest_cat))
                    closest_cat["speech_cooldown"] = config.SPEECH_PROXIMITY_COOLDOWN

        # Proximity speech trigger (mouse nearby, not close enough to pet)
        for cat in s.cats:
            cx = cat.get("x", 500.0)
            cy = cat.get("y", 700.0)
            dx = cursor.x() - cx
            dy = cursor.y() - cy
            dist = math.hypot(dx, dy)

            if (dist < config.SPEECH_PROXIMITY_RADIUS and dist >= 40
                    and cat["state"] not in (config.STATE_SLEEP, config.STATE_CHASE, config.STATE_PLAY)
                    and cat.get("speech", {}).get("text") is None
                    and cat.get("speech_cooldown", 0) <= 0):
                self._trigger_speech("alert", cat_idx=s.cats.index(cat))
                cat["speech_cooldown"] = config.SPEECH_PROXIMITY_COOLDOWN

        # Approach walk (cat[0] backward compat — mouse within 80px)
        cat0 = s.cats[0] if s.cats else None
        if cat0 is not None:
            cx0 = cat0["x"]
            cy0 = cat0["y"]
            dx0 = cursor.x() - cx0
            dy0 = cursor.y() - cy0
            dist0 = math.hypot(dx0, dy0)

            if dist0 < 80 and cat0["state"] == config.STATE_SIT:
                if (time.monotonic() - cat0.get("last_interaction", 0.0) > 3.0 and
                    random.random() < 0.01):
                    cat0["facing"] = cursor.x() > cx0
                    cat0["state"] = config.STATE_WALK
                    cat0["walk_duration"] = max(0.8, random.uniform(1.5, 3.0))
                    cat0["walk_elapsed"] = 0.0
                    cat0["walk_accel"] = 0.0
                    cat0["walk_pause"] = False
                    cat0["walk_frame"] = 0
                    cat0["walk_accum"] = 0.0
                    self._walk_et.start()

        # ── Laser pointer chase (click-through OFF) for cat[0] ──
        if cat0 is not None:
            cx0 = cat0["x"]
            cy0 = cat0["y"]
            dx0 = cursor.x() - cx0
            dy0 = cursor.y() - cy0
            dist0 = math.hypot(dx0, dy0)

            if not s.click_through and dist0 < 300 and cat0["state"] in (config.STATE_SIT,):
                if self._mouse_moving:
                    cat0["toy_target"] = (cursor.x(), cursor.y())
                    cat0["toy_active"] = True
                    cat0["toy_type"] = "laser"
                    cat0["chase_timeout"] = config.CHASE_TIMEOUT
                    cat0["state"] = config.STATE_CHASE

            if cat0["state"] == config.STATE_CHASE:
                cat0["toy_target"] = (cursor.x(), cursor.y())

        # ── Check if cat caught the toy ──
        if cat0 is not None and cat0["state"] == config.STATE_PLAY and cat0.get("toy_active"):
            tx, ty = cat0["toy_target"]
            td = math.hypot(tx - cat0["x"], ty - cat0["y"])
            if td <= config.PLAY_TOY_REACH_DISTANCE:
                navigation._spawn_hearts_for_cat(cat0, count=5)
                cat0["state"] = config.STATE_SIT
                cat0["toy_active"] = False
                cat0["toy_type"] = None
                cat0["toy_target"] = None
                try:
                    self.sound.play("footstep")
                except Exception:
                    pass

    # ── Toy system ────────────────────────────────────────────────────

    def _update_toys(self, dt: float) -> None:
        """Handle yarn ball spawning and chase timeout."""
        s = self.state
        if not s.cats:
            return
        cat = s.cats[0]

        if s.click_through:
            self._toy_spawn_timer = 0.0
            return

        if cat["state"] in (config.STATE_CHASE, config.STATE_PLAY, config.STATE_SLEEP):
            return

        self._toy_spawn_timer += dt
        if self._toy_spawn_timer >= config.PLAY_TOY_INTERVAL and cat["state"] == config.STATE_SIT:
            self._toy_spawn_timer = 0.0

            mx, my = s.mouse_pos
            tx = mx + random.uniform(-60, 60)
            ty = my + random.uniform(-40, 40)

            margin = 50
            tx = max(float(margin), min(tx, float(s.screen_width - margin)))
            y_min = s.screen_height * config.CAT_MIN_Y_FRACTION
            y_max = s.screen_height - config.CAT_BASELINE
            ty = max(float(y_min), min(ty, float(y_max)))

            cat["toy_target"] = (tx, ty)
            cat["toy_active"] = True
            cat["toy_type"] = "ball"
            cat["toy_timer"] = config.PLAY_TOY_DURATION

            tdx = tx - cat["x"]
            tdy = ty - cat["y"]
            tdist = math.hypot(tdx, tdy)
            if tdist <= 100.0:
                cat["state"] = config.STATE_PLAY

        # Chase timeout
        if cat["state"] == config.STATE_CHASE:
            if not self._mouse_moving:
                cat["chase_timeout"] = cat.get("chase_timeout", config.CHASE_TIMEOUT) - dt
                if cat["chase_timeout"] <= 0:
                    cat["state"] = config.STATE_SIT
                    cat["toy_active"] = False
                    cat["toy_type"] = None
                    cat["toy_target"] = None
            else:
                cat["chase_timeout"] = config.CHASE_TIMEOUT

        # Yarn ball timer
        if cat["state"] == config.STATE_PLAY:
            cat["toy_timer"] = cat.get("toy_timer", 0.0) - dt
            if cat["toy_timer"] <= 0:
                cat["state"] = config.STATE_SIT
                cat["toy_active"] = False
                cat["toy_type"] = None

        # Advance toy drift
        if cat.get("toy_active") and cat.get("toy_type") == "ball" and cat.get("toy_target") is not None:
            tx, ty = cat["toy_target"]
            tx += math.sin(time.monotonic() * 0.5) * 5 * dt
            ty += math.cos(time.monotonic() * 0.7) * 3 * dt
            margin = 50
            tx = max(float(margin), min(tx, float(s.screen_width - margin)))
            y_min = s.screen_height * config.CAT_MIN_Y_FRACTION
            y_max = s.screen_height - config.CAT_BASELINE
            ty = max(float(y_min), min(ty, float(y_max)))
            cat["toy_target"] = (tx, ty)

    def _process_actions(self) -> None:
        navigation.process_actions(self.state)

    def _trigger_purr(self) -> None:
        if self.state.cats:
            navigation.trigger_purr(self.state)

    def reload_settings(self):
        """Reload settings from disk (called after settings dialog closes)."""
        try:
            from ui.settings import AppSettings
            settings = AppSettings.load()
            self._sound_enabled = settings.sound_enabled
        except ImportError:
            pass

    def _clamp_needs(self) -> None:
        for cat in self.state.cats:
            cat["energy"] = max(0.0, min(100.0, cat.get("energy", 80.0)))
            cat["hunger"] = max(0.0, min(100.0, cat.get("hunger", 20.0)))
            cat["boredom"] = max(0.0, min(100.0, cat.get("boredom", 0.0)))

    # ── System idle detection ───────────────────────────────────────────

    def _poll_idle(self):
        """Check GetLastInputInfo for system-wide idle (Windows only)."""
        if sys.platform != "win32":
            return
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
                    for cat in self.state.cats:
                        cat["deep_sleep"] = True
                else:
                    for cat in self.state.cats:
                        cat["deep_sleep"] = False
        except Exception as e:
            logging.warning("Idle detection failed: %s", e)