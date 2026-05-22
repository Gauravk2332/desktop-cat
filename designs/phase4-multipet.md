# Phase 4: Multi-Pet Architecture

## Design Overview

This is the largest structural change to date. The core shift: **CatState goes from single-cat to multi-cat**, with a backward-compat migration layer so existing code paths don't break.

---

## 1. Data Model

### New: `state.cats` list

```python
# In CatState.__init__
self.cats: list[dict] = [
    {
        "id": 0,
        "x": 500.0, "y": 700.0,
        "state": "SIT",
        "facing": True,
        "energy": 80.0, "hunger": 20.0, "boredom": 0.0,
        "at_home": False,
        "home_cooldown": 0.0,
        "home_linger": 0.0,
        "walk_duration": 0.0,
        "walk_elapsed": 0.0,
        "walk_pause": False,
        "walk_pause_start": 0.0,
        "walk_accel": 1.0,
        "walk_frame": 0,
        "walk_accum": 0.0,
        "wander_duration": 0.0,
        "wander_elapsed": 0.0,
        "wander_cooldown": 0.0,
        "wander_session_count": 0,
        "wander_vx": 1.0,
        "wander_vy": 0.0,
        "tail_phase": 0.0,
        "blinking": False,
        "blink_timer": 0.0,
        "next_blink": 2.0,
        "sleep_breath": 0.0,
        "deep_sleep": False,
        "zzz_particles": [],
        "reaction_type": None,
        "reaction_timer": 0.0,
        "purr_vibrate": 0.0,
        "mouth_open": 0.0,
        "consecutive_pets": 0,
        "eye_target": (0.0, 0.0),
        "eye_current": (0.0, 0.0),
        "hearts": [],
        "last_interaction": 0.0,
        "speech": {"text": None, "emoji": None, "timer": 0.0, "fading": False, "opacity": 0.0, "queue": []},
        "speech_cooldown": 0.0,
        "speech_idle_timer": 0.0,
        "expression": {"ew": 4, "eh": 4, "pw": 2.5, "ph": 2.5, "px": 0, "py": 0},
        "expr_target": {"ew": 4, "eh": 4, "pw": 2.5, "ph": 2.5, "px": 0, "py": 0},
        "expr_timeout": 0.0,
        "blush_alpha": 0.0,
        "blush_target": 0.0,
        "pupil_dilation": 0.5,
        "toy_target": None,
        "toy_timer": 0.0,
        "toy_active": False,
        "toy_type": None,
        "chase_timeout": 0.0,
        "coat": 0,              # coat color index
        "hut_index": 0,         # which hut this cat owns (0, 1, 2...)
    }
]
```

### Shared State (stays at top level)

```python
# These remain as direct CatState attributes:
mouse_pos, mouse_near, click_through, screen_width, screen_height,
weather_condition, weather_last_fetch, weather_raw,
speech (top-level — unused? Actually speech goes per-cat), save_accum
```

### Migration: Backward-Compatible Properties

```python
@property
def cat_x(self) -> float:
    return self.cats[0]["x"] if self.cats else 500.0

@cat_x.setter
def cat_x(self, value: float):
    if self.cats:
        self.cats[0]["x"] = value

@property
def cat_y(self) -> float:
    return self.cats[0]["y"] if self.cats else 700.0

@cat_y.setter
def cat_y(self, value: float):
    if self.cats:
        self.cats[0]["y"] = value

# Same pattern for all single-cat fields:
# state, facing, energy, hunger, boredom, at_home, home_cooldown, home_linger,
# walk_duration, walk_elapsed, walk_pause, walk_pause_start, walk_accel,
# walk_frame, walk_accum, wander_duration, wander_elapsed, wander_cooldown,
# wander_session_count, wander_vx, wander_vy, tail_phase, blinking, blink_timer,
# next_blink, sleep_breath, deep_sleep, zzz_particles, reaction_type, reaction_timer,
# purr_vibrate, mouth_open, consecutive_pets, eye_target, eye_current, hearts,
# speech, speech_cooldown, speech_idle_timer, expression, expr_target, expr_timeout,
# blush_alpha, blush_target, pupil_dilation, toy_target, toy_timer, toy_active,
# toy_type, chase_timeout
```

For each field `foo`:
```python
@property
def foo(self):
    return self.cats[0]["foo"] if self.cats else _DEFAULT_FOO

@foo.setter
def foo(self, value):
    if self.cats:
        self.cats[0]["foo"] = value
```

