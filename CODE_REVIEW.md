# CODE REVIEW — Phase A: Orange Tabby Coat + 4-Leg Walk + Stripes

**Reviewer:** Lens 🔍  
**Commit:** `3340e58`  
**Status:** CONDITIONAL — Fix issues before merge

---

## Verdict: CONDITIONAL — 1 medium, 3 low items

---

## Issues

### MEDIUM — Gait: "diagonal trot" comment does not match data

**File:** `cat/legs.py:4-5`  
**Description:** The file header and GAIT_FRAMES_4LEG comment claim "The 8-frame gait cycles diagonal pairs (trot pattern)." The paw_dx values actually implement a lateral (same-side) pair pattern: FL+BL move together in frames 0-3, FR+BR move together in frames 4-7. This is a pace gait, not a trot.

**Impact:** Low for visual quality — a pace gait still looks like walking. But the documentation is wrong, which misled the test writer (see next item) and will confuse future maintainers who try to adjust the gait.

**Fix:** Update the comment to accurately describe the pattern:
```
# 8-frame lateral pair (pace) gait: left-side legs (FL, BL) cycle together,
# right-side legs (FR, BR) cycle together. Body bob and tilt sync per frame.
```

---

### LOW — `white` alias maps to Solid Black (index 5)

**File:** `config.py:295-296`  
**Description:** `COAT_NAME_INDEX["white"] = 5` maps the "white" coat name to `COAT_COLORS_STRUCTURED[5]` which is Solid Black (`#1A1A1A`). This means "selecting white" in settings would make the cat black. The existing `coats.json` has a white entry (`#F0F0F0`), so this regresses the user experience for anyone who chose white.

**Fix:** Map "white" to index 3 (Calico, `#FEFAF0`), which is cream-white — the closest match available:
```python
"white": 3,   # closest to white — calico body is cream-white #FEFAF0
```

---

### LOW — Test comments claim wrong diagonal pairs

**File:** `tests/test_gait.py:189-195`  
**Description:** `TestGaitDiagonalPairPattern` docstring says "Frames 0-3: right-front + left-hind step forward (diagonal pair 1)" and "Frames 4-7: left-front + right-hind step forward (diagonal pair 2)". This describes diagonal pairs, but the gait uses lateral pairs. The actual test assertions are minimal (just checking `assertIsNotNone`) so they don't verify the pattern — only the documentation is wrong.

**Fix:** Update docstring to match the actual lateral pair pattern:
```python
"""4-leg gait uses lateral pair (pace) pattern.
Frames 0-3: left-front + left-hind step forward (lateral pair)
Frames 4-7: right-front + right-hind step forward (lateral pair)
"""
```

---

### LOW — Dead import in test_gait.py

**File:** `tests/test_gait.py:24`  
**Description:** `from cat.tail import draw_tail_walk` is imported but never called in any test.

**Fix:** Remove the unused import.

---

### NIT — `_H` lambda unused

**File:** `config.py:210`  
**Description:** The helper `_H = lambda h: QColor(h)` is defined but never used. All coat definitions use `QColor(...)` directly.

**Fix:** Remove the unused lambda.

---

## Clean Items ✓

All tests pass (378 passed, 1 skipped). The following areas are clean:

### Correctness
- **`get_coat()` fallback**: Correctly handles negative, out-of-range, and boundary indices by returning index 0.
- **Backward compat**: Legacy `C_BODY`, `C_BELLY`, `C_PAW`, etc. constants are preserved as aliases to coat 0 (Gray Tabby / old Russian Blue). Code in `cat/home.py` that references these continues to work.
- **coat_index threading**: All draw functions accept `coat_index: int = 0` with default, so existing calls without the parameter still work.
- **COAT_NAME_INDEX**: All 7 structured coats + 2 aliases (ginger, white) map to valid indices.
- **Stripe dispatch**: `draw_coat_pattern()` correctly dispatches by `stripe_style` and skips gracefully for solid/none styles.

### Edge cases
- **Multi-cat**: Each cat stores its own `coat` in state dict. Save/load cycle preserves per-cat coat selection (tested in `test_multipet.py`).
- **Settings change**: `reload_settings()` applies the selected coat to all cats. Multi-cat differentiation is preserved through save/load but overwritten on settings changes — acceptable given current single-coat settings UI.
- **Missing coat names**: `COAT_NAME_INDEX.get("nonexistent", 0)` correctly returns default 0 (Gray Tabby).

### Code quality
- **Stripes.py**: Clean, stateless, well-commented. Each pattern function is independent with no side effects.
- **Legs.py**: Articulated leg drawing (2 segments per leg) with proper facing-aware coordinate transforms.
- **Tail.py**: Sinusoidal sway synchronized with `walk_frame` for natural gait-correlated movement.
- **Window.py**: `_draw_sit`/`_draw_walk`/`_draw_sleep` properly pass `coat_index` through the pipeline. Sleep pose uses `config.get_coat()` for all fills.

### Test coverage
- **test_coats.py** (40 tests): Covers all 7 coats' colors, stripe styles, forehead M, chin/chest, eye colors, boundary indices, index name mapping, property stability.
- **test_gait.py** (22 tests): Covers 8-frame count, leg key presence, 4-value tuples, joint-above-paw invariant, body bob/tilt ranges and symmetry, leg bases, tail sway.

---

## Summary

| Severity | Count | Key action |
|----------|-------|------------|
| Block    | 0     | — |
| Medium   | 1     | Fix gait comment (trot→pace) |
| Low      | 3     | Fix white alias, test docs, dead import |
| Nit      | 1     | Remove unused lambda |
| Clean    | —     | Everything else passes |

Fix the 4 issues above and we're green. Ready after those changes.
