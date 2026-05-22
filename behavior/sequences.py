"""
behavior/sequences.py — Predefined behavioral sequences for Desktop Cat.

Each sequence is a list of steps the cat performs in order.
Sequences can be interrupted at step boundaries (via can_interrupt flag).

Sequences:
  MorningWake, HungerWalk, PlayBurst, GroomSession, SleepSequence,
  GreetingUser, WindowWatch, Patrol, Contemplation, TheStare
"""

import random
from typing import Optional

import config

# ─── Sequence schema ──────────────────────────────────────────────────
# Each sequence is a list of dicts:
#   {"step": str, "duration": float, "can_interrupt": bool}

# ─── Individual Sequences ─────────────────────────────────────────────

MORNING_WAKE = [
    {"action": "stretch",    "duration": 3.2, "can_interrupt": True},
    {"action": "yawn",       "duration": 2.7, "can_interrupt": True},
    {"action": "sit",        "duration": 1.0, "can_interrupt": True},
    {"action": "look_around", "duration": 2.0, "can_interrupt": True},
    {"action": "meow",       "duration": 0.5, "can_interrupt": True},
]

HUNGER_WALK = [
    {"action": "stand",      "duration": 0.8, "can_interrupt": True},
    {"action": "walk_to_food","duration": 5.0, "can_interrupt": False},
    {"action": "eat",        "duration": 4.0, "can_interrupt": False},
    {"action": "groom_face",  "duration": 3.0, "can_interrupt": True},
    {"action": "sit",        "duration": 2.0, "can_interrupt": True},
]

PLAY_BURST = [
    {"action": "stalk",      "duration": 2.0, "can_interrupt": True},
    {"action": "pounce",     "duration": 1.0, "can_interrupt": True},
    {"action": "bat",        "duration": 3.0, "can_interrupt": True},
    {"action": "bunny_kick",  "duration": 2.5, "can_interrupt": True},
    {"action": "groom_fur",   "duration": 4.0, "can_interrupt": True},
    {"action": "sit",        "duration": 3.0, "can_interrupt": True},
]

GROOM_SESSION = [
    {"action": "paw_lick",   "duration": 2.0, "can_interrupt": True},
    {"action": "paw_lick",   "duration": 2.0, "can_interrupt": True},
    {"action": "paw_lick",   "duration": 2.0, "can_interrupt": True},
    {"action": "paw_lick",   "duration": 2.0, "can_interrupt": True},
    {"action": "rub_face",   "duration": 3.0, "can_interrupt": True},
    {"action": "shake",      "duration": 1.0, "can_interrupt": True},
    {"action": "sit",        "duration": 2.0, "can_interrupt": True},
]

SLEEP_SEQUENCE = [
    {"action": "lie_down",   "duration": 1.5, "can_interrupt": True},
    {"action": "curl",       "duration": 2.0, "can_interrupt": True},
    {"action": "deep_sleep",  "duration": 600.0, "can_interrupt": True},
    {"action": "rem_sleep",  "duration": 60.0, "can_interrupt": True},
    {"action": "rem_sleep",  "duration": 60.0, "can_interrupt": True},
    {"action": "rem_sleep",  "duration": 60.0, "can_interrupt": True},
    {"action": "light_sleep","duration": 120.0, "can_interrupt": True},
    {"action": "wake",       "duration": 1.0, "can_interrupt": True},
]

GREETING_USER = [
    {"action": "look_toward","duration": 1.0, "can_interrupt": True},
    {"action": "walk_to_user","duration": 4.0, "can_interrupt": True},
    {"action": "sit_near_user","duration": 2.0, "can_interrupt": True},
    {"action": "slow_blink",  "duration": 1.5, "can_interrupt": True},
    {"action": "chirp",      "duration": 0.5, "can_interrupt": True},
]

WINDOW_WATCH = [
    {"action": "walk_to_window","duration": 3.0, "can_interrupt": True},
    {"action": "sit_look",   "duration": 30.0, "can_interrupt": True},
    {"action": "head_track",  "duration": 15.0, "can_interrupt": True},
    {"action": "chirp",      "duration": 0.5, "can_interrupt": True},
    {"action": "tail_twitch", "duration": 2.0, "can_interrupt": True},
]

PATROL = [
    {"action": "walk_zone",  "duration": 5.0, "can_interrupt": True},
    {"action": "sniff",      "duration": 3.0, "can_interrupt": True},
    {"action": "walk_zone",  "duration": 5.0, "can_interrupt": True},
    {"action": "sniff",      "duration": 3.0, "can_interrupt": True},
    {"action": "walk_zone",  "duration": 5.0, "can_interrupt": True},
    {"action": "mark",       "duration": 2.0, "can_interrupt": True},
]

