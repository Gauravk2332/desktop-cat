# Sprite & Rendering Pipeline — Desktop Cat Overlay (PyQt6)

**Status:** Final decisions with rationale. Ready for implementation.
**Target:** Orange tabby overlay, 33fps, transparent full-screen, Windows 11.

---

## 1. Sprite Format → Pre-rendered PNG spritesheets

**Decision: Strip-based PNG spritesheets (horizontal filmstrip, per state)**

Rationale for rejecting alternatives:

| Format | Verdict | Why |
|---|---|---|
| QPainter procedural | ❌ | Current approach. Geometric shapes look fake. No amount of bezier curves makes a realistic cat fur. |
| SVG per frame | ❌ | librsvg / QSvgRenderer can't hit 33fps for complex SVGs. Inkscape export is inconsistent. |
| Individual PNG files | ❌ | 200+ loose files is a packaging and loading nightmare. |
| Vertical spritesheet | ❌ | Harder to memory-map, less cache-friendly for horizontal scan rendering. |
| **Horizontal strip** | **✅** | Single file per animation state. Easy to load as QPixmap, slice by frame width. |

**Layout convention:**
```
sprites/
  cat_idle.png         # 4 frames × 300px wide → 1200px total width
  cat_walk.png         # 12 frames × 300px → 3600px
  cat_sleep.png        # 6 frames × 300px → 1800px
  cat_transition_sit_to_walk.png  # 6 frames
  ...
```

**Frame count per animation:**

| State | Frames | Rationale |
|---|---|---|
| Idle | 4 | Subtle breathing. 4 frames at 8fps = smooth enough. |
| Walk | 12 | Full gait cycle. 12 at 12fps = fluid walk. |
| Sit → Walk | 6 | Short transition, 6 at 12fps = 0.5s. |
| Walk → Sit | 6 | Same. |
| Lie down | 8 | Slow deliberate movement. |
| Curled sleep | 4 | Very slow breathing cycle. |
| Groom | 8 | Paw-lick-repeat cycle. |
| Stretch (one-shot) | 8 | 8 frames, plays once, returns to idle. |
| Jump down | 6 | Quick transition. |
| **Total** | **~60 frames** | Comfortable for a single spritesheet session. |

**Resolution per frame:** 300×300 px — cat is ~200-250px tall, padding for tail/whiskers. Scales well across all monitor sizes.

**Alpha handling:** Standard RGBA PNG. PyQt6 `QPixmap` handles native per-pixel alpha. For scaling, use `Qt.SmoothTransformation` to avoid aliasing on the alpha edge.

---

## 2. Performance — 33fps is trivially achievable

**Decision: No special optimization needed at this scale.**

### Compositing budget
- 300×300 RGBA QPixmap blit: ~0.01ms on any GPU from the last 10 years.
- 33fps budget = 30ms per frame.
- Even with 2 sprites (crossfade) + shadow + eye overlay = <1ms total compositing.

### Bottlenecks to watch
| Concern | Actual risk | Mitigation |
|---|---|---|
| QPainter `drawPixmap` on full-screen transparent window | Low. PyQt5/PyQt6 uses Direct3D/OpenGL backend on Windows. Standard `QWidget` with `WA_TranslucentBackground` + `WA_NoSystemBackground` handles this well. | Use `paintEvent` with `QPainter`, not QGraphicsScene. |
| Loading 200 frames at startup | Medium. ~200 × 300×300 RGBA = ~72MB uncompressed. Fine. | Load spritesheets lazily per state. Pre-load idle + walk. |
| 4K screen with 200% scaled cat | Negligible. `drawPixmap` with scaling is hardware-accelerated. SmoothTransformation for the final scale. | Cache the scaled pixmap on resize. |

### Memory budget

| Asset | Frames | Uncompressed (RGBA) |
|---|---|---|
| All spritesheets | ~60 | ~21 MB |
| Scaled cache | ~60 | ~21 MB |
| Crossfade buffer (2 frames) | 2 | ~0.7 MB |
| Shadow pixmap | 1 | ~0.36 MB |
| Eye overlay sprites | ~20 | ~7 MB |
| **Total** | | **~50 MB** |

No concern. Even on a 4GB RAM machine, this is pocket change.

### Multi-cat future-proofing
Each additional cat = +~50 MB + 0.5ms compositing. 10 cats = 500 MB + 5ms. Still within budget.

---

## 3. Sprite Generation Pipeline

**Decision: Blender 3D → render frames → composite spritesheets**

For a solo dev with no art skills, this is the fastest path to *good-looking* results:

### Why Blender wins

