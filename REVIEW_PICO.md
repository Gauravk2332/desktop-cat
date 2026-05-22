# Pico's POV: Desktop Cat Overhaul — Master Plan Review

**Plan:** 6 phases, 18-27 dev sessions, ~2-3 months
**Sources reviewed:** MASTER_PLAN_DRAFT.md (1 file), TECH_ARCHITECTURE_REDESIGN.md (~1.5K lines), TECH_SPRITE_AND_RENDER.md (~400 lines), ARCHITECTURE_REVIEW.md (existing codebase analysis)

---

## 1. Phasing: Mostly correct, one reorder recommended

**Current order:** Foundation → Visual → Behavior → Memory → LLM → Sound → Polish

The overall sequence is logical: sprites before animation, animation before behavior, behavior before intelligence. However:

**Phase 2 (Behavior Engine) and Phase 3 (Memory/Territory) are interdependent and should be merged or run in tighter parallel.** The BehaviorPlanner needs memory to make informed decisions (remembering favorite spots, owner schedule). Building sequences without memory means the cat acts on immediate needs only — which is exactly what the plan aims to fix. If you build Phase 3 first (data layer), Phase 2 can use it immediately and you avoid a "v1 that gets rewritten in v2" cycle.

**Recommended reorder:**
- Phase 0: Foundation (sprites) — stay as-is
- Phase 1: Visual Overhaul — stay as-is
- **Phase 2+3 merged: Behavior + Memory** (4-7 sessions, not 6-10) — build the data layer first (circadian, personality, memory), then the planner that consumes it

This saves at least 2 sessions of rework.

**Phase 5 (Sound)** could also be folded into Phase 1-2 as incremental additions rather than a separate phase. Sounds are married to behavior states — adding them later means retrofitting. Better to wire basic sound triggers during sequence development.

## 2. Missing Research Areas (will cause problems if unaddressed)

| Area | Severity | Why It Matters |
|------|----------|----------------|
| **Error/corruption handling for sprite assets** | Medium | If a spritesheet PNG is corrupted or missing, the render pipeline could crash silently or draw garbage. The plan mentions graceful fallback to QPainter cat but no explicit error handling in sprite loading. |
| **Taskbar/DWM collision** | Medium | The cat walks on screen. On Windows 11, the taskbar is part of the DWM composition. Cat needs to know taskbar bounds and avoid them (QScreen.availableGeometry() is mentioned but no explicit taskbar-avoidance logic in walk/navigation). |
| **Multi-monitor behavior** | Low-Medium | The plan says "create overlay on primary screen or track cursor." But what happens when the user drags a window across monitors? Does the cat teleport? Walk across the gap? Stay on primary? This needs a decision before Phase 2. |
| **Performance under GPU load (gaming)** | Medium | The plan targets 33fps. If the user is gaming at 144fps+, the overlay competes for GPU composition. PyQt6 QPainter with WA_TranslucentBackground uses DWM for composition — if DWM is throttled, the cat stutters. The tech doc doesn't address this. |
| **No testing strategy** | Low-Medium | The plan has no mention of automated tests. The behavior engine is complex (5 priority layers, sequences, circadian, personality, memory). Without tests, regressions will be caught only visually. At minimum: planner unit tests, sequence manager tests, memory CRUD tests. |
| **Battery/power management** | Low | Cat overlay keeps the GPU composition pipeline active. On a laptop, this prevents the dGPU from idling. A subtle but real battery drain. |
| **Windows sleep/hibernate resume** | Low | Mentioned briefly ("override changeEvent to reload textures"). But memory state, circadian clock, and sequence cooldowns also need to handle clock discontinuities on resume. |

## 3. Risk Assessment: Accurate but incomplete

**Existing risks (from plan):**

| Risk | Verdict |
|------|---------|
| Sprite generation takes too long | Correct. Mitigation is solid (commission first sheet). |
| Memory system over-complicates | Correct. JSON-first escape hatch is good. |
| LLM still used too often | Correct. 30s cooldown + priority chain handles this. |
| PyQt6 can't do smooth crossfade | **Underestimated.** Impact should be Medium, not Low. QPainter transparent overlay crossfade on Windows can have compositing glitches (white flash, transparency corruption). Test in Phase 0, not Phase 1. |
| Cat feels less alive in pure rule mode | Correct assessment. Noise/variation/personality is the right answer. |
| Windows transparent overlay performance | Correct. Pre-rendered sprites make this trivial. |

**Missing risks:**

| Missing Risk | Probability | Impact | Suggested Mitigation |
|-------------|------------|--------|---------------------|
| Blender pipeline produces inconsistent frame dimensions/aspect ratios | Medium | Medium | Add validation step in stitch script: assert all frames are same size before composing |
| Windows 11 DPI scaling causes sprite misalignment (especially mixed-DPI multi-monitor) | Medium | Medium | Test on actual 150% DPI display early in Phase 0; pixel-snap coordinates |
| SQLite write contention on main thread (even WAL mode has write locks) | Low | Medium | Offload writes to worker thread or batch writes at 5-30s intervals (current 30s save is fine) |
| LLM proxy (clowbot) unavailable → cat loses novelty | Low | Medium | Cat should behave identically without LLM (rule-based fallback must be complete, not just "partial"). The plan assumes this implicitly but doesn't test it. |
| Sequence manager blocks on LLM call | Low | High | Planner explicitly returns None from _ask_llm if unavailable, but this needs enforcement: LLM call must have a timeout (2s max, default to None) |

