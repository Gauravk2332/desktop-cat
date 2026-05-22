# MASTER PLAN DRAFT — Desktop Cat Overhaul

> Based on 6 research/design/architecture docs totaling 4,451 lines.
> Targets: PyQt6 overlay, Windows 11, 33fps tick, single-process.
> Cat: Orange mackerel tabby, ~200-250px tall, semi-realistic painterly style.
> AI: DeepSeek V4 Flash via clowbot proxy (optional novelty layer).

---

## Phase 0: Foundation — Sprite Pipeline & Bigger Cat
**Duration:** 2-3 dev sessions
**Dependencies:** None (new code, clean layer)

### Deliverables
- Blender rig setup — orange tabby model with mackerel stripe textures
- Python sprite pipeline — render script that exports PNG frames → stitches spritesheets
- New asset folder structure (`assets/sprites/`)
- QPainter → QPixmap swap in render loop — cat drawn from pre-rendered sprite instead of geometry
- Cat scaled to ~200px height (configurable)
- Drop shadow (simple ellipse under cat)
- One working pose: sit (breathing animation, 3-4 frames)

### Key Decisions
- **Format:** PNG horizontal strip spritesheets (not SVG, not QPainter procedural)
- **Pipeline:** Blender 3D → Python render script → PIL stitch → .png file
- **Fallback:** Old QPainter cat still works if sprites missing (graceful degradation)
- **Shortcut:** Commission first spritesheet on Fiverr ($30-50) or use Blender + free cat model

### Exit Criteria
- [ ] Cat shown on screen at 200px+ from spritesheet
- [ ] Breathing animation loop plays smoothly at 33fps
- [ ] Drop shadow visible under cat
- [ ] Scale slider changes cat size in real-time
- [ ] No performance regression (still 33fps)

---

## Phase 1: Visual Overhaul — All Poses & Transitions
**Duration:** 3-5 dev sessions
**Dependencies:** Phase 0 complete (pipeline + spritesheet format)

### Deliverables
- All spritesheets rendered:
  - Sit (4 frames, breathing)
  - Walk (12 frames, full gait cycle)
  - Trot (8 frames)
  - Sleep curled (6 frames, breathing)
  - Sleep sprawl (6 frames, breathing)
  - Loaf (4 frames)
  - Groom (12 frames, loopable, paw-lick cycle)
  - Stretch (8 frames, one-shot — front stretch)
  - Yawn (4 frames, one-shot)
  - Alert (2 frames, ears up)
  - Eat (6 frames, head down/chewing)
  - Play bat (4 frames, paw swipe)
- Transition sheets (6 frames each):
  - sit→walk, walk→sit, sit→lie, lie→sit, sit→groom, groom→sit
- Eye overlay system:
  - Open (2 variants: normal, dilated)
  - Half-closed (relaxed)
  - Closed (sleeping)
  - Slow-blink (4-frame animation: open → half → closed → half → open)
  - Wide (alert/fear)
- Tail independent animation system:
  - 5 pre-baked tail sprites (relaxed sway, upright, low, puffed, wrapped)
  - Tail composite overlay (body sprite + tail sprite)
- Body bob/tilt during walk (pre-baked into walk frames, not calculated)
- Crossfade transitions between states (200ms, InOutCubic)
- Color palette shift for night mode (slightly cooler tones)

### Exit Criteria
- [ ] All 12+ poses renderable with correct sprites
- [ ] Walk animation shows smooth 12-frame 4-leg gait
- [ ] Transitions between states crossfade smoothly
- [ ] Eyes blink naturally every 10-20s (independent of body state)
- [ ] Tail moves independently during idle states (not frozen)
- [ ] Night palette shift works
- [ ] All animations loop/ping-pong correctly

---

## Phase 2: Behavior Engine — Circadian Rhythm & Needs Rewrite
**Duration:** 3-5 dev sessions
**Dependencies:** Phase 1 visual system stable (sprites in place)

