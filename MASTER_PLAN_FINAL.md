# MASTER PLAN — Desktop Cat Overhaul (FINAL)

> **Approval:** Unanimous APPROVED with Changes — Pico 🎯, Muse ✨, Coder 💻, Lens 🔍
> **6 research/design/architecture docs:** 4,451 lines synthesized
> **4 agent reviews:** All incorporated
> **Target:** PyQt6 overlay, Windows 11, 33fps tick, single-process, transparent overlay
> **Cat:** Orange mackerel tabby, ~200-250px tall, semi-realistic painterly style, amber eyes

---

## 1. Scope & Philosophy

### Core Design Principles

1. **The 70% Rule (Muse)** — A real cat spends 70% of its time doing nothing interesting. The 30% that is interesting only feels real because of the 70% that isn't. This plan builds *presence*, not just *activity*.
2. **Data-First Architecture (Pico)** — Build the data layer (memory/personality/circadian) before the planner that consumes it. Avoids the v1→v2 rewrite cycle.
3. **Right-Sized Engineering (Coder)** — JSON over SQLite, 5 traits over 8, predefined zones over auto-discovery, commissioned art over Blender learning curve. Don't engineer what you can buy or simplify.
4. **Test-Integrated Delivery (Lens)** — Unit tests alongside implementation, not after. Every phase has specific, binary-pass/fail exit criteria. CI/CD gates from pre-commit to nightly.

### Key Architectural Decisions (Locked)

| Decision | Chosen Approach | Alternative Rejected | Reason |
|----------|----------------|---------------------|--------|
| Sprite format | PNG horizontal spritesheets (400×400px) | SVG (slow), QPainter (fake-looking) | Performance + quality |
| Sprite source | Commission Fiverr ($30-50) | Blender 3D (steep learning curve) | Time-to-quality: 2 days vs 2 weeks |
| Eye system | Eye-window approach: neutral-open eyes baked in, iris+pupil composited at runtime | All baked (no expression range) | Maximum flexibility without multiplying sprite count |
| Persistence | JSON (temp-file+rename) | SQLite (FPS risk on UI thread) | Avoids blocking I/O in render loop |
| Personality | 5 traits: boldness, playfulness, affection, laziness, curiosity | 8-10 traits (invisible through 200px sprite) | Visible behavioral differences without over-engineering |
| Territory | 6 predefined screen zones | Auto-discovery (grid binning, SQLite) | Simpler, same perceived effect |
| LLM integration | <10% of decisions, 2s timeout, behavioral intent output | Primary decision engine (too slow, unpredictable) | Novelty without latency cost |
| Transitions | 200ms InOutCubic crossfade + 300-500ms dwell | Instant swap (jarring) | Smooth with natural hesitation |

---

## Pre-Phase: Risk Register & Vertical Slice Milestone

### Risk Register (Team-Curated)

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|------------|--------|------------|-------|
| R1 | PyQt6 transparent overlay broken on gk-pc GPU | Low | **Critical** | Day 1 Hour 1 smoke test. Fallback: Direct2D/Skia rendering. | Coder |
| R2 | Crossfade compositing glitch on Windows DWM | Low | **Medium** | Test 200ms InOutCubic in Phase 0 with 10+ rapid transitions. Fallback: instant swap. [Bumped from Low→Medium per Pico] | Coder |
| R3 | Commissioned spritesheet doesn't match spec | Medium | High | Review first draft frame. Require stripe consistency clause in contract. Test on gk-pc before accepting. | Coder |
| R4 | Blender pipeline frame misalignment (if used) | Medium | Medium | Lock camera + origin before render. Validate all frames same size in stitch script. | Coder |
| R5 | DPI scaling (125%) misaligns overlays | Medium | Medium | Test on gk-pc early. Use QScreen.devicePixelRatio for pixel-snapping. | Coder |
| R6 | Stripe inconsistency on commissioned sprites | Medium | High | Contract must specify UV-mapped single texture. Review first animation frames before proceeding. | Coder |
| R7 | Sprite quality ceiling (cat looks fake) | Medium | High | Commission with detailed brief. Review first deliverable before full order. Fiverr portfolio review. | Coder, Muse |
| R8 | GPU gaming load drops overlay FPS | Medium | Low | Cat gracefully lowers animation rate if DWM throttled. No frame skipping. | Coder |
| R9 | JSON file corruption on crash | Low | Medium | Temp-file+rename write pattern. Auto-backup last 3 versions. | Coder, Lens |
| R10 | LLM proxy (clowbot) down | Low | Low | Complete rule fallback. 2s timeout. 5min blackout before retry. | Pico, Coder |
| R11 | Sequence manager stuck-state | Low | High | Auto-reset after 5s. Unit test edge cases. | Coder, Lens |
| R12 | Cat feels like clockwork toy (no soul) | Medium | High | Soul layer built into Phase 2 architecturally. Cannot be skipped. | Muse |

