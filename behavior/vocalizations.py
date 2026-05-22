"""
behavior/vocalizations.py — Realistic cat behavioral sound system.

Evaluates per-cat state + needs + environment each tick and selects
the appropriate sound based on a priority queue. Designed as a
drop-in system registered in the engine.

Based on real cat behavior research:
  - Purr (25-150Hz): contentment, bonding, petted, sleeping
  - Trill (400→700Hz rising): happy greeting, "follow me"
  - Short meow (300-500Hz): greeting, solicitation
  - Long meow (600→350Hz descending): demand, complaint
  - Chirp (1-1.5kHz bird-like): excitement + prey frustration
  - Chatter (teeth-clicking): hunting fixation, laser excitement
  - Hiss (white noise 3-6kHz): fear, threat, sudden approach
  - Growl (80-150Hz rumbling): escalating warning
  - Yowl (800→400Hz descending): distress, pain, loneliness
  - Alert chirp: startle, curiosity

Sources:
  - blog.catcognition.com (3 acoustic categories, 21 vocalizations)
  - petmd.com (9 cat noises and meanings)
  - moderncat.com (cat sounds explained)
"""

import logging
import math
import random
import time
from collections import deque
from typing import Optional

import config

logger = logging.getLogger(__name__)

# ── Priority Tiers ──────────────────────────────────────────────────────
# Lower number = higher priority (played first)

TIER_DISTRESS = 0      # yowl, hiss — critical needs
TIER_URGENT = 1        # hungry meow, bored meow — moderate needs
TIER_INTERACT = 2      # greeting trill, play chirp — owner interaction
TIER_IDLE = 3          # random trill, idle chirp — voluntary
TIER_SILENT = 4        # no sound this tick

# ── Thresholds ──────────────────────────────────────────────────────────

# Distances in pixels (on 1920×1080 reference; scaled to screen width)
FAR_THRESHOLD = 400     # "owner is far away"
NEAR_THRESHOLD = 200    # "owner is nearby"
PET_DISTANCE = 60       # "owner is petting"
SUDDEN_SPEED = 800      # px/s — fast mouse movement toward cat

# Proximity history window
PROXIMITY_HISTORY_LEN = 10
MOUSE_POS_HISTORY_LEN = 5

# ── Sound Definition ────────────────────────────────────────────────────
# (name: str, cooldown: float, tier: int, description: str)

SOUND_DEFS = {
    # On-shot vocalizations
    "trill":       ("trill",       60.0, TIER_INTERACT, "Happy greeting"),
    "chirp":       ("chirp",       15.0, TIER_INTERACT, "Prey excitement chirp"),
    "chatter":     ("chatter",     20.0, TIER_INTERACT, "Hunting frustration chatter"),
    "hiss":        ("hiss",        120.0, TIER_DISTRESS,  "Fear/threat hiss"),
    "growl":       ("growl",       120.0, TIER_DISTRESS,  "Warning growl"),
    "yowl":        ("yowl",        180.0, TIER_DISTRESS,  "Distress howl"),
    "meow_short":  ("meow_short",  30.0, TIER_URGENT,   "Short greeting/want meow"),
    "meow_long":   ("meow_long",   60.0, TIER_URGENT,   "Long demand meow"),
    "alert":       ("alert",       30.0, TIER_INTERACT, "Startle chirp"),
}

# ── Helper Functions ────────────────────────────────────────────────────

def _distance(ax, ay, bx, by) -> float:
    return math.hypot(ax - bx, ay - by)


def _screen_scale(screen_width: int, val: float, ref_width: int = 1920) -> float:
    """Scale a pixel distance threshold relative to the actual screen width."""
    return val * (screen_width / ref_width)


# ── VocalizationState ──────────────────────────────────────────────────