## 4. Timeline Estimate: Realistic but Phase 1 is tight

| Phase | Estimated | Pico's Assessment |
|-------|-----------|-------------------|
| 0 — Foundation | 2-3 sessions | **Correct.** Well-scoped. |
| 1 — Visual Overhaul | 3-5 sessions | **Slightly under.** 12+ poses, 6 transition sheets, eye overlay, tail system, crossfade, night palette. Realistically 4-6 sessions. The pose count doubles the animation workload. |
| 2 — Behavior Engine | 3-5 sessions | **Tight.** Circadian clock + needs rewrite + planner + sequences + behavioral sequences + LLM integration. Minimally 4-6 sessions if memory is built first (see reorder above). |
| 3 — Memory & Territory | 3-5 sessions | **Slightly over if merged with Phase 2** (saves 1-2 sessions from shared planner work). Standalone: correct. |
| 4 — LLM Layer | 2-3 sessions | **Correct.** Mostly integration work. |
| 5 — Sound & Polish | 2-3 sessions | **Correct if folded** into earlier phases (sounds during sequence dev). Standalone: correct. |
| 6 — Settings & Ship | 2-3 sessions | **Correct.** |
| **Total** | **18-27 sessions** | **20-30 sessions** (leaning toward upper bound) |

**Calendar estimate:** 2-3 months is realistic for weekends+evenings. 3 months is safer given the behavioral complexity.

## 5. Shortcuts & Optimizations (with quality preserved)

**Already identified in plan:**
- Commission first spritesheet ($30-50 saves 2-3 sessions)
- Skip LLM layer for MVP
- Simplify memory to JSON before SQLite
- Feature flags for safe rollout

**Additional recommendations:**

1. **Placeholder sprites for Phase 2 development.** Use colored rectangles or silhouettes for all poses while building behavior. Test the planner, sequences, and circadian clock before the art is ready. This decouples art creation from behavior engineering.

2. **Start with 5-6 poses, not 12+.** For the first behavior-visible release: sit, walk, sleep, loaf, groom, stretch. Add the rest (trot, yawn, alert, eat, play bat) in a Phase 1.5. Reduces sprite workload by ~50% while still demonstrating the full behavior engine.

3. **Eye overlay can start as procedural circles.** A colored ellipse with a black pupil dot takes 5 minutes in QPainter. It validates the overlay layer position/offset without waiting for eye sprites.

4. **Move sound wiring into Phase 1-2.** Instead of a separate sound phase, attach sound triggers directly to Sequence steps during development. "Knead → purr" is a one-liner in SequenceStep. This eliminates Phase 5 as a separate phase.

5. **Per-phase automated tests.** Write planner unit tests during Phase 2 (before integration makes debugging harder). High-leverage: test circadian phase transitions, sequence priority resolution, personality modifier application, and memory save/load cycles.

6. **Vertical slice before horizontal.** Instead of building all systems at 50% completion, get one full behavior loop working end-to-end in Phase 1: sit → hunger → walk to bowl → eat → groom → sit. This validates the entire stack (sprites → animation → planner → memory) before scaling to all 12 poses.

## 6. Overall Approval: **Approve with Changes**

**The plan is well-researched, architecturally sound, and the research docs are thorough.** The foundation in the existing architecture review (which found no critical issues) gives confidence that the current codebase can support the expansion.

**Conditions for approval:**

1. **Merge Phase 2 and Phase 3** — Build memory/circadian/personality first, then the planner that depends on them
2. **Bump crossfade risk to Medium impact** — Test it in Phase 0, not Phase 1
3. **Add the missing risks** to the risk table (taskbar collision, sprite corruption handling, DPI scaling, performance under gaming load)
4. **Add a vertical slice milestone** before completing all 12 poses
5. **Write planner/sequence unit tests** during Phase 2, not after

**This plan goes from good to great with these adjustments.** The core architecture — CircadianClock, BehaviorPlanner with 5-layer priority chain, SequenceManager, CatAnimator with spring physics, territory zones — is well-designed and the tech doc proves it fits in the 33fps budget.

The only architectural concern worth watching: the BehaviorPlanner's emergency override system sits above the sequence manager. If a sequence can be aborted mid-step by a low-energy emergency, the cat might snap out of a groom animation abruptly. Consider adding a "finish current step" threshold (abort only if energy < 10, not < 15) to make emergency transitions less jarring.

**Approved with changes. Estimated delta: +1-2 sessions to the upper bound, but cleaner result.**