### Vertical Slice Milestone (Pico)
Before scaling to all 12 poses and all sequences, ship **one complete horizontal slice**:

**Target:** Sit → Hunger > 60 → walk to bowl → eat → groom → sit
This validates sprite pipeline, navigation, needs system, sequences, transitions, and memory in a single end-to-end test.

---

## 2. Phase 0: Foundation — Sprite Pipeline & Bigger Cat

**Duration:** 2-3 dev sessions | **Calendar:** ~1 week
**Dependencies:** None (greenfield)
**Led by:** Coder 💻

### Day 1, Hour 1: Overlay Smoke Test
Before ANY other work, run this on the target gk-pc:
```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
app = QApplication([])
win = QMainWindow()
win.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
win.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
win.setStyleSheet("background: transparent")
win.show()
app.exec()
```
**If failed:** white box, flicker, or compositing artifacts → investigate Direct2D, Skia, or document the limitation. Do NOT proceed to Phase 1 until this works. [Coder, Pico — Critical risk gate]

### Deliverables

**A. Commission Spritesheet (Fiverr)**
- 3 poses: sit-breathing (4 frames), walk (12 frames), loaf (4 frames)
- All frames: 400×400px, PNG with transparency
- Consistent stripe UV-mapping — stripes must not wobble across frames
- Neutral-open eye state with `eye_rect` coordinates per frame
- Color: base #E88D3B, stripes #C46A2A, belly/chest/snout #F5DEB3
- Soft painterly style, upper-left key lighting at 45°, no hard outlines

**B. Render Pipeline**
- Python PIL script: stitch PNG frames into horizontal strip spritesheets
- QPixmap slice + cache in memory
- Sprite manifest JSON: file paths, frames, FPS defaults, eye_rects
- **Validation step:** assert all frames same size before stitching [Pico]

**C. Engine Integration**
- QPainter → QPixmap swap in render loop (replace procedural geometry with sprite blit)
- Cat scaled to configurable height (default ~200px, range 120-350px)
- Drop shadow: blur ellipse at 8-12% opacity behind cat
- **Silhouette shadow layer:** dark blur behind cat to separate from busy backgrounds [Muse]
- Fallback to old QPainter cat when sprites missing (graceful degradation) [Lens]
- Crossfade test: 200ms InOutCubic between two QPixmaps

### Exit Criteria (Binary — Lens-verified)
- [ ] Transparent overlay works on gk-pc (WA_TranslucentBackground, no flicker)
- [ ] Cat visible at 200px+ from spritesheet
- [ ] Breathing loop plays at 33fps smooth
- [ ] Drop shadow visible and separates cat from background
- [ ] Scale slider changes size in real-time
- [ ] **Frame timing gate:** each QPixmap blit < 30ms (33fps budget) [Lens]
- [ ] Fallback: missing sprites → QPainter cat, logged warning, no crash [Lens]

---

## 3. Phase 1: Visual Overhaul — All Poses, Transitions & Life Signals

**Duration:** 4-6 dev sessions | **Calendar:** 1-2 weeks
**Dependencies:** Phase 0 (pipeline + spritesheet format)
**Led by:** Coder 💻 (commission mgmt) + Muse ✨ (spec quality)

