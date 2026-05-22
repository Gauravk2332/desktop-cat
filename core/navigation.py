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
    """Wander in 2D — random direction, bounces off all edges."""
    state.wander_elapsed += dt

    # Random direction change
    if random.random() < config.WANDER_TURN_CHANCE:
        angle = random.uniform(0, math.pi * 2)
        state.wander_vx = math.cos(angle)
        state.wander_vy = math.sin(angle)
        # Ensure cat doesn't go straight up or down (unnatural)
        if abs(state.wander_vx) < 0.3:
            state.wander_vx = 0.3 if state.facing else -0.3

    # Check if wander timer expired
    if state.wander_elapsed >= state.wander_duration:
        state.state = config.STATE_SIT
        state.wander_session_count += 1
        state.wander_cooldown = config.WANDER_COOLDOWN
        return

    # Move
    speed = config.WALK_SPEED * dt * 1.0
    margin = config.WANDER_OFFSET

    # Normalize direction vector
    mag = math.hypot(state.wander_vx, state.wander_vy)
    if mag > 0:
        vx = state.wander_vx / mag
        vy = state.wander_vy / mag
    else:
        vx, vy = 1.0, 0.0

    new_x = state.cat_x + vx * speed
    new_y = state.cat_y + vy * speed

    # Y-range limits (don't go too high or off bottom)
    y_min = state.screen_height * config.CAT_MIN_Y_FRACTION
    y_max = state.screen_height - config.CAT_BASELINE

    # Bounce off ALL edges
    if new_x + margin >= state.screen_width:
        new_x = float(state.screen_width - margin)
        state.wander_vx = -state.wander_vx
    elif new_x - margin <= 0:
        new_x = float(margin)
        state.wander_vx = -state.wander_vx

    if new_y + margin >= y_max:
        new_y = float(y_max)
        state.wander_vy = -state.wander_vy
    elif new_y - margin <= y_min:
        new_y = float(y_min)
        state.wander_vy = -state.wander_vy

    state.cat_x = new_x
    state.cat_y = new_y

    # Facing direction mirrors horizontal velocity
    state.facing = vx > 0

    # Walk frame
    state.walk_accum = (state.walk_accum + speed) % 1.0
    state.walk_frame = int((state.wander_elapsed * 6.5) % 4)


def update_go_home(dt: float, state) -> None:
    """Navigate toward hut door in 2D."""
    from cat.home import _hut_door_center
    hx, hy = _hut_door_center(state)

    dx = hx - state.cat_x
    dy = hy - state.cat_y
    dist = math.hypot(dx, dy)

    if dist <= config.HOME_TOLERANCE:
        state.cat_x = float(hx)
        state.cat_y = float(hy - 2)  # slightly above door floor (cat sits on floor)
        state.at_home = True
        state.state = config.STATE_SLEEP
        state.sleep_breath = 0.0
        state.zzz_particles = []
        state.walk_elapsed = 0.0
        return

    speed = config.WALK_SPEED * dt * 1.2
    if dist < speed * 5:
        speed = dist / 5.0  # ease in

    # Move toward target
    if dist > 0:
        state.cat_x += (dx / dist) * speed
        state.cat_y += (dy / dist) * speed

    state.facing = dx > 0  # face toward home
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
            # Spawn floating hearts
            _spawn_hearts(s)
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


def _spawn_hearts(state, count: int = 3) -> None:
    """Spawn floating hearts above the cat."""
    for _ in range(count):
        state.hearts.append([
            random.uniform(-12, 12),  # x_offset from cat center
            random.uniform(-30, -20),  # y_offset (above cat)
            1.5,                       # lifetime (seconds)
            random.uniform(6, 10),     # size (radius)
        ])
