# Desktop Cat 🐱

> A living desktop pet that roams your screen, sleeps when tired,
> and comes home when bored. Full-screen transparent overlay.

## Demo

<!-- GIF / screenshot placeholder -->

## Features

- **Full-screen transparent overlay** — sits on top of everything, click-through with `WA_TransparentForMouseEvents`
- **Autonomous behavior** — sits, walks, wanders, sleeps, goes home
- **Home bed** — cushioned oval at bottom-right corner, always visible in the background
- **Needs system** — three vital stats: Energy (drains active, recharges sleeping), Hunger (rises slowly, feedable via API), Boredom (rises while sitting, resets on pet/mouse)
- **Circadian rhythm** — most active at dawn (5-7) and dusk (17-19), sleeps more at night (22-6)
- **Sleep modes** — home nap (wakes at energy > 60) vs field sleep anywhere (wakes at energy > 85)
- **Deep sleep** — auto-detects system idle > 120s and dims the cat to 60% opacity
- **Wander behavior** — exploratory walks with random direction changes, bounces off screen edges, 45s cooldown between sessions
- **Mouse interaction** — eyes track cursor, proximity (40px) triggers pet reaction, proximity (80px) may trigger approach walk
- **Eye tracking** — pupils smoothly follow the mouse, works only when awake
- **Blink animation** — random 2-6s intervals, 0.15s closure
- **Purring** — triggered by 5+ consecutive pets, body vibrates sinusoidally at 40Hz
- **Meowing** — reacts when petted while sleeping, mouth opens with sinusoidal animation
- **Zzz particles** — float upward with horizontal drift while sleeping
- **Expression system** — 7 moods (neutral, happy, sleepy, alert, squint, angry, surprised) with configurable eye/pupil geometry and blush
- **Breathing animation** — gentle body expansion/contraction at state-dependent speed (sit: 1.5Hz, walk: 2.5Hz, sleep: 0.8Hz, deep sleep: 0.3Hz)
- **HTTP API** — pet, feed, and wake the cat from any tool (port 18789)
- **State persistence** — saves every 30s, survives restarts with catch-up drain
- **Russian Blue color palette** — steel gray-blue body, soft pink inner ears and nose, light warm gray belly

## Architecture

### Module map

```
desktop-cat/
├── main.py              # Entry point — wires the module graph
├── config.py            # All constants (single source of truth)
├── core/
│   ├── engine.py        # QTimer game loop, navigation, mouse tracking, persistence
│   ├── window.py        # Qt full-screen overlay + draw pipeline (z-ordered)
│   ├── state.py         # CatState dataclass (pure data, zero logic)
│   └── api.py           # HTTP API daemon (threaded, non-blocking)
├── cat/
│   ├── body.py          # Body silhouette + belly (sit/walk poses)
│   ├── head.py          # Head circle, ears (with inner pink), nose triangle, whiskers
│   ├── eyes.py          # Eye tracking, blink arcs, happy-eye arcs
│   ├── legs.py          # Paws (sit) + 4-frame leg animation (walk)
│   ├── tail.py          # Tail: sinusoidal swish (sit), held up (walk), curled around (sleep)
│   └── home.py          # Bed cushion + curled cat on bed + Z badge
├── behavior/
│   ├── needs.py         # Per-tick need drain/recharge by state
│   └── transitions.py   # State machine with priority-ordered triggers
├── animation/
│   └── breathe.py       # Breathing oscillation — scale + vertical bob
└── tests/
    └── test_state_machine.py   # 30+ tests covering transitions, needs, navigation, persistence, API, bed coords
```

### State machine