| Path | Time to first good sprite | Quality ceiling | Autonomy |
|---|---|---|---|
| Commission artist | 1-3 days (waiting) | High | ❌ Need artist |
| Blender | 1-2 weeks learning + creating | Very high (photorealistic possible) | ✅ Full control |
| AI (SD + ControlNet) | 1-2 days | Medium — inconsistent frames, stripe float | ❌ Needs post-processing |
| Hand-draw in Krita | Months | Depends on skill | ✅ But slow |

### Blender pipeline (recommended)

1. **Model the cat** — Follow a YouTube tutorial for a low-poly cat base (~1 day)
2. **Texture** — Use procedural orange tabby texture in Blender (stripe node setup, no UV painting needed)
3. **Rig** — Simple armature: spine, 4 legs, head, tail (~2 hours)
4. **Pose/Animate** — One action per animation state: Idle (loop walk action, blend to idle)
5. **Render** — Eevee render engine (fast, good enough), orthographic side view
   - Output format: PNG RGBA (transparent background via Film → Transparent)
   - Resolution: 300×300 per frame
   - Track each action to a separate folder
6. **Stitch** — Simple Python script to assemble horizontal strips

**AI alternative (if Blender is too much):**
1. Generate side-view orange tabby reference with Stable Diffusion
2. Use Krita + layer-based animation to create frames manually
3. Export each frame as PNG, stitch with script

**Fastest path recommendation:**
1. **Hour 0-2:** Commission a single spritesheet on Fiverr ($30-50) for the base orange tabby
2. **Hour 2-4:** Build the animation controller and render pipeline in PyQt6
3. **Future:** Replace commissioned sprites with Blender-generated ones

This gets you a working cat on screen by end of day 1.

---

## 4. Orange Tabby Specifics

### Stripe consistency

**Critical problem:** Tabby stripes on legs must flow naturally during walk cycle.

**Solution: 3D texture approach (Blender).**
- The fur texture is UV-mapped onto the 3D mesh.
- The walk animation is driven by the armature.
- Every rendered frame naturally has consistent stripes because the UV doesn't change, only the mesh deforms.

If using 2D sprites (commissioned or AI):
- **One-shot spritesheets only.** No stitching together frames from different renders — stripes misalign.
- Commission a *complete* spritesheet with all states, not individual frames.
- Verify stripe continuity on leg bends before accepting.

### Fur texture

**Decision: Pre-baked texture + subtle post-effect overlay.**

| Method | Cost | Quality |
|---|---|---|
| Pre-baked in source art | Free (done in modeling) | Best — all visual quality is in the sprite |
| Per-frame noise overlay in QPainter | ~0.05ms extra | OK but looks like noise, not fur |
| Shader-based fur (GLSL) | Overkill for 2D | Best but requires OpenGL |

**Recommendation:** Pre-bake fur into the sprite texture. If the cat still looks too smooth, add a subtle 1-pixel dither overlay (static, generated once at startup) painted at 20% opacity over the body region.

### Eye animation

**Decision: Separate sprite overlay layer.**

- Eye sprites are separate, smaller PNGs (32×32 px per eye, positioned at known offsets on the cat body).
- Eye states: `open`, `half`, `closed`, `dilated`, `constricted`, `blink_1`, `blink_2`.
- Two independent eyes for natural look (one blinks slightly before the other).
- Pupil dilation independent of eyelid.
- Eye layer composites on top of the body sprite after the main draw call.

**File structure:**
```
sprites/eyes/
  open.png        # default
  half.png        # sleepy
  closed.png      # fully shut
  blink_01.png    # first frame of blink
  blink_02.png    # second frame
  dilated.png     # big pupil (excited/low light)
  constricted.png # small pupil (bright/alert)
```

---

## 5. Animation System Architecture

### Architecture diagram

```
+----------------+     +------------------+     +------------------+
| State Machine  | --> | Animation        | --> | Render Pipeline  |
| (FSM)          |     | Controller       |     | (paintEvent)     |
+----------------+     +------------------+     +------------------+
| - current_state |    | - spritesheet     |    | - shadow pass    |
| - requested     |    | - current_frame   |    | - body pass      |
|   transition    |    | - crossfade_prog  |    | - tail pass      |
| - transition    |    | - target_state    |    | - eye pass       |
|   queue         |    | - frame_timer     |    | - whisker pass   |
+----------------+     +------------------+     +------------------+
                              |
                        +-----------+
                        | Sprite    |
                        | Cache     |
                        | (loaded   |
                        | QPixmaps) |
                        +-----------+
```

### State machine

```
States: IDLE, WALK, SIT, LIE, SLEEP, GROOM, STRETCH, JUMP_DOWN
Transitions:
  IDLE ←→ WALK       (6 frames, 0.5s)
  IDLE → SIT         (4 frames, 0.3s)
  SIT → LIE          (6 frames, 0.5s)
  LIE → SLEEP        (8 frames, 0.7s)
  SLEEP → LIE        (4 frames, 0.3s)
  LIE → SIT          (6 frames, 0.5s)
  SIT → IDLE         (4 frames, 0.3s)
  IDLE → GROOM       (6 frames, 0.5s) → auto-return to IDLE
  IDLE → STRETCH     (8 frames, 0.7s) → auto-return to IDLE
  (any) → JUMP_DOWN  (6 frames, 0.5s) → auto-return to IDLE or SIT
```