### Deliverables
- **CircadianClock class** (core/circadian.py):
  - 24-hour phase tracking: DAWN, MORNING, MIDDAY, DUSK, EVENING, NIGHT, DEEP_NIGHT
  - Phase change events broadcast to BehaviorPlanner
  - Phase-aware energy curve (sinusoidal, not linear)
  - Real-time-of-day sync (PC clock)
- **Needs system rewrite** (behavior/needs.py):
  - Hunger: 0-100, decays at rate × circadian phase (faster at dawn/dusk, slower at night)
  - Energy: 0-100, recovers during sleep at rate × circadian phase
  - Boredom: 0-100, decays during play/exploration, rises during inactivity
  - Social: 0-100, new need — desire for owner interaction
  - Comfort: 0-100, new need — affected by warm spots, soft surfaces
  - Elimination pressure: 0-100, new need — builds over hours, triggers litter box visit
- **BehaviorPlanner class** (behavior/planner.py):
  - Decides cat's high-level goal based on needs + circadian phase + personality
  - Selects behavioral sequences (not individual actions)
  - Monitors sequence progress and handles interruptions
- **Behavior Sequences** (behavior/sequences.py):
  - `MorningWake`: sleep → stretch → yawn → sit → look around → meow
  - `HungerWalk`: sit → stand → walk to food bowl → eat → groom
  - `PlayBurst`: idle → stalk → pounce → bat → bunny-kick → groom
  - `GroomSession`: sit → lift paw → lick paw → rub face → lick shoulder → lick flank → lick tail → shake
  - `SleepSequence`: sit → lie down → curl → close eyes → deep sleep → REM twitch
  - `Greeting`: walk toward user → sit → meow → head bunt (toward user location)
  - `WindowWatch`: walk to window → sit → watch → chirp → tail tip twitch
  - `Patrol`: walk along territory path → pause → sniff → continue
- **LLM downgrade**: Only called when BehaviorPlanner hits uncertainty (novel situation, conflicting needs). ~90% of decisions are rule-driven.

### Exit Criteria
- [ ] Circadian clock runs and drives energy curve (peak at 6AM/6PM, trough at midnight-3PM)
- [ ] Needs interact naturally (hungry + dawn = seek food; tired + night = seek sleep)
- [ ] Sequences play through fully (stretch → walk → sit, not random action cycling)
- [ ] Sequences can be interrupted (user clicks → cat looks at cursor → resumes or changes plan)
- [ ] LLM only fires on novel situations (verified by log)

---

## Phase 3: Memory, Territory & Personality
**Duration:** 3-5 dev sessions
**Dependencies:** Phase 2 Behavior Engine running

### Deliverables
- **Short-term memory** (behavior/memory_short.py):
  - Dict-based: last 20 events with timestamps
  - What happened, where, how long ago
  - Used by BehaviorPlanner for immediate context
- **Long-term memory** (behavior/memory_long.py):
  - SQLite file at `data/cat_memory.db`
  - Tables: `favorite_spots`, `owner_schedule`, `interactions`, `territory_marks`
  - Favorite spots learned from repeated behavior (if cat sits at window 3 days in a row at same time → remembers)
  - Owner schedule learned from observation (user active at 8AM → cat starts being active at 7:45AM)
- **Personality system** (behavior/personality.py):
  - 8 trait dimensions (boldness, playfulness, affection, laziness, vocalness, chattering, skittishness, territoriality)
  - Each trait: 0-10 scale, time-series of changes
  - Personality delta after each user interaction (play +1 playfulness after 10 sessions)
  - Slow drift toward archetype (orange tabby defaults)
  - Triggers different behavior probabilities per personality type
- **Territory system** (behavior/territory.py):
  - Screen split into zones: sleeping zone, play zone, observation zone, food zone
  - Cat marks territory by visiting → frequency decays over time → re-marking needed
  - Favorite spots emerge organically from repeated visits
- **Learning system**: 
  - User schedule detection (when does user type? when idle? when on calls?)
  - Event association (user opens Notepad → cat may sleep nearby; user opens game → cat may play)