### Add Cat Method

```python
def add_cat(self, coat: int = 0, x: float | None = None, y: float | None = None) -> int:
    """Add a new cat. Returns cat ID. Returns -1 if at max cats."""
    max_cats = config.MAX_CATS  # default 3
    if len(self.cats) >= max_cats:
        return -1
    
    cat_id = len(self.cats)
    if x is None:
        # Offset from last cat
        last_x = self.cats[-1]["x"] if self.cats else self.screen_width / 2
        x = last_x + random.randint(-40, 40)
        x = max(50.0, min(x, float(self.screen_width - 50)))
    if y is None:
        y = float(self.screen_height - config.CAT_BASELINE)
    
    cat = _default_cat_dict(cat_id, coat, x, y)
    cat["hut_index"] = cat_id  # each cat gets its own hut
    self.cats.append(cat)
    return cat_id

def remove_cat(self, cat_id: int) -> bool:
    """Remove cat by id. Cannot remove cat 0 (minimum 1 cat)."""
    if cat_id == 0 or cat_id >= len(self.cats):
        return False
    self.cats.pop(cat_id)
    # Reassign hut indices
    for i, c in enumerate(self.cats):
        c["hut_index"] = i
    return True
```

---

## 2. Painting: Window Modifications (`ui/window.py`)

### Paint Event

```python
def paintEvent(self, event):
    painter = QPainter(self)
    # ... background, grass, etc ...
    
    # Draw huts — one per cat
    for i, cat in enumerate(self.state.cats):
        self._draw_hut(painter, hut_index=cat["hut_index"])
    
    # Draw cats
    for cat in self.state.cats:
        self._draw_cat(painter, cat)
    
    # Draw top-layer effects (hearts, speech) per cat
    for cat in self.state.cats:
        draw_hearts(painter, cat["x"], cat["y"], cat["hearts"])
        draw_speech_bubble(painter, cat["x"], cat["y"], cat["speech"])
```

### Hut Layout

- Huts placed left-to-right along bottom
- First hut: x = `screen_width - HUT_PADDING_RIGHT - HUT_WIDTH`
- Second hut: x = that - `HUT_WIDTH - 10` (10px gap)
- Third: same logic, more left
- `_hut_door_center(state, hut_index)` now takes `hut_index` parameter

```python
def _hut_x(state, hut_index: int = 0) -> int:
    """Return x position of hut for given index (0 = rightmost)."""
    gap = 10
    total_w = config.HUT_WIDTH + gap
    return state.screen_width - config.HUT_PADDING_RIGHT - config.HUT_WIDTH - (hut_index * total_w)

def _hut_door_center(state, hut_index: int = 0) -> tuple:
    hx = _hut_x(state, hut_index)
    hy = state.screen_height - config.HUT_PADDING_BOTTOM
    door_cx = hx + config.HUT_WIDTH // 2
    door_cy = hy - config.HUT_DOOR_H // 2
    return (door_cx, door_cy)
```

---

## 3. Navigation / Behavior

### Per-Cat State Machines

Each cat needs independent:
- Need values (energy, hunger, boredom)
- Position & facing
- State & all walk/wander/home internals
- Timer values (breath, blink, Zzz particles)
- Toy state (toy_target, toy_active, toy_type, chase_timeout)
- Speech bubble & cooldown
- Expression system

### Engine Loop Changes

```python
def _on_tick(self):
    dt = ... # same as before
    
    # Iterate cats for systems
    for cat in self.state.cats:
        needs_system.update(dt, cat, self.state)  # pass cat dict + shared state
        transitions_system.update(dt, cat, self.state)
    
    # Weather (shared — only needs one fetch)
    weather.update(self.state, dt)
    
    # Mouse proximity — check all cats
    for cat in self.state.cats:
        self._check_mouse_for_cat(cat)
    
    # Repaint
    self.window.update()
```

Systems signature changes:
```python
# behavior/needs.py
def update(dt: float, cat: dict, state: CatState) -> None:
    """Update a single cat's needs."""
    ...

# behavior/transitions.py
def update(dt: float, cat: dict, state: CatState) -> None:
    """Check transition conditions for a single cat."""
    ...
```

### Performance Note

2-3 cats means 2-3x computation for needs + transitions. Still trivial at `TICK_S=0.05s`. Canvas painting is the bottleneck (drawing 2-3x sprites). If FPS drops below 20, cache painted cat sprites to QPixmap and blit instead of re-drawing each frame.

