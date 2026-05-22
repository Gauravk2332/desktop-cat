# Desktop Cat Overhaul Plan

**Status**: Plan (ready for Coder implementation)
**Sources**: Muse design spec (MUSE_DESIGN.md), Pico research (horse gaits — not used), Mira cat gait knowledge synthesis
**Goal**: Real 4-leg walking cat + realistic behaviors + orange tabby coat

---

## Overview — 3 Phases

| Phase | Scope | Est. files changed | Est. tests |
|-------|-------|-------------------|------------|
| **A** | Orange tabby coat + 4-leg walk animation | 6 | 20+ |
| **B** | New cat behaviors (stretch, groom, scratch, yawn, etc.) | 8 | 40+ |
| **C** | Additional coat options (tuxedo, calico, etc.) | 2 | 10+ |

**Total estimated**: ~70 new tests, ~16 files changed

---

## Phase A — Orange Tabby + 4-Leg Walk (HIGH PRIORITY)

### A.1 Coat System Refactor

**File**: `config.py`
- Replace flat `C_BODY`, `C_BELLY`, `C_NOSE` etc. with a structured `CoatColors` dataclass
- Add `COAT_COLORS_STRUCTURED` dict with 7 coat definitions
- Add `DEFAULT_COAT` = index 0 (current gray tabby) for backward compatibility
- Add `ORANGE_TABBY` = index 1 (orange body, darker stripes, green eyes, white chin/chest)
- Add legacy aliases: `C_BODY = COAT_COLORS[0]["body"]` etc.

```python
@dataclass
class CoatColors:
    name: str
    body: QColor
    belly: QColor
    stripe: QColor
    nose: QColor
    ear_inner: QColor
    eye: QColor
    pupil: QColor
    whisker: QColor
    chin_chest: QColor      # NEW — for orange tabby white patch
    paw_pads: QColor        # NEW
    stripe_style: str        # "mackerel" | "classic" | "solid" | "tuxedo" | "calico" | "point" | "tortie"
    has_forehead_m: bool     # orange/gray tabbies only
```

Orange tabby colors: `#E89B5D` body, `#FCE6C9` belly, `#C47A3C` stripe, `#F08080` nose, `#4CAF50` eyes.

### A.2 4-Leg Walk Gait Cycle

**File**: `cat/legs.py`
- Rewrite `draw_legs_walk()` from 2-line oscillation to 4-leg articulated limbs
- Each leg has 2 segments (upper + lower) meeting at a joint
- Front legs base at shoulder: ~(cx-10, cy-16) FL, ~(cx+6, cy-16) FR
- Back legs base at hip: ~(cx-20, cy-14) BL, ~(cx+16, cy-14) BR
- 8-frame gait cycle using diagonal pairs (RF+LH, then LF+RH):
  - Trot pattern: frames 0-3 one diagonal, frames 4-7 the other
  - At any time, 2-3 feet on ground (never all 4 off)
  - Forward leg = bent forward, backward leg = stretched back
  - Per-frame max paw extension: ±12px from base

**Joint positions per frame** (simplified from Muse spec):

```python
# (upper_end_x, upper_end_y, paw_x, paw_y) relative to leg_base
GAIT_FRAMES_4LEG = {
    0: {"fl": (-2,-4, -8,-2), "fr": (-2,-4, -8,-2),   # both front reaching back
        "bl": (2,-4, 8,-2), "br": (2,-4, 8,-2)},       # both hind reaching forward
    1: {"fl": (-1,-6, -10,-4), "fr": (0,-2, -4,0),
        "bl": (1,-6, 10,-4), "br": (0,-2, 4,0)},
    2: {"fl": (0,-6, -8,-6), "fr": (2,-2, 0,2),
        "bl": (0,-6, 8,-4), "br": (-2,-2, 0,2)},
    3: {"fl": (2,-4, -4,-4), "fr": (0,-4, 4,2),
        "bl": (-2,-4, 4,-2), "br": (0,-4, -4,2)},
    4: {"fl": (-2,-4, -8,-2), "fr": (-2,-4, -8,-2),   # swap diagonal
        "bl": (2,-4, 8,-2), "br": (2,-4, 8,-2)},       # (mirror of 0 but offset)
    5: {"fl": (0,-2, -4,0), "fr": (-1,-6, -10,-4),
        "bl": (0,-2, 4,0), "br": (1,-6, 10,-4)},
    6: {"fl": (2,-2, 0,2), "fr": (0,-6, -8,-6),
        "bl": (-2,-2, 0,2), "br": (0,-6, 8,-4)},
    7: {"fl": (0,-4, 4,2), "fr": (2,-4, -4,-4),
        "bl": (0,-4, -4,2), "br": (-2,-4, 4,-2)},
}
```