class VocalizationState:
    """Per-cat tracking state for vocalization system."""

    __slots__ = (
        "last_sound_time",
        "last_sound_name",
        "cooldowns",
        "mouse_proximity",
        "mouse_positions",
        "mouse_timestamps",
        "was_near",
        "was_far",
        "was_pet",
        "greeting_cooldown",
        "idle_timer",
        "last_proximity_event",
        "alert_triggered",
    )

    def __init__(self):
        self.last_sound_time: float = 0.0
        self.last_sound_name: str = ""
        self.cooldowns: dict[str, float] = {}
        self.mouse_proximity: deque[float] = deque(maxlen=PROXIMITY_HISTORY_LEN)
        self.mouse_positions: deque[tuple[float, float]] = deque(maxlen=MOUSE_POS_HISTORY_LEN)
        self.mouse_timestamps: deque[float] = deque(maxlen=MOUSE_POS_HISTORY_LEN)
        self.was_near: bool = False
        self.was_far: bool = True   # start as "far" so first near triggers greeting
        self.was_pet: bool = False
        self.greeting_cooldown: float = 0.0
        self.idle_timer: float = random.uniform(5.0, 15.0)  # first idle sound after delay
        self.last_proximity_event: str = ""  # "returned", "sudden", "none"
        self.alert_triggered: bool = False

    def record_proximity(self, cat_x: float, cat_y: float, mouse_x: float, mouse_y: float, now: float):
        """Record mouse distance and position for motion analysis."""
        d = _distance(cat_x, cat_y, mouse_x, mouse_y)
        self.mouse_proximity.append(d)
        self.mouse_positions.append((mouse_x, mouse_y))
        self.mouse_timestamps.append(now)


# ── Proximity Event Detection ──────────────────────────────────────────

def _detect_proximity_events(vs: VocalizationState, cat_x: float, cat_y: float,
                             screen_width: int) -> dict:
    """Detect owner proximity events from mouse position history.

    Returns dict with keys:
      - "owner_returned": bool — mouse just entered near from far
      - "owner_left": bool — mouse just exited near
      - "sudden_approach": bool — fast mouse movement toward cat
      - "petting": bool — mouse within pet distance
      - "just_petted": bool — transition into pet range
      - "mouse_still": bool — mouse hasn't moved much
      - "current_distance": float
    """
    result = {
        "owner_returned": False,
        "owner_left": False,
        "sudden_approach": False,
        "petting": False,
        "just_petted": False,
        "mouse_still": False,
        "current_distance": 9999.0,
    }

    if len(vs.mouse_proximity) < 2:
        return result

    far_thresh = _screen_scale(screen_width, FAR_THRESHOLD)
    near_thresh = _screen_scale(screen_width, NEAR_THRESHOLD)
    pet_thresh = _screen_scale(screen_width, PET_DISTANCE)
    sudden_speed = _screen_scale(screen_width, SUDDEN_SPEED)

    current_dist = vs.mouse_proximity[-1]
    prev_dist = vs.mouse_proximity[-2] if len(vs.mouse_proximity) > 1 else current_dist
    result["current_distance"] = current_dist

    # Petting detection
    result["petting"] = current_dist <= pet_thresh
    result["just_petted"] = current_dist <= pet_thresh and prev_dist > pet_thresh
    vs.was_pet = result["petting"]

    # Owner returned: far → near transition (with hysteresis)
    is_near = current_dist <= near_thresh
    if is_near and not vs.was_near:
        # Check they were actually far before
        if len(vs.mouse_proximity) >= PROXIMITY_HISTORY_LEN:
            recent_far = sum(1 for d in vs.mouse_proximity if d > far_thresh)
            if recent_far >= PROXIMITY_HISTORY_LEN // 2 and vs.greeting_cooldown <= 0:
                result["owner_returned"] = True
                vs.greeting_cooldown = 60.0  # don't re-greet for 60s
    vs.was_near = is_near

    # Owner left: near → far
    if not is_near and vs.was_near:
        result["owner_left"] = True

    # Sudden approach: mouse velocity toward cat over threshold
    if len(vs.mouse_positions) >= 2 and len(vs.mouse_timestamps) >= 2:
        px, py = vs.mouse_positions[-1]
        ppx, ppy = vs.mouse_positions[-2]
        dt = vs.mouse_timestamps[-1] - vs.mouse_timestamps[-2]
        if dt > 0:
            speed = _distance(px, py, ppx, ppy) / dt
            # Check if moving toward cat
            old_dist = _distance(ppx, ppy, cat_x, cat_y)
            new_dist = _distance(px, py, cat_x, cat_y)
            moving_toward = new_dist < old_dist
            if speed > sudden_speed and moving_toward and current_dist <= near_thresh * 2:
                result["sudden_approach"] = True
                vs.alert_triggered = True

    # Mouse still detection
    if len(vs.mouse_positions) >= 3:
        positions = list(vs.mouse_positions)[-3:]
        total_move = sum(
            _distance(positions[i][0], positions[i][1], positions[i - 1][0], positions[i - 1][1])
            for i in range(1, len(positions))
        )
        result["mouse_still"] = total_move < 5.0

    return result