### Exit Criteria
- [ ] Cat "remembers" favorite spot (returns to same window corner after sleep)
- [ ] Cat shows schedule awareness (more active before user's typical wake time)
- [ ] Personality feels distinct after 3+ days (shy cat avoids cursor, bold cat approaches)
- [ ] Territory marks decay and refresh naturally
- [ ] Long-term memory survives restart (loads from SQLite)

---

## Phase 4: LLM Intelligence Layer
**Duration:** 2-3 dev sessions
**Dependencies:** Phase 3 complete (memory + personality)

### Deliverables
- Smart context builder (behavior/context.py):
  - Builds richer context: current time, phase, needs, recent events, personality state, user activity
  - Only called when BehaviorPlanner decides "need creative input"
- LLM call triggers:
  - Novel user action (first time doing something)
  - Conflicting needs (hungry but playful — what to prioritize?)
  - Social situation (user returns after long absence)
  - Unusual time/event (middle of night disturbance)
  - Cat "thinking" visible (head tilt, ear swivel → decision moment)
- LLM output parsed into behavioral intent, not raw action:
  - "The cat wants attention but is sleepy" → partial wake, meow, return to sleep
  - Not "MEOW greeting" or "WALK left"
- Fallback frequency logging (how often does LLM get invoked?)

### Exit Criteria
- [ ] LLM invoked <10% of decisions (90% rule-driven)
- [ ] When invoked, output is natural (not robotic "MEOW greeting" actions)
- [ ] Cat appears to "think" for a moment before acting on LLM suggestions

---

## Phase 5: Sound Polish & Micro-Details
**Duration:** 2-3 dev sessions
**Dependencies:** Phase 2+ (all behavior states stable)

### Deliverables
- Sound system rewrite to match new behavior states
- Sounds triggered by sequences, not random (groom → purr; stretch → quiet hum; play → chirp)
- 5+ new WAVs: meow_welcome, meow_demand, purr_deep, chirp_excited, chatter
- Micro-details:
  - Ear twitch animation (independent timer, random 3-10s)
  - Tail tip flick during idle (independent timer)
  - Slow blink on user proximity
  - Head tilt on new object in environment
  - Whisker forward on curiosity
  - Sleep REM twitches (eye/whisker movement during deep sleep)
- Weather response (thunder → hide; sunny → window watch colder palette shift)

### Exit Criteria
- [ ] Sounds fire from sequences, not RNG
- [ ] Micro-details visible and feel organic
- [ ] Cat reacts to weather appropriately

---

## Phase 6: Settings UI, Polish & Ship
**Duration:** 2-3 dev sessions
**Dependencies:** All prior phases

### Deliverables
- Settings panel rewrite: size slider, personality display, memory wipe button, time acceleration (debug)
- Screensaver-proofing (cat aware of screen-off state)
- Performance optimization pass
- Installer update
- Documentation update

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Sprite generation takes too long | Medium | High | Commission first sheet; Blender free model as backup |
| Memory system over-complicates simple cat | Medium | Medium | Start with JSON persistence; upgrade to SQLite only if needed |
| LLM still used too often | Low | Medium | Tune confidence thresholds; give BehaviorPlanner more rules |
| PyQt6 can't do smooth crossfade | Low | High | Test early in Phase 0; fallback to instant swap |
| Cat feels less alive during pure rule mode | Medium | Medium | Add noise/variation parameters; personality ensures variety |
| Windows transparent overlay performance | Low | Low | Pre-render, cache, no per-frame computation |

---

## Master Timeline Estimate

| Phase | Dev Sessions | Calendar (weekends + evenings) |
|-------|-------------|-------------------------------|
| 0 | 2-3 | 1 week |
| 1 | 3-5 | 1-2 weeks |
| 2 | 3-5 | 1-2 weeks |
| 3 | 3-5 | 1-2 weeks |
| 4 | 2-3 | 1 week |
| 5 | 2-3 | 1 week |
| 6 | 2-3 | 1 week |
| **Total** | **18-27** | **2-3 months approx** |

> **Shortcuts available:** Skip Phase 4 (LLM layer) for MVP. Phase 3 (memory) can be simplified to JSON-only. Phase 0 (commission spritesheet) can save 2-3 sessions.
