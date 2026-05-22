"""behavior/mood.py — Continuous happiness + trust signals. Persisted JSON."""

import json
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


class MoodState:
    """Tracks cat mood (happiness, trust) with persistence and time decay.

    Happiness (0-100): boosted by petting/play, decays without interaction.
    Trust (0-100): slower to change, reflects long-term relationship.
    """

    def __init__(self, load_from_file=True, persist_dir=None):
        self.happiness = 65.0  # 0-100
        self.trust = 70.0      # 0-100
        self._clock = 0.0
        self.persist_dir = persist_dir or os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            "Nova", "desktop-cat"
        )
        self.persist_file = os.path.join(self.persist_dir, "mood.json")
        self._decay_interval = 300.0  # 5 minutes
        self._happiness_decay_per_interval = 1.0
        self._happiness_minimum = 30.0
        self._happiness_maximum = 100.0
        self._trust_minimum = 0.0
        self._trust_maximum = 100.0

        if load_from_file:
            self._load()

    def apply_interaction(self, interaction_type: str) -> None:
        """Apply mood changes from user interaction."""
        if interaction_type == "pet":
            self.happiness = min(self._happiness_maximum, self.happiness + 3)
            self.trust = min(self._trust_maximum, self.trust + 1)
        elif interaction_type == "play":
            self.happiness = min(self._happiness_maximum, self.happiness + 5)
            self.trust = min(self._trust_maximum, self.trust + 2)
        elif interaction_type == "startle":
            self.happiness = max(0, self.happiness - 10)
            self.trust = max(0, self.trust - 5)
        self._save()

    def update(self, dt: float) -> None:
        """Decay mood over time when no interaction."""
        self._clock += dt
        if self._clock >= self._decay_interval:
            n_decays = int(self._clock / self._decay_interval)
            self.happiness = max(self._happiness_minimum,
                                 self.happiness - n_decays * self._happiness_decay_per_interval)
            self._clock %= self._decay_interval
            self._save()

    def get_greeting_multiplier(self) -> float:
        """Return greeting frequency multiplier based on happiness."""
        if self.happiness >= 80:
            return 2.0  # Happy cat greets 2x more
        elif self.happiness >= 50:
            return 1.0  # Normal
        elif self.happiness >= 30:
            return 0.5  # Sad cat greets half as much
        else:
            return 0.2  # Very unhappy cat rarely greets

    def get_approach_distance(self) -> float:
        """Return preferred approach distance based on trust.

        Trusting cat approaches closer (minimum ~50px).
        Untrusting cat keeps distance (up to ~200px).
        """
        return max(30.0, 200.0 - self.trust * 1.5)

    @property
    def mood_multiplier(self) -> float:
        """Alias for greeting_multiplier — used by planner."""
        return self.get_greeting_multiplier()

    def _load(self) -> None:
        """Load persisted mood state from disk."""
        try:
            if os.path.exists(self.persist_file):
                with open(self.persist_file) as f:
                    d = json.load(f)
                    self.happiness = float(d.get("happiness", 65.0))
                    self.trust = float(d.get("trust", 70.0))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load mood: %s", e)

    def _save(self) -> None:
        """Persist mood state to disk atomically."""
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self.persist_dir)
            with os.fdopen(fd, 'w') as f:
                json.dump({
                    "happiness": self.happiness,
                    "trust": self.trust,
                }, f)
            os.replace(tmp, self.persist_file)
        except OSError as e:
            logger.warning("Failed to save mood: %s", e)
