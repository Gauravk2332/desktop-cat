"""
behavior/transitions.py — State machine logic.

Triggers:
  SIT    → SLEEP      : energy < 40, or boredom > 90
  SIT    → GO_HOME    : low energy, high boredom (cooldown), circadian
  SIT    → WANDER     : cooldown expired + circadian chance
  WANDER → SIT        : wander timer expired (handled by engine)
  SLEEP  → SIT        : energy threshold (home=60, field=85)
  GO_HOME → SLEEP     : handled by engine._update_go_home on arrival
  WALK   → SIT        : walked decel to stop

Updated for multi-cat: accepts (dt, cat_or_state, state) signature.
When called with (dt, state) — legacy mode, uses state.cats[0].
When called with (dt, cat_dict, state) — per-cat mode.
"""

import math
import random
from datetime import datetime

import config


def update(dt: float, state_or_cat, state=None) -> None:
    """Check transition conditions and change state when met.

    Two calling modes:
      update(dt, state)           — legacy: operates on state.cats[0]
      update(dt, cat_dict, state) — per-cat: operates on cat_dict
    """
    if state is None:
        cat = state_or_cat.cats[0]
        st = state_or_cat
    else:
        cat = state_or_cat
        st = state

    # Timer housekeeping
    cat["home_cooldown"] = max(0.0, cat["home_cooldown"] - dt)
    cat["home_linger"] = max(0.0, cat["home_linger"] - dt)
    cat["wander_cooldown"] = max(0.0, cat["wander_cooldown"] - dt)

    s = cat["state"]
    if s == config.STATE_SLEEP:
        _update_sleep(dt, cat, st)
    elif s == config.STATE_SIT:
        _update_sit(dt, cat, st)
    elif s == config.STATE_WALK:
        _update_walk(dt, cat)
    elif s == config.STATE_GO_HOME:
        _update_go_home(dt, cat, st)
    elif s == config.STATE_WANDER:
        _update_wander(dt, cat, st)


def _update_sleep(dt: float, cat: dict, state) -> None:
    """Wake up when recharged. Home sleep wakes earlier than field sleep."""
    threshold = config.HOME_NAP_MIN_ENERGY if cat["at_home"] else 85.0
    if cat["energy"] > threshold:
        cat["state"] = config.STATE_SIT
        cat["deep_sleep"] = False
        cat["zzz_particles"] = []
        cat["sleep_breath"] = 0.0

        # After home sleep: linger + prevent immediate GO_HOME
        if cat["at_home"]:
            cat["home_linger"] = config.HOME_LINGER_DURATION
            cat["home_cooldown"] = config.HOME_VISIT_COOLDOWN


def _update_sit(dt: float, cat: dict, state) -> None:
    """Check triggers in priority order."""

    # Redraw support: if linger expired, leave home zone
    if cat["at_home"] and cat["home_linger"] <= 0:
        cat["at_home"] = False
        cat["home_cooldown"] = config.HOME_VISIT_COOLDOWN

    # 1. Energy low → GO_HOME (but not if already at home)
    if cat["energy"] < config.HOME_ENERGY_THRESHOLD and not cat["at_home"]:
        _enter_go_home(cat)
        return

    # 2. Boredom high + cooldown expired → GO_HOME
    if cat["boredom"] > config.HOME_BOREDOM_THRESHOLD and cat["home_cooldown"] <= 0:
        _enter_go_home(cat)
        return

    # 3. Random circadian home visit (only when not on linger)
    if not cat["at_home"] and cat["home_cooldown"] <= 0 and random.random() < _home_chance_per_tick(cat, state):
        _enter_go_home(cat)
        return

    # 4. Wander — cat explores away from home (only when not at home, cooldown expired)
    if not cat["at_home"] and cat["wander_cooldown"] <= 0 and random.random() < _wander_chance_per_tick(cat, state):
        _enter_wander(cat)
        return

    # 5. Sleep due to low energy (field sleep — fallback)
    if cat["energy"] < 40.0:
        _enter_sleep(cat)
        return

    # 6. Sleep due to boredom (field sleep)
    if cat["boredom"] > 90.0:
        _enter_sleep(cat)
        return

    # 7. Regular random walk
    _maybe_walk(dt, cat, state)


def _update_walk(dt: float, cat: dict) -> None:
    """Sit down when walk decelerates to a stop."""
    if cat["walk_elapsed"] > cat["walk_duration"] + 0.5:
        cat["state"] = config.STATE_SIT
        cat["walk_elapsed"] = 0.0