```
                       ┌──────────────────────────┐
                       │         GO_HOME           │
                       │  Engine navigates to bed  │
                       └─────────┬────────────────┘
                                 │ arrives (within HOME_TOLERANCE = 2px)
                                 ▼
                       ┌──────────────────────────┐
                ┌─────►│       SLEEP (at home)     │◄──── GO_HOME
                │      │  Wakes at energy > 60     │
                │      └────────────┬──────────────┘
                │                   │
                │      ┌────────────▼──────────────┐
                │      │       SLEEP (field)        │
                │      │  Wakes at energy > 85      │
                │      └────────────┬──────────────┘
                │                   │
                │      ┌────────────▼──────────────┐
                │      │         SIT                │
                │      │  Entry state               │
                │      │  Default pose              │
                │      └──┬─────┬─────┬─────┬──────┘
                │         │     │     │     │
                │         │     │     │     │
                ▼         │     │     │     │
           WANDER ◄───────┘     │     │     │
           (exploratory)        │     │     │
                │               │     │     │
                ▼               ▼     │     │
            timout ──────► SIT        │     │
                                      │     │
                        WALK ◄────────┘     │
                        (short walk)        │
                            │               │
                            ▼               │
                        timout ────► SIT    │
                                            │
                              GO_HOME ◄─────┘
                              (energy < 40, boredom > 70,
                               circadian chance, wander low-energy)
```

### Trigger table (SIT exit conditions, checked in priority order)

| Trigger | Condition | Target State | Note |
|---|---|---|---|
| Low energy | energy < 40 | GO_HOME | Mandatory — overrides everything |
| High boredom | boredom > 70, cooldown expired | GO_HOME | Home visit cooldown: 90s |
| Circadian home | Per-tick probability (dawn/dusk: 0.2%) | GO_HOME | Home visit cooldown respected |
| Wander chance | Cooldown expired + circadian roll | WANDER | Morning (7-10): 0.3%, dusk (17-20): 0.25% |
| Field sleep (low energy) | energy < 40 | SLEEP (field) | Fallback if GO_HOME didn't trigger |
| Field sleep (boredom) | boredom > 90 | SLEEP (field) | Cat collapses anywhere |
| Random walk | Per-tick probability (boredom-modulated) | WALK | Faster near center, 0.5-3s duration |

### Needs system

| Need | While sitting | While walking | While sleeping |
|---|---|---|---|
| Energy | -0.003/s | -0.02/s | +0.08/s (home) / +0.08/s (field) |
| Hunger | +0.003/s | +0.003/s | +0.003/s |
| Boredom | +0.005/s | Frozen | -0.02/s |

### Wander behavior

- Entered randomly when sitting, cooldown expired (45s between sessions)
- Random facing direction at entry
- Walks in that direction with random direction reversal (1% per tick)
- Bounces off screen edges (margin: 60px)
- Duration: 2-5 seconds per session (uniform random)
- Circadian modulation: most active morning (7-10, 0.3%) and evening (17-20, 0.25%)
- Cancels if energy drops below 40 (transitions to GO_HOME)

### Circadian activity profile

| Time | Activity level |
|---|---|
| 22 - 6 | Night — minimal activity (walk: 0.05%, home: 0.02%, wander: 0.03%) |
| 5 - 7 | Dawn — elevated (walk: 0.3%, home: 0.2%) |
| 7 - 10 | Morning peak — high wander (0.3%) |
| 10 - 17 | Day — moderate (walk: 0.15%, wander: 0.15%) |
| 17 - 20 | Evening peak — high (walk: 0.3%, home: 0.2%, wander: 0.25%) |
| 20 - 22 | Wind-down (walk: 0.15%) |

### Expression system

The cat dynamically morphs eye shape and pupil geometry based on context:

| Expression | Eye width | Eye height | Pupil width | Pupil height | When used |
|---|---|---|---|---|---|
| Neutral | 4 | 4 | 2.5 | 2.5 | Default |
| Happy | 5 | 3 | 3 | 2 | Pet/purr reaction |
| Sleepy | 3 | 2 | 1.5 | 1.5 | Approaching sleep |
| Alert | 6 | 5 | 1.5 | 3 | Mouse detected / sudden interaction |
| Squint | 4 | 2 | 1.5 | 1.5 | Blink recovery |
| Angry | 4 | 4 | 2.5 | 2.5 | Top-flat eye shape |
| Surprised | 6 | 6 | 2 | 2.5 | Unexpected wake |

Blush alpha also modulates (0.0 neutral → 0.0-1.0 based on reaction context).

## Installation

### Prerequisites

- Windows 11
- Python 3.11+
- PyQt6