# ── Sound Candidate ────────────────────────────────────────────────────

class SoundCandidate:
    """A potential sound to play, created by a trigger function."""

    __slots__ = ("name", "tier", "volume_boost")

    def __init__(self, name: str, tier: int, volume_boost: float = 0.0):
        self.name = name
        self.tier = tier
        self.volume_boost = volume_boost


# ── Trigger Functions ──────────────────────────────────────────────────

def _check_distress(vs: VocalizationState, cat: dict, now: float,
                   proximity: dict = None) -> Optional[SoundCandidate]:
    """Check for critical need distress: yowl when very hungry or exhausted."""
    hunger = cat.get("hunger", 20.0)
    energy = cat.get("energy", 80.0)
    state = cat.get("state", "SIT")

    if state == config.STATE_SLEEP:
        return None

    # Yowl at critical needs (only if cooldown expired)
    if hunger > 90 or energy < 15:
        cd = vs.cooldowns.get("yowl", 0.0)
        if now - cd >= 180.0:
            return SoundCandidate("yowl", TIER_DISTRESS)
        # If already yowled recently, escalate to urgent meow
        cd_short = vs.cooldowns.get("meow_long", 0.0)
        if now - cd_short >= 60.0:
            return SoundCandidate("meow_long", TIER_URGENT)

    # Urgent meow at moderate hunger
    if hunger > 70:
        cd = vs.cooldowns.get("meow_long", 0.0)
        if now - cd >= 60.0:
            return SoundCandidate("meow_long", TIER_URGENT)

    return None


def _check_boredom(vs: VocalizationState, cat: dict, now: float,
                   proximity: dict) -> Optional[SoundCandidate]:
    """Check for boredom-based meows."""
    boredom = cat.get("boredom", 0.0)
    state = cat.get("state", "SIT")

    if state in (config.STATE_SLEEP, config.STATE_CHASE, config.STATE_PLAY):
        return None

    # Escalating boredom meows
    if boredom > 80:
        cd = vs.cooldowns.get("meow_long", 0.0)
        if now - cd >= 45.0:
            return SoundCandidate("meow_long", TIER_URGENT)

    if boredom > 60:
        cd = vs.cooldowns.get("meow_short", 0.0)
        if now - cd >= 30.0 and random.random() < 0.4:
            return SoundCandidate("meow_short", TIER_URGENT)

    # Idle meow at moderate boredom (less frequent)
    if boredom > 40 and state == config.STATE_SIT:
        cd = vs.cooldowns.get("meow_short", 0.0)
        if now - cd >= 60.0 and random.random() < 0.15:
            return SoundCandidate("meow_short", TIER_IDLE)

    return None


def _check_proximity(vs: VocalizationState, cat: dict, now: float,
                     proximity: dict) -> Optional[SoundCandidate]:
    """Check for proximity-based vocalizations."""
    state = cat.get("state", "SIT")

    # Sudden approach → hiss or alert
    if proximity.get("sudden_approach") and state != config.STATE_SLEEP:
        cd = vs.cooldowns.get("hiss", 0.0)
        if now - cd >= 120.0:
            return SoundCandidate("hiss", TIER_DISTRESS)

    # Owner returned → greeting trill (or short meow if trill on cooldown)
    if proximity.get("owner_returned"):
        cd = vs.cooldowns.get("trill", 0.0)
        if now - cd >= 60.0:
            return SoundCandidate("trill", TIER_INTERACT)
        else:
            cd_short = vs.cooldowns.get("meow_short", 0.0)
            if now - cd_short >= 30.0:
                return SoundCandidate("meow_short", TIER_INTERACT)

    # Just started petting → purr (handled by engine loop, but also trill)
    if proximity.get("just_petted") and random.random() < 0.3:
        cd = vs.cooldowns.get("trill", 0.0)
        if now - cd >= 120.0:
            return SoundCandidate("trill", TIER_INTERACT)

    return None


