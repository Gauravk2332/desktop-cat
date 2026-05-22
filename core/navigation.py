"""
core/navigation.py — Pure movement/navigation functions.

Standalone logic extracted from Engine._update_walk/_update_wander/_update_go_home
and Engine._process_actions/_trigger_purr.
No Qt imports. Operates on CatState and per-cat dicts.

All functions accept (dt, cat_dict, state) for per-cat mode.
Legacy mode: pass (dt, state) — they self-dispatch to cats[0].
"""

import math
import random
import time

import config


# ── Dispatch helpers ─────────────────────────────────────────

def _resolve(state_or_cat, state=None):
    """Return (cat_dict, state) from either calling mode."""
    if state is None:
        return state_or_cat.cats[0], state_or_cat
    return state_or_cat, state


# ── Walk ───────────────────────────────────────────────────────────

def update_walk(dt: float, state_or_cat, state=None) -> None:
    """Update walk navigation in 2D — horizontal + slight vertical drift.

    Two calling modes:
      update_walk(dt, state)           — legacy: cats[0]
      update_walk(dt, cat_dict, state) — per-cat
    """
    cat, _ = _resolve(state_or_cat, state)

    # Walk pause check
    if cat.get("walk_pause"):
        elapsed = time.monotonic() - cat.get("walk_pause_start", 0.0)
        if elapsed > random.uniform(1.0, 2.0):
            cat["walk_pause"] = False
        return

    cat["walk_elapsed"] = cat.get("walk_elapsed", 0.0) + dt
    total = cat.get("walk_duration", 1.0)
    elapsed = cat["walk_elapsed"]

    if elapsed < config.WALK_ACCEL_TIME:
        cat["walk_accel"] = elapsed / config.WALK_ACCEL_TIME
    elif elapsed > total - config.WALK_ACCEL_TIME:
        rem = total - elapsed
        cat["walk_accel"] = max(0.0, rem / config.WALK_ACCEL_TIME)
    else:
        cat["walk_accel"] = 1.0

    speed = config.WALK_SPEED * cat["walk_accel"] * dt
    screen_w = _screen_w(state_or_cat, state)
    screen_h = _screen_h(state_or_cat, state)

    # ── Horizontal movement (existing) ──
    facing = cat.get("facing", True)
    if facing:
        cat["walk_accum"] = cat.get("walk_accum", 0.0) + speed
        whole = math.floor(cat["walk_accum"])
        cat["x"] = cat.get("x", 500.0) + whole
        cat["walk_accum"] -= whole
        if cat["x"] + 80 >= screen_w:
            cat["x"] = float(screen_w - 80)
            cat["state"] = config.STATE_SIT
            cat["facing"] = False
            return
    else:
        cat["walk_accum"] = cat.get("walk_accum", 0.0) + speed
        whole = math.floor(cat["walk_accum"])
        cat["x"] = cat.get("x", 500.0) - whole
        cat["walk_accum"] -= whole
        if cat["x"] - 80 <= 0:
            cat["x"] = 80.0
            cat["state"] = config.STATE_SIT
            cat["facing"] = True
            return

    # ── Vertical drift (new) — slight y-movement so cat isn't confined to a line ──
    walk_vy = cat.get("walk_vy", 0.0)
    if walk_vy == 0.0:
        # Smoothly fade in y-drift over 10 ticks to avoid teleport
        walk_vy = random.uniform(-0.25, 0.25)
        cat["walk_vy"] = walk_vy

    new_y = cat.get("y", 700.0) + walk_vy * speed * 1.5
    y_min = screen_h * config.CAT_MIN_Y_FRACTION
    y_max = screen_h - config.CAT_BASELINE

    # Clamp and bounce
    if new_y >= y_max:
        new_y = float(y_max)
        cat["walk_vy"] = -abs(walk_vy) if walk_vy > 0 else walk_vy  # bounce down→up
    elif new_y <= y_min:
        new_y = float(y_min)
        cat["walk_vy"] = abs(walk_vy) if walk_vy < 0 else walk_vy  # bounce up→down

    cat["y"] = new_y
    cat["walk_frame"] = int((cat["walk_elapsed"] * 8.0) % 8)