### Quick start

```bash
# Clone
git clone https://github.com/Gauravk2332/desktop-cat.git
cd desktop-cat

# Install dependencies
pip install PyQt6

# Run
python main.py
```

## Configuration

All tunable constants in `config.py`. No runtime changes — single source of truth per session.

### Timing

| Constant | Default | Description |
|---|---|---|
| TICK_MS | 50 | Main loop tick rate (20 Hz) |
| SAVE_INTERVAL | 30.0 | State persistence interval (seconds) |
| IDLE_SLEEP_DELAY | 120.0 | System-idle seconds before deep sleep mode |

### Needs rates (per second)

| Constant | Default | Description |
|---|---|---|
| ENERGY_DRAIN_ACTIVE | 0.02 | Energy drain while walking/wandering |
| ENERGY_DRAIN_SIT | 0.003 | Energy drain while sitting |
| ENERGY_RECHARGE_SLEEP | 0.08 | Energy recharge while sleeping |
| HUNGER_DRAIN | 0.003 | Hunger increase rate (all states) |
| BOREDOM_INCREASE_SIT | 0.005 | Boredom increase while sitting |

### Movement

| Constant | Default | Description |
|---|---|---|
| WALK_SPEED | 80.0 | px/s walk speed |
| WALK_ACCEL_TIME | 0.4 | Seconds to reach full speed (smooth accel/decel) |
| WALK_DURATION_MIN | 0.5 | Minimum walk duration |

### State thresholds

| Constant | Default | Description |
|---|---|---|
| HOME_ENERGY_THRESHOLD | 40.0 | Go home when energy below this |
| HOME_NAP_MIN_ENERGY | 60.0 | Wake from home nap at this |
| HOME_BOREDOM_THRESHOLD | 70.0 | Go home when boredom above this |
| HOME_LINGER_DURATION | 8.0 | Seconds to sit near bed after waking |
| HOME_VISIT_COOLDOWN | 90.0 | Seconds between auto home visits |

### Wander

| Constant | Default | Description |
|---|---|---|
| WANDER_DURATION_MIN | 2.0 | Min seconds per wander leg |
| WANDER_DURATION_MAX | 5.0 | Max seconds per wander leg |
| WANDER_BASE_CHANCE | 0.002 | Per-tick base probability to wander |
| WANDER_COOLDOWN | 45.0 | Seconds between wander sessions |
| WANDER_OFFSET | 60 | Margin px from screen edges (no wall-hugging) |
| WANDER_TURN_CHANCE | 0.01 | Per-tick chance to reverse direction |

### Home bed

| Constant | Default | Description |
|---|---|---|
| HOME_BED_RX | 37 | Bed ellipse horizontal radius |
| HOME_BED_RY | 27 | Bed ellipse vertical radius |
| HOME_BED_INNER | 0.62 | Inner depression ratio (donut shape) |
| HOME_PADDING_RIGHT | 20 | px from screen's right edge |
| HOME_PADDING_BOTTOM | 48 | px from screen's bottom edge |
| HOME_TOLERANCE | 2.0 | px arrival tolerance for GO_HOME |

### API

| Constant | Default | Description |
|---|---|---|
| API_PORT | 18789 | HTTP API port (localhost only) |

### Drawing

| Constant | Default | Description |
|---|---|---|
| HEAD_R | 14 | Head circle radius |
| EAR_W | 8 | Ear base width |
| EAR_H | 10 | Ear height |
| EYE_R | 4 | Eye radius |
| PUPIL_R | 2.5 | Pupil radius |
| WHISKER_LEN | 12 | Whisker length |

## HTTP API

Listens on `127.0.0.1:18789`. Runs in a daemon thread, non-blocking.

### GET /

Returns full cat state.

```json
{
  "status": "alive",
  "state": "desktop-cat-v2-modular",
  "cat": {
    "state": "SIT",
    "energy": 72.4,
    "hunger": 14.2,
    "boredom": 3.1,
    "facing": true,
    "x": 960,
    "y": 1060,
    "at_home": false
  }
}
```

### POST /

Accepts JSON body with an `action` field.