---

## 4. Interaction

### Mouse Proximity (Multi-Cat)

```python
def _check_mouse_for_cat(self, cat: dict):
    """Check mouse proximity for a single cat."""
    cursor = QCursor.pos()
    dx = cursor.x() - cat["x"]
    dy = cursor.y() - cat["y"]
    dist = math.hypot(dx, dy)
    
    cat["mouse_near"] = dist < 150  # not stored in cat dict? Add it.
    
    # Pet detection
    if dist < 40 and cat["state"] not in (STATE_SLEEP, STATE_CHASE, STATE_PLAY):
        # same pet logic as before but operating on cat dict
        ...
```

If mouse is near multiple cats, only the closest cat reacts (pet priority: closest non-sleeping cat).

### Focus: Ctrl+1, 2, 3

```python
def focus_cat(self, index: int):
    """Bring cat[index] to center of screen. Others follow within 50px."""
    if index >= len(self.state.cats):
        return
    
    target = self.state.cats[index]
    target_x = self.state.screen_width / 2
    
    # This cat walks to center
    target["state"] = "WALK"
    target["walk_target_x"] = target_x
    target["walk_target_y"] = target["y"]
    
    # Other cats follow with offset
    for i, other in enumerate(self.state.cats):
        if i == index:
            continue
        other_x = target_x + random.randint(-40, 40)
        other_x = max(50.0, min(other_x, float(self.state.screen_width - 50)))
        other["state"] = "WALK"
        other["walk_target_x"] = other_x
        other["walk_target_y"] = other["y"]
```

Keyboard binding: `shortcut = QShortcut(QKeySequence("Ctrl+1"), self); shortcut.activated.connect(lambda: focus_cat(0))` (same for 2, 3).

### Click-Through Mode

When `click_through = True` (default), all cats ignore mouse — pass-through to desktop.
When `click_through = False`, all cats react interactively.

### Tray Menu: Add/Remove Cat

```python
def _add_cat(self):
    cat_id = self.state.add_cat()
    if cat_id >= 0:
        self.state.save_state()
        show_tray_notification(f"🐱 Cat #{cat_id+1} joined!")
```

```python
def _remove_last_cat(self):
    if len(self.state.cats) <= 1:
        show_tray_notification("Minimum 1 cat required")
        return
    removed = self.state.cats.pop()
    self.state.save_state()
    show_tray_notification(f"🐱 Cat #{len(self.state.cats)+1} left.")
```

---

## 5. Persistence (save / load)

### save_state()

```python
def save_state(self) -> None:
    s = self.state
    data = {
        "cats": [
            {
                k: cat[k]
                for k in ("id", "x", "y", "state", "facing", "coat",
                          "energy", "hunger", "boredom",
                          "at_home", "home_cooldown", "home_linger",
                          "walk_duration", "walk_elapsed",
                          "wander_duration", "wander_elapsed", "wander_cooldown",
                          "wander_vx", "wander_vy", "hut_index")
            }
            for cat in s.cats
        ],
        "weather_condition": s.weather_condition,
        "weather_raw": s.weather_raw,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        os.makedirs(config.STATE_DIR, exist_ok=True)
        with open(config.STATE_PATH, "w") as f:
            json.dump(data, f, default=str)
    except OSError:
        pass
```

### load_state()

```python
def load_state(self) -> None:
    try:
        with open(config.STATE_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return

    s = self.state
    cats_data = data.get("cats", [])
    if not cats_data:
        # Legacy single-cat state — migrate
        s.cats = [_migrate_legacy_cat(data)]
    else:
        s.cats = []
        for cd in cats_data:
            cat = _default_cat_dict(cd.get("id", len(s.cats)),
                                     cd.get("coat", 0),
                                     cd.get("x", 500.0),
                                     cd.get("y", 700.0))
            cat.update(cd)  # overlay saved fields
            s.cats.append(cat)
    
    # Restore shared state
    s.weather_condition = data.get("weather_condition", "cloudy")

    # Apply time-offset decay for all cats
    try:
        saved_ts = datetime.fromisoformat(data["timestamp"])
        elapsed = (datetime.now() - saved_ts).total_seconds()
        if elapsed > 0:
            for cat in s.cats:
                cat["energy"] = max(0.0, cat["energy"] - config.ENERGY_DRAIN_SIT * elapsed)
                cat["hunger"] = min(100.0, cat["hunger"] + config.HUNGER_DRAIN * elapsed)
    except (KeyError, ValueError):
        pass
```