def _update_wander(dt: float, cat: dict, state) -> None:
    """Wander state — engine handles movement. We just check exit."""
    if cat["energy"] < config.HOME_ENERGY_THRESHOLD:
        _enter_go_home(cat)
        return


def _update_go_home(dt: float, cat: dict, state) -> None:
    """Wait during go-home. Engine handles navigation."""
    pass


def _enter_go_home(cat: dict) -> None:
    """Start walking toward the home hut."""
    cat["state"] = config.STATE_GO_HOME
    cat["walk_elapsed"] = 0.0
    cat["walk_frame"] = 0
    cat["walk_accel"] = 1.0


def _enter_sleep(cat: dict) -> None:
    """Transition to sleep (field sleep)."""
    cat["state"] = config.STATE_SLEEP
    cat["sleep_breath"] = 0.0
    cat["zzz_particles"] = []
    cat["at_home"] = False


def _enter_wander(cat: dict) -> None:
    """Start wandering — walk in a random 2D direction."""
    angle = math.radians(random.randint(0, 360))
    cat["wander_vx"] = math.cos(angle)
    cat["wander_vy"] = math.sin(angle)
    cat["facing"] = cat["wander_vx"] > 0
    cat["state"] = config.STATE_WANDER
    cat["wander_duration"] = random.uniform(config.WANDER_DURATION_MIN, config.WANDER_DURATION_MAX)
    cat["wander_elapsed"] = 0.0
    cat["walk_frame"] = 0


def _maybe_walk(dt: float, cat: dict, state) -> None:
    """Roll for a regular random walk (short, mouse-interactive)."""
    if random.random() < _walk_chance_per_tick(cat, state):
        geo_w = state.screen_width if hasattr(state, 'screen_width') else 1920
        center = geo_w / 2.0
        if cat["x"] < center - 40:
            cat["facing"] = True
        elif cat["x"] > center + 40:
            cat["facing"] = False
        else:
            cat["facing"] = random.choice([True, False])

        cat["state"] = config.STATE_WALK
        cat["walk_duration"] = max(0.8, random.uniform(1.5, 3.0))
        cat["walk_elapsed"] = 0.0
        cat["walk_accel"] = 0.0
        cat["walk_pause"] = False
        cat["walk_frame"] = 0
        cat["walk_accum"] = 0.0
        cat["walk_vy"] = random.uniform(-0.3, 0.3)


def _get_weather_behavior_mod(state) -> dict:
    """Get weather behavior multipliers (wander, sleep, chase)."""
    try:
        from core.weather import get_weather_modifier
        return get_weather_modifier(state)
    except (ImportError, AttributeError):
        return {"wander": 1.0, "sleep": 1.0, "chase": 1.0}


def _walk_chance_per_tick(cat: dict, state) -> float:
    """Chance of starting a random walk per tick."""
    hour = datetime.now().hour
    boredom_mod = cat["boredom"] / 200.0
    if 5 <= hour < 7 or 17 <= hour < 19:
        base = 0.003
    elif hour >= 22 or hour < 6:
        base = 0.0005
    else:
        base = 0.0015
    return base * (1.0 + boredom_mod)


def _home_chance_per_tick(cat: dict, state) -> float:
    """Chance of deciding to go home per tick."""
    hour = datetime.now().hour
    if 5 <= hour < 7 or 17 <= hour < 19:
        base = 0.002   # dawn/dusk
    elif hour >= 22 or hour < 6:
        base = 0.0002  # night
    else:
        base = 0.0008  # day
    boredom_mod = cat["boredom"] / 200.0
    return base * (1.0 + boredom_mod)


def _wander_chance_per_tick(cat: dict, state) -> float:
    """Chance of deciding to wander off from home per tick."""
    hour = datetime.now().hour
    if 7 <= hour < 10:
        base = 0.003   # morning zoomies
    elif 17 <= hour < 20:
        base = 0.0025  # evening activity
    elif 10 <= hour < 17:
        base = 0.0015  # daytime
    elif hour >= 22 or hour < 6:
        base = 0.0003  # night
    else:
        base = 0.001   # dawn/dusk
    boredom_mod = cat["boredom"] / 200.0
    wmod = _get_weather_behavior_mod(state).get("wander", 1.0)
    return base * (1.0 + boredom_mod) * wmod
