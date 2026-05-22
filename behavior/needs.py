"""
behavior/needs.py — Energy, hunger, and boredom decay/recharge.

Runs every tick. Mutates state. Stateless module.
"""

import config


def update(dt: float, state) -> None:
    """Decay or recharge needs based on current state."""
    if state.state == config.STATE_SLEEP:
        # Recharging
        state.energy = min(100.0, state.energy + config.ENERGY_RECHARGE_SLEEP * dt)
        state.hunger = min(100.0, state.hunger + config.HUNGER_DRAIN * dt)
        # Boredom resets while sleeping
        state.boredom = max(0.0, state.boredom - 0.02 * dt)

    elif state.state == config.STATE_WALK:
        # Active drain
        state.energy = max(0.0, state.energy - config.ENERGY_DRAIN_ACTIVE * dt)
        state.hunger = min(100.0, state.hunger + config.HUNGER_DRAIN * dt)

    else:  # STATE_SIT
        state.energy = max(0.0, state.energy - config.ENERGY_DRAIN_SIT * dt)
        state.hunger = min(100.0, state.hunger + config.HUNGER_DRAIN * dt)
        state.boredom = min(100.0, state.boredom + config.BOREDOM_INCREASE_SIT * dt)
