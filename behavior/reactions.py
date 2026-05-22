"""
behavior/reactions.py — Delayed reaction system for user interactions.

Cats don't respond instantly. Every user-initiated interaction has a
0.5-2.5s randomized latency before the cat visibly reacts. Before the
reaction, the cat may flick an ear or glance toward the user (pre-reaction).

Bold cats: 0.5-1.5s delay · Shy cats: 1.5-2.5s delay
"""

import random

from behavior.personality import Personality


DELAY_BOLD = (0.5, 1.5)
DELAY_SHY = (1.5, 2.5)


# Pre-reaction cues — quick micro-movements before the main reaction
PRE_REACTIONS = [
    "ear_flick",
    "glance",
    "ear_twitch",
    None,  # No pre-reaction (sometimes direct)
    None,
    None,  # Weight toward no pre-reaction for variety
]


class ReactionSystem:
    """Determines reaction delays and pre-reaction cues for user interactions.

    Args:
        personality: A Personality instance used to calibrate delay ranges.
    """

    def __init__(self, personality: Personality):
        self._personality = personality

    def get_reaction_delay(self, interaction_type: str = "click") -> float:
        """Return the delay in seconds before the cat should visibly react.

        Interaction type mapping:
          - "click"    → faster end of range (attention-grabbing)
          - "hover"    → slower end (more passive)
          - "proximity" → fastest (spatial awareness)

        The base range is determined by boldness, then the interaction
        type shifts within it.
        """
        bold = self._personality.get("boldness", normalized=True)  # 0.0-1.0

        # Base delay range from boldness
        if bold >= 0.5:
            low, high = DELAY_BOLD
        else:
            low, high = DELAY_SHY

        # Interaction type modifier (shift within range)
        type_offset = self._type_offset(interaction_type)

        delay = low + (high - low) * type_offset
        return round(random.uniform(0.0, delay) if delay > 0 else delay, 3)

    def get_pre_reaction(self) -> tuple:
        """Return a pre-reaction cue before the main reaction.

        Returns:
            (cue_name: str | None, duration: float)
            cue_name is None when there's no pre-reaction.
            duration is in seconds (0.15-0.4s typically).
        """
        # 25% chance of no pre-reaction (sometimes cats just react)
        cue = random.choice(PRE_REACTIONS)
        if cue is None:
            return (None, 0.0)

        duration = random.uniform(0.15, 0.4)
        return (cue, duration)

    # ── Internal ────────────────────────────────────────────────────

    def _type_offset(self, interaction_type: str) -> float:
        """Return a 0.0-1.0 offset for the interaction type.

        Lower offset → faster reaction (within the base range).
        """
        mapping = {
            "proximity": 0.0,
            "click": 0.3,
            "drag": 0.5,
            "hover": 0.7,
            "keypress": 0.4,
            "speech": 0.5,
            "pet": 0.1,  # petting is fast to acknowledge
        }
        return mapping.get(interaction_type, 0.5)

    def __repr__(self) -> str:
        bold = self._personality.get("boldness")
        return f"<ReactionSystem boldness={bold:.1f}/10>"
