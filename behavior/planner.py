"""
behavior/planner.py — Behavior planner for Desktop Cat.

5-layer priority chain evaluated every tick:
1. EMERGENCY     → energy < 5 → collapse and sleep
2. SEQUENCE      → currently running sequence → continue it
3. INTERACTION   → user just clicked/hovered → respond (if cooldown)
4. NEEDS         → highest-priority unmet need → select sequence
5. IDLE          → no urgent needs → idle behaviors + micro-behaviors
"""

import logging
import random
from typing import Optional, Any

import config
from behavior.sequences import SequenceRunner, SEQUENCE_REGISTRY, register_trigger
from behavior.needs import update as needs_update

logger = logging.getLogger(__name__)


class BehaviorPlanner:
    """Behavior planner: evaluates cat state and selects behavioral sequences.

    Integrates circadian, needs, personality, and memory to choose what
    the cat does next.
    """

    def __init__(self):
        self.sequence_runner = SequenceRunner()
        self._last_priority = None
        self._lull_timer = 0.0
        self._lull_active = False
        self._stare_timer = 0.0
        self._micro_timer = 0.0
        self._activity_burst_start = None

    def update(
        self,
        dt: float,
        cat: dict,
        state,
        circadian=None,
        personality=None,
        memory=None,
    ) -> tuple:
        """Run the behavior selection chain.

        Args:
            dt: Delta time in seconds.
            cat: Cat state dict.
            state: Global state object.
            circadian: CircadianClock instance (optional).
            personality: Personality instance (optional).
            memory: CatMemory instance (optional).

        Returns:
            Tuple of (action: str, is_sequence: bool, priority: int)
            where action is the selected behavior action.
        """
        chain = self._evaluate_chain(cat, state, circadian, personality, memory)

        if chain is None:
            return ("idle", False, 0)

        action, is_sequence, priority = chain

        # If running a sequence, advance it
        if is_sequence and self.sequence_runner.running:
            seq_action = self.sequence_runner.current_action
            if seq_action:
                return (seq_action, True, priority)

        # Store last priority for debugging
        self._last_priority = priority

        return (action, is_sequence, priority)

    def _evaluate_chain(
        self,
        cat: dict,
        state,
        circadian,
        personality,
        memory,
    ) -> Optional[tuple]:
        """Evaluate 5-layer priority chain. Returns (action, is_sequence, priority)."""

        # Layer 1: EMERGENCY — energy critically low
        emergency_result = self._check_emergency(cat)
        if emergency_result:
            return emergency_result

        # Layer 2: SEQUENCE — currently running sequence
        if self.sequence_runner.running:
            seq_action = self.sequence_runner.current_action
            if seq_action:
                return (seq_action, True, 1)

        # Layer 3: INTERACTION — user just interacted
        interaction_result = self._check_interaction(cat, state, personality)
        if interaction_result:
            return interaction_result

        # Layer 4: NEEDS — bodily needs
        needs_result = self._check_needs(cat, state, circadian, personality)
        if needs_result:
            return needs_result

        # Layer 5: IDLE — nothing urgent
        return self._check_idle(cat, personality, circadian, memory)

    def _check_emergency(self, cat: dict) -> Optional[tuple]:
        """Layer 1: Emergency — energy critical."""
        if cat.get("energy", 100) < config.ENERGY_CRITICAL_THRESHOLD:
            logger.debug("EMERGENCY: energy=%d < %d", 
                         cat.get("energy", 100), config.ENERGY_CRITICAL_THRESHOLD)
            return ("sleep", False, 1)
        return None

    def _check_interaction(
        self, cat: dict, state, personality
    ) -> Optional[tuple]:
        """Layer 3: User interaction."""
        # Check if user recently interacted
        user_near = cat.get("user_nearby", False)
        pet_timer = cat.get("pet_timer", 0.0)

        if pet_timer > 0 and user_near:
            # ── Phase 3 Social: mood can suppress or boost greeting ──
            mood_mult = cat.get("mood_multiplier", 1.0)
            if mood_mult <= 0 or random.random() > mood_mult:
                # Cat doesn't feel like greeting right now
                return None
            return ("greet", False, 3)

        return None

    def _check_needs(
        self,
        cat: dict,
        state,
        circadian,
        personality,
    ) -> Optional[tuple]:
        """Layer 4: Highest-priority unmet need.

        Returns a need-driven action or None if all needs are satisfied.
        """
        if not config.NEEDS_ENABLED:
            return None

        hunger = cat.get("hunger", 0.0)
        boredom = cat.get("boredom", 0.0)
        energy = cat.get("energy", 100.0)

        # Hunger > 60 and dawn/dusk → HungerWalk
        if hunger > 60:
            hour = circadian.internal_hour if circadian else 0.0
            if 5 <= hour <= 7 or 17 <= hour <= 19:
                logger.debug("NEEDS: hunger=%.0f, hour=%.1f → HungerWalk", hunger, hour)
                return ("walk_to_food", False, 4)

        # Boredom > 60 → Play
        if boredom > 60:
            logger.debug("NEEDS: boredom=%.0f → play", boredom)
            return ("play", False, 4)

        # Energy low → sleep
        if energy < 40:
            logger.debug("NEEDS: energy=%.0f → sleep", energy)
            return ("sleep", False, 4)

        # High energy, low boredom, calm needs → window watch or patrol
        if energy > 70 and boredom < 30:
            if random.random() < 0.3:
                return ("window_watch", False, 5)

        return None

    def _check_idle(
        self,
        cat: dict,
        personality,
        circadian,
        memory,
    ) -> Optional[tuple]:
        """Layer 5: Idle — nothing urgent.

        Returns idle micro-behaviors and contemplative states.
        """
        # Micro-behaviors during idle (every 3-5s)
        self._micro_timer += 0.05  # approximate tick
        if self._micro_timer > random.uniform(3.0, 5.0):
            self._micro_timer = 0.0
            micro = random.choice([
                "ear_twitch", "slow_blink", "tail_twitch",
                "weight_shift", "look_around",
            ])
            return (micro, False, 6)

        # The Stare (5% chance per idle check)
        if random.random() < 0.05:
            return ("stare", False, 6)

        # Default: passive sit
        return ("sit", False, 6)

    def handle_interaction(self, interaction_type: str, cat: dict, state) -> None:
        """React to a user interaction (click, hover, etc.)."""
        cat["pet_timer"] = 2.0  # 2 seconds of engagement
        cat["user_nearby"] = True

    def is_cat_busy(self, cat: dict) -> bool:
        """Check if the cat is in a non-interruptible state."""
        if self.sequence_runner.running:
            return not self.sequence_runner.is_interruptible()
        return False

    def get_current_sequence_name(self) -> str:
        """Return the name of the currently running sequence."""
        return self.sequence_runner.name if self.sequence_runner.running else ""

    def reset(self) -> None:
        """Reset the planner state."""
        self.sequence_runner.stop()
        self._lull_timer = 0.0
        self._stare_timer = 0.0
        self._micro_timer = 0.0
