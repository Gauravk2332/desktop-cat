# CODE_REVIEW — desktop-cat

**Reviewer:** Lens 🔍
**Files reviewed:** 18 (all `.py` sources including tests)
**Scope:** Bug patterns, imports, drawing pipeline, state init, performance, security, code quality

---

## Critical

### 1. `except Exception: pass` in `engine._on_tick` and `window.paintEvent` silently swallows all errors

**File:** `core/engine.py` (line ~179) and `core/window.py` (line ~72)

Both `_on_tick` (the main loop) and `paintEvent` (the draw pipeline) wrap their entire body in:

```python
try:
    ...
except Exception:
    pass
```

This means any error — a `ZeroDivisionError`, an `AttributeError` on a misspelled variable, a `TypeError` from a wrong argument — disappears without a trace. The cat freezes, stops moving, and no one knows why. No log, no stderr, no indicator.

**Recommendation:** At minimum, log the exception:
```python
except Exception as e:
    import logging
    logging.exception("paintEvent failed: %s", e)
```

Better: catch specific expected errors (e.g. `OSError` on file I/O) and let unexpected ones propagate so they appear on stderr during development. Remove the blanket wrapper in debug builds entirely. At a minimum, log with traceback.

---

### 2. `_poll_idle` uses Windows-specific ctypes — crashes on Linux/macOS

**File:** `core/engine.py` (lines ~260–275)

```python
def _poll_idle(self):
    try:
        import ctypes
        class _LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        lii = _LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        ...
    except Exception:
        pass
```

`ctypes.windll` only exists on Windows. On Linux you get `AttributeError: module 'ctypes' has no attribute 'windll'`. The bare `except Exception: pass` catches this silently and idle detection becomes a no-op, but every 5 seconds the code attempts and silently fails.

Additionally, even if `ctypes.windll` were available, `GetLastInputInfo`/`GetTickCount` may not work as expected on Wine/Proton.

**Recommendation:** Abstract idle detection behind a platform-conditional import. Use `xprintidle` via subprocess on Linux, `IOKit` via pyobjc on macOS. Fail loudly during import if the platform is unsupported rather than silently every 5 seconds.

---

### 3. `_draw_sleep` uses `painter.scale()` without centering — coordinates shift

**File:** `core/window.py` (lines ~175–180)

```python
def _draw_sleep(self, painter, cx, cy):
    breath = math.sin(self.state.sleep_breath) * 0.02 + 1.0
    painter.save()
    painter.scale(breath, breath)
    ...
    # All subsequent coordinates are drawn at (cx, cy) but scale is applied
    # from (0,0), so everything shifts away from the origin
    painter.restore()
```

`painter.scale(s, s)` scales from the origin `(0,0)`. The cat is drawn at screen coordinates `(cx, cy)` — typically the middle of the screen for field sleep. After scaling by `breath` (which oscillates between ~0.98 and ~1.02), the entire drawing shifts because the scale pivot is `(0,0)`, not `(cx, cy)`.

This produces a visible jitter: the sleeping cat drifts left/up when breath decreases and right/down when breath increases.

**Recommendation:** Translate to center before scaling:
```python
painter.translate(cx, cy)
painter.scale(breath, breath)
painter.translate(-cx, -cy)
```

Or draw relative to `(cx, cy)`:
```python
painter.translate(cx, cy)
painter.scale(breath, breath)
# draw everything relative to (0,0)
```

---

## High

### 4. `from cat.home import _bed_center` imported INSIDE methods — runtime import overhead

**File:** `core/engine.py::_update_go_home` and `behavior/transitions.py::_enter_go_home`

```python
def _update_go_home(self, dt: float) -> None:
    from cat.home import _bed_center  # ← runtime import every tick
    ...
```

```python
def _enter_go_home(state) -> None:
    from cat.home import _bed_center  # ← runtime import
    ...
```

These imports execute every time the method runs. For `_update_go_home`, that's every tick (50ms) while the cat is walking home. `_bed_center` is a simple pure function — there's no circular import risk. The module-level import would be cleaner and faster.

**Recommendation:** Move both to top-of-file imports in `engine.py` and `transitions.py`.

---

### 5. Cat draws in screen coordinates — fragile across monitors and DPIs

**File:** `core/window.py` and all `cat/*.py` drawing modules

The drawing pipeline renders everything at `state.cat_x, state.cat_y` as absolute screen pixel coordinates. This works for a single 1920×1080 monitor, but fails under:
- Multi-monitor setups (cat might span displays)
- High-DPI / scaled displays (Qt scaling factors)
- Screen resolution changes at runtime

The window itself is correctly sized via `QApplication.primaryScreen().availableGeometry()`, but the drawing does not participate in any coordinate remapping.

**Recommendation:** Choose one of:
- Use a virtual canvas (e.g. `cat_x` and `cat_y` as 0.0–1.0 normalized, then map to window size in `paintEvent`)
- Add device pixel ratio awareness: `painter.setDevicePixelRatio(screen.devicePixelRatio())` and scale coordinates accordingly
- At minimum, document the assumption and guard against zero-width/height screens