### Key Decisions (from reviews)
- **Per-animation FPS config** — not uniform 12fps. Real cat timing: groom 3s, yawn 2.7s, stretch 3.2s, sleep breath 12s [Coder]
- **Ear independence** — 6 overlay pieces (3 positions × 2 ears, asymmetric allowed). Independent timer 3-10s random interval [Muse]
- **Eye-window system** — iris tile (64×64 amber #D4942B) + pupil oval (dynamic dilation via affine transform). Gaze direction via pupil offset within eye window. [Muse]
- **Tail overlay** — 5 pre-baked sprites + tip-flick. Independent timer. [from original]
- **300-500ms minimum dwell** between all state transitions — cat visibly hesitates [Muse]
- **Color palette:** CAT_VISUAL_DESIGN.md §6. Night mode: 20%/30% desaturate. [from original]
- **Size-dependent LOD** — at Small size, reintroduce 1px dark outline for legibility (painterly style loses detail below 150px) [Muse]

### Spritesheets Required

| Pose | Frames | FPS | Duration | Type | Notes |
|------|--------|-----|----------|------|-------|
| Sit (alert) | 4 | 3 | 1.3s | Loop | Upright, breathing |
| Sit (relaxed) | 4 | 3 | 1.3s | Loop | Slight slouch, one paw tucked |
| Loaf | 4 | 2 | 2.0s | Loop | All paws tucked |
| Walk | 12 | 12 | 1.0s | Loop | Full 4-beat gait cycle, stripe consistency critical |
| Trot | 8 | 15 | 0.53s | Loop | Faster, brief suspension |
| Sleep (curled) | 6 | 0.5 | 12.0s | Loop | Deep breathing |
| Sleep (sprawl) | 6 | 0.5 | 12.0s | Loop | Side lie, eye flutter at apex |
| Groom | 12 | 4 | 3.0s | Loop | Paw-lick cycle, head turn |
| Stretch | 8 | 2.5 | 3.2s | One-shot | Full cat yoga, front extension |
| Yawn | 4 | 1.5 | 2.7s | One-shot | Mouth fully open, tongue curl |
| Alert | 2 | — | Static | Static | Ears up, eyes wide |
| Eat | 6 | 6 | 1.0s | Loop | Head down, chewing |

**Transition sheets** (6 frames each @ 12fps, same commissioner):
- sit↔walk (both directions) · sit↔lie (both directions) · sit↔groom (both directions)
- walk→turn (6 frames, 180°)
- startle (3 frames: freeze → eye wide → recovery — one-shot)

**Overlay assets:**
- Tail (6, 128×128): relaxed sway, upright, low/tucked, puffed, wrapped, tip-flick
- Eyes (7 tiles, 64×64): open normal, open dilated, half-closed, closed, slow-blink strip (4-frame), wide, REM-twitch
- Ears (6, 64×64): L-forward, L-rotated, L-flat, R-forward, R-rotated, R-flat

### Commissioner Brief (template)
> "I need one horizontal spritesheet for an orange mackerel tabby cat, side view. The sheet contains 12 pose strips and 6 transition strips (see list). Each strip is a horizontal frame sequence. All frames: 400×400px PNG with transparency. Critical: consistent stripe UV-mapping across ALL frames — stripes must not wobble or shift independently of the body. Color: base #E88D3B, stripes #C46A2A, belly/chest/snout #F5DEB3 (cream). Eyes: amber #D4942B with dark eyeliner. Nose: pink. Eyes in 'neutral open' state (pupil/iris handled at runtime). Include eye_rect coordinates per frame. Lighting: upper-left key at 45°. No hard outlines — soft painterly style."

### Exit Criteria (Lens-verified)
- [ ] All 12 poses renderable (manifest check: frame count matches) [Lens]
- [ ] Walk shows smooth 12-frame 4-leg gait
- [ ] Per-animation FPS: groom 3s, yawn 2.7s, sleep breath 12s [Coder]
- [ ] Crossfade 200ms InOutCubic smooth, no white flash
- [ ] Transitions have 300-500ms dwell hesitation before starting
- [ ] Eyes blink every 10-20s independent of body (logged, not tied to state) [Muse]
- [ ] Pupil dilation tracks: narrow in bright, wide in dark
- [ ] Ears twitch at random 3-10s intervals, asymmetric allowed [Muse]
- [ ] Startle/freeze: 3-frame lockdown + recovery
- [ ] Turn-in-place: plays during 180° direction change
- [ ] Night palette: desaturate 20%/30%
- [ ] **Visual regression:** all poses ≤ 1% pixel diff from baseline [Lens]
- [ ] **Frame timing:** all sheets < 2s cumulative load [Lens]
- [ ] Missing sprite = logged warning, QPainter fallback [Lens]
- [ ] LOD: small size (≤150px) has 1px outline for legibility [Muse]

---

## 4. Phase 2: Circadian + Needs + Memory + Personality + Behavior Planner + Soul Layer

**Duration:** 5-8 dev sessions | **Calendar:** ~2 weeks (largest phase)
**Dependencies:** Phase 1 (sprites — can use placeholder silhouettes during dev)
**Led by:** Coder 💻 (engine) + Muse ✨ (soul layer design) + Lens 🔍 (tests)

### Key Decisions (from reviews)
- **Phases 2+3 merged** — Build circadian/memory/personality first, then planner that consumes them. [Pico]
- **No SQLite** — JSON persistence only. Short-term = dict deque (last 20 events). Long-term = `data/cat_memory.json`. [Coder, Pico, Lens]
- **Personality: 5 traits** — boldness, playfulness, affection, laziness, curiosity. 0-10 scale. JSON persisted. No time-series. [Coder ↔ Muse]
- **Territory: 6 predefined zones** — no auto-discovery, no grid binning. [Coder]
- **Soul layer (Muse)** — 3 critical additions built into planner:
  1. Delayed reaction system (0.5-2.5s latency on all user responses)
  2. Habituation module (cooldown per interaction type, response downgrades on repetition)
  3. Contemplation / "The Stare" as first-class behavioral state (the 70% rule)
- **Feature flags:** Every system behind a config flag. Old behavior = default. [Coder verified]
- **Unit tests alongside implementation, not after** [Pico, Lens]
- **LLM downgrade:** <10% of decisions, 2s timeout, unavailability = non-fatal [Pico, Coder]
- **SequenceManager edge cases:** stuck-state detection (auto-reset 5s), sleep-cooldown drift fix [Coder]

### Deliverables

#### A. Circadian Clock (`core/circadian.py`)

```python
class CircadianClock:
    """Drives ALL time-dependent behavior. Single authoritative clock."""
    PHASES = ["DAWN", "MORNING", "MIDDAY", "DUSK", "EVENING", "NIGHT", "DEEP_NIGHT"]
    
    def update(self, dt):
        # advance internal_hour (0-24)
        # detect phase transitions → emit event
        # return current energy_multiplier (0.0-1.0 sinusoidal)
    
    @property
    def energy_level(self):
        # sinusoidal: 0.0 at midnight, 1.0 at noon, 0.8 at 6pm
        # Used by NeedsSystem to scale decay rates
        pass
```

- 7 phases: DAWN, MORNING, MIDDAY, DUSK, EVENING, NIGHT, DEEP_NIGHT
- Phase change events broadcast to BehaviorPlanner
- Energy curve: sinusoidal, peak at 6AM/6PM, trough at midnight-3PM
- **Clock jump tolerance:** if `abs(real_delta - expected_delta) > 300s`, treat as discontinuity (sleep resume / timezone change) [Lens]

#### B. Needs System (`behavior/needs.py`)

| Need | Range | Default | Decay | Recovers via | Phase effect |
|------|-------|---------|-------|-------------|--------------|
| Hunger | 0-100 | 70 | 0.5-1.5/hr | Eating | Faster dawn/dusk |
| Energy | 0-100 | 70 | 2-4/hr active | Sleep (5-8× faster) | Peak dawn/dusk |
| Boredom | 0-100 | 20 | -1/hr (rises) | Play, explore, user interaction | Faster when inactive |
| Social | 0-100 | 50 | -2/hr (rises) | User proximity/interaction | Higher during day |
| Elimination | 0-100 | 0 | +3/hr (only advances) | Litter box visit (off-screen) | — |

- Decay rates scaled by CircadianClock.energy_level
- **Unit test:** hunger=80 + dawn → BehaviorPlanner picks HungerWalk, not GroomSession [Lens]

#### C. Personality (`behavior/personality.py`)

```python
PERSONALITY_SCHEMA = {
    "boldness": {"default": 5, "affects": ["reaction_speed", "mouse_approach_rate"]},
    "playfulness": {"default": 7, "affects": ["play_frequency"]},
    "affection": {"default": 7, "affects": ["greeting_frequency", "follow_rate"]},
    "laziness": {"default": 3, "affects": ["activity_duration", "sleep_preference"]},
    "curiosity": {"default": 6, "affects": ["investigation_frequency", "object_response"]},
}
```

- Each trait: 0-10 scale, stored in `data/personality.json`
- Personality *delta* after interaction: `affection += 0.1` when user lingers near cat
- Affects: reaction speed (bold: 0.5s → shy: 2.5s), behavior probabilities, sequence selection bias
- **Lens test:** personality A (bold=8, lazy=2) vs personality B (bold=2, lazy=8) produce different action distributions after 10 minutes of identical input

#### D. Memory (`behavior/memory.py`)

```python
class CatMemory:
    def __init__(self):
        self.short_term = deque(maxlen=20)  # (event_type, position, timestamp)
        self.long_term = self._load_json("data/cat_memory.json")
    
    # long_term schema:
    # {
    #   "favorite_zones": {"desk_center": 43, "window_perch": 28},
    #   "schedule": {"hourly_activity": [0.2]*24},  # rolling 7-day avg
    #   "interactions_today": 7,
    #   "mood": {"happiness": 65, "trust": 70},
    #   "current_territory_marks": {"desk_center": 1234567890}
    # }
```

- Short-term: deque of last 20 events with (type, position, timestamp) — provides immediate context
- Long-term: JSON dict, temp-file+rename for write atomicity [Coder]
- Territory: 6 zones calculated from screen dimensions (sleep corner, window perch, desk center, food, play, litter)

#### E. Behavior Planner (`behavior/planner.py`)

5-layer priority chain evaluated every tick:

```
1. EMERGENCY     → energy < 5 → collapse and sleep (lowest possible energy)
2. SEQUENCE      → currently running sequence → continue it
3. INTERACTION   → user just clicked/hovered → respond (if cooldown allows)
4. STATE MACHINE → no urgent need → pick best sequence from needs + personality + time
5. LLM           → novelty only if uncertainty detected
```

- Selects full behavioral sequences, not individual actions
- Sequences can be interrupted (step-level `can_interrupt` flag)
- If no sequence selected: idle animation loops + micro-behaviors
- **LLM path:** only entered when:
  - Needs conflict (hungry + playful both > 70 — which wins?)
  - Novel user action (first-time interaction)
  - Social situation (user absent > 2h, just returned)
  - Middle-of-night disturbance

#### F. Behavior Sequences (`behavior/sequences.py`)

| Sequence | Steps | Duration | Trigger | Interruptible? |
|----------|-------|----------|---------|----------------|
| MorningWake | sleep → stretch → yawn → sit → look → meow | 8s | Dawn + energy<50 | Yes |
| HungerWalk | sit → stand → walk to food → eat → groom | 15-30s | Hunger>60 + dawn/dusk | No (eat) |
| PlayBurst | idle → stalk → pounce → bat → bunny-kick → groom | 10-20s | Boredom>60 + dawn/dusk | Yes |
| GroomSession | sit → paw-lick ×4 → rub face → shake → resume | 12-25s | After eating, after play, idle>5min | Yes |
| SleepSequence | sit → lie → curl → deep sleep → REM ×1-3 → lighter | 30min-2h | Energy<30 + night/midday | Yes |
| GreetingUser | look → walk toward user → sit → slow blink → chirp | 5-10s | Social>60 + user proximity | Yes |
| WindowWatch | walk to window → sit → watch → chirp → tail twitch | 2-15min | Curiosity>50 + daytime | Yes |
| Patrol | walk along territory stops → sniff → continue | 30-60s | Boredom>30 + every 2h | Yes |
| **Contemplation** | loaf → stare → blink → ear flick → shift → keep staring | 30s-5min | Any idle moment | Yes |
| **The Stare** | FREEZE mid-any-action → stare at nothing → blink → resume | 15-45s | Random 5% chance per idle tick | Yes |

#### G. Soul Layer (Muse — Critical)

1. **Delayed Reaction System** (`behavior/reactions.py`)
   - 0.5-2.5s randomized latency on ALL user-initiated responses
   - Bold cats: 0.5-1.5s · Shy cats: 1.5-2.5s
   - Interaction type weights: click=faster, hover=slower, sustained proximity=fastest
   - Before reacting: cat may flick ear or glance toward user

2. **Habituation Module** (`behavior/habituation.py`)
   - Each interaction type has a cooldown counter (0-ignore_threshold)
   - Response sequence: full → ear flick → glance → ignore
   - Cooldown decays at 1 count / 3-5 minutes of no interaction
   - ~5th rapid click → cat stops reacting entirely until cooldown decays

3. **Lull Generator**
   - After N minutes of activity → LullGenerator triggers: "do nothing for 2-10 minutes"
   - During lull: cat cycles Contemplation → The Stare → micro-behaviors → repeat
   - Micro-behaviors during lull: ear flick, slow blink, tail twitch, weight shift, deep breath
   - **Without this:** cat is always doing something = clockwork toy

4. **Micro-narrative** — tiny events that break perfect patterns:
   - Every 15-30s during idle: ear twitch or tail switch
   - Every 30-60s during loaf: slow blink
   - Every 1-3min: weight shift (subtle body position change)
   - Every 3-5min: look around (head turn, scan environment)

### Exit Criteria (Lens-verified)
- [ ] Circadian energy curve verified: peak at system dawn/dusk, trough midnight-3PM
- [ ] Needs → correct sequence selection (verifiable with deterministic test) [Lens]
- [ ] Sequences play through fully without cycling (log shows start→step progression→end→next) [Lens]
- [ ] Interruptible: user click during sequence → cat glances → suspends or continues within 2.5s
- [ ] **Soul layer:** click 10× in 5 seconds → response downgrades by the 5th click [Muse]
- [ ] **Delayed reaction:** all user-initiated responses have 0.5-2.5s latency (measured) [Muse]
- [ ] Contemplation or The Stare logged: cat idle 70%+ of total runtime
- [ ] LLM fires in <10% of decisions (verified by log counter)
- [ ] **Unit tests:** circadian phase transitions, need decay rates, sequence priority resolution [Pico, Lens]
- [ ] **Integration test:** deterministic 5-min script replayable, identical behavior log [Lens]
- [ ] **Frame timing:** behavior system adds < 1ms per tick (JSON reads, no blocking I/O)
- [ ] JSON persistence: 100 save/load cycles, no corruption [Lens]
- [ ] All feature flags: old behavior = exact pre-Phase 2 output

---

## 5. Phase 3: Learning, Social Referencing & Mood Persistence

**Duration:** 2-3 dev sessions | **Calendar:** ~1 week
**Dependencies:** Phase 2 (behavior planner + memory layer functional)
**Led by:** Coder 💻 + Muse ✨

### Scope Reduction
**Cut from original plan:** SQLite tables, 8 traits, territory auto-discovery, time-series tracking. All can be added in v2 if users ask for them. [Coder, Pico]

### Deliverables

1. **Favorite Spot Learning**
   - Visit counter per zone in `data/cat_memory.json`
   - After N=10 visits to a zone → marked as "favorite"
   - Favorite zones weighted 3× for idle/sleep sequence selection
   - Zones decay at 1 visit/day if not visited (removes inactive favorites)

2. **Owner Schedule Detection**
   - 24 hourly slots: count user activity level (typing + mouse) in each
   - Running 7-day average in JSON
   - Cat predicts: be 30min pre-active before user's typical peak hour
   - Simple: `active_hour = max(hourly_activity.values())`
   - Personality modifier: lazy cats care less (predictive shift is smaller)

3. **Social Referencing** [Muse]
   - Cat looks at user location → looks at object of interest → looks back at user → chirp (soft)
   - Triggers: Curiosity > 5 + user within range + cat has an "interesting" object in view (cursor, new window, screensaver change)
   - Duration: 2-3 seconds, barely visible but profoundly communicative

4. **Mood Persistence** [Muse]
   - Continuous signal: happiness (0-100), trust (0-100)
   - +happiness: user interaction, play, proximity
   - -happiness: being ignored for >30min, startled, absence
   - +trust: gentle interactions, predictable schedule
   - -trust: startling, sudden movements
   - Effects: happy cat → higher greeting frequency, tail higher. Trusting cat → closer approaches, belly-up sleep more often.
   - Persisted in JSON across sessions

5. **Contagious Behavior (Lightweight)** [Muse]
   - Monitor user input *rate* in 5-second windows
   - Fast/agitated typing → cat's tail swish rate increases, ears go to "airplane" (rotated)
   - Slow/absent → cat settles nearby, may sleep
   - Only visual effect — no state change required

6. **Sleep REM Twitching** [Muse]
   - During SleepSequence deep sleep phase: 1-3 REM episodes per cycle
   - REM = 2-frame animation: paw kick + eye flutter overlay
   - Duration: 0.5-1s burst, then back to stillness
   - Random timing within deep sleep phase

### Exit Criteria (Lens-verified)
- [ ] Cat returns to most-visited zone after restarts (visit counter verified: zone with N=10+ gets 3× more idle time)
- [ ] Cat active ~30min before user's typical active hour (schedule detected, logged)
- [ ] Social referencing visible: head turn → look → chirp sequence in log [Muse]
- [ ] Mood persists across restart: happiness/trust within ±2 of saved value
- [ ] Sleep REM twitch fires during deep sleep (logged with timestamp)
- [ ] Contagious behavior: rapid mouse → tail swish logged (frequency threshold test)

---

## 6. Phase 4: LLM Intelligence Layer

**Duration:** 2-3 dev sessions | **Calendar:** ~1 week
**Dependencies:** Phase 2 (behavior planner + soul layer)
**Led by:** Coder 💻 + Lens 🔍

### Key Decisions
- **LLM < 10% of decisions** — enforced by log counter + CI lint check [Lens]
- **2s timeout** — if proxy unresponsive, `decide()` returns None, rule engine handles [Pico, Coder]
- **Non-fatal unavailability** — cat behaves identically without LLM (rule system is complete) [Coder]
- **Output = behavioral intent, not raw action** — describes *motivation*, planner converts to sequences [Muse]
- **Every call logged** — trigger, context sent, raw output, parsed intent, latency

### Deliverables

1. **Context Builder** (`behavior/context.py`)
   ```python
   def build_context(circadian, needs, personality, memory, user):
       return {
           "time": circadian.phase_name,
           "energy": needs.energy,
           "hunger": needs.hunger,
           "boredom": needs.boredom,
           "social": needs.social,
           "personality": personality.traits,  # e.g., "bold and curious"
           "mood": f"happy={memory.mood.happiness}, trusting={memory.mood.trust}",
           "user": user.status,  # present, typing, absent, idle
           "recent_events": memory.short_term.peek(),  # last 5
           "last_user_interaction": f"{ago}s ago",
       }
   ```

2. **LLM Call Triggers** (exclusive list — nothing else invokes LLM):
   - Needs conflict: two needs > 70 simultaneously (e.g., hungry + playful)
   - Novel interaction: first time seeing a specific user action
   - Social return: user absent > 2 hours, just returned
   - Night disturbance: middle-of-night user activity (cat expresses mild annoyance)
   - Decision pause: BehaviorPlanner's uncertainty flag triggered

3. **Output Parser**
   - Input: `"The cat wants attention but is sleepy"` → parsed intent: `{"motivation": "social", "energy_level": "low", "suggested": "partial_wake_and_greet"}`
   - Input: `"Cat is confused by the cursor doing something new"` → `{"motivation": "curiosity", "suggested": "investigate_slowly"}`
   - NOT: `"MEOW greeting"` or `"WALK left"` — those are engine commands, not what the LLM emits
   - Invalid parse (< 5% target) → fallback to rule behavior [Lens]

4. **Circuit Breaker**
   - 2s timeout: `asyncio.wait_for(call_remote_api(...), timeout=2.0)`
   - Proxy down → logged + skip LLM for 5 minutes (don't hammer proxy) [Pico]
   - After 5 min, retry once. If still down → extend blackout another 5 min.

5. **LLM Frequency Lint Check**
   - CI step: replay 5-min deterministic script
   - Count LLM calls: fail if > 10% of decisions
   - Fails build, not runtime

### Exit Criteria (Lens-verified)
- [ ] LLM invoked < 10% of all decisions (5-min replay, counter logged) [Lens]
- [ ] Invalid parse rate < 5% (test: 50 varied LLM responses → at most 2 unparseable) [Lens]
- [ ] Cat visibly "thinks" (head tilt + 1s hold) before LLM-driven actions
- [ ] Proxy down → cat behavior identical to proxy up (no difference in transition log)
- [ ] **Lens edge case test:** 100 sequential proxy-down calls → 0 errors, 0 delays, all rule-handled
- [ ] All LLM calls logged with full traceability

---

## 7. Phase 5: Sound + Micro-Details

**Duration:** 1-2 dev sessions | **Calendar:** Few days
**Dependencies:** Phase 2 (sequence framework needed for sound triggers)
**Led by:** Coder 💻 + Muse ✨

### Key Decisions
- Sounds fire from sequence steps, not RNG [Pico: fold into Phase 2 dev]
- No separate sound phase — wire triggers during sequence development
- Missing WAV = logged warning + graceful continuation (no crash) [Lens]

### Deliverables

1. **Sound Labels per Sequence Step**
   - `MorningWake.steps[3] = ("meow_greeting", sound="meow_greeting")`
   - `GroomSession.steps[2] = ("purr", sound="purr_deep")`
   - `HungerWalk.steps[3] = ("eat", sound="eat_crunch")`
   - `WindowWatch.steps[1] = ("chirp", sound="chirp_excited")`

2. **WAV File Requirements**
   | File | Existing | Duration | Purpose |
   |------|----------|----------|---------|
   | meow_short.wav | ✅ | 0.3s | Generic, fallback |
   | meow_greeting.wav | ✅ | 0.4s | MorningWake, GreetingUser |
   | meow_plaintive.wav | ✅ | 0.7s | Lonely, needs unmet |
   | meow_demand.wav | ❌ New | 0.6s | HungerWalk (at food bowl) |
   | purr_deep.wav | ❌ New | 3.0s loop | GroomSession, Sleep curl |
   | chirp_excited.wav | ❌ New | 0.2s | WindowWatch, SocialReferencing |
   | chatter.wav | ❌ New | 0.5s | WindowWatch (bird frustration) |

   Generation: `scripts/generate_sounds.py` (programmatic WAV generation, existing pattern)

3. **Weather Response**
   - Weather awareness (from existing `core/weather.py`)
   - Thunder/loud weather → cat walks off-screen, returns after storm timer
   - Sunny → WindowWatch probability ×2
   - Palette: slight cool shift for rain (already in Phase 1 night mode)

4. **REM Sleep Visual**
   - Phase 1 eye overlays include REM-twitch tile
   - Timer: during SleepSequence deep phase, 1-3 bursts per cycle
   - Each burst: REM tile overlay on eyes + paw kick (earlier overlays)
   - Duration: 0.5-1s

### Exit Criteria
- [ ] Sounds fire from sequence context only (verified by log: no sound outside sequence)
- [ ] Purr plays during GroomSession and SleepSequence curl phase
- [ ] Chirp plays during WindowWatch (fired by sequence step, not RNG)
- [ ] Thunder → cat hides (off-screen) → returns when storm ends
- [ ] Missing WAV → logged warning, no crash, sequence continues [Lens]
- [ ] REM twitch visible (eye flutter + paw kick, logged during deep sleep)

---

## 8. Phase 6: Settings, CI/CD, Testing & Ship

**Duration:** 2-3 dev sessions | **Calendar:** ~1 week
**Dependencies:** All prior phases
**Led by:** Lens 🔍 (test infrastructure) + Coder 💻 (installer)

### CI/CD Gate Architecture (Lens)

```
[Pre-commit] → [PR-level] → [Nightly / Pre-release]
```

#### Pre-Commit Gates (every push, runs in <30s)
1. **Unit tests pass** — all modules: circadian, needs, personality, memory, planner
2. **Lint + type check** — no undefined state transitions or unresolved imports
3. **Frame timing** — all spritesheets load in < 2s cumulative
4. **No slow I/O on UI thread** — static analysis: no `open()`, `sqlite3`, `file.read()` in render path

#### PR-Level Gates (every merge to main, <2min)
5. **Visual regression** — all poses rendered, compared to baseline at ≤ 1% pixel diff
6. **Behavior replay** — 5-min deterministic input script → identical behavior log (state transitions, sequence picks, needs values)
7. **Performance baseline** — idle CPU < 10%, GPU memory < 50MB, no frame drop in 60s
8. **State machine coverage** — all valid state transitions covered by test; any new state must add all edges

#### Nightly / Pre-Release Gates
9. **24-hour endurance test** — FPS, memory, state transitions logged every 5 minutes. Verify: no FPS degradation, no memory leak (>50MB over baseline), no sequence stuck-states
10. **Personality stability test** — 5 cats with identical seeds run for 1 hour → each should show different action distributions (personality actually matters)
11. **Memory integrity test** — JSON runs 100 save/load cycles with simulated crash mid-write. Verify: temp-file+rename prevents corruption

### Ship Deliverables
- **Settings panel:** size slider (120-350px), personality display (5 traits as bar graph with labels), memory reset button (clears JSON, preserves current session), time acceleration toggle (debug: 2×/5×/10× clock for testing)
- **Screensaver-proofing:** cat detects display-off / screen-sleep state via QApplication.primaryScreen(). Cat goes to sleep (faster energy recovery), resumes on display-on
- **Installer:** PyInstaller single-file build. NSIS wrapper for Windows (or existing scheduled task approach). Verify: survives reboot, no startup crash
- **README update:** architecture overview, phase summaries, config flags, commissioning notes for future sprite work

### Exit Criteria (Lens-verified)
- [ ] All 11 CI/CD gates passing (pre-commit, PR-level, nightly)
- [ ] 24-hour endurance test: stable FPS (±2 FPS from start), memory < 50MB, no stuck sequences
- [ ] Settings panel functional: size changes cat immediately, personality visible, memory reset works
- [ ] Installer tested on clean gk-pc instance: install → reboot → cat starts
- [ ] README updated: architecture, config flags, sprite commissioner brief template