### Legacy Migration

```python
def _migrate_legacy_cat(data: dict) -> dict:
    """Convert old single-cat state format to multi-cat dict."""
    cat = _default_cat_dict(0, 0, data.get("x", 500.0), data.get("y", 700.0))
    cat["state"] = data.get("state", "SIT")
    cat["facing"] = data.get("facing", True)
    cat["energy"] = float(data.get("energy", 80.0))
    cat["hunger"] = float(data.get("hunger", 20.0))
    cat["boredom"] = float(data.get("boredom", 0.0))
    # All other fields stay as defaults
    return cat
```

---

## 6. Config Additions

```python
# ─── Multi-Pet ────────────────────────────────────────────────────────
MAX_CATS = 3                    # max number of cats (configurable)
DEFAULT_CATS = 1                # number of cats at fresh install
CAT_SPAWN_OFFSET_MIN = 20       # px offset range for new cats
CAT_SPAWN_OFFSET_MAX = 80
MULTI_HUT_GAP = 10              # px gap between huts
```

---

## 7. Files Changed

| File | Change |
|---|---|
| `core/state.py` | Add `cats: list[dict]`, backward-compat `@property` aliases, `add_cat()`, `remove_cat()`, `_default_cat_dict()` |
| `core/engine.py` | Iterate cats in tick loop, per-cat `_check_mouse_for_cat()`, per-cat systems, update save/load |
| `config.py` | Add `MAX_CATS`, `DEFAULT_CATS`, `CAT_SPAWN_OFFSET_*`, `MULTI_HUT_GAP` |
| `cat/home.py` | Accept `hut_index` parameter in `_hut_x()` and `_hut_door_center()` |
| `behavior/needs.py` | Accept `(dt, cat, state)` signature, operate on cat dict |
| `behavior/transitions.py` | Accept `(dt, cat, state)` signature, operate on cat dict |
| `ui/window.py` | Paint loop over cats, multi-hut layout |
| `ui/controls.py` | Ctrl+1/2/3 focus handlers, tray Add/Remove Cat |
| `behavior/cat.py` | `_draw_cat(painter, cat)` uses cat dict instead of state attrs |

---

## 8. Coat Colors

```python
COAT_COLORS = [
    # (body, belly, paw) - each is a QColor
    QColor(0x7C, 0x8E, 0x9E),  # 0: Russian Blue (default)
    QColor(0xF5, 0xDE, 0xB3),  # 1: Cream
    QColor(0x8B, 0x6F, 0x47),  # 2: Brown Tabby
    QColor(0x2F, 0x2F, 0x2F),  # 3: Black
    QColor(0xFF, 0xFF, 0xFF),  # 4: White
    QColor(0xD4, 0x7E, 0x6A),  # 5: Ginger
    QColor(0xA0, 0xA0, 0xA0),  # 6: Gray
]
```

`draw_cat(painter, cat)` picks colors from `COAT_COLORS[cat["coat"] % len(COAT_COLORS)]`.

---

## 9. Test Plan (~270 tests)

- `test_multi_cat_default_single` — fresh state has 1 cat with id=0
- `test_add_cat_increments` — add_cat() returns sequential ids
- `test_add_cat_at_max` — returns -1 when at MAX_CATS
- `test_remove_cat` — removes by id, reassigns hut indices
- `test_remove_cat_0_fails` — cannot remove first cat
- `test_backward_compat_cat_x` — state.cat_x reads cats[0]["x"]
- `test_backward_compat_cat_x_setter` — state.cat_x = 100 writes cats[0]["x"]
- `test_legacy_state_migration` — old format state.json loads into cats[0]
- `test_multi_state_save_load` — 2 cats save and restore correctly
- `test_multi_hut_positions` — huts don't overlap, placed left-to-right
- `test_mouse_proximity_closest_cat` — closest non-sleeping cat gets pet
- `test_focus_cat_ctrl_1` — focus cat 0 walks to center
- `test_per_cat_needs_independent` — feeding cat 0 doesn't affect cat 1
- `test_per_cat_transitions_independent` — cat 0 sleeps while cat 1 wanders
- `test_coat_color_lookup` — coat index maps to correct color
- `test_tray_add_cat_menu_entry` — menu item exists and creates cat
- `test_tray_remove_cat_menu_entry` — removes last cat