- Draw each leg as a `QPainterPath` with 2 fat lines (stroke 5px, RoundCap)
- Upper: base → joint; Lower: joint → paw
- Front legs: slightly forward of body center
- Back legs: slightly behind body center

### A.3 Body Bob + Tilt

**File**: `cat/body.py` or inline in `window.py`

Add a `GAIT_BODY_BOB` table:
```python
GAIT_BODY_BOB = [0, -1, -2, -1, 0, 1, 2, 1]  # px y-offset per frame
GAIT_BODY_TILT = [-2, -1, 0, 1, 2, 1, 0, -1]  # degrees tilt per frame
```
Apply in `_draw_walk()` before drawing body:
```python
bob_offset = GAIT_BODY_BOB[state.walk_frame]
tilt_angle = GAIT_BODY_TILT[state.walk_frame]
painter.save()
painter.translate(0, bob_offset)
painter.rotate(tilt_angle)
# ... draw body, legs, tail ...
painter.restore()
```

Body bob range: ±2px. Tilt range: ±2°.

### A.4 Tail Sway

**File**: `cat/tail.py`
- `draw_tail_walk()`: add sinusoidal sway synchronized with gait
- Tail base at body rear, tip sways ±5-8px horizontally
- Formula: `sway = math.sin(frame * 0.785) * 6`
- Tail curve: use a bezier path from body-rear through mid-point to tip

### A.5 Stripes Drawing

**File**: `cat/body.py` (new function `draw_stripes()`)
- Only drawn for stripe_style = "mackerel" or "classic"
- 5-7 short curved lines over the body ellipse
- Tail has 4-5 ring stripes
- Forehead "M" marking (3 strokes)
- Cheek stripes (2 per side)
- Leg stripes (1 per leg)
- White chin/chest patch (orange tabby specific)

### A.6 Window Dispatch

**File**: `core/window.py`
- `_draw_walk()`: call new 4-leg draw, body bob/tilt, stripe overlay
- `_draw_sit()`: call updated sit legs, stripe overlay
- Pass `cat_state.coat_index` through to all draw functions
- Each draw function reads `COAT_COLORS[cat_state.coat_index]` for colors

### A.7 State Field

**File**: `core/state.py`, `core/engine.py`
- Add `"coat_index": 0` to `default_cat_dict()`
- Add `"coat_index"` to `_per_cat_fields()` for save/load
- Settings dialog: coat picker now indexes into `COAT_COLORS` list

---

## Phase B — Real Cat Behaviors

### B.1 Behavior Lock System

**File**: `core/engine.py`, `behavior/transitions.py`

Add `cat["behavior_lock"]` — a string or None. When set:
- Normal state transitions are skipped
- Behavior-specific timer/phase update runs instead
- On completion: clear `behavior_lock`, set state → SIT

### B.2 New States

| State | Duration | Trigger | Sound | Draw function |
|-------|----------|---------|-------|---------------|
| STRETCH | 1.5s | SLEEP→SIT transition | yawn.wav | `_draw_stretch()` |
| YAWN | 1.2s | Low energy + sit | yawn.wav | head modifier |
| GROOM | 3-6s | idle 30s+ (15% chance/tick) | — | `_draw_groom()` |
| SCRATCH | 2.5s | idle 60s+ (10% chance) | scratch.wav | `_draw_scratch()` |
| ROLL_OVER | 2.0s | trust+idle (mouse near + 120s CD) | trill.wav | `_draw_roll_over()` |
| PLAY_BOW | 1.0s | Play phase start | chirp.wav | `_draw_play_bow()` |