def _check_play_excitement(vs: VocalizationState, cat: dict, now: float,
                           proximity: dict) -> Optional[SoundCandidate]:
    """Check for play/hunt excitement sounds."""
    state = cat.get("state", "SIT")

    if state == config.STATE_CHASE:
        # Chirp when chasing laser
        cd = vs.cooldowns.get("chirp", 0.0)
        if now - cd >= 10.0 and random.random() < 0.3:
            return SoundCandidate("chirp", TIER_INTERACT)
        # Chatter during chase (less frequent)
        cd_chat = vs.cooldowns.get("chatter", 0.0)
        if now - cd_chat >= 20.0 and random.random() < 0.15:
            return SoundCandidate("chatter", TIER_INTERACT)

    if state == config.STATE_PLAY:
        cd = vs.cooldowns.get("chirp", 0.0)
        if now - cd >= 15.0 and random.random() < 0.2:
            return SoundCandidate("chirp", TIER_INTERACT)

    return None


def _check_idle_vocalizations(vs: VocalizationState, cat: dict, now: float,
                              proximity: dict) -> Optional[SoundCandidate]:
    """Check for random idle sounds: trills, chirps, meows."""
    state = cat.get("state", "SIT")
    boredom = cat.get("boredom", 0.0)

    if state in (config.STATE_SLEEP, config.STATE_CHASE, config.STATE_PLAY):
        vs.idle_timer = random.uniform(8.0, 20.0)  # reset
        return None

    # Owner nearby but not petting = cat is more likely to chirp/trill
    owner_near = proximity.get("current_distance", 9999) < _screen_scale(
        cat.get("_screen_width", 1920), NEAR_THRESHOLD
    )
    owner_petting = proximity.get("petting")

    if vs.idle_timer <= 0:
        vs.idle_timer = random.uniform(8.0, 30.0)  # next idle sound delay

        candidates = []

        # Trill when owner is near (happy, showing off)
        if owner_near:
            cd = vs.cooldowns.get("trill", 0.0)
            if now - cd >= 90.0 and random.random() < 0.4:
                candidates.append(SoundCandidate("trill", TIER_IDLE))

        # Short meow when owner is near but not engaging
        if owner_near and not owner_petting and boredom > 30:
            cd = vs.cooldowns.get("meow_short", 0.0)
            if now - cd >= 60.0 and random.random() < 0.3:
                candidates.append(SoundCandidate("meow_short", TIER_IDLE))

        # Rare chirp when sitting and bored
        if boredom > 20 and random.random() < 0.2:
            cd = vs.cooldowns.get("chirp", 0.0)
            if now - cd >= 45.0:
                candidates.append(SoundCandidate("chirp", TIER_IDLE))

        # Random purr-like trill when content (low boredom, not hungry)
        if boredom < 30 and cat.get("hunger", 20) < 50 and random.random() < 0.25:
            cd = vs.cooldowns.get("trill", 0.0)
            if now - cd >= 60.0:
                candidates.append(SoundCandidate("trill", TIER_IDLE))

        if candidates:
            return random.choice(candidates)

    return None


# ── VocalizationSystem ─────────────────────────────────────────────────

