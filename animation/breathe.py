"""
animation/breathe.py — Subtle breathing oscillation.

Makes the cat look alive with a gentle body expansion/contraction.
+ Sleep breathing was already handled in the sleep draw function (coexists).
"""

import math

import config


def update(dt: float, state) -> None:
    """Advance breath phase at state-dependent speed."""
    if state.state == config.STATE_SLEEP:
        speed = 0.8 if not state.deep_sleep else 0.3
    elif state.state == config.STATE_WALK:
        speed = 2.5
    else:
        speed = 1.5  # SIT

    state.breath_phase += dt * speed


def breath_value(state) -> tuple[float, float]:
    """Returns (scale, bob_px) for the current breath phase."""
    s = math.sin(state.breath_phase)
    scale = s * 0.006 + 1.0      # ±0.6% size oscillation
    bob = s * 0.8                  # ±0.8px vertical bob
    return scale, bob
