"""
core/navigation.py — Pure movement/navigation functions.

Standalone logic extracted from Engine._update_walk/_update_wander/_update_go_home
and Engine._process_actions/_trigger_purr.
No Qt imports. Operates on CatState only.
"""

import math
import random
import time

import config


def update_walk(dt: float, state) -> None:
    """Update walk navigation. Extracted from Engine._update_walk."""
    # Walk pause check — walk_pause is set to True by mouse tracking
    if state.walk_pause:
        elapsed = time.monotonic() - state.walk_pause_start
        if elapsed > random.uniform(1.0, 2.0):
            state.walk_pause = False
        return

    state.walk_elapsed += dt
    total = state.walk_duration
    elapsed = state.walk_elapsed

    if elapsed < config.WALK_ACCEL_TIME:
        state.walk_accel = elapsed / config.WALK_ACCEL_TIME
    elif elapsed > total - config.WALK_ACCEL_TIME:
        rem = total - elapsed
        state.walk_accel = max(0.0, rem / config.WALK_ACCEL_TIME)
    else:
        state.walk_accel = 1.0

    speed = config.WALK_SPEED * state.walk_accel * dt
    screen_w = state.screen_width

    if state.facing:
        state.walk_accum += speed
        whole = math.floor(state.walk_accum)
        state.cat_x += whole
        state.walk_accum -= whole
        if state.cat_x + 80 >= screen_w:
            state.cat_x = float(screen_w - 80)
            state.state = config.STATE_SIT
            state.facing = False
            return
    else:
        state.walk_accum += speed
        whole = math.floor(state.walk_accum)
        state.cat_x -= whole
        state.walk_accum -= whole
        if state.cat_x - 80 <= 0:
            state.cat_x = 80.0
            state.state = config.STATE_SIT
            state.facing = True
            return

    state.walk_frame = int((state.walk_elapsed * 6.5) % 4)


def update_wander(dt: float, state) -> None:
    """Update wander navigation. Extracted from Engine._update_wander."""
    state.wander_elapsed += dt

    # Random direction reversal
    if random.random() < config.WANDER_TURN_CHANCE:
        state.facing = not state.facing

    # Check if wander timer expired
    if state.wander_elapsed >= state.wander_duration:
        state.state = config.STATE_SIT
        state.wander_session_count += 1
        state.wander_cooldown = config.WANDER_COOLDOWN
        return

    # Walk movement in facing direction
    speed = config.WALK_SPEED * dt * 1.0
    margin = config.WANDER_OFFSET

    if state.facing:
        state.cat_x += speed
        if state.cat_x + margin >= state.screen_width:
            state.cat_x = float(state.screen_width - margin)
            state.facing = False
    else:
        state.cat_x -= speed
        if state.cat_x - margin <= 0:
            state.cat_x = float(margin)
            state.facing = True

    state.walk_accum = (state.walk_accum + speed) % 1.0
    state.walk_frame = int((state.wander_elapsed * 6.5) % 4)


def update_go_home(dt: float, state) -> None:
    """Update go-home navigation. Extracted from Engine._update_go_home."""
    from cat.home import _hut_door_center
    hx, hy = _hut_door_center(state)
    remaining = hx - state.cat_x

    if remaining <= config.HOME_TOLERANCE:
        # Arrived at home
        state.cat_x = hx
        state.at_home = True
        state.state = config.STATE_SLEEP
        state.sleep_breath = 0.0
        state.zzz_particles = []
        state.walk_elapsed = 0.0
        return

    # Accelerate toward home, decelerate near arrival
    speed = config.WALK_SPEED * dt * 1.2
    if remaining < speed * 5:
        speed = remaining / 5.0  # ease in

    state.cat_x += speed
    state.walk_elapsed += dt
    state.walk_frame = int((state.walk_elapsed * 6.5) % 4)


def trigger_purr(state) -> None:
    """Trigger purr reaction on state."""
    state.reaction_type = "purr"
    state.reaction_timer = 1.5
    state.purr_vibrate = 1.0


def process_actions(state) -> None:
    """Process external action queue. Extracted from Engine._process_actions."""
    from core.api import action_queue
    s = state
    while not action_queue.empty():
        try:
            action = action_queue.get_nowait()
        except Exception:
            break
        s.last_interaction = time.monotonic()
        s.boredom = 0.0
        if action == "pet":
            s.consecutive_pets += 1
            if s.consecutive_pets >= 5:
                trigger_purr(s)
                s.consecutive_pets = 0
            elif s.state == config.STATE_SLEEP:
                s.reaction_type = "meow"
                s.reaction_timer = 0.8
            else:
                s.reaction_type = random.choice(["purr", "meow"])
                s.reaction_timer = 2.0 if s.reaction_type == "purr" else 0.8
        elif action == "feed":
            s.hunger = max(0.0, s.hunger - 15.0)
        elif action == "wake":
            if s.state == config.STATE_SLEEP:
                s.state = config.STATE_SIT
                s.energy = min(100.0, s.energy + 10.0)
                s.deep_sleep = False
