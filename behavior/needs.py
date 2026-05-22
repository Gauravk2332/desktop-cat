"""
behavior/needs.py — Energy, hunger, and boredom decay/recharge.

Integrates weather modifiers + time-of-day multipliers + AFK detection.
Runs every tick. Mutates state. Stateless module.

Dual-signature:
  update(dt, state)         — legacy: cats[0]
  update(dt, cat, state)    — per-cat
"""

import random
import time
from datetime import datetime

import config


def _resolve(state_or_cat, state=None):
    """Return (cat_dict, state) from either calling mode."""
    if state is None:
        return state_or_cat.cats[0], state_or_cat
    return state_or_cat, state


def _get_tod_multipliers() -> dict:
    """Return combined time-of-day multipliers for current hour."""
    hour = datetime.now().hour
    result = {"energy": 1.0, "hunger": 1.0, "boredom": 1.0}
    for need, ranges in config.NEED_TIME_MULTIPLIERS.items():
        if need not in result:
            continue
        for start, end, mult in ranges:
            if start <= end:
                if start <= hour < end:
                    result[need] *= mult
            else:
                if hour >= start or hour < end:
                    result[need] *= mult
    return result


def _get_weather_multipliers(state) -> dict:
    try:
        from core.weather import get_weather_modifier
        return get_weather_modifier(state)
    except (ImportError, AttributeError, Exception):
        return {"energy": 1.0, "hunger": 1.0, "boredom": 1.0,
                "wander": 1.0, "sleep": 1.0, "chase": 1.0}


def _is_owner_afk(state) -> bool:
    return (time.monotonic() - state.last_interaction) > config.AFK_THRESHOLD


def update(dt: float, state_or_cat, state=None) -> None:
    """Decay or recharge needs for a specific cat.

    Two calling modes:
      update(dt, state)           — legacy: cats[0]
      update(dt, cat_dict, state) — per-cat
    """
    cat, s = _resolve(state_or_cat, state)

    tod = _get_tod_multipliers()
    wea = _get_weather_multipliers(s)

    energy_mul = tod.get("energy", 1.0) * wea.get("energy", 1.0)
    hunger_mul = tod.get("hunger", 1.0) * wea.get("hunger", 1.0)
    boredom_mul = tod.get("boredom", 1.0) * wea.get("boredom", 1.0)

    # ── Energy ─────────────────────────────────────────────────────
    cur_state = cat["state"]
    if cur_state == config.STATE_SLEEP:
        cat["energy"] = min(100.0, cat.get("energy", 80.0) + config.ENERGY_RECHARGE_SLEEP * dt)
    elif cur_state in (config.STATE_WALK, config.STATE_WANDER,
                       config.STATE_CHASE, config.STATE_PLAY):
        cat["energy"] = max(0.0, cat.get("energy", 80.0) - config.ENERGY_DRAIN_ACTIVE * dt * energy_mul)
    else:
        cat["energy"] = max(0.0, cat.get("energy", 80.0) - config.ENERGY_DRAIN_SIT * dt * energy_mul)

    # ── Hunger ─────────────────────────────────────────────────────
    cat["hunger"] = min(100.0, cat.get("hunger", 20.0) + config.HUNGER_DRAIN * dt * hunger_mul)

    # ── Boredom ────────────────────────────────────────────────────
    if cur_state == config.STATE_SLEEP:
        cat["boredom"] = max(0.0, cat.get("boredom", 0.0) - 0.02 * dt)
    elif cur_state in (config.STATE_WALK, config.STATE_WANDER,
                       config.STATE_CHASE, config.STATE_PLAY):
        cat["boredom"] = max(0.0, cat.get("boredom", 0.0) - 0.005 * dt)
    else:
        boredom_increase = config.BOREDOM_INCREASE_SIT * dt * boredom_mul
        if _is_owner_afk(s):
            boredom_increase *= config.AFK_BOREDOM_MULTIPLIER
        cat["boredom"] = min(100.0, cat.get("boredom", 0.0) + boredom_increase)

    # ── Critical threshold triggers ────────────────────────────────
    _check_critical_triggers(cat, s)


def _check_critical_triggers(cat, s) -> None:
    """Check and respond to critical need thresholds for a single cat."""
    if cat["energy"] < config.ENERGY_CRITICAL_THRESHOLD and cat["state"] != config.STATE_SLEEP:
        cat["state"] = config.STATE_SLEEP
        cat["sleep_breath"] = 0.0
        cat["zzz_particles"] = []
        cat["at_home"] = False

    if cat["boredom"] > config.BOREDOM_ERRATIC_THRESHOLD and cat["state"] == config.STATE_SIT:
        if random.random() < 0.1:
            _trigger_erratic(cat, s)


def _trigger_erratic(cat, s) -> None:
    """Trigger erratic walking pattern when extremely bored."""
    cat["state"] = config.STATE_WALK
    cat["walk_duration"] = random.uniform(0.3, 1.0)
    cat["walk_elapsed"] = 0.0
    cat["walk_accel"] = 2.0
    cat["facing"] = random.choice([True, False])

    if cat.get("speech_cooldown", 0) <= 0:
        texts = ["!!", "argh", "bored!", "ughh"]
        # Speech bubble is stored per-cat in the dict now
        cat["speech"] = {
            "text": random.choice(texts),
            "emoji": "😵",
            "timer": config.SPEECH_DISPLAY,
            "fading": False,
            "opacity": 0.0,
            "queue": [],
        }
        cat["speech_cooldown"] = 15.0
