# PHASE 3 — Engine Integration Plan

## Goal
Wire Phase 2 modules (CircadianClock, Personality, Memory, Sequences, Planner, Soul Layer) into the engine update loop so the cat acts on its internal state.

## Architecture

```
_on_tick()
  ├─ CircadianClock.update(dt) → energy_multiplier
  ├─ Needs.update(dt, cat, state) ← uses circadian.energy_multiplier
  ├─ BehaviorPlanner.update() → action (replaces 90% of old state machine)
  ├─ _execute_planner_action(cat, action, dt) → state transitions
  ├─ Memory.record_event() → tracks zone visits, interactions
  ├─ Habituation.update(dt) → decay counters
  ├─ [old systems: breathe, weather, sound, animation, toys, save, repaint]
```

## Package Tasks

### 1. Coder: Wire planner into engine + needs circadian modulation
Files: `core/engine.py`, `behavior/needs.py`, `tests/test_engine_planner.py`
- Add `BehaviorPlanner._initialize()` with CircadianClock, Personality, Memory, Habituation, Reactions
- Add `_execute_planner_action(cat, action, dt)` — maps 12 planner actions to engine state
- Replace agent decision block with planner as primary decider
- Modify `behavior/needs.update()` to accept `circadian.energy_multiplier` for modulated decay
- Tests: planner action → state transition mapping (all 12 actions)

### 2. Muse: Wire Personality + Memory + Soul Layer into interaction flow
Files: `core/engine.py`, `tests/test_engine_soul.py`
- Memory initialization per cat (`CatMemory(cat_id)`)
- Hook `_check_mouse()` → `memory.record_interaction()` on pet/click
- Hook habituation: `response_level = habituation.get_response_level("click")` — skip reaction if ignore level
- Hook reactions: pre-reaction ear flick before full response
- Personality trait affects approach walk probability
- Tests: interaction chain → reaction delay → habituation escalation → ignore

### 3. Me: Integration test suite + final wiring
- Write `tests/test_engine_phase3.py` — end-to-end integration suite
  - Full tick cycle: circadian advance → needs update → planner decision → state change
  - Interaction chain: mouse proximity → habituation → reaction delay → response
  - Sequence running: planner picks HungerWalk → steps advance → completion
  - Personality bias: bold cat vs shy cat response times
  - Memory zone tracking: cat walks → zone visits counted
  - Circadian modulation: energy multiplier affects need decay
  - Edge cases: null circadian, empty memory, rapid interactions, system sleep resume
- Final integration pass: verify 0 regressions (must stay at 570+)

## Sequence
1. Write integration tests (me)
2. Coder: planner wiring + needs mod + tests
3. Muse: soul wiring + tests
4. Me: final integration → run full suite → fix issues
5. Lens: review changes (edge cases, safety)
6. Deploy to gk-pc → verify cat runs