### B.3 State Transitions

**File**: `behavior/transitions.py`

Add behavior triggers after the existing transition chain:

```python
# Before _maybe_walk, check behavior triggers
if cat.get("behavior_lock"):
    return  # don't override active behavior

# Stretch after waking
if cat["state"] == config.STATE_SLEEP and cat["previous_state"] == config.STATE_SLEEP:
    pass  # handled by SLEEP→SIT transition in engine

# Grooming (idle cat)
if cat["state"] in (config.STATE_SIT,) and cat["boredom"] > 30 and not cat.get("groom_cooldown"):
    if random.random() < 0.001:  # ~1 tick per 50s
        _enter_groom(cat)
        return

# Scratching
if cat["state"] in (config.STATE_SIT,) and cat.get("at_home", False) and not cat.get("scratch_cooldown"):
    if random.random() < 0.0005:
        _enter_scratch(cat)
        return

# Play bow (before chase interaction)
if cat["state"] == config.STATE_SIT and cat["toy_type"] in (config.TOY_LASER, config.TOY_YARN) and random.random() < 0.3:
    _enter_play_bow(cat)
    return
```

### B.4 Animation Timers

**File**: `core/engine.py`

In the main update loop, after navigation update but before draw:

```python
if cat.get("behavior_lock"):
    timer = cat.get(f"{cat['behavior_lock'].lower()}_timer", 0.0)
    timer += dt
    cat[f"{cat['behavior_lock'].lower()}_timer"] = timer
    duration = getattr(config, f"{cat['behavior_lock']}_DURATION", 1.0)
    if timer >= duration:
        cat["behavior_lock"] = None
        cat[f"{cat['behavior_lock'].lower()}_timer"] = 0.0
        cat["state"] = config.STATE_SIT
```

For multi-phase behaviors (groom, stretch, scratch), track phase:
```python
phase_time = timer / duration * 3  # 3 phases
cat[f"{cat['behavior_lock'].lower()}_phase"] = int(phase_time) % 3
```

### B.5 Draw Functions

**File**: `core/window.py`

Add new draw methods following the existing pattern:

- `_draw_stretch(painter, cx, cy, wrapped)` — Phase 0: front stretch (paws forward, back arch), Phase 1: full stretch (body elongates), Phase 2: recovery
- `_draw_groom(painter, cx, cy, wrapped)` — Phase 0: lift paw to mouth, Phase 1: lick paw motion, Phase 2: switch paw, Phase 3: face wash circle
- `_draw_scratch(painter, cx, cy, wrapped)` — Rapid alternating paw motion, 4 legs anchored, body bobs
- `_draw_roll_over(painter, cx, cy, wrapped)` — Phase 0: lean to side, Phase 1: belly up (draw from bottom), Phase 2: roll back
- `_draw_play_bow(painter, cx, cy, wrapped)` — Front legs low, butt up, tail up

### B.6 Tail Swish, Ear Rotate, Head Look, Slow Blink

**File**: `cat/tail.py`, `cat/head.py`, `cat/eyes.py`, `core/engine.py`

These are continuous modifiers (not full states):
- **Tail swish**: `engine.py` sets `tail_swish_active` when mouse is near but not interacting; `tail.py` oscillates tail tip ±10px at 3Hz
- **Ear rotation**: `engine.py` sets `ear_angle` based on mouse position; `head.py:draw_ears()` accepts angle param, rotates ear triangles ±15°
- **Head look**: `engine.py` detects mouse above cat; `head.py` shifts eye/head position up
- **Slow blink**: triggered when mouse is near and cat is relaxed; eyes close slowly over 1.5s