class VocalizationSystem:
    """Per-cat behavioral sound system. Evaluates state each tick and
    enqueues sound candidates resolved by priority.

    Designed to be registered as an engine system and called per cat.
    """

    def __init__(self, state):
        self._vocal_states: list[VocalizationState] = []
        self._last_sound_played: str = ""
        self._last_sound_time: float = 0.0

        # Initialize per-cat vocal states
        for cat in getattr(state, "cats", []):
            self._vocal_states.append(VocalizationState())

        self._pad_vocal_states(len(getattr(state, "cats", [])))

    def _pad_vocal_states(self, target: int):
        """Ensure vocal_states list matches cats count."""
        while len(self._vocal_states) < target:
            self._vocal_states.append(VocalizationState())
        while len(self._vocal_states) > target:
            self._vocal_states.pop()

    def get_vocal_state(self, cat_idx: int) -> VocalizationState:
        """Get vocalization state for a specific cat."""
        while len(self._vocal_states) <= cat_idx:
            self._vocal_states.append(VocalizationState())
        return self._vocal_states[cat_idx]

    def update(self, dt: float, cat: dict, state) -> Optional[SoundCandidate]:
        """Evaluate one cat and return the best sound to play (or None).

        This should be called per-cat by the engine's tick loop.
        The engine is responsible for actually calling sound.play().

        Args:
            dt: Delta time since last tick
            cat: Per-cat state dict
            state: Global CatState (for screen dimensions)

        Returns:
            SoundCandidate if a sound should play, None otherwise.
        """
        cat_idx = cat.get("id", 0)
        vs = self.get_vocal_state(cat_idx)
        now = time.monotonic()

        # Update greeting cooldown
        vs.greeting_cooldown = max(0.0, vs.greeting_cooldown - dt)

        # Record mouse proximity (from global state mouse tracking)
        mouse_x = getattr(state, "_mouse_x", 0.0)
        mouse_y = getattr(state, "_mouse_y", 0.0)
        vs.record_proximity(cat["x"], cat["y"], mouse_x, mouse_y, now)

        # Detect proximity events
        proximity = _detect_proximity_events(vs, cat["x"], cat["y"],
                                             getattr(state, "screen_width", 1920))
        # Store screen width for scaling
        cat["_screen_width"] = getattr(state, "screen_width", 1920)

        # Decrement idle timer (using real dt from game loop)
        vs.idle_timer -= dt

        # Collect sound candidates from all trigger functions
        candidates: list[SoundCandidate] = []

        for check_fn in [
            _check_distress,
            _check_boredom,
            _check_proximity,
            _check_play_excitement,
            _check_idle_vocalizations,
        ]:
            result = check_fn(vs, cat, now, proximity)
            if result is not None:
                candidates.append(result)

        if not candidates:
            return None

        # Priority resolution: select the highest-priority (lowest tier number) sound.
        # Within same tier, random selection weighted by urgency.
        candidates.sort(key=lambda c: c.tier)

        best_tier = candidates[0].tier
        same_tier = [c for c in candidates if c.tier == best_tier]

        if not same_tier:
            return None

        # Resolve ties randomly
        winner = random.choice(same_tier)

        # Check cooldown explicitly (shouldn't normally fail since trigger
        # functions check their own cooldowns, but safety net)
        _, _, definition_tier, _ = SOUND_DEFS.get(winner.name, ("", 0, TIER_SILENT, ""))
        if winner.name in vs.cooldowns:
            cd_duration = SOUND_DEFS.get(winner.name, (winner.name, 60.0, TIER_IDLE, ""))[1]
            if now - vs.cooldowns[winner.name] < cd_duration:
                # Cooldown not expired — pick next best
                candidates = [c for c in candidates if c.name != winner.name]
                if candidates:
                    candidates.sort(key=lambda c: c.tier)
                    winner = random.choice([c for c in candidates if c.tier == candidates[0].tier])
                else:
                    return None

        # Record cooldown
        vs.cooldowns[winner.name] = now
        vs.last_sound_name = winner.name
        vs.last_sound_time = now

        return winner

    def update_mouse_position(self, mouse_x: float, mouse_y: float):
        """Update the global mouse position reference on state."""
        # This is called from engine._check_mouse
        pass

    def reset(self, cat_idx: int = 0):
        """Reset vocalization state for a specific cat (e.g., after load)."""
        while len(self._vocal_states) <= cat_idx:
            self._vocal_states.append(VocalizationState())
        self._vocal_states[cat_idx] = VocalizationState()