```json
{"action": "pet"}   // Resets boredom to 0, triggers purr or meow reaction
{"action": "feed"}  // Reduces hunger by 15
{"action": "wake"}  // Wakes from sleep (SLEEP → SIT, +10 energy)
```

## Development

```bash
# Setup venv
python -m venv .venv
.venv\Scripts\activate
pip install PyQt6 pytest

# Run tests (30+ unit tests, no Qt display needed)
pytest tests/ -v

# Run cat
python main.py
```

### Test structure

| Test class | Covers |
|---|---|
| `TestConfigSanity` | Config value sanity checks (thresholds ordered, rates positive, dimensions sane) |
| `TestStateTransitions` | All state machine transitions: SIT→SLEEP, SLEEP→SIT, SIT→GO_HOME, WALK→SIT, boredom/energy priority, home linger, wander entry |
| `TestNeedsSystem` | Per-state drain/recharge rates, clamping, boredom freezing during walk, boredom decay during sleep |
| `TestNavigation` | Walk movement (left/right), edge stopping, wander timing/edge bounce, GO_HOME navigation/arrival, accel/decel curve, walk frame progression |
| `TestPersistence` | State save/load logic (engine.load_state/save_state) |
| `TestAPI` | Action queue processing: pet resets boredom, feed reduces hunger, wake transitions sleep |
| `TestBedCoordinates` | Bed center calculation, screen-size scaling |

## Design notes

- **Full-screen overlay** over multi-window approach: avoids z-order wars, simplifies state management. One static window covers the screen, the cat draws at screen-relative coordinates.
- **Screen-relative coordinates**: `cat_x`/`cat_y` are true screen positions. The bed center is computed from `screen_width`/`screen_height`, not window dimensions.
- **No `window.move()`**: the overlay is static. Only the cat moves (via QPainter coordinates).
- **Modular packages**: `core/` (engine/lifecycle), `cat/` (drawing), `behavior/` (logic), `animation/` (curves) — each with a single responsibility.
- **`WA_TransparentForMouseEvents`**: the window is invisible to mouse input — all clicks pass through to underlying applications.
- **Config-driven**: every tunable value lives in `config.py`. No magic numbers in logic or drawing code.
- **State persistence**: writes JSON to `%LOCALAPPDATA%/Nova/desktop-cat/state.json` every 30 seconds. On load, applies catch-up drain for elapsed offline time.
- **Priority-ordered transitions**: the state machine checks conditions in strict order (energy → boredom → circadian → wander → random walk), so critical needs always take precedence.
- **Expression tweening**: eye/pupil geometry smooth-interpolates between targets at the animation tick rate, making expression transitions seamless.

## Colour palette (Russian Blue)

```
Body:           #7C8E9E  steel gray-blue
Belly:          #D4D9DE  light warm gray
Paw pads:       #CCD5DC  muted pink-gray
Inner ear:      #FFB8C6  soft pink
Nose:           #FF9494  soft coral
Whiskers:       #A8B0B8  light gray
Iris:           #6BA3D6  soft blue
Bed rim:        #D4A574  warm tan
Bed inner:      #C49A6C  darker tan
```

## State machine diagram (text)

```
SIT ──(energy < 40)────────────────────▶ GO_HOME ──(arrived)──▶ SLEEP(at_home)
SIT ──(boredom > 70 + cooldown)────────▶ GO_HOME
SIT ──(circadian roll + cooldown)──────▶ GO_HOME
SIT ──(wander roll + cooldown)─────────▶ WANDER ──(timout)─────▶ SIT
SIT ──(walk roll)──────────────────────▶ WALK ────(timout)─────▶ SIT
SIT ──(energy < 40 or boredom > 90)────▶ SLEEP(field)
WANDER ──(energy < 40)─────────────────▶ GO_HOME
SLEEP(at_home) ──(energy > 60 + linger)▶ SIT
SLEEP(field) ────(energy > 85)─────────▶ SIT
WALK ──(edge collision)────────────────▶ SIT
```

## Acknowledgements

- Russian Blue cat colours
- Inspired by Neko and desktop pet games of the 90s/2000s
- Built with PyQt6 on Windows 11