### Animation controller

```
class AnimationController(QObject):
    def __init__(self):
        self.spritesheets: dict[str, QPixmap] = {}
        self.state: str = "idle"
        self.frame_index: int = 0
        self.frame_timer: QTimer  # ticks at animation FPS

        # Crossfade state
        self.crossfading: bool = False
        self.from_pixmap: QPixmap | None = None
        self.to_pixmap: QPixmap | None = None
        self.fade_progress: float = 0.0  # 0.0 → 1.0
        self.fade_timer: QTimer  # ticks at ~60fps during transition

    def request_state(self, new_state: str):
        """Queue a state transition. Interrupts current if priority allows."""

    def update_frame(self):
        """Advance frame_index. Handle looping vs one-shot animations."""

    def get_render_pixmap(self) -> tuple[list[QPixmap], list[float]]:
        """Return [(pixmap, alpha), ...] for layered compositing.
           During crossfade: returns from_pixmap at (1-fade) + to_pixmap at fade."""
```

### Easing

Transitions use `QEasingCurve.InOutCubic` mapped onto the fade timer.

```
fade_duration = 200ms  # 12 frames at 60fps
One-shot animations (stretch, groom): play at normal speed, fire on_finished
Looping animations (walk, idle): loop last frame → first frame seamlessly
```

### Layered rendering (paintEvent)

```
1. Clear entire window to transparent (QPainter.CompositionMode_Clear)
2. Draw shadow (translucent black ellipse under cat, offset ~5px down)
3. Draw body sprite (the main spritesheet frame)
4. Draw tail sprite (if separate — see Layered vs single below)
5. Draw head sprite (if separate — see Layered vs single below)
6. Draw eyes overlay
```

**Decision: Single-layer sprites for body, separate eyes only.**

Rationale:
- Rendering body + tail + head as separate sprites = 3× the sprite generation work (each frame needs 3 renders in Blender).
- For a solo dev, keep it simple: render the *full cat* (body + tail + head) to a single sprite frame.
- Only eyes are separate because they need independent animation (blink, pupil, focus).
- If later you want tail swishing independent of body, add a tail layer then.

### Looping vs one-shot

| Type | Animation | Behavior |
|---|---|---|
| Loop | idle, walk, sleep | Frame 0 → N-1 → 0 → ... |
| One-shot | stretch, groom, jump | Frame 0 → N-1, emit finished, transition back |
| Ping-pong | breathing (idle) | Frame 0 → N-1 → N-2 → 0 → ... |

---

## 6. Tools & Assets

### Recommended toolchain

| Purpose | Tool | Cost | Notes |
|---|---|---|---|
| 3D modeling + animation | Blender 3.x | Free | Eevee render, transparent PNG export |
| Sprite stitching | Python (PIL) | Free | Simple script to assemble horizontal strips |
| Sprite editing | Krita | Free | Touch-ups, eye sprites, compositing tests |
| Pixel-art refinement | Aseprite | $20 | Only if you want to hand-tweak frames |
| Commission sprites | Fiverr / r/HungryArtists | $30-100 | One-off spritesheet, specify PNG RGBA |

### PyQt6 QML integration

**Decision: Skip QML. Stick to QWidget + paintEvent.**

Rationale:
- QML adds a second rendering pipeline (Qt Quick) on top of QPainter.
- Mixing QWidget transparent overlay + QML SceneGraph causes compositing issues on Windows (z-order, click-through).
- QPainter `drawPixmap` is simpler, faster to develop, and the bottleneck is nowhere near QPainter.
- If you want smooth transitions, use the crossfade timer approach above instead of QML animations.

### Offscreen pre-rendering

**Decision: Not needed.**

Loading all spritesheets as QPixmap at startup takes ~50ms. That's the "pre-rendering." No need to render to offscreen surfaces when the source is already pixel data.

If scaling is expensive (e.g., user resizes window), cache the scaled version:
```python
self.scaled_cache: dict[str, QPixmap] = {}
def get_scaled(self, key: str, scale: float) -> QPixmap:
    # Check cache, else scale and cache
```

### Drop shadow

```python
def draw_shadow(self, painter: QPainter, rect: QRectF):
    shadow = QPainterPath()
    shadow.addEllipse(rect.translated(5, 8))  # offset right+down
    painter.fillPath(shadow, QColor(0, 0, 0, 40))  # translucent black
```

No blur needed at this scale. A simple filled ellipse gives enough depth.

---

## 7. File Structure