---

### 6. `_draw_sit` and `_draw_walk` import `animation.breathe` at call time — same as #4

**File:** `core/window.py` (lines ~95, 130)

```python
def _draw_sit(self, painter, cx, cy):
    from animation.breathe import breath_value  # ← runtime import every repaint
    ...
```

```python
def _draw_walk(self, painter, cx, cy):
    from animation.breathe import breath_value  # ← runtime import every repaint
    ...
```

`paintEvent` can fire at 60 FPS. These imports re-run hundreds of times per second. `breathe` is already imported at the top of `engine.py` — just add `from animation.breathe import breath_value` once at the top of `window.py`.

**Recommendation:** Move both imports to module level.

---

### 7. Zzz particles — mutation pattern is safe but inefficient

**File:** `core/engine.py` (lines ~212–218)

```python
for p in list(s.zzz_particles):
    p[1] -= 10 * dt
    p[2] -= dt
    p[3] += dt
    if p[2] <= 0 or p[3] > 2.5:
        s.zzz_particles.remove(p)
```

`list(s.zzz_particles)` creates a shallow copy, so iterating is safe. But `s.zzz_particles.remove(p)` is O(n) per particle and does an equality search on a list-of-lists object. For 10–20 particles this is nominally fine, but it's a latent O(1)→O(n²) bug if particle count grows.

Also, `p[0]` has no drift (initial random offset stays fixed) — particles float vertically but don't drift sideways, which looks unnatural.

**Recommendation:** Use a list comprehension for the filter step:
```python
s.zzz_particles = [p for p in s.zzz_particles if p[2] > 0 and p[3] <= 2.5]
```

This also fixes any accidental mutation bugs and is O(n). Add horizontal drift: `p[0] += random.uniform(-3, 3) * dt`.

---

## Medium

### 8. `CatState.cat_x = 0.0` default immediately overwritten — suggests unclear initialization

**File:** `core/state.py` and `core/window.py::_position_window`

`CatState.cat_x` defaults to `0.0`, but `_position_window` overwrites it with `float(geo.width() // 2)`. The `0.0` value is never valid — it would put the cat off-screen left if the window weren't initialized before the first paint.

**Recommendation:** Either:
- Remove the default and make `cat_x` `None` or some sentinel that forces initialization
- Initialize `cat_x` to `-1.0` and assert `cat_x >= 0` before first draw
- Better: move the default to a classmethod factory that takes screen geometry

---

### 9. `screen_width: int = 1920` default hardcodes a specific resolution

**File:** `core/state.py`

The `screen_width` and `screen_height` defaults (1920×1080) are overwritten by `_position_window`, but there's no enforcement that this happens before any system reads them. If `_position_window` fails (screen is None), the entire system runs at 1920×1080 regardless of actual hardware.

**Recommendation:** Default to `-1` and raise a `RuntimeError` in any system that reads them while they're still `-1`. Or remove the defaults entirely and make them required constructor params.

---

### 10. Engine class has too many responsibilities — SRP violation

**File:** `core/engine.py` (~275 lines)

The Engine class currently handles:
- Game loop / tick lifecycle
- Animation systems (breathe, blink, tail, sleep)
- Navigation (walk, wander, go-home move logic)
- Mouse tracking + proximity reactions
- Action queue processing (pet, feed, wake)
- State persistence (save/load)
- System-wide idle detection (platform-specific)
- Eye tracking smooth interpolation
- Expression system (blush, pupil dilation)