def update_wander(dt: float, state_or_cat, state=None) -> None:
    """Wander in 2D — random direction, bounces off all edges."""
    cat, st = _resolve(state_or_cat, state)

    cat["wander_elapsed"] = cat.get("wander_elapsed", 0.0) + dt

    # Random direction change
    if random.random() < config.WANDER_TURN_CHANCE:
        angle = random.uniform(0, math.pi * 2)
        cat["wander_vx"] = math.cos(angle)
        cat["wander_vy"] = math.sin(angle)
        if abs(cat["wander_vx"]) < 0.3:
            cat["wander_vx"] = 0.3 if cat.get("facing", True) else -0.3

    # Check if wander timer expired
    if cat["wander_elapsed"] >= cat.get("wander_duration", 2.0):
        cat["state"] = config.STATE_SIT
        cat["wander_session_count"] = cat.get("wander_session_count", 0) + 1
        cat["wander_cooldown"] = config.WANDER_COOLDOWN
        return

    speed = config.WALK_SPEED * dt * 1.0
    margin = config.WANDER_OFFSET
    screen_w = cat.get("x", 500.0)
    screen_h = cat.get("y", 700.0)

    vx = cat.get("wander_vx", 1.0)
    vy = cat.get("wander_vy", 0.0)
    mag = math.hypot(vx, vy)
    if mag > 0:
        vx /= mag
        vy /= mag
    else:
        vx, vy = 1.0, 0.0

    new_x = cat.get("x", 500.0) + vx * speed
    new_y = cat.get("y", 700.0) + vy * speed

    scr_w = _screen_w(state_or_cat, state)
    scr_h = _screen_h(state_or_cat, state)
    y_min = scr_h * config.CAT_MIN_Y_FRACTION
    y_max = scr_h - config.CAT_BASELINE

    if new_x + margin >= scr_w:
        new_x = float(scr_w - margin)
        cat["wander_vx"] = -cat.get("wander_vx", 1.0)
    elif new_x - margin <= 0:
        new_x = float(margin)
        cat["wander_vx"] = -cat.get("wander_vx", 1.0)

    if new_y + margin >= y_max:
        new_y = float(y_max)
        cat["wander_vy"] = -cat.get("wander_vy", 0.0)
    elif new_y - margin <= y_min:
        new_y = float(y_min)
        cat["wander_vy"] = -cat.get("wander_vy", 0.0)

    cat["x"] = new_x
    cat["y"] = new_y
    cat["facing"] = vx > 0

    walk_accum = cat.get("walk_accum", 0.0)
    walk_accum = (walk_accum + speed) % 1.0
    cat["walk_accum"] = walk_accum
    cat["walk_frame"] = int((cat.get("wander_elapsed", 0.0) * 8.0) % 8)


# ── Go Home ─────────────────────────────────────────────────────

def update_go_home(dt: float, state_or_cat, state=None) -> None:
    """Navigate toward hut door in 2D."""
    cat, _ = _resolve(state_or_cat, state)
    hut_idx = cat.get("hut_index", 0)

    from cat.home import _hut_door_center
    hx, hy = _hut_door_center(state_or_cat if state is None else state, hut_idx)

    dx = hx - cat.get("x", 500.0)
    dy = hy - cat.get("y", 700.0)
    dist = math.hypot(dx, dy)

    if dist <= config.HOME_TOLERANCE:
        cat["x"] = float(hx)
        cat["y"] = float(hy - 2)
        cat["at_home"] = True
        cat["state"] = config.STATE_SLEEP
        cat["sleep_breath"] = 0.0
        cat["zzz_particles"] = []
        cat["walk_elapsed"] = 0.0
        return

    speed = config.WALK_SPEED * dt * 1.2
    if dist < speed * 5:
        speed = dist / 5.0

    if dist > 0:
        cat["x"] = cat.get("x", 500.0) + (dx / dist) * speed
        cat["y"] = cat.get("y", 700.0) + (dy / dist) * speed

    cat["facing"] = dx > 0
    cat["walk_elapsed"] = cat.get("walk_elapsed", 0.0) + dt
    cat["walk_frame"] = int((cat.get("walk_elapsed", 0.0) * 8.0) % 8)


# ── Chase ────────────────────────────────────────────────────────

def update_chase(dt: float, state_or_cat, state=None) -> None:
    """Chase toward laser pointer / cursor position."""
    cat, _ = _resolve(state_or_cat, state)

    toy_target = cat.get("toy_target")
    if toy_target is None:
        cat["state"] = config.STATE_SIT
        cat["toy_active"] = False
        cat["toy_type"] = None
        return

    tx, ty = toy_target
    dx = tx - cat.get("x", 500.0)
    dy = ty - cat.get("y", 700.0)
    dist = math.hypot(dx, dy)

    cat["facing"] = dx > 0

    if dist <= config.CHASE_REACH_DISTANCE:
        cat["state"] = config.STATE_SIT
        cat["toy_active"] = False
        cat["toy_type"] = None
        return

    speed = config.WALK_SPEED * config.CHASE_SPEED_MULTIPLIER * dt
    if dist > 0:
        cat["x"] = cat.get("x", 500.0) + (dx / dist) * speed
        cat["y"] = cat.get("y", 700.0) + (dy / dist) * speed

    scr_w = _screen_w(state_or_cat, state)
    scr_h = _screen_h(state_or_cat, state)
    margin = config.WANDER_OFFSET
    y_min = scr_h * config.CAT_MIN_Y_FRACTION
    y_max = scr_h - config.CAT_BASELINE
    cat["x"] = max(float(margin), min(cat["x"], float(scr_w - margin)))
    cat["y"] = max(float(y_min), min(cat["y"], float(y_max)))

    cat["walk_elapsed"] = cat.get("walk_elapsed", 0.0) + dt
    cat["walk_frame"] = int((cat.get("walk_elapsed", 0.0) * 10.0) % 8)


