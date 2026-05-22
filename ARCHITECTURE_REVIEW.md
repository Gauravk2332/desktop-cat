# Architecture Review: desktop-cat

Reviewed sources: `behavior/transitions.py`, `behavior/needs.py`, `core/engine.py`, `core/state.py`, `core/api.py`, `core/window.py`, `config.py`, `cat/home.py`, `animation/breathe.py`, `tests/test_state_machine.py`

---

## 1. State Machine Soundness

**Finding → Impact → Recommendation**

**1a. Field sleep from low energy is structurally unreachable from SIT**

`_update_sit` checks energy < 40 (HOME_ENERGY_THRESHOLD) at step 1 and unconditionally transitions to GO_HOME. Step 5 also checks energy < 40 for field SLEEP — but step 1 catches every low-energy case first. The energy < 40 → SLEEP path in step 5 is dead code; it can never be reached from SIT.

- **Impact**: Medium. The field-sleep-on-low-energy mechanic doesn't exist — the cat always goes home when tired. Field sleep is only reachable via boredom > 90. A cat with 0 boredom and draining energy will forever GO_HOME, never sleep in the field.
- **Recommendation**: Either remove the dead field-sleep check (step 5) since GO_HOME subsumes it, or gate step 1 with `not state.at_home` and a cooldown so a cat that *can't* go home (e.g., cooldown) falls through to field sleep.

**1b. GO_HOME can bounce to SLEEP on the next tick when cat is already at home**

If state.energy < 40 while `state.at_home=True` and `home_linger > 0`, step 1 triggers `_enter_go_home(state)`. The next tick, `_update_go_home` finds remaining ≤ HOME_TOLERANCE (cat_x == bed_x) and immediately transitions to SLEEP at home.

- **Impact**: Low. The wasted tick is invisible to the user.
- **Recommendation**: Guard step 1 with `not state.at_home` or `not (state.at_home and state.home_linger > 0)`.

**1c. WANDER→GO_HOME only checks energy, not boredom**

`_update_wander` transitions to GO_HOME when `energy < HOME_ENERGY_THRESHOLD`. If the cat wanders due to high boredom and is still bored when wander ends, it sits (via timer expiry). Boredom-driven GO_HOME is only checked from SIT.

- **Impact**: Low. One-tick delay.
- **Recommendation**: Optional — add a boredom check to `_update_wander` for consistency.

---

## 2. Navigation Logic

**Finding → Impact → Recommendation**

**2a. GO_HOME always sets `facing=True` — safe because cat is always left of bed**

The bed is at `screen_width - HOME_PADDING_RIGHT - HOME_BED_RX` (≈1863 on 1920px). WALK clamps at `screen_width - 80 = 1840`. WANDER clamps at `screen_width - WANDER_OFFSET = 1860`. So the cat is always left of the bed. `facing=True` is correct.

- **Impact**: None for current layout.
- **Recommendation**: If bed position becomes configurable, add `state.facing = bed_x > state.cat_x`.

---

## 3. Config Balance

**Finding → Impact → Recommendation**

**3a. Energy balance feels right for a desktop pet**

Sit drain: 0.003/s → ~5.5h from 100→0. Sleep recharge: 0.08/s → ~250s from 40→60. Cadence: sit for 1-2h → wander 30s → sit → 3-4h → home nap 5min → repeat.

- **Impact**: Good. Feels alive without hyperactivity.
- **Recommendation**: None.

**3b. Hunger has no consequence at max**

Hunger rises to 100 in ~9h from 0. No penalty at max — no behavior change.

- **Impact**: Low. Decorative stat only.
- **Recommendation**: Add subtle effect when hungry: slower walk, more sleep, or a pleading expression.

---

## 4. Mouse Interaction

**Finding → Impact → Recommendation**

**4a. 3% per tick at 50ms = ~46%/s approach walk probability**

`random.random() < 0.03` when dist < 80px and SIT. At 20 ticks/s: `1 - 0.97^20 ≈ 46%`.

- **Impact**: Medium-High. Cat feels "sticky" when mouse is near.
- **Recommendation**: Reduce to 0.01/tick or add a cooldown after reaching cursor.

---

## 5. Thread Safety

**Finding → Impact → Recommendation**

**5a. Queue-based API is thread-safe**

`queue.Queue` is internally locked. Engine consumes in main tick. API thread only pushes.

- **Impact**: None. Correct design.
- **Recommendation**: None.

**5b. State mutation confined to Engine tick**

API thread never touches CatState directly — only pushes to Queue.

- **Impact**: None.
- **Recommendation**: None.

---

## 6. Circadian Curves

**Finding → Impact → Recommendation**

**6a. datetime.now().hour per tick is negligible**

~1μs/call at 20 calls/s = 0.002% CPU.

- **Impact**: None.
- **Recommendation**: Leave as-is.

---

## 7. Persistence

**Finding → Impact → Recommendation**

**7a. 30s save interval is reasonable**

Max 30s state loss on crash. Energy/hunger drift by fractions — unnoticeable.

- **Impact**: Low.
- **Recommendation**: Keep 30s. More frequent saves just adds SSD writes.

---

## Summary: Recommended Changes

| # | Issue | Severity | Action |
|---|-------|----------|--------|
| 1a | Dead code: field-sleep from low energy unreachable | Medium | Remove or reorder dead branch |
| 1b | SIT→GO_HOME→SLEEP bounce when already at home | Low | Guard with `not state.at_home` |
| 3b | Hunger has no consequence | Low | Add subtle visual feedback |
| 4a | Approach walk probability high (46%/s) | Medium | Reduce to 0.01/tick |

**No critical issues found. Architecture is sound.**
