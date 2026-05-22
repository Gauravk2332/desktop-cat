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
"""

import random
from datetime import datetime

import config


def update(dt: float, state) -> None:
    """Check transition conditions and change state when met."""
    # Timer housekeeping
    state.home_cooldown = max(0.0, state.home_cooldown - dt)
    state.home_linger = max(0.0, state.home_linger - dt)
    state.wander_cooldown = max(0.0, state.wander_cooldown - dt)

    if state.state == config.STATE_SLEEP:
        _update_sleep(dt, state)
    elif state.state == config.STATE_SIT:
        _update_sit(dt, state)
    elif state.state == config.STATE_WALK:
        _update_walk(dt, state)
    elif state.state == config.STATE_GO_HOME:
        _update_go_home(dt, state)
    elif state.state == config.STATE_WANDER:
        _update_wander(dt, state)


def _update_sleep(dt: float, state) -> None:
    """Wake up when recharged. Home sleep wakes earlier than field sleep."""
    threshold = config.HOME_NAP_MIN_ENERGY if state.at_home else 85.0
    if state.energy > threshold:
        state.state = config.STATE_SIT
        state.deep_sleep = False
        state.zzz_particles = []
        state.sleep_breath = 0.0

        # After home sleep: linger + prevent immediate GO_HOME
        if state.at_home:
            state.home_linger = config.HOME_LINGER_DURATION
            state.home_cooldown = config.HOME_VISIT_COOLDOWN


def _update_sit(dt: float, state) -> None:
    """Check triggers in priority order."""

    # Redraw support: if linger expired, leave home zone
    if state.at_home and state.home_linger <= 0:
        state.at_home = False
        state.home_cooldown = config.HOME_VISIT_COOLDOWN

    # 1. Energy low → GO_HOME (but not if already at home)
    if state.energy < config.HOME_ENERGY_THRESHOLD and not state.at_home:
        _enter_go_home(state)
        return

    # 2. Boredom high + cooldown expired → GO_HOME
    if state.boredom > config.HOME_BOREDOM_THRESHOLD and state.home_cooldown <= 0:
        _enter_go_home(state)
        return

    # 3. Random circadian home visit (only when not on linger)
    if not state.at_home and state.home_cooldown <= 0 and random.random() < _home_chance_per_tick(state):
        _enter_go_home(state)
        return

    # 4. Wander — cat explores away from home (only when not at home, cooldown expired)
    if not state.at_home and state.wander_cooldown <= 0 and random.random() < _wander_chance_per_tick(state):
        _enter_wander(state)
        return

    # 5. Sleep due to low energy (field sleep — fallback)
    if state.energy < 40.0:
        _enter_sleep(state)
        return

    # 6. Sleep due to boredom (field sleep)
    if state.boredom > 90.0:
        _enter_sleep(state)
        return

    # 7. Regular random walk
    _maybe_walk(dt, state)


def _update_walk(dt: float, state) -> None:
    """Sit down when walk decelerates to a stop."""
    if state.walk_elapsed > state.walk_duration + 0.5:
        state.state = config.STATE_SIT
        state.walk_elapsed = 0.0


def _update_wander(dt: float, state) -> None:
    """Wander state — engine handles movement. We just check exit."""
    # Wander -> GO_HOME: if energy is getting low while wandering
    if state.energy < config.HOME_ENERGY_THRESHOLD:
        _enter_go_home(state)
        return


def _update_go_home(dt: float, state) -> None:
    """Wait during go-home. Engine handles navigation."""
    pass  # navigation is managed by engine._update_go_home


def _enter_go_home(state) -> None:
    """Start walking toward the home hut (bottom-right of screen)."""
    from cat.home import _hut_door_center
    hx, hy = _hut_door_center(state)
    state.state = config.STATE_GO_HOME
    state.walk_elapsed = 0.0
    state.walk_frame = 0
    state.walk_accel = 1.0


def _enter_sleep(state) -> None:
    """Transition to sleep (field sleep)."""
    state.state = config.STATE_SLEEP
    state.sleep_breath = 0.0
    state.zzz_particles = []
    state.at_home = False


def _enter_wander(state) -> None:
    """Start wandering — walk in a random 2D direction."""
    import math as _math
    angle = _math.radians(random.randint(0, 360))
    state.wander_vx = _math.cos(angle)
    state.wander_vy = _math.sin(angle)
    state.facing = state.wander_vx > 0
    state.state = config.STATE_WANDER
    state.wander_duration = random.uniform(config.WANDER_DURATION_MIN, config.WANDER_DURATION_MAX)
    state.wander_elapsed = 0.0
    state.walk_frame = 0


def _maybe_walk(dt: float, state) -> None:
    """Roll for a regular random walk (short, mouse-interactive)."""
    if random.random() < _walk_chance_per_tick(state):
        geo_w = state.screen_width
        center = geo_w / 2.0
        if state.cat_x < center - 40:
            state.facing = True
        elif state.cat_x > center + 40:
            state.facing = False
        else:
            state.facing = random.choice([True, False])

        state.state = config.STATE_WALK
        state.walk_duration = max(0.8, random.uniform(1.5, 3.0))
        state.walk_elapsed = 0.0
        state.walk_accel = 0.0
        state.walk_pause = False
        state.walk_frame = 0
        state.walk_accum = 0.0


def _walk_chance_per_tick(state) -> float:
    """Chance of starting a random walk per tick."""
    hour = datetime.now().hour
    boredom_mod = state.boredom / 200.0
    if 5 <= hour < 7 or 17 <= hour < 19:
        base = 0.003
    elif hour >= 22 or hour < 6:
        base = 0.0005
    else:
        base = 0.0015
    return base * (1.0 + boredom_mod)


def _home_chance_per_tick(state) -> float:
    """Chance of deciding to go home per tick."""
    hour = datetime.now().hour
    if 5 <= hour < 7 or 17 <= hour < 19:
        base = 0.002   # dawn/dusk
    elif hour >= 22 or hour < 6:
        base = 0.0002  # night
    else:
        base = 0.0008  # day
    boredom_mod = state.boredom / 200.0
    return base * (1.0 + boredom_mod)


def _wander_chance_per_tick(state) -> float:
    """Chance of deciding to wander off from home per tick."""
    hour = datetime.now().hour
    # More active during day, less at night
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
    boredom_mod = state.boredom / 200.0
    return base * (1.0 + boredom_mod)