# ── Play ──────────────────────────────────────────────────────────

def update_play(dt: float, state_or_cat, state=None) -> None:
    """Play with yarn ball / butterfly toy."""
    cat, _ = _resolve(state_or_cat, state)

    if not cat.get("toy_active") or cat.get("toy_target") is None:
        cat["state"] = config.STATE_SIT
        cat["toy_active"] = False
        cat["toy_type"] = None
        return

    cat["toy_timer"] = cat.get("toy_timer", 0.0) - dt
    if cat["toy_timer"] <= 0:
        cat["state"] = config.STATE_SIT
        cat["toy_active"] = False
        cat["toy_type"] = None
        return

    tx, ty = cat["toy_target"]
    dx = tx - cat.get("x", 500.0)
    dy = ty - cat.get("y", 700.0)
    dist = math.hypot(dx, dy)

    cat["facing"] = dx > 0

    if dist <= config.PLAY_TOY_REACH_DISTANCE:
        _spawn_hearts_for_cat(cat, count=5)
        cat["state"] = config.STATE_SIT
        cat["toy_active"] = False
        cat["toy_type"] = None
        return

    speed = config.WALK_SPEED * dt
    if dist > 0:
        cat["x"] = cat.get("x", 500.0) + (dx / dist) * speed
        cat["y"] = cat.get("y", 700.0) + (dy / dist) * speed

    scr_w = _screen_w(state_or_cat, state)
    scr_h = _screen_h(state_or_cat, state)
    margin = config.WANDER_OFFSET
    y_min = scr_h * config.CAT_MIN_Y_FRACTION
    y_max = scr_h - config.CAT_BASELINE
    cat["x"] = max(float(margin), min(cat["x"], float(scr_w - margin)))
    cat["y"] = max(float(y_min), min(cat["y"], float(y_max)))

    cat["walk_elapsed"] = cat.get("walk_elapsed", 0.0) + dt
    cat["walk_frame"] = int((cat.get("walk_elapsed", 0.0) * 8.0) % 8)


# ── Purr / Reactions ────────────────────────────────────────────

def trigger_purr(state_or_cat, state=None) -> None:
    """Trigger purr reaction."""
    cat, _ = _resolve(state_or_cat, state)
    cat["reaction_type"] = "purr"
    cat["reaction_timer"] = 1.5
    cat["purr_vibrate"] = 1.0


def process_actions(state) -> None:
    """Process external action queue from API.
    Operates on all cats (pet/feed/wake affects cats[0] for backward compat).
    """
    from core.api import action_queue
    while not action_queue.empty():
        try:
            action = action_queue.get_nowait()
        except Exception:
            break

        # Operate on cats[0] for backward compat
        if not state.cats:
            continue
        cat = state.cats[0]
        cat["last_interaction"] = time.monotonic()
        cat["boredom"] = 0.0
        if action == "pet":
            cat["consecutive_pets"] = cat.get("consecutive_pets", 0) + 1
            _spawn_hearts_for_cat(cat)
            if cat["consecutive_pets"] >= 5:
                trigger_purr(state)
                cat["consecutive_pets"] = 0
            elif cat["state"] == config.STATE_SLEEP:
                cat["reaction_type"] = "meow"
                cat["reaction_timer"] = 0.8
            else:
                cat["reaction_type"] = random.choice(["purr", "meow"])
                cat["reaction_timer"] = 2.0 if cat["reaction_type"] == "purr" else 0.8
        elif action == "feed":
            cat["hunger"] = max(0.0, cat["hunger"] - 15.0)
        elif action == "wake":
            if cat["state"] == config.STATE_SLEEP:
                cat["state"] = config.STATE_SIT
                cat["energy"] = min(100.0, cat["energy"] + 10.0)
                cat["deep_sleep"] = False


def _spawn_hearts(state, count: int = 3) -> None:
    """Spawn floating hearts above the cat (legacy: uses cats[0])."""
    if state.cats:
        _spawn_hearts_for_cat(state.cats[0], count)


def _spawn_hearts_for_cat(cat: dict, count: int = 3) -> None:
    """Spawn floating hearts above a single cat dict."""
    hearts = cat.get("hearts", [])
    for _ in range(count):
        hearts.append([
            random.uniform(-12, 12),
            random.uniform(-30, -20),
            1.5,
            random.uniform(6, 10),
        ])
    cat["hearts"] = hearts


def _screen_w(state_or_cat, state=None):
    """Get screen width from whichever arg has it."""
    if state is not None:
        return state.screen_width
    return getattr(state_or_cat, 'screen_width', 1920)


def _screen_h(state_or_cat, state=None):
    """Get screen height from whichever arg has it."""
    if state is not None:
        return state.screen_height
    return getattr(state_or_cat, 'screen_height', 1080)
