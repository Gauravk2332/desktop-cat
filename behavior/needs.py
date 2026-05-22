"""
behavior/needs.py — Energy, hunger, and boredom decay/recharge.

Integrates weather modifiers + time-of-day multipliers + AFK detection.
Runs every tick. Mutates state. Stateless module.
"""

import random
import time
from datetime import datetime

import config


def _get_tod_multipliers() -> dict:
    """Return combined time-of-day multipliers for current hour.

    Keys: energy, hunger, boredom. Default multiplier = 1.0.
    Overnight ranges (e.g. 22→6) wrap correctly.
    """
    hour = datetime.now().hour
    result = {"energy": 1.0, "hunger": 1.0, "boredom": 1.0}

    for need, ranges in config.NEED_TIME_MULTIPLIERS.items():
        if need not in result:
            continue
        for start, end, mult in ranges:
            if start <= end:
                if start <= hour < end:
                    result[need] *= mult
            else:  # overnight (e.g. 22→6)
                if hour >= start or hour < end:
                    result[need] *= mult

    return result


def _get_weather_multipliers(state) -> dict:
    """Delegate to weather module. Returns safe defaults on failure."""
    try:
        from core.weather import get_weather_modifier
        return get_weather_modifier(state)
    except (ImportError, AttributeError, Exception):
        return {"energy": 1.0, "hunger": 1.0, "boredom": 1.0,
                "wander": 1.0, "sleep": 1.0, "chase": 1.0}


def _is_owner_afk(state) -> bool:
    """Check if owner hasn't interacted in AFK_THRESHOLD seconds."""
    return (time.monotonic() - state.last_interaction) > config.AFK_THRESHOLD


def update(dt: float, state) -> None:
    """Decay or recharge needs based on current state, weather, and time-of-day."""
    tod = _get_tod_multipliers()
    wea = _get_weather_multipliers(state)

    energy_mul = tod.get("energy", 1.0) * wea.get("energy", 1.0)
    hunger_mul = tod.get("hunger", 1.0) * wea.get("hunger", 1.0)
    boredom_mul = tod.get("boredom", 1.0) * wea.get("boredom", 1.0)

    # ── Energy ─────────────────────────────────────────────────────
    if state.state == config.STATE_SLEEP:
        state.energy = min(100.0, state.energy + config.ENERGY_RECHARGE_SLEEP * dt)
    elif state.state in (config.STATE_WALK, config.STATE_WANDER,
                         config.STATE_CHASE, config.STATE_PLAY):
        state.energy = max(0.0, state.energy - config.ENERGY_DRAIN_ACTIVE * dt * energy_mul)
    else:  # STATE_SIT or GO_HOME
        state.energy = max(0.0, state.energy - config.ENERGY_DRAIN_SIT * dt * energy_mul)

    # ── Hunger ─────────────────────────────────────────────────────
    state.hunger = min(100.0, state.hunger + config.HUNGER_DRAIN * dt * hunger_mul)

    # ── Boredom ────────────────────────────────────────────────────
    if state.state == config.STATE_SLEEP:
        state.boredom = max(0.0, state.boredom - 0.02 * dt)
    elif state.state in (config.STATE_WALK, config.STATE_WANDER,
                         config.STATE_CHASE, config.STATE_PLAY):
        # Active states reduce boredom slightly
        state.boredom = max(0.0, state.boredom - 0.005 * dt)
    else:  # STATE_SIT or GO_HOME
        boredom_increase = config.BOREDOM_INCREASE_SIT * dt * boredom_mul
        # AFK: boredom increases 2x when sitting and owner is away
        if _is_owner_afk(state):
            boredom_increase *= config.AFK_BOREDOM_MULTIPLIER
        state.boredom = min(100.0, state.boredom + boredom_increase)

    # ── Critical threshold triggers ────────────────────────────────
    _check_critical_triggers(state)


def _check_critical_triggers(state) -> None:
    """Check and respond to critical need thresholds.

    - hunger > 80: urgent meow (handled by engine speech)
    - energy < 20: auto-sleep regardless of position
    - boredom > 80: erratic walking pattern
    """
    # Energy critical → auto-sleep (anywhere)
    if state.energy < config.ENERGY_CRITICAL_THRESHOLD and state.state != config.STATE_SLEEP:
        state.state = config.STATE_SLEEP
        state.sleep_breath = 0.0
        state.zzz_particles = []
        state.at_home = False  # field sleep

    # Boredom erratic → short erratic walk burst
    if state.boredom > config.BOREDOM_ERRATIC_THRESHOLD and state.state == config.STATE_SIT:
        if random.random() < 0.1:  # 10% per tick
            _trigger_erratic(state)


def _trigger_erratic(state) -> None:
    """Trigger erratic walking pattern when extremely bored."""
    state.state = config.STATE_WALK
    state.walk_duration = random.uniform(0.3, 1.0)
    state.walk_elapsed = 0.0
    state.walk_accel = 2.0  # fast accel for jerky movement
    state.facing = random.choice([True, False])

    # Quick speech if cooldown allows
    if state.speech_cooldown <= 0:
        texts = ["!!", "argh", "bored!", "ughh"]
        state.speech["text"] = random.choice(texts)
        state.speech["emoji"] = "😵"
        state.speech["timer"] = config.SPEECH_DISPLAY
        state.speech["fading"] = False
        state.speech["opacity"] = 0.0
        state.speech_cooldown = 15.0
