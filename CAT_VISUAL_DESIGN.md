# CAT_VISUAL_DESIGN.md — Desktop Pet Orange Tabby

> Written for PyQt6 desktop overlay (Windows 11). Current state: simple geometric polygon cat. Target: hyper-realistic orange tabby with charm.

---

## 1. Orange Tabby Appearance — The Reference Cat

### 1.1 Tabby Pattern Recommendation: **Mackerel Tabby**

| Pattern | Description | Suitability |
|---------|-------------|-------------|
| **Mackerel (striped)** | Thin vertical stripes curving along the body. M on forehead. Cheek stripes. Necklaces. Leg bracelets. Tail rings. | **Best** — Most iconic "orange cat" look. Clean stripes read clearly at small sizes. |
| Classic (blotched) | Swirled bullseye patterns on sides. | Too busy for small sprite. Loses clarity at ~150px. |
| Ticked | Salt-and-pepper agouti hairs. Near-solid from distance. | Looks like a solid orange cat. No tabby visual identity. |
| Spotted | Broken stripes into spots. | Uncommon for orange tabbies. Less recognizable. |

**Verdict:** Mackerel tabby. The vertical stripes create a distinct silhouette that reads instantly as "orange tabby" even at reduced sizes. Classic/blotched requires more pixels to distinguish from abstract swirls.

### 1.2 Coat Color Range

```
Pale ginger ────── Medium amber ────── Rich burnt orange ────── Deep red-orange
  #F4A460            #E88D3B              #D4732A                   #C45A1C
```

