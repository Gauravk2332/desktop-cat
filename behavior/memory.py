"""
behavior/memory.py — Cat memory system.

Stores short-term (last 20 events) and long-term (JSON-persisted) memory.
Provides territory awareness from screen zones.

Long-term schema:
{
    "favorite_zones": {"sleep_corner": 12, "window_perch": 28},
    "schedule": {"hourly_activity": [0.2]*24},
    "interactions_today": 7,
    "mood": {"happiness": 65, "trust": 70},
    "current_territory_marks": {"sleep_corner": 1712345678}
}
"""

import json
import logging
import os
import tempfile
import time
from collections import deque
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)

# 6 predefined territory zones (relative fraction of screen)
# Calculated from screen_width, screen_height at runtime
TERRITORY_ZONES = [
    "sleep_corner",      # bottom-left
    "window_perch",      # top-center
    "desk_center",       # center area
    "food_area",         # bottom-right quadrant
    "play_area",         # center-right
    "litter_corner",     # far bottom-left/offscreen
]


def get_zone_for_position(x: float, y: float, screen_w: int, screen_h: int) -> str:
    """Map a position to a territory zone name."""
    if screen_w <= 0 or screen_h <= 0:
        return "unknown"

    # Normalize position to screen fraction
    nx = x / screen_w
    ny = y / screen_h

    if nx < 0.3 and ny > 0.6:
        return "sleep_corner"
    elif nx > 0.35 and nx < 0.65 and ny < 0.4:
        return "window_perch"
    elif nx > 0.35 and nx < 0.65 and ny >= 0.4 and ny < 0.7:
        return "desk_center"
    elif nx > 0.65 and ny > 0.6:
        return "food_area"
    elif nx > 0.5 and ny >= 0.3 and ny < 0.6:
        return "play_area"
    else:
        return "litter_corner"


class CatMemory:
    """Cat memory: short-term event log + long-term preference store."""

    def __init__(self, cat_id: int = 0):
        self.cat_id = cat_id
        self.short_term: deque = deque(maxlen=20)

        self._memory_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
        )
        self._memory_file = os.path.join(self._memory_dir, f"cat_memory_{cat_id}.json")
        self._territory_file = os.path.join(self._memory_dir, f"cat_territory_{cat_id}.json")

        self.long_term: dict = self._load_json(self._memory_file, self._default_memory())
        self.territory: dict = self._load_json(self._territory_file, {})

        self._last_territory_update = 0.0

    def _default_memory(self) -> dict:
        return {
            "favorite_zones": {},
            "schedule": {"hourly_activity": [0.0] * 24},
            "interactions_today": 0,
            "last_interaction_date": time.strftime("%Y-%m-%d"),
            "mood": {"happiness": 65, "trust": 70},
            "current_territory_marks": {},
        }

    @staticmethod
    def _load_json(filepath: str, default: dict) -> dict:
        """Load JSON with fallback to default."""
        try:
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except (json.JSONDecodeError, OSError, PermissionError) as e:
            logger.warning("Failed to load %s: %s — using defaults", filepath, e)
        return default

    def _save_json(self, filepath: str, data: dict) -> None:
        """Atomic write via temp-file+rename."""
        try:
            os.makedirs(self._memory_dir, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(dir=self._memory_dir, suffix=".tmp")
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, filepath)
        except (OSError, PermissionError) as e:
            logger.warning("Failed to save %s: %s", filepath, e)

    # ─── Event recording ──────────────────────────────────────────────

    def record_event(self, event_type: str, position: tuple, state: str = "") -> None:
        """Record an event in short-term memory."""
        event = {
            "type": event_type,
            "position": position,
            "state": state,
            "timestamp": time.time(),
        }
        self.short_term.append(event)

        # Update long-term: track zone visits
        if event_type in ("enter_zone", "walk", "sit", "sleep"):
            zone = get_zone_for_position(
                position[0], position[1],
                1920, 1080,  # fallback; caller should set screen size
            )
            self.long_term["favorite_zones"][zone] = \
                self.long_term["favorite_zones"].get(zone, 0) + 1

        # Daily reset check
        today = time.strftime("%Y-%m-%d")
        if self.long_term.get("last_interaction_date") != today:
            self.long_term["interactions_today"] = 0
            self.long_term["last_interaction_date"] = today

    def record_interaction(self) -> None:
        """Record a user interaction (click, hover, etc.)."""
        today = time.strftime("%Y-%m-%d")
        if self.long_term.get("last_interaction_date") != today:
            self.long_term["interactions_today"] = 0
            self.long_term["last_interaction_date"] = today
        self.long_term["interactions_today"] = \
            self.long_term.get("interactions_today", 0) + 1
        self.long_term["mood"]["happiness"] = min(100,
            self.long_term["mood"].get("happiness", 65) + 1)
        self.long_term["mood"]["trust"] = min(100,
            self.long_term["mood"].get("trust", 70) + 0.5)
        self.save()

    def get_recent_events(self, n: int = 5) -> list:
        """Get the N most recent events."""
        events = list(self.short_term)
        return events[-n:]

    def get_favorite_zone(self) -> str:
        """Return the most-visited territory zone."""
        zones = self.long_term.get("favorite_zones", {})
        if not zones:
            return "desk_center"
        return max(zones, key=zones.get)  # type: ignore

    def get_activity_at_hour(self, hour: int) -> float:
        """Return activity level (0.0-1.0) for a given hour of day."""
        schedule = self.long_term.get("schedule", {})
        hourly = schedule.get("hourly_activity", [0.0] * 24)
        if 0 <= hour < 24:
            return min(1.0, hourly[hour])
        return 0.0

    def record_activity(self, hour: int, amount: float = 1.0) -> None:
        """Record activity at a given hour (rolling average)."""
        schedule = self.long_term.get("schedule", {})
        hourly = schedule.get("hourly_activity", [0.0] * 24)
        if 0 <= hour < 24:
            # Rolling average: weight new value at 0.3
            hourly[hour] = hourly[hour] * 0.7 + min(1.0, amount) * 0.3
        self.save()

    # ─── Territory ────────────────────────────────────────────────────

    def update_territory_mark(self, zone: str) -> None:
        """Mark territory (set timestamp)."""
        self.long_term["current_territory_marks"][zone] = time.time()

    def is_territory_stale(self, zone: str, max_age: float = 3600.0) -> bool:
        """Check if a territory mark is older than max_age seconds."""
        marks = self.long_term.get("current_territory_marks", {})
        last = marks.get(zone, 0)
        return (time.time() - last) > max_age

    # ─── Persistence ──────────────────────────────────────────────────

    def save(self) -> None:
        """Save all memory to disk."""
        self._save_json(self._memory_file, self.long_term)
        self._save_json(self._territory_file, self.territory)

    def update_screen_size(self, width: int, height: int) -> None:
        """Update screen dimensions for zone calculation."""
        self.screen_width = width
        self.screen_height = height