### B.7 Engine Loop Integration

**File**: `core/engine.py`

Add per-tick calls in the main update loop:

```python
def _update_behaviors(self, dt):
    for cat in self.state.cats:
        self._update_behavior_lock(dt, cat)
        if not cat.get("behavior_lock"):
            self._check_groom_trigger(cat)
            self._check_scratch_trigger(cat)
            self._check_play_bow_trigger(cat)
        self._update_tail_swish(cat)
        self._update_ears(cat)
        self._update_head_look(cat)
        self._update_slow_blink(dt, cat)
```

---

## Phase C — Additional Coat Options

### C.1 Coat Definitions

Add to config.py:

```python
COATS = [
    CoatColors("Gray Tabby",    C_BODY, C_BELLY, C_NOSE, ...),  # index 0 (legacy)
    CoatColors("Orange Tabby",  orange, cream,   dark_orange, ...),  # index 1 (NEW)
    CoatColors("Tuxedo",        black,  white,   pink, ...),
    CoatColors("Calico",        white,  white,   N/A, ...),  # uses patches
    CoatColors("Siamese",       cream,  cream,   pink, ...),  # uses points
    CoatColors("Solid Black",   black,  black,   pink, ...),
    CoatColors("Tortie",        #B06555, #D4956A, N/A, ...),  # uses mixed patches
]
```

Each coat's `stripe_style` determines how markings are drawn:
- `"mackerel"` — vertical stripe curves (gray tabby, orange tabby)
- `"classic"` — swirled/blotched stripes (less common)
- `"solid"` — no stripes (tuxedo, black)
- `"tuxedo"` — solid with white chest/belly/paws
- `"calico"` — white base with orange+black oval patches
- `"point"` — solid body with darker extremities (Siamese)
- `"tortie"` — mixed orange+black patches (tortoiseshell)

### C.2 Stripe Drawing by Style

**File**: `cat/body.py`

```python
def draw_coat_pattern(painter, cx, cy, state, coat):
    if coat.stripe_style in ("mackerel", "classic"):
        draw_tabby_stripes(painter, cx, cy, state, coat)
    elif coat.stripe_style == "tuxedo":
        draw_white_chest_belly(painter, cx, cy, state, coat)
    elif coat.stripe_style == "calico":
        draw_calico_patches(painter, cx, cy, state, coat)
    elif coat.stripe_style == "point":
        draw_dark_points(painter, cx, cy, state, coat)
    elif coat.stripe_style == "tortie":
        draw_tortie_patches(painter, cx, cy, state, coat)
    # solid = nothing extra
```

---

## Implementation Order

1. **Phase A.1** — Coat colors dataclass + orange tabby definition → config.py
2. **Phase A.2** — 4-leg gait frames → legs.py
3. **Phase A.3-A.4** — Body bob + tail sway → body.py, tail.py
4. **Phase A.5-A.6** — Stripes + window dispatch → body.py, window.py
5. **Phase A.7** — State fields + save/load → state.py, engine.py
6. **Phase B.1-B.4** — Behavior lock + new states → engine.py, transitions.py
7. **Phase B.5** — Behavior draw functions → window.py
8. **Phase B.6-B.7** — Continuous modifiers → engine.py, head.py, eyes.py, tail.py
9. **Phase C** — Additional coat options → config.py, body.py
10. **Tests** — All phases

**Lens review** after every 2-3 steps.

---

## Testing Strategy

| Test file | Tests | Coverage |
|-----------|-------|----------|
| `tests/test_coats.py` | 15 | Each coat renders, color values correct, stripe drawing by style |
| `tests/test_gait.py` | 15 | Walk frames cycle, body bob values, leg positions per frame |
| `tests/test_behaviors.py` | 25 | Each behavior triggers/cancels/timesout correctly, behavior lock prevents conflicts |
| `tests/test_modifiers.py` | 15 | Tail swish, ear angle, head look, slow blink all set/clear correctly |

~70 new tests + all existing 315 must still pass.
