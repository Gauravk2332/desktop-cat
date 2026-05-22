# VERTICAL_SLICE_MAP.md — Sit → Eat → Groom → Sit Feasibility

**Source:** MASTER_PLAN_FINAL.md Vertical Slice Milestone (Pico)
**Target sequence:** Sit (idle) → hunger > 60 → walk to food bowl → eat → groom → sit

---

## 1. Minimum Sprites Required

### Phase 0 Sprite Set (3 poses = 20 frames)

| Pose | Frames | Purpose in Vertical Slice |
|------|--------|--------------------------|
| Sit-breathing | 4 (loop) | Idle state, start and end of the sequence |
| Walk | 12 (loop) | Cat crosses screen to food bowl zone |
| Eat | 6 (loop) | Head-down eating at food bowl |

**Total: 22 frames across 3 spritesheets** — this is the Phase 0 deliverable from the master plan. The vertical slice only needs these 3 poses.

### What's NOT needed for the vertical slice

| Pose | Frames | Deferred To | Reason |
|------|--------|-------------|--------|
| Loaf | 4 | Phase 1 | 70% rule variant of sit — not in slice |
| Trot | 8 | Phase 1 | Not needed for short distance to food |
| Sleep (curl + sprawl) | 12 | Phase 1 | Not in slice |
| Groom | 12 | Phase 2 | Part of slice END state — cat returns to sit, groom loop plays BEFORE Phase 2 |
| Stretch | 8 | Phase 1 | Not in slice |
| Yawn | 4 | Phase 1 | Not in slice |
| Alert | 2 static | Phase 1 | Not in slice |
| Transitions (6 types) | 36 | Phase 1 | Slice can use simple 200ms crossfade instead |
| Tail overlays | 6 | Phase 1 | Not needed — tail follows body |
| Ear overlays | 6 | Phase 1 | Not needed — ears on main sprites |
| Eye overlays | 7 tiles | Phase 1 | Use baked eye state for slice |

### Groom at Sequence End

The vertical slice says: eat → groom → sit. Groom is listed in Phase 1 of the master plan (12 frames, Phase 1 deliverable). For the vertical slice:

**Options for groom at end of slice:**
1. **Defer groom sprite** — End slice at eating complete → sit. Sequence shows: eat → sit (groom doesn't play yet). Groom gets added in Phase 1. **Recommended.**
2. **Add groom to Phase 0** — Expand to 4 poses (22+12=34 frames). Adds $10-15 to Fiverr cost and 1-2 days. Acceptable but unnecessary for vertical validation.
3. **Use shortened groom** — Commission just 4-frame groom loop instead of full 12. Loses smoothness.

**Decision:** End vertical slice at eat → sit. Groom is Phase 1. The slice validates the critical path: **needs detection → navigation → sequence execution → state return**.

---

## 2. Minimum Code Required

### Must Exist for Vertical Slice (Build in Phase 0)

| Module | What's Needed | Complexity | Effort |
|--------|--------------|------------|--------|
| **Sprite pipeline** | Load PNG spritesheet → slice into QPixmap frames → cache → blit | Medium | Coder: 1 session |
| **Render loop** | 33fps tick, frame advance per animation, loop/bounce modes | Medium | Coder: 1 session |
| **Crossfade** | 200ms InOutCubic between state changes | Low | Coder: 2hr |
| **Screen zones** | Predefined zones (food bowl = right 20% of screen) | Low | Coder: 30min |
| **Simple walk navigation** | Move cat sprite from current X → food zone X at walk speed | Medium | Coder: 2hr |
| **Needs system (MINIMAL)** | Hunger: 0-100, decays over time, triggers when > 60 | Low | Coder: 1hr |
| **Sequence framework (MINIMAL)** | HungerWalk sequence: detect trigger → walk to zone → eat animation → return | Medium | Coder: 2-3hr |
| **State machine (MINIMAL)** | States: IDLE, WALKING_TO_FOOD, EATING, RETURNING_TO_IDLE | Low | Coder: 1hr |

### Should Exist but Can Be Stubbed

| Module | Stub Approach | When Real |
|--------|--------------|-----------|
| **Full needs system** (all 5 needs) | Only hunger implemented. Others at defaults. | Phase 2 |
| **Behavior planner** | Simple if-statement: if hunger > 60 → start HungerWalk. Plenty for slice. | Phase 2 |
| **Personality** | Hardcoded values. | Phase 2 |
| **Memory** | No persistence needed. | Phase 2 |
| **Circadian clock** | Use system clock or fixed "daytime". | Phase 2 |
| **Soul layer** | No delays, no habituation. | Phase 2 |
| **LLM integration** | No LLM calls. | Phase 4 |

### Not Needed at All for Vertical Slice

| Feature | Why Skip |
|---------|----------|
| 12 poses | Only need 3 for slice |
| Eye overlay system | Use baked eye state |
| Ear overlays | Use baked ear state |
| Tail overlays | Tail follows body on sprites |
| Sound system | No sound in slice |
| Weather response | Not needed |
| LOD / size scaling | Fixed size |
| Night mode | Not needed |
| Settings panel | Not needed |
| CI/CD gates | Defer to Phase 6 |
| Installer | Defer to Phase 6 |
| Persistence (JSON) | Can skip — hunger resets on restart |

---

## 3. Phase Mapping: What Goes Where

### Phase 0 (This Slice, ~1 week)

**Sprites:**
- [x] Sit-breathing (4 frames)
- [x] Walk (12 frames)
- [x] Eat (6 frames)
- [ ] ~~Groom~~ → **Deferred to Phase 1**

**Code:**
- [x] PyQt6 transparent overlay smoke test (Day 1 Hour 1 — critical gate)
- [x] PNG spritesheet loader + QPixmap cache
- [x] 33fps render loop with animation frame advance
- [x] Crossfade transition (200ms InOutCubic)
- [x] Cat sprite blit at configurable size (~200px)
- [x] Drop shadow render
- [x] Fallback to QPainter cat if sprites missing
- [x] 6 predefined screen zones (food bowl in zone 6)
- [x] Basic walk navigation (move X → target X)
- [x] Simple hunger need (0-100, decay timer)
- [x] Min state machine (IDLE → WALK → EAT → IDLE)
- [x] Sequence runner (HungerWalk sequence)
- [ ] ~~Sprite validation script~~ → **Add to Phase 0** (already in master plan deliverable B)

### Phase 2 Addition (After Slice Validates)

**Code:**
- [ ] Full needs system (energy, boredom, social, elimination)
- [ ] Circadian clock (dawn/dusk curves)
- [ ] Personality system (5 traits)
- [ ] Memory (short-term deque + long-term JSON)
- [ ] Full behavior planner (5-layer priority)
- [ ] Remaining sequences (see master plan §4F)
- [ ] Soul layer (delayed reactions, habituation, contemplation)
- [ ] Feature flags per system

**Sprites (Phase 1, between 0 and 2):**
- [ ] All remaining 9 poses (loaf, sleep ×2, groom, stretch, yawn, alert, trot)
- [ ] 6 transition sheets
- [ ] Tail overlays, ear overlays, eye tiles

### Deferred (Phase 3+)

| Feature | Phase | Why Deferred |
|---------|-------|-------------|
| Learning (favorite spots) | 3 | Needs memory system first |
| Mood persistence | 3 | Needs memory + personality |
| Social referencing | 3 | Nice-to-have |
| Contagious behavior | 3 | Nice-to-have |
| Sleep REM twitching | 3 | Nice-to-have |
| LLM integration | 4 | Needs full behavior system |
| Sound (WAVs) | 5 | Can add anytime |
| Settings panel | 6 | Nice-to-have |
| CI/CD gates | 6 | Needed before "ship" |
| Installer | 6 | Needed before "ship" |

---

## 4. Vertical Slice: Pass/Fail Criteria

### Pass Conditions (All Must Be True)

- [ ] Transparent overlay renders on gk-pc without flicker
- [ ] Sprite loads and displays cat at ~200px height
- [ ] Sit-breathing loop plays smoothly at 33fps
- [ ] When hunger > 60: cat transitions (crossfade) from sit → walks to food zone
- [ ] Cat reaches food zone X-position and eat animation plays
- [ ] After eating sequence completes, cat returns to sit state
- [ ] Drop shadow visible
- [ ] All QPixmap blits < 30ms per frame
- [ ] Missing sprites → QPainter fallback cat (no crash)

### Fail Scenarios

| Failure | Impact | Recovery |
|---------|--------|----------|
| Transparent overlay broken | CRITICAL | Investigate Direct2D/Skia. Do NOT proceed. |
| Walk navigation doesn't reach zone | HIGH | Debug X-position calculation |
| Eating animation doesn't trigger after walk | HIGH | Debug state machine transition |
| Frame timing > 30ms | HIGH | Reduce frame resolution or optimize blit |
| Hunger decay not triggering walk | MEDIUM | Debug need threshold check |
| Crossfade leaves artifacts | LOW | Fallback to instant swap |

---

## 5. Code Structure for the Slice

```
desktop-cat/
├── main.py                   # PyQt6 app entry, transparent overlay, render loop
├── sprites/
│   ├── loader.py             # PNG spritesheet → QPixmap cache
│   ├── renderer.py           # Frame advance, blit to widget
│   └── manifest.json         # Frame counts, FPS, eye_rects
├── navigation/
│   ├── zones.py              # 6 predefined screen zones
│   └── walk.py               # Move cat X across screen
├── behavior/
│   ├── needs.py              # MINIMAL: hunger only
│   ├── state_machine.py      # IDLE → WALK → EAT → IDLE
│   └── sequences.py          # HungerWalk sequence steps
├── art/
│   └── spritesheet.png       # Single commissioned sheet (Phase 0)
└── scripts/
    ├── stitch_frames.py      # PIL stitch script (for Blender if used)
    └── validate_frames.py    # Frame size validation
```

---

## 6. What the Vertical Slice PROVES

When the vertical slice works end-to-end, it validates:

1. **Sprite pipeline** — PNG spritesheets load, cache, render at 33fps
2. **Screen zones** — Cat can navigate to a predefined target zone
3. **Need-driven behavior** — A need (hunger) triggers a behavioral sequence
4. **Sequence execution** — Multi-step sequence plays through (walk → eat → return)
5. **State machine** — Clean transitions between states
6. **Performance** — All blits within 30ms budget
7. **Transparent overlay** — Core infrastructure works

**What it does NOT prove** (and doesn't need to for Phase 0):
- Personality-driven behavior
- Complex multi-sequence selection
- Circadian rhythm effects
- Memory/persistence
- Soul layer (delays, habituation)
- All 12 poses

**Bottom line:** If the vertical slice works, the architecture is sound. Everything else is layering on top. If the vertical slice fails, fix it before scaling.