**Recommendation:** Medium amber base (#E88D3B) with burnt orange stripes (#C46A2A). This sits in the sweet spot — warm enough to feel cozy, not so pale it washes out on bright backgrounds, not so dark it looks brown in dim light.

### 1.3 Anatomical Markings (Must-Have)

| Marking | Position | Visual Role | Priority |
|---------|----------|-------------|----------|
| **M** on forehead | Center of brow, parallel lines converging down | Instant identity marker — makes any cat read as "tabby" | **Critical** |
| Cheek stripes | 2-3 horizontal lines from eye corner down cheek | Frames the face, gives character | Critical |
| Necklaces (neck stripes) | 3-4 partial rings around upper chest/neck | Creates visual depth between head and body | High |
| Eye liner | Dark line rimming the eye, extending slightly outward | Defines eye shape, adds expression | High |
| Leg bracelets | Horizontal bands around each leg | Grounds the cat visually | High |
| Tail rings | Alternating bands along the tail | One of the most readable tabby features | High |
| Belly spots | Rows of small spots on belly/underside | Only visible during sit, stretch, roll | Medium |
| Spine stripe | Continuous dark line from M down the spine | Defines back contour | Medium |

### 1.4 Facial Features

| Feature | Specification |
|---------|--------------|
| **Nose** | Pink (#FF9999) with darker pink outline (#E87373). Triangular, small, slightly tilted up. |
| **Eye color** | **Amber/copper** (#D4942B with #FFD700 iris gradient). Green (#5D8C4B) is a secondary option. Amber provides maximum contrast on orange fur. |
| **Pupil** | Dark slit/ellipse that dilates based on lighting/emotion. Vertical slit for alert, round for relaxed/dark. |
| **Eye shape** | Almond-shaped, slightly angled (outer corner higher than inner). This is the most universally appealing cat eye shape. |
| **Paw pads** | Pink (#FFA5A5), roughly heart-shaped on front, bean-shaped on back. |
| **Whiskers** | White/light grey (#F0EDE8), 24 total (12 per side), 4 rows. Curved slightly downward. |

### 1.5 White Accents

Most orange tabbies have white on:
- **Muzzle and chin** — White from nose downward, extending under the jaw
- **Chest** — White patch/bib, often triangular
- **Belly** — Cream to white, softer fur
- **Paw tips** — White "socks" on some or all paws
- **Tail tip** — Can have white tip (less common but charming)

**Recommendation:** White muzzle + chin + chest + paw tips. This creates the classic "tuxedo-lite" orange tabby look and adds visual breaks that read well at scale.

---

## 2. Drawing Style — Semi-Realistic with Charm

### 2.1 Desktop Pet Style Analysis

| Reference | Style | Strengths | Weaknesses for Our Goal |
|-----------|-------|-----------|------------------------|
| **Desktop Goose** | Low-res pixel art (~64px) | Charming, simple, iconic | Too low-fi for realistic cat |
| **Desktop Mate** | Anime/chibi 2D | Expressive, smooth animation | Wrong aesthetic for realistic |
| **Bongo Cat** | Minimalist flat art | Clean, legible at any size | No depth or texture |
| **Nintendogs** | Toon-shaded 3D | Warm, expressive, detailed | Heavy rendering; our overlay needs lightweight |
| **Stardew Valley animals** | Pixel art with charm | Personality in few pixels | Too retro |
| **Animal Crossing** | Soft toon-shaded 3D | Friendly, warm aesthetic | Too stylized |

### 2.2 Recommended Style: **Soft Render (Painterly-Stylized Hybrid)**

Position between realistic fur texture and cartoon charm:

```
Photo-realistic ── Soft Render ── Toon-shaded ── Minimalist ── Pixel art
     (uncanny)        ★             (AC/Nintendo)   (Bongo)     (Goose)
```

**Key characteristics:**
- Fur has visible texture (soft brush strokes or noise-based) but not photorealistic individual hairs
- Shadows are soft and painted, not hard-edged
- Highlights are warm, suggesting subsurface scattering in ears
- Silhouettes are slightly simplified — real cat anatomy with subtle chibi proportions
- Colors are slightly saturated beyond reality — not muted natural, but "memory of a cat" colors
- Outline: no hard lineart. Shape defined by value contrast, not strokes.

### 2.3 Why This Works

1. **Avoids uncanny valley** — Photorealism at small size with limited animation looks dead, not alive
2. **Reads as "real"** — Fur texture and soft lighting trick the brain into seeing a real cat
3. **Sustainable rendering** — Doesn't require detailed rigging or 3D shading
4. **Charming at scale** — The subtle stylization makes it cute at 120px and beautiful at 300px

---

## 3. Orange Tabby Archetype & Personality

### 3.1 The Data

- **~80% of orange tabbies are male** — The ginger gene (O) is sex-linked. Males only need one copy. Females need two.
- **"Orange cat energy"** — Internet culture has memed orange cats as sharing one collective brain cell. Friendly, food-motivated, a bit dumb but deeply affectionate.
- **Common stereotypes:** Loud purrers, chatty, bold, lap cats, dog-like (follow owners, play fetch), high food drive.

### 3.2 Famous Orange Tabbies

| Character | Personality | Iconic Traits |
|-----------|-------------|---------------|
| **Garfield** | Lazy, cynical, food-obsessed | Lasagna, Monday-hating, sarcastic |
| **Puss in Boots** | Charming, brave, cunning | Big eyes (purr-suasion), hat/boots, swashbuckler |
| **Heathcliff** | Street-smart, tough | Comic strip, adventures |
| **Orange cats (meme)** | Derpy, friendly, one brain cell | Wide-eyed, confused, affectionate |

### 3.3 Recommended Archetype: **Warm Companion (lean IN)**

The cat should read as:
- **Friendly** — Approaches the cursor or user without fear
- **Slightly dopey** — Tilts head at things, occasionally gets distracted mid-walk
- **Food-motivated** — Reacts to clicks with hopeful expectation
- **Affectionate** — Rubs against screen edges, purrs when petted
- **Self-aware charming** — Knows it's cute. Uses the big eyes.

**Visual personality cues:**
- Slightly oversized head relative to body (chibi proportion, ~1:1.1 head-to-body vs real cat's ~1:1.5)
- Large, expressive eyes (1.3x real proportion)
- Ears slightly wider apart than real (adds "innocent" look)
- Tail always slightly curled up at the tip (default happy)
- Blinks slowly (cat for "I trust you")

**Gender:** The cat should read as subtly male but not explicitly gendered. Pronouns: he/him. Name: TBD (suggestions: Mango, Pumpkin, Biscuit, Toast).

### 3.4 Subvert or Lean In?

**Lean IN.** The orange tabby archetype is beloved for a reason. Lean into:
- The friendly, food-motivated energy
- The one-brain-cell charm
- The self-aware goofiness
- But give him **high-quality animations** that show genuine cat-like dignity — he might trip, but he'll pretend he meant to do that

---

## 4. Scaling & Screen Presence

### 4.1 Current vs Target

| Metric | Current | Target |
|--------|---------|--------|
| Size | ~80x60px | ~180x130px (body) |
| DPI consideration | None | 125% DPI (1536x816 effective) |
| Proportion | Geometric | Realistic with subtle chibi |

### 4.2 Ideal On-Screen Size

**On 1920x1080 at 125% DPI (1536x816 effective):**

| Size Variant | Body Box (WxH) | % of Screen | Role |
|-------------|---------------|-------------|------|
| **Small** | 120x90px | ~8% width | Minimal mode, stays out of way |
| **Medium (default)** | 180x135px | ~12% width | Good visibility, doesn't block content |
| **Large** | 250x188px | ~16% width | Showcase mode, full detail |
| **Chibi Large** | 220x200px | ~14% width | Larger head, extra charm |

**Recommendation:** Default to Medium (180x135px) with a simple toggle or right-click menu to switch sizes. The cat shouldn't feel obstructive — at 12% screen width it's present but easy to work around.

### 4.3 Real Cat Proportion Reference

Real cat (domestic shorthair):
- Shoulder height: 22-25cm
- Body length (nose to tail base): 40-50cm
- Tail length: 25-30cm
- Head width: ~12cm
- Eye diameter: ~1.5cm

**Scaled proportions for our cat:**
- Head:body ratio: 1:1.1 (slightly chibi, vs 1:1.5 real)
- Eyes: 1.3x real proportion for expressiveness
- Tail: Same length as body (real cats have tail = ~60% body length)
- Paws: Slightly oversized (adds to charm, like kitten proportions)

### 4.4 Positioning

- Default: bottom-right corner with 20px margin from edge
- Can wander across bottom 20% of screen (taskbar zone)
- Can climb up screen edges (vertical exploration)
- Returns to default position on idle timeout

---

## 5. Animation Frames & Quality

### 5.1 Frame Count Recommendations

#### Locomotion

| State | Frames | Type | Notes |
|-------|--------|------|-------|
| **Walk cycle** | 12 frames | Full cycle (6 per leg pair) | Smooth enough for 60fps display. Each leg has 3 key poses per cycle. |
| **Walk (ultra smooth)** | 16-20 frames | Full cycle | Optional for quality mode. Diminishing returns beyond 20. |
| **Run** | 8 frames | Full cycle | Faster pace, half the walk frames |
| **Sit → stand** | 6 frames | Transition | Front legs straighten, body rises, hind legs lock |
| **Stand → sit** | 8 frames | Transition | Hind legs bend, body lowers, tail curls around |
| **Turn (180°)** | 6 frames | Transition | Pivot on hind legs, front legs step around |
| **Trot start** | 4 frames | Initial step | Anticipation lean forward, first step |

#### Idle & Comfort

| State | Frames | Type | Notes |
|-------|--------|------|-------|
| **Idle breathing** | 6 frames | Loop | Subtle chest rise/fall, 1.5s loop at 6fps |
| **Sit idle 1** | 4 frames | Loop | Tail tip twitch, slow blink |
| **Sit idle 2** | 8 frames | Loop | Head look around, ear flick |
| **Lie down** | 8 frames | Transition | Front paws slide forward, body lowers, hind legs tuck |
| **Sleep breathing** | 6 frames | Loop (slow) | 3s loop at 2fps — subtle body rise/fall, ears relaxed |
| **Head tilt** | 4 frames | Trigger | Curiosity response |
| **Ear flick** | 2 frames | Trigger | Subtle ear rotation |
| **Tail swish (sit)** | 4 frames | Loop | Side-to-side tail movement |
| **Tail swish (stand)** | 6 frames | Loop | More pronounced, wider arc |
| **Slow blink** | 4 frames | Trigger | Eyes close halfway, hold, reopen — cat trust signal |
| **Yawn** | 10 frames | Trigger (uncommon) | Mouth opens wide, eyes squint, stretch follows |
| **Groom** | 12 frames | Loopable | Paw lick → head rub cycle. 3 sub-poses: lift paw, lick, rub ear/face |
| **Stretch** | 10 frames | Transition | Front paws extend forward, back arches up (downward dog style), rear stretches |
| **Scratch (post)** | 8 frames | Loop | Alternating paw scratches (air scratch or on screen edge) |
| **Sneeze** | 6 frames | Trigger (rare) | Tiny head shake, sneeze, reset |
| **Meow (mouth)** | 4 frames | Partial | Mouth open, eyes slightly wider, close |

#### Interactive

| State | Frames | Type | Notes |
|-------|--------|------|-------|
| **Paw at cursor** | 6 frames | Trigger | Bat at mouse pointer like a toy |
| **Chase cursor** | 8-12 frames | Follow | Head tracking, then body turn |
| **Head rub (screen edge)** | 6 frames | Loop | Rub cheek against screen edge, eyes closed happily |
| **Jump start** | 4 frames | Transition | Crouch, coil, spring |
| **Jump mid-air** | 4 frames | Arc | Tucked position, arc trajectory |
| **Jump land** | 4 frames | Transition | Paws hit, absorb, stand |
| **Purr** | 0 frames | Audio/visual | Subtle vibration overlay on idle pose, eyes half-closed |

### 5.2 Total Frame Estimate

| Category | States | Total Frames |
|----------|--------|-------------|
| Locomotion | 6 | ~56 frames |
| Idle & comfort | 11 | ~70 frames |
| Interactive | 5 | ~28 frames |
| **Total (all states)** | **~22** | **~154 frames** |

### 5.3 Resolution Per Frame

| Mode | Resolution | Rationale |
|------|-----------|-----------|
| **Standard** | 256x256 canvas, cat ~180x135 within | Clean at 1x. Scales to 2x without artifacts. |
| **High quality** | 512x512 canvas, cat ~360x270 within | For large mode or high-DPI screens. |
| **Rendering format** | PNG with transparency | Best quality, lossless, alpha channel. |
| **Fallback** | WebP with transparency | Smaller file size (~40% of PNG) for distribution. |

### 5.4 Transition Handling

**Approach: Interpolation with crossfade (3-frame blend)**

```
Pose A ──→ Interp1 ──→ Interp2 ──→ Pose B
  30%       40%        30%
```

- When transitioning between states (e.g., walk → sit), the last 2 frames of the outgoing animation blend with the first 2 frames of the incoming animation
- 3-frame crossfade: Frame N (100% old), Frame N+1 (66% old / 33% new), Frame N+2 (33% old / 66% new), Frame N+3 (100% new)
- This prevents the jarring "snap" between states

**For blending during turns while walking:**
- Track the intended direction. If direction changes mid-cycle, smoothly rotate the sprite using 2D transforms on the current frame rather than switching to a new direction sprite immediately.
- Only switch to the new direction sprite set when the rotation completes.

### 5.5 Animation Architecture

```
Frame Data Model:
{
  state: 'walk',
  frames: [img1, img2, ..., img12],  // Pre-loaded sprites
  loop: true,
  fps: 12,  // Display frames per second for this state
  transitions: {
    sit: { blend: 3 },
    idle: { blend: 3 },
    run: { blend: 2 }
  }
}
```

- **Direction sets:** 4-8 directional sprites per state frame (front, 3/4 front, side, 3/4 back, back, and diagonals). Minimum: side (L/R) + 3/4 front (L/R) for walk states.
- **Sprite sheet approach:** Each state has its own sprite sheet with all directional frames in a grid. Atlas loaded at startup.

---

## 6. Color Palette & Lighting

### 6.1 Core Palette

```yaml
# Fur
base_orange:     '#E88D3B'  # Medium amber — primary body color
stripe_dark:     '#C46A2A'  # Burnt orange — tabby stripes
stripe_mid:      '#D88F3A'  # Intermediate stripe edge
belly_cream:     '#F5DEB3'  # Warm cream — belly, chin, muzzle highlight
paw_white:       '#FAF0E6'  # Off-white — paw socks, chin
chest_white:     '#F5E6D0'  # Warm white — chest bib

# Face
nose_pink:       '#FF9999'  # Nose surface
nose_outline:    '#E87373'  # Nose edge
eye_amber:       '#D4942B'  # Base amber iris
eye_gold:        '#FFD700'  # Iris highlight/shine
eye_pupil:       '#1A1A1A'  # Pupil
eye_white:       '#F5F0E8'  # Sclera (minimal — cat eyes show little white)
eye_liner:       '#2C1810'  # Dark brown eye rim (softer than black)
inner_ear:       '#FFB5A0'  # Inner ear pink
whisker:         '#F0EDE8'  # Whisker color

# Shadows & Highlights
shadow_deep:     '#A0601A'  # Deep fur shadow (under chin, belly)
shadow_mid:      '#C47830'  # Mid-tone shadow (under body, between legs)
highlight:       '#F8B86A'  # Soft highlight (top of head, back, ear rims)
ambient_low:     '#2A1A0A'  # Ambient occlusion (in deep corners, between stripes)

# Night mode
night_desat:     '#7A5530'  # Everything shifts 20% cooler, 30% darker
night_glow_eye:  '#FFAA33'  # Eye glow at night (slight emissive)
night_bg_rim:    '#442200'  # Rim light from monitor glow
```

### 6.2 Lighting Model

**Style:** Soft diffuse lighting (cloudy day / indoor window light)

- **Key light:** Upper-left, 45° angle. 60% opacity soft brush.
- **Fill light:** Lower-right, 0° angle (monitor glow). 20% opacity.
- **Rim light:** On top of head, ear tips, top of back. 15% opacity.

**For sprite rendering (per-frame):**
- Each frame starts as a flat color base
- Multiply layer for shadows (20-30% opacity, soft airbrush)
- Screen/add layer for highlights (10-20% opacity)
- The lighting direction is consistent across all frames

**Night mode:**
- Desaturate palette by 20%
- Reduce contrast (shadows lighter, highlights dimmer)
- Add soft eye glow (emissive rim on iris)
- Add monitor rim light from below (warm glow on chin, belly)

### 6.3 Shadow System

```
Shadow Layers (from bottom to top):
1. Ambient occlusion — deep shadow in armpits, between legs, under chin (#2A1A0A, multiply 40%)
2. Core shadow — under body, far-side from light (#A0601A, multiply 25%)
3. Mid shadow — transition zones between light and core shadow (#C47830, multiply 15%)
4. Cast shadow — on ground/desktop surface below cat (#1A1A0A, soft, 30% opacity, blurred)
```

### 6.4 Fur Texture

Not individual hairs (too expensive). Instead:

1. **Noise overlay** — Low-frequency noise (20px grain) applied to fur areas at 15% opacity
2. **Stripe edge softening** — Stripes have slightly feathered edges (2-3px gaussian blur) rather than hard vector shapes
3. **Directional fur suggestion** — Short (8-12px) soft brush strokes in fur direction on the base layer
4. **Ear tufts** — Small fuzzy edges on ear tips (2-3px scatter)

---

## 7. Technical Implementation Notes

### 7.1 Rendering Pipeline (PyQt6)

```
QImage (or QPixmap) ── load PNG with alpha
        │
        ▼
QPainter ── draw image at position
        │
        ▼
Apply color transforms: brightness, contrast, color balance (for night mode)
        │
        ▼
Apply QGraphicsEffect (glow, shadow) if needed
```

**Performance considerations:**
- Pre-load all frames into memory as QPixmap at startup (~154 frames × 256KB = ~40MB)
- Use QPixmap cache for frequently accessed frames
- For smooth animation: use QTimeLine or QPropertyAnimation driving a frame index
- Frame rate: target 60fps. Animation frame rate varies by state (6-24fps) but rendering is always 60fps

### 7.2 Frame Generation Pipeline

For the artist or AI generation:

```
Step 1: Generate base cat model (3D or 2D rigged)
Step 2: Pose each frame of each state
Step 3: Render with consistent lighting
Step 4: Export as PNG with alpha
Step 5: Name convention: {state}_{direction}_{frameNumber}.png
         e.g., walk_side_01.png, sit_front_08.png
Step 6: Generate sprite atlas per state
```

### 7.3 File Naming Convention

```
<state>_<direction>_<frameNN>.png

States: walk, run, sit, idle_sit, idle_stand, lie, sleep,
        transition_sit2stand, transition_stand2sit, turn,
        groom, stretch, yawn, sneeze, paw, head_rub,
        scratch, meow, jump_start, jump_mid, jump_land

Directions: front, front34, side, back34, back
            (mirrored for L/R — only need one side, flip in code)

Example: walk_side_01.png ... walk_side_12.png
         sit_front_01.png ... sit_front_04.png
         groom_front34_01.png ... groom_front34_12.png
```

---

## 8. State Machine Overview

```
                     ┌─────────────────────────────────────┐
                     │              IDLE_STAND              │
                     │  (breathing, tail swish, look around)│
                     └─────┬─────────────┬─────────────┬───┘
                           │             │             │
                    stand→sit         walk          turn
                           │             │             │
                     ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
                     │  IDLE_SIT   │ │   WALK     │ │   TURN     │
                     │(tail twitch,│ │(12-frame   │ │(6-frame    │
                     │ slow blink, │ │ cycle)     │ │ transition)│
                     │ groom, yawn)│ └─────┬──────┘ └────────────┘
                     └─────┬──────┘       │
                     │     │             │
              sit→stand    │          run→walk
                     │     │             │
                  ┌──▼──┐ │         ┌────▼────┐
                  │ LIE │ │         │   RUN   │
                  └──┬──┘ │         │(8-frame)│
                     │    │         └─────────┘
                  ┌──▼──┐ │
                  │SLEEP│ │
                  └─────┘ │
                          │
            Interactive triggers (can interrupt any idle state):
            ─────────────────────────────────────────────────
            cursor_near → head_tilt, paw_at_cursor
            cursor_move → chase_cursor (if playful mode)
            click → head_rub, purr
            drag → resist (slight push back), then yield
            idle 15s → groom or stretch or yawn
            idle 60s → lie down
            idle 180s → sleep
            double_click → meow
```

---

## 9. EVALUATION & RISK

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Uncanny valley at high res | High | Soft render style, not photorealistic. Chibi proportions avoid it. |
| Too large / blocks content | Medium | Default size is 12% screen. Multiple size options. User can move it. |
| 154 frames is too expensive for small team | High | Start with core ~80 frames. Add secondary states later. |
| PyQt6 overlay performance with animated sprites | Medium | QPixmap cache, sprite atlases, 60fps render with 6-24fps animation. |
| Night mode palette shift required per frame | Low | Apply color transform at render time, not per-sprite. |

---

## 10. PRIORITY ORDER FOR IMPLEMENTATION

| Phase | States | Frame Count | Rationale |
|-------|--------|-------------|-----------|
| **P1 — MVP** | idle_stand, walk, sit, idle_sit, transition_sit2stand, transition_stand2sit | ~45 frames | Core loop: cat walks around, sits, exists |
| **P2 — Personality** | groom, stretch, yawn, head_tilt, slow_blink, meow | ~30 frames | Makes the cat feel alive |
| **P3 — Interactive** | paw_at_cursor, chase_cursor, head_rub, turn | ~20 frames | Desktop pet engagement |
| **P4 — Sleep & rest** | lie_down, sleep, run, jump | ~25 frames | Complete daily cycle |
| **P5 — Polish** | night_mode, extra idle variants, sneeze, scratch | ~20 frames | Delight and finish |

---

## APPENDIX A: Color Swatch Reference

```
🟧 E88D3B — Base fur
🟧 C46A2A — Dark stripes
🟨 F5DEB3 — Belly/chin cream
⬜ FAEBD7 — Paw white
🟥 FF9999 — Nose pink
🟫 D4942B — Iris amber
🟡 FFD700 — Iris highlight
⬛ 1A1A1A — Pupil
🟫 F5F0E8 — Eye white
🟫 2C1810 — Eye liner
🟥 FFB5A0 — Inner ear
⬜ F0EDE8 — Whiskers
🟨 F8B86A — Fur highlight
🟫 A0601A — Shadow deep
🟫 C47830 — Shadow mid
```

## APPENDIX B: Visual Reference List (for artist)

1. Real orange mackerel tabby photos — for anatomy and stripe pattern reference
2. Nintendogs (DS) — for the "warm virtual pet" feel
3. Desktop Mate — for the overlay interaction pattern
4. Animal Crossing: New Horizons cats — for the soft, charming aesthetic
5. Studio Ghibli cat designs (Kiki's Delivery Service, The Cat Returns) — for the "real but not real" sensibility
6. Cat taxidermy reference (dry, clinical) — for understanding muscle and bone structure under fur. Use only for structural understanding, not aesthetic.

---

# SPRITE SPECIFICATION — Per-State, Per-Angle, Per-Frame

> This section defines exactly how every sprite frame should be drawn. The spec uses a consistent coordinate system and proportional body model. Numbers are relative to the `body_box` (the smallest rectangle that contains the cat body excluding tail, default 180x135 for Medium size).

---

## Coordinate & Proportion System

```
Body Model (side view, standing):
                          ┌── Head ──┐
        Ear tip ─────────┤           ├───────── Ear tip
                         │   Face    │
        Eye level ───────┤  ════     │
        Nose ────────────┤    ●      │
        Chin ────────────┴───────────┘
                              │ Neck
        Shoulder ─────────────┼─────────────
                    ╱        ││        ╲
                  ╱  Front  ││  Back    ╲
        Chest ──┤    leg    ││   leg     ├── Rump
                  ╲         ││          ╱
                    ╲        ││        ╱
                              ││
        Wrist ───────────────────────────────
        Paw ────████████████████████████────
        ───── Tail ──────────────────────────
```

**Proportional units** (1 unit = 1% of body_box height):
- Head height: 40% of body_box
- Head width: 35% of body_box
- Body length (shoulder to rump): 65% of body_box
- Body height (shoulder to belly): 50% of body_box
- Leg length: 35% of body_box
- Tail length: 60-80% of body_box
- Ear height: 12% of body_box (from head top)
- Eye diameter: 8% of body_box
- Nose width: 5% of body_box
- Paw width: 8% of body_box

---

## WALK — 12-Frame Cycle (Side View)

### Strip Map
```
Frame 01: Left front forward, right front back. Right hind forward, left hind back.
          Body lowest (weight centered).
Frame 02: Left front starts moving back. Right front starts moving forward.
          Right hind starts moving back. Left hind starts moving forward.
Frame 03: Left front mid-back. Right front mid-forward.
          Right hind mid-back. Left hind mid-forward.
Frame 04: Left front back. Right front forward (full extension).
          Right hind back. Left hind forward (full extension).
          Body highest (weight transfer).
Frame 05: Left front starts forward. Right front starts back.
          Right hind starts forward. Left hind starts back.
Frame 06: Left front mid-forward. Right front mid-back.
          Right hind mid-forward. Left hind mid-back.
Frame 07: = Frame 01 (opposite diagonal). Right front forward, left front back.
          Left hind forward, right hind back.
Frame 08: = Frame 02 (opposite)
Frame 09: = Frame 03 (opposite)
Frame 10: = Frame 04 (opposite)
Frame 11: = Frame 05 (opposite)
Frame 12: = Frame 06 (opposite)
```

### Per-Frame Drawing Spec (Side View)

| Frame | Head bob (↑↓) | Body bob (↑↓) | Tail arc | Key details |
|-------|--------------|--------------|----------|------------|
| 01 | -1% | -2% (lowest) | Down sweep | LF forward, RH forward. Compact. Head slightly down. |
| 02 | 0% | -1% | Mid | Legs crossing. Front legs vertical, rear legs pushing. |
| 03 | +1% | 0% | Up | LF mid-back, RF mid-forward. Body rising. |
| 04 | +2% | +2% (highest) | High | RF full forward, LF full back. Body stretched. |
| 05 | +1% | +1% | Mid-top | RF starts back, LF starts forward. |
| 06 | 0% | 0% | Mid | Legs crossing again. |
| 07 | -1% | -2% | Down sweep | RF forward, LH forward. Mirror of 01. |
| 08 | 0% | -1% | Mid | Mirror of 02. |
| 09 | +1% | 0% | Up | Mirror of 03. |
| 10 | +2% | +2% | High | Mirror of 04. |
| 11 | +1% | +1% | Mid-top | Mirror of 05. |
| 12 | 0% | 0% | Mid | Finish, ready to loop back to 01. |

**Tail animation during walk:**
- Synchronized: tail arcs upward as the opposite hind leg pushes forward
- Peak at frames 04 and 10 (highest body position)
- Trough at frames 01 and 07 (lowest body position)
- Tail tip curls slightly inward at the arc peaks (classic cat walk tail)

**Head motion:**
- Subtle horizontal sway (≈3% body width) opposite to the leading front leg
- Eyes slightly forward gaze, no blinking during walk
- Ears: slightly forward (alert/curious while moving)

### Per-Angle Variations

**34 Front (L/R):** Same leg cycle. Body rotates ~30° toward viewer. Show partial opposite-side front leg peeking behind. Head shows both eyes but primary eye larger. M on forehead is visible but angled. One cheek visible, one partially hidden. Tail wraps toward viewer side (adds depth).

**Front:** Legs directly toward viewer. Paws visible as ovals. Body width narrowest. Head full face. M mark prominent. Walk becomes a 