```
desktop-cat/
├── main.py                    # Entry point, transparent window setup
├── cat_overlay.py             # CatOverlayWidget (QWidget with paintEvent)
├── animation_controller.py    # AnimationController + StateMachine
├── sprite_cache.py            # SpriteSheet: loads, slices, caches pixmaps
├── eye_controller.py          # Independent eye animation logic
├── config.py                  # Constants: paths, timing, colors
│
├── assets/
│   ├── sprites/
│   │   ├── cat_idle.png             # 4 frames horizontal
│   │   ├── cat_walk.png             # 12 frames
│   │   ├── cat_sleep.png            # 4 frames
│   │   ├── cat_sit.png              # 4 frames
│   │   ├── cat_lie.png              # 6 frames
│   │   ├── cat_groom.png            # 8 frames
│   │   ├── cat_stretch.png          # 8 frames
│   │   ├── cat_jump_down.png        # 6 frames
│   │   ├── transition_idle_walk.png # 6 frames
│   │   ├── transition_walk_idle.png # 6 frames
│   │   ├── transition_idle_sit.png  # 4 frames
│   │   ├── transition_sit_idle.png  # 4 frames
│   │   ├── transition_sit_lie.png   # 6 frames
│   │   ├── transition_lie_sleep.png # 8 frames
│   │   ├── transition_sleep_lie.png # 4 frames
│   │   └── transition_lie_sit.png   # 6 frames
│   │
│   └── eyes/
│       ├── open.png
│       ├── half.png
│       ├── closed.png
│       ├── blink_01.png
│       ├── blink_02.png
│       ├── dilated.png
│       └── constricted.png
│
├── scripts/
│   └── stitch_sprites.py      # PIL script: individual frames → horizontal strip
│
└── TECH_SPRITE_AND_RENDER.md  # This file
```

Total: **~60 spritesheet frames + ~7 eye sprites = ~67 asset files.**

---

## Implementation Plan (ordered)

### Phase 1: Get a cat on screen (Day 1)

1. **Commission or generate** a single idle cat sprite (300×300 PNG). Even a static png works to start.
2. **Build `CatOverlayWidget`** — transparent full-screen window, `paintEvent` draws the single sprite centered.
3. **Build `SpriteCache`** — load QPixmap, slice by frame width.
4. **Build `AnimationController`** — timer-driven frame switching.
5. **Verify** 33fps on target Windows machine with a single idle animation.

### Phase 2: Spritesheet pipeline (Day 2-3)

1. **Model and texture** the orange tabby in Blender.
2. **Rig and animate** all states.
3. **Render** all spritesheets with transparent background.
4. **Run `stitch_sprites.py`** to assemble.
5. **Replace placeholder sprites** with real ones.

### Phase 3: Polish (Day 4+)

1. **Eye layer** — independent blink, pupil, gaze.
2. **Crossfade transitions** — smooth state changes.
3. **Drop shadow**.
4. **State machine** — reactive to mouse, time of day, activity.
5. **Multi-cat support** (optional) — each cat has its own controller + render position.

---

## Appendix: Blender export settings

| Setting | Value |
|---|---|
| Render Engine | Eevee |
| Resolution | 300×300 px |
| Frame Range | 0 to N-1 (N = frames per animation) |
| Output Format | PNG |
| Color → RGBA | ✅ |
| Film → Transparent | ✅ |
| Output Path | `//exports/<animation_name>/frame_####.png` |
| Sampling | 32 (Eevee) — good enough for orthographic cat |

### Stitch script (PIL)

```python
from PIL import Image
import glob, os

def stitch(folder: str, output: str):
    frames = sorted(glob.glob(os.path.join(folder, "*.png")))
    if not frames:
        return
    first = Image.open(frames[0])
    frame_w, frame_h = first.size
    strip = Image.new("RGBA", (frame_w * len(frames), frame_h))
    for i, path in enumerate(frames):
        strip.paste(Image.open(path), (i * frame_w, 0))
    strip.save(output)
```

---

## Appendix: Windows 11 specifics

| Concern | Resolution |
|---|---|
| Transparent click-through window | `setAttribute(Qt.WA_TransparentForMouseEvents)` on the overlay widget |
| Per-monitor DPI awareness | `Qt.AA_EnableHighDpiScaling` + `setAttribute(Qt.AA_UseHighDpiPixmaps)` |
| Always-on-top | `self.setWindowFlags(Qt.WindowStaysOnTopHint \| Qt.FramelessWindowHint \| Qt.Tool)` |
| Multi-monitor | Create overlay on the primary screen, or track cursor position for cat location |
| Taskbar avoidance | Use `QScreen.availableGeometry()` to constrain cat bounds |
| Sleep/hibernate resume | Override `changeEvent` to reload textures on `Qt.ApplicationState.Active` |
