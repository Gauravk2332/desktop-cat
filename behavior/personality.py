"""
behavior/personality.py — 5-trait personality system.

Each cat has five traits (0-10 scale) that modulate behavior parameters:
  - boldness: reaction speed, mouse approach rate
  - playfulness: play frequency
  - affection: greeting frequency, follow rate
  - laziness: activity duration, sleep preference
  - curiosity: investigation frequency, object response

Persisted to data/personality.json (atomic writes with temp-file+rename).
"""

import json
import os
import random

import config


PERSONALITY_SCHEMA = {
    "boldness": {"default": 5, "affects": ["reaction_speed", "mouse_approach_rate"]},
    "playfulness": {"default": 7, "affects": ["play_frequency"]},
    "affection": {"default": 7, "affects": ["greeting_frequency", "follow_rate"]},
    "laziness": {"default": 3, "affects": ["activity_duration", "sleep_preference"]},
    "curiosity": {"default": 6, "affects": ["investigation_frequency", "object_response"]},
}


class Personality:
    """5-trait personality for a single cat.

    Traits are 0-10 (raw) but also available normalized to 0.0-1.0.
    Mutations auto-persist to disk via atomic write.
    """

    def __init__(self, cat_index: int = 0, load_from_file: bool = True):
        self._traits: dict[str, int] = {}
        self._cat_index = cat_index

        if load_from_file:
            self._load()
        self._apply_defaults()

    # ── Public API ──────────────────────────────────────────────────

    def get(self, trait: str, normalized: bool = False) -> float:
        """Return trait value.

        Args:
            trait: One of 'boldness', 'playfulness', 'affection', 'laziness', 'curiosity'
            normalized: If True, return 0.0-1.0 instead of 0-10

        Returns:
            float: trait value
        """
        if normalized:
            return self._traits.get(trait, PERSONALITY_SCHEMA[trait]["default"]) / 10.0
        return float(self._traits.get(trait, PERSONALITY_SCHEMA[trait]["default"]))

    def get_raw(self, trait: str) -> int:
        """Return raw integer trait value (0-10)."""
        return int(round(self._traits.get(trait, PERSONALITY_SCHEMA[trait]["default"])))

    def modify(self, trait: str, delta: int) -> None:
        """Adjust a trait by delta, clamped to 0-10, and auto-save."""
        if trait not in PERSONALITY_SCHEMA:
            raise ValueError(f"Unknown trait: {trait}")

        current = self._traits.get(trait, PERSONALITY_SCHEMA[trait]["default"])
        new_value = max(0, min(10, current + delta))
        self._traits[trait] = new_value
        self.save()

    # ── Behavior Mapping ────────────────────────────────────────────

    def get_reaction_delay(self) -> float:
        """Map boldness to reaction delay.

        bold=2 → 2.2s, bold=5 → 1.5s, bold=8 → 0.8s, bold=10 → 0.5s
        """
        bold = self.get("boldness", normalized=True)  # 0.0-1.0
        # Inverse linear: low boldness = long delay
        delay = 2.5 - bold * 2.0  # range: 2.5s down to 0.5s
        return max(0.5, delay)

    def get_behavior_bias(self) -> dict[str, float]:
        """Return a dict of behavior weights based on all 5 traits.

        Weights are returned as positive floats; higher = more likely.
        """
        b = self.get("boldness", normalized=True)
        p = self.get("playfulness", normalized=True)
        a = self.get("affection", normalized=True)
        l = self.get("laziness", normalized=True)
        c = self.get("curiosity", normalized=True)

        return {
            "walk":          0.5 + b * 0.5,
            "sleep":         0.1 + l * 0.9,
            "play":          0.1 + p * 0.9,
            "greet":         0.1 + a * 0.9,
            "investigate":   0.1 + c * 0.9,
            "flee":          0.5 - b * 0.4,
            "follow_mouse":  0.1 + b * 0.4 + a * 0.3,
        }

    def get_play_chance(self) -> float:
        """Probability boost for play behavior based on playfulness."""
        return self.get("playfulness", normalized=True) * 0.8 + 0.1

    def get_sleep_threshold(self) -> float:
        """Energy threshold to trigger sleep (inversely proportional to laziness)."""
        lazy = self.get("laziness", normalized=True)
        # Lazy cats sleep earlier (higher energy threshold)
        return 30.0 + lazy * 40.0  # range: 30-70

    def get_wake_threshold(self) -> float:
        """Energy threshold to wake up (proportional to laziness)."""
        lazy = self.get("laziness", normalized=True)
        # Lazy cats sleep longer (higher wake threshold)
        return 60.0 + lazy * 30.0  # range: 60-90

    def get_approach_chance(self) -> float:
        """Chance to approach mouse cursor based on boldness+affection."""
        return self.get("boldness", normalized=True) * 0.4 + self.get("affection", normalized=True) * 0.3

    # ── Persistence ─────────────────────────────────────────────────

    def save(self) -> None:
        """Atomically persist traits to data/personality.json."""
        data = self._load_file()
        data[str(self._cat_index)] = dict(self._traits)
        self._atomic_write(data)

    def _load(self) -> None:
        """Load traits from disk, populating self._traits."""
        data = self._load_file()
        stored = data.get(str(self._cat_index), {})
        for trait_name in PERSONALITY_SCHEMA:
            if trait_name in stored:
                self._traits[trait_name] = stored[trait_name]

    def _apply_defaults(self) -> None:
        """Fill any missing traits with defaults from schema."""
        for name, info in PERSONALITY_SCHEMA.items():
            if name not in self._traits:
                self._traits[name] = info["default"]

    def _load_file(self) -> dict:
        """Read entire personality file, or return empty dict."""
        path = config.PERSONALITY_FILE
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _atomic_write(self, data: dict) -> None:
        """Write data to disk via temp-file + rename for crash safety."""
        path = config.PERSONALITY_FILE
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, path)
        except OSError:
            # Best effort — don't let persistence crashes affect runtime
            pass

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        traits = ", ".join(f"{k}={v}" for k, v in sorted(self._traits.items()))
        return f"<{cls} cat={self._cat_index} [{traits}]>"
