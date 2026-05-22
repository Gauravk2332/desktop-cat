"""
animation/breathe.py — Subtle breathing oscillation.

Makes the cat look alive with a gentle body expansion/contraction.
+ Sleep breathing was already handled in the sleep draw function (coexists).
"""

import math

import config


def _get(state, key, default=None):
    """Get from dict (preferred) or attribute fallback."""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def update(dt: float, state) -> None:
    """Advance breath phase at state-dependent speed.

    Accepts both CatState (attribute access) and cat dict (key access).
    """
    s = _get(state, "state", "SIT")
    if s == config.STATE_SLEEP:
        speed = 0.8 if not _get(state, "deep_sleep", False) else 0.3
    elif s == config.STATE_WALK:
        speed = 2.5
    else:
        speed = 1.5  # SIT

    if isinstance(state, dict):
        state["breath_phase"] = state.get("breath_phase", 0.0) + dt * speed
    else:
        state.breath_phase += dt * speed


def breath_value(state) -> tuple[float, float]:
    """Returns (scale, bob_px) for the current breath phase.

    Accepts both CatState and cat dict.
    """
    bp = state.get("breath_phase", 0.0) if isinstance(state, dict) else getattr(state, "breath_phase", 0.0)
    s = math.sin(bp)
    scale = s * 0.006 + 1.0      # ±0.6% size oscillation
    bob = s * 0.8                  # ±0.8px vertical bob
    return scale, bob