CONTEMPLATION = [
    {"action": "loaf",       "duration": 15.0, "can_interrupt": True},
    {"action": "stare",      "duration": 10.0, "can_interrupt": True},
    {"action": "slow_blink",  "duration": 2.0, "can_interrupt": True},
    {"action": "ear_flick",   "duration": 1.0, "can_interrupt": True},
    {"action": "shift_weight","duration": 1.5, "can_interrupt": True},
    {"action": "stare",      "duration": 15.0, "can_interrupt": True},
]

THE_STARE = [
    {"action": "freeze",     "duration": 0.5, "can_interrupt": True},
    {"action": "stare_vacant","duration": 15.0, "can_interrupt": True},
    {"action": "slow_blink",  "duration": 2.0, "can_interrupt": True},
    {"action": "stare_vacant","duration": 10.0, "can_interrupt": True},
    {"action": "resume",     "duration": 1.0, "can_interrupt": True},
]

# ─── Sequence Registry ────────────────────────────────────────────────

SEQUENCE_REGISTRY = {
    "MorningWake": MORNING_WAKE,
    "HungerWalk": HUNGER_WALK,
    "PlayBurst": PLAY_BURST,
    "GroomSession": GROOM_SESSION,
    "SleepSequence": SLEEP_SEQUENCE,
    "GreetingUser": GREETING_USER,
    "WindowWatch": WINDOW_WATCH,
    "Patrol": PATROL,
    "Contemplation": CONTEMPLATION,
    "TheStare": THE_STARE,
}

# Trigger conditions: (sequence_name, priority, condition_fn)
# Priority: 1=highest, 10=lowest

_SEQUENCE_TRIGGERS: list = []


def register_trigger(name: str, priority: int, condition_fn) -> None:
    """Register a condition function for a sequence.

    Args:
        name: Sequence name (must be in SEQUENCE_REGISTRY)
        priority: 1=highest, 10=lowest
        condition_fn: callable(cat_dict, state) → bool
    """
    if name not in SEQUENCE_REGISTRY:
        raise ValueError(f"Unknown sequence: {name}")
    _SEQUENCE_TRIGGERS.append((priority, name, condition_fn))
    _SEQUENCE_TRIGGERS.sort(key=lambda x: x[0])  # sort by priority


def get_best_sequence(cat: dict, state) -> Optional[list]:
    """Evaluate all triggers and return the highest-priority matching sequence.

    Returns None if no sequence matches (idle fallback).
    """
    for priority, name, condition_fn in _SEQUENCE_TRIGGERS:
        try:
            if condition_fn(cat, state):
                return SEQUENCE_REGISTRY.get(name)
        except Exception:
            continue
    return None


class SequenceRunner:
    """Executes a behavioral sequence step by step."""

    def __init__(self):
        self.sequence: Optional[list] = None
        self.step_index: int = 0
        self.step_timer: float = 0.0
        self.name: str = ""
        self.running: bool = False

    def start(self, name: str, sequence: list) -> None:
        """Start a new sequence from the beginning."""
        self.name = name
        self.sequence = sequence
        self.step_index = 0
        self.step_timer = 0.0
        self.running = True

    def update(self, dt: float) -> Optional[str]:
        """Advance the sequence timer. Returns current action or None if stuck/idle.

        Returns the current step's action string, or None if no sequence is running.
        When a sequence completes, sets running=False and returns None.
        """
        if not self.running or not self.sequence:
            self.running = False
            return None

        sequence = self.sequence
        if self.step_index >= len(sequence):
            self.running = False
            return None

        step = sequence[self.step_index]
        self.step_timer += dt

        if self.step_timer >= step["duration"]:
            self.step_timer = 0.0
            self.step_index += 1
            if self.step_index >= len(sequence):
                self.running = False
                return None

        return step["action"]

    def get_current_step(self) -> Optional[dict]:
        """Return the current step dict, or None."""
        if not self.running or not self.sequence:
            return None
        if 0 <= self.step_index < len(self.sequence):
            return self.sequence[self.step_index]
        return None

    def is_interruptible(self) -> bool:
        """Check if the current step can be interrupted."""
        step = self.get_current_step()
        return step is None or step.get("can_interrupt", True)

    def stop(self) -> None:
        """Force-stop the current sequence."""
        self.running = False
        self.sequence = None
        self.step_index = 0
        self.step_timer = 0.0

    def get_progress(self) -> float:
        """Return progress through current sequence (0.0-1.0)."""
        if not self.sequence:
            return 0.0
        total_duration = sum(s["duration"] for s in self.sequence)
        if total_duration <= 0:
            return 0.0
        elapsed = 0.0
        for i in range(self.step_index):
            elapsed += self.sequence[i]["duration"]
        elapsed += self.step_timer
        return min(1.0, elapsed / total_duration)

    @property
    def current_action(self) -> str:
        """Return the current action string, or empty string."""
        step = self.get_current_step()
        return step["action"] if step else ""