This is ~7–8 responsibilities in one class. Makes testing hard, forces fixture imports that create QTimers (see #16), and mixes concerns at different levels of abstraction.

**Recommendation:** Extract into separate modules/classes:
- `MouseTracker` (QCursor polling, proximity, eye target)
- `NavigationSystem` (walk, wander, go-home movement math)
- `PersistenceManager` (save/load JSON)
- `IdleDetector` (platform-specific idle — see #2)
- `Engine` keeps only: tick orchestration, system list, dt calculation

---

### 11. `_check_mouse` writes to `self._mouse_moving` but never reads it

**File:** `core/engine.py` (line ~249)

```python
self._mouse_moving = abs(dx_move) > 2 or abs(dy_move) > 2
```

This is the only assignment to `self._mouse_moving` in the entire codebase. It's never referenced anywhere else — not for blink reactivity, not for expression changes, not for animation. Dead code.

**Recommendation:** Remove it, or use it for its intended purpose (e.g. suppress blink when mouse is moving).

---

### 12. `flip_x` function corrects X but doesn't help with yaw — mirroring is incomplete

**File:** `config.py`

```python
def flip_x(x: float, facing: bool) -> float:
    return x if facing else -x
```

This correctly mirrors x-coordinates when facing left. However, cubic bezier control points that are not symmetric in X (e.g., `draw_body_sit`'s `body.cubicTo` calls) produce visibly different shapes when flipped because Y-coordinates aren't adjusted. The tail drawing adds extra sin/cos on top of flipped coordinates, which can produce unnatural curves when facing left.

**Recommendation:** This works for the current art style (reasonably symmetrical cat), but document the assumption explicitly. Add a note: "Control points must be X-symmetric for proper mirroring."

---

## Low

### 13. Test suite imports delete `sys.modules` entries — fragile and stateful

**File:** `tests/test_state_machine.py`

```python
def _import_transitions(self):
    if "behavior.transitions" in sys.modules:
        del sys.modules["behavior.transitions"]
    import behavior.transitions
    return behavior.transitions
```

Same pattern for `needs`, `engine`, `api`. This works but is fragile — if another test module imported transitions at module level, the delete won't fully clear it, and leftover module state can leak between tests.

**Recommendation:** Make `update()` functions accept only `(dt, state)` and compute all random/timed decisions based on `state` values. No module-level state = no need to reimport. Alternatively, use `importlib.reload()` instead of `del sys.modules`.

---

### 14. `_update_go_home` assumes bed is always to the right — wrong if screen layout changes

**File:** `core/engine.py:230` and `behavior/transitions.py:128`

`_enter_go_home` hardcodes `state.facing = True` (right-facing), and `_update_go_home` checks `remaining = bed_x - cat_x` and moves right. This assumes the bed is always to the right of the cat's current position.

If the cat is already to the right of the bed (e.g. after screen resize, or on a wide monitor where the cat started center-right), the cat walks AWAY from the bed, not toward it.

**Recommendation:** Set facing based on sign of `remaining`:
```python
state.facing = (bed_x - state.cat_x) > 0
```

---

### 15. `_update_wander` modifies `state.facing` during iteration — could cause mid-tick inconsistency

**File:** `core/engine.py` (lines ~155–178)

`_update_wander` changes `state.facing` on bounce, but the transitions system also reads `state.facing` in the same tick. Since both run in `_on_tick` (transitions first, then animations), there's no race, but `facing` is mutated mutably mid-tick without coordination — a future refactor that reorders systems could silently break bounce behavior.

**Recommendation:** Document the ordering dependency or compute the new facing into a local and assign once at the end.

---

### 16. Engine tests create QTimer/ElapsedTimer — fails without Qt event loop

**File:** `tests/test_state_machine.py::TestNavigation`

```python
def _import_engine_nav(self):
    from core.engine import Engine
    class MockWindow:
        def update(self): pass
    engine = Engine(self.state, MockWindow())
    ...
```

`Engine.__init__` creates `QTimer`, `QElapsedTimer` instances that depend on a running `QApplication`. These tests will fail if run without one (e.g. headless CI).

**Recommendation:** Either:
- Check for `QApplication.instance()` in Engine init and skip Qt initialization if None
- Or: extract navigation math into a pure stateless function (mutating only state) that engines tests can call without instantiating Engine

---

### 17. `_draw_z_badge` uses `QPainter.drawText()` — coordinates may need adjustment

**File:** `cat/home.py::_draw_z_badge`

```python
painter.drawText(int(zx), int(zy), "Z")
```

`drawText(x, y, ...)` in Qt draws the text baseline at `y` from the left, which means the "Z" sits below the `(zx, zy)` point. Combined with the bounce: `zy = by - HOME_BED_RY - 4 + bounce`, the Z badge position varies noticeably — could overlap with the cat's ear at minimum bounce.

**Recommendation:** Use `painter.setFont()` with `painter.boundingRect()` to compute the actual text height and offset, or use `drawText(QRect, Qt.AlignCenter, "Z")`.

---

## Verdict

**Request changes** — the code is structurally well-organized (modular, clean separation of drawing from logic, config-driven), but has several correctness bugs that reach Gk's users.

### Must-fix before production
- [ ] **Critical-1**: `except Exception: pass` in both `_on_tick` and `paintEvent` — add logging at minimum
- [ ] **Critical-2**: `_poll_idle` uses `ctypes.windll` — platform abstraction needed
- [ ] **Critical-3**: `_draw_sleep` scale transform not centered — visible jitter
- [ ] **High-4**: Runtime imports of `_bed_center` — move to module level
- [ ] **High-7**: Zzz particle mutation — use list comprehension
- [ ] **Medium-8/9**: State initialization defaults that are immediately overwritten
- [ ] **Medium-11**: Dead `_mouse_moving` code

### Should-fix
- [ ] **Medium-10**: Engine SRP violation — extract subsystems
- [ ] **Medium-12**: Test suite fragility (`del sys.modules`)
- [ ] **Low-14**: `_enter_go_home` facing direction unconditional right
- [ ] **Low-16**: Engine tests need Qt event loop

### Nit
- [ ] `_draw_sit` and `_draw_walk` runtime imports of `breathe` — move to module level
- [ ] `_draw_z_badge` text baseline alignment
- [ ] Wander particles have no horizontal drift

---

🔍 **Summary:** The architecture is clean and the modular split into `cat/`, `behavior/`, `animation/`, `core/` is well done. The primary risk is the blanket `except Exception: pass` — this turns every bug into silent deadlock. Once that's replaced with proper logging, the platform-specific idle detection is abstracted, and the scale transform center is fixed, the code is ready.
