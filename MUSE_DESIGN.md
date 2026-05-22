# MUSE_DESIGN.md — Desktop Cat Visual & Behavioral Overhaul

**Status**: Design specification for Coder implementation  
**Date**: 2026-05-22  
**Purpose**: Transform the abstract geometric cat into a realistic orange tabby with 4 legs, lifelike behaviors, and multiple coat options.

---

## A. Visual Design — 4-Leg Walking Cat

### A.1 Coordinate System

All coordinates are relative to the cat's **body center** `(cx, cy)`, which is the center of the body ellipse at rest. The cat sits on the ground at `y = cy`. `x` increases to the right when `facing = True` (facing right). Use `config.flip_x()` as before.

**Cat footprint**: approximately 80px wide × 70px tall (standing/walking).  
**Sitting footprint**: approximately 50px wide × 75px tall.

### A.2 Body Proportions (Standing/Walking)

| Part     | Shape          | Size (w×h) | Offset from body center (cx, cy) |
|----------|----------------|------------|----------------------------------|
| Body     | Ellipse        | 52×34      | (0, -22) centered at (0, -22)   |
| Head     | Circle         | r=14       | (0, -52)                        |
| Front L  | 3-segment      | —          | shoulder at (-12, -12)           |
| Front R  | 3-segment      | —          | shoulder at (12, -12)            |
| Back L   | 3-segment      | —          | hip at (-16, -14)                |
| Back R   | 3-segment      | —          | hip at (16, -14)                 |
| Tail     | Cubic bezier   | ~30 long   | base at (-20, -10)               |

### A.3 The 4-Leg Gait Cycle

**Strategy**: The gait uses 8 frames (0–7) cycling every 200ms at walk speed. Each leg has a `shoulder/hip` joint and a `knee` joint. We draw each leg as 3 connected segments (or 2 filled shapes with a joint).

**Leg Anatomy** (per leg):
- **Upper segment**: shoulder/hip → elbow/knee (thick, 5px)
- **Lower segment**: elbow/knee → paw (slightly thinner, 4px)
- **Paw**: small ellipse at foot tip (6×4px)

#### Gait Frame Table (facing right)

| Frame | Front-Left (FL)   | Front-Right (FR)  | Back-Left (BL)    | Back-Right (BR)   | Body Bob |
|-------|-------------------|-------------------|-------------------|-------------------|----------|
| 0     | Extended forward  | Lifting backward  | Lifting backward  | Extended forward  | -2px     |
| 1     | Planting forward  | Reaching back     | Reaching back     | Planting forward  | +1px     |
| 2     | Ground contact    | Extended backward | Extended backward | Ground contact    | +2px     |
| 3     | Lifting backward  | Extended forward  | Extended forward  | Lifting backward  | +1px     |
| 4     | Reaching back     | Planting forward  | Planting forward  | Reaching back     | -1px     |
| 5     | Extended backward | Ground contact    | Ground contact    | Extended forward  | 0px      |
| 6     | Extended forward  | Lifting backward  | Lifting backward  | Extended forward  | -2px     |
| 7     | Lifting backward  | Extended forward  | Extended forward  | Lifting backward  | +2px     |

**Diagonal pairs**: FL+BR move together, FR+BL move together (trot-like). This gives the cat a natural walking appearance.

#### Leg Joint Positions Per Frame (relative to hip/shoulder)

Each leg has 3 key points:
- **BaseB**: shoulder/hip — where leg attaches to body
- **MidB**: knee/elbow — middle joint
- **PawB**: foot — ground contact or lifted

**Front-Left leg** (FL), base at `(cx - 12, cy - 12)`:

| Frame | MidB (elbow)       | PawB (foot)        |
|-------|--------------------|--------------------|
| 0     | (-14, +2)          | (-18, +10)         |
| 1     | (-10, +4)          | (-12, +12)         |
| 2     | (-6, +2)           | (-4, +12)          |
| 3     | (-4, -2)           | (0, +8)            |
| 4     | (-6, -4)           | (-4, +4)           |
| 5     | (-10, -4)          | (-12, +4)          |
| 6     | (-14, -2)          | (-18, +6)          |
| 7     | (-16, +0)          | (-20, +10)         |

**Front-Right leg** (FR), base at `(cx + 12, cy - 12)`:

| Frame | MidB (elbow)       | PawB (foot)        |
|-------|--------------------|--------------------|
| 0     | (6, -4)            | (4, +4)            |
| 1     | (4, -2)            | (0, +8)            |
| 2     | (2, +2)            | (-2, +12)          |
| 3     | (6, +4)            | (6, +12)           |
| 4     | (10, +2)           | (14, +10)          |
| 5     | (12, -2)           | (18, +6)           |
| 6     | (10, -4)           | (14, +4)           |
| 7     | (8, -4)            | (10, +4)           |

**Back-Left leg** (BL), base at `(cx - 16, cy - 14)`:

| Frame | MidB (knee)        | PawB (foot)        |
|-------|--------------------|--------------------|
| 0     | (-14, -4)          | (-12, +4)          |
| 1     | (-10, -4)          | (-4, +4)           |
| 2     | (-6, -2)           | (0, +8)            |
| 3     | (-4, +2)           | (4, +12)           |
| 4     | (-8, +4)           | (8, +12)           |
| 5     | (-12, +2)          | (12, +10)          |
| 6     | (-16, -2)          | (14, +6)           |
| 7     | (-18, -4)          | (14, +4)           |

**Back-Right leg** (BR), base at `(cx + 16, cy - 14)`:

| Frame | MidB (knee)        | PawB (foot)        |
|-------|--------------------|--------------------|
| 0     | (16, -4)           | (14, +6)           |
| 1     | (12, -4)           | (8, +6)            |
| 2     | (8, -2)            | (4, +10)           |
| 3     | (6, +2)            | (2, +12)           |
| 4     | (10, +4)           | (6, +12)           |
| 5     | (14, +2)           | (12, +10)          |
| 6     | (18, -2)           | (16, +6)           |
| 7     | (18, -4)           | (16, +4)           |

**Implementation**: Store each paw as a tuple `(mid_x, mid_y, paw_x, paw_y)` per leg per frame. `mid` = elbow/knee joint, `paw` = foot tip. Draw each leg with:
```python
path = QPainterPath()
path.moveTo(base_x, base_y)
path.lineTo(mid_x, mid_y)
path.lineTo(paw_x, paw_y)
```
Use pen width 5 for upper segment, 4 for lower segment. Add small paw ellipse (6×4) at paw position.

### A.4 Body Bob While Walking

The body center `(cx, cy)` oscillates vertically during walking. Use `walk_bob` value from the gait frame table (max ±2px). Apply as:
```python
bob_y = GAIT_FRAMES[state.walk_frame]["body_bob"]
body_cy = cy + bob_y
```
Also tilt the body ellipse slightly (rotate by ±2 degrees) to simulate weight shift:
- Frames 0,4: tilt -2° (left)
- Frames 2,6: tilt +2° (right)
- Others: 0°

### A.5 Tail Sway While Walking

Replace the static tail-up with a smooth sinusoidal sway:
```python
tail_sway = math.sin(state.walk_accum * 4.0) * 8
# Tail tip deviates tail_sway px horizontally from neutral
```
Tail base: `(cx - 16, cy - 28)`  
Tail tip: `(cx - 12 + tail_sway, cy - 55)`  
Use a cubic bezier with control points midway.

### A.6 Sitting Cat

The sitting cat keeps the 4-leg paw positions tucked:
- Front legs: straight down from shoulders, paws at ground
- Back legs: folded (thigh horizontal, shin vertical, paw tucked under body)
- Tail curls around one side

**Front paws (sit)**:
- FL: base `(-12, -12)`, mid `(-10, 0)`, paw `(-10, +8)`
- FR: base `(+12, -12)`, mid `(+10, 0)`, paw `(+10, +8)`

**Back legs (sit, folded)**:
- BL: base `(-16, -14)`, mid `(-20, +2)`, paw `(-12, +10)`
- BR: base `(+16, -14)`, mid `(+20, +2)`, paw `(+12, +10)`

**Tail (sit, curled)** — current implementation is fine, just update to use proper curve.

---

## B. Orange Tabby Design

### B.1 Color Palette

| Part       | Hex       | QColor                      | Notes                    |
|------------|-----------|-----------------------------|--------------------------|
| Body       | `#E89B5D` | `QColor(0xE8, 0x9B, 0x5D)` | Warm ginger orange       |
| Belly      | `#FCE6C9` | `QColor(0xFC, 0xE6, 0xC9)` | Cream/light tan          |
| Stripe     | `#C47A3C` | `QColor(0xC4, 0x7A, 0x3C)` | Darker orange-brown      |
| Nose       | `#F08080` | `QColor(0xF0, 0x80, 0x80)` | Light coral              |
| Inner ear  | `#FFB6C1` | `QColor(0xFF, 0xB6, 0xC1)` | Soft pink                |
| Eye        | `#4CAF50` | `QColor(0x4C, 0xAF, 0x50)` | Green — tabby classic    |
| Pupil      | `#1A1A1A` | `QColor(0x1A, 0x1A, 0x1A)` | Near-black               |
| Whisker    | `#D4D4D4` | `QColor(0xD4, 0xD4, 0xD4)` | Very light gray          |
| Chin/Chest | `#FEFEFE` | `QColor(0xFE, 0xFE, 0xFE)` | White chin + chest patch |
| Paw pads   | `#D4956A` | `QColor(0xD4, 0x95, 0x6A)` | Warm pink-brown          |

### B.2 Stripe Pattern (Mackerel Tabby)

Draw stripes as **short curved lines** (QPainterPath arcs) overlaid on the body. Use a list of stripe positions relative to the body ellipse.

**Body stripes** (5-7 stripes, drawn after belly fill):

```
Stripe 0: starts (-4, -40) → (-4, -32) — first vertical stripe (neck)
Stripe 1: starts (4, -40)  → (4, -32)  — second neck stripe
Stripe 2: starts (-8, -34) → (-6, -22) — left shoulder
Stripe 3: starts (8, -34)  → (6, -22)  — right shoulder
Stripe 4: starts (-12, -30) → (-10, -18) — left mid-body
Stripe 5: starts (12, -30)  → (10, -18)  — right mid-body
Stripe 6: starts (-14, -22) → (-12, -12) — left lower body
Stripe 7: starts (14, -22)  → (12, -12)  — right lower body
```

Each stripe drawn as:
```python
path = QPainterPath()
path.moveTo(x1, y1)
path.cubicTo((x1+x2)/2 - 2, (y1+y2)/2, (x1+x2)/2 + 2, (y1+y2)/2, x2, y2)
painter.strokePath(path, QPen(stripe_color, 2.5, cap=Qt.PenCapStyle.RoundCap))
```

**Tail stripes** (4-5 dark rings on tail):
Draw as small curved arcs across the tail path at regular intervals.

**Forehead "M" marking**:
A stylized "M" drawn above the eyes on the head circle. Use 3 short strokes:
```python
# Left upstroke
p1.moveTo(cx - 6, head_y - 8)
p1.cubicTo(cx - 4, head_y - 12, cx - 2, head_y - 12, cx, head_y - 10)
# Right upstroke  
p2.moveTo(cx + 6, head_y - 8)
p2.cubicTo(cx + 4, head_y - 12, cx + 2, head_y - 12, cx, head_y - 10)
# Center V
p3.moveTo(cx - 3, head_y - 11)
p3.cubicTo(cx - 2, head_y - 10, cx + 2, head_y - 10, cx + 3, head_y - 11)
```
Stroke each with `QPen(stripe_color, 1.5)`.

**Cheek stripes** (2 thin horizontal lines on each cheek):
```python
FL: (-8, head_y - 2) → (-12, head_y - 1)
FR: (+8, head_y - 2) → (+12, head_y - 1)
```

### B.3 Leg Stripes

Each leg gets 1-2 horizontal stripe marks near the upper segment:
```
FL upper: (-15, -6) → (-9, -6)  | FR upper: (9, -6) → (15, -6)
BL upper: (-19, -8) → (-13, -8) | BR upper: (13, -8) → (19, -8)
```
Drawn as short lines, `QPen(stripe_color, 1.5)`.

### B.4 White Chin & Chest

Draw a small white ellipse/path at the chin and upper chest:
```python
chin = QPainterPath()
chin.addEllipse(cx - 4, head_y + 3, 8, 5)  # under chin
painter.fillPath(chin, QColor(0xFE, 0xFE, 0xFE))

chest = QPainterPath()
chest.addEllipse(cx - 6, head_y + 5, 12, 8)  # upper chest
painter.fillPath(chest, QColor(0xFE, 0xFE, 0xFE))
```

---

## C. Real Cat Behaviors

### C.1 Stretching After Waking (`STRETCH` state)

**Trigger**: Transition from SLEEP → SIT. Cat enters a 1.5s stretch animation before sitting normally. Also triggered manually when mouse is nearby after waking.

**Duration**: 1.5 seconds (30 ticks at 50ms)

**Visual elements**:
- **Phase 1 (0-0.5s)**: Front legs extend forward. Body tilts forward and down. Head lowers. Butt stays up.
  - Body: tilt -15°, shift forward (+8px on x), downward (+4px on y)
  - Front legs: fully extended forward (shoulder → full reach, +20px x, +4px y)
  - Back legs: straighten slightly (hip → back +6px y)
  - Tail: lift straight up and back
  - Head: lower by 6px, tilt -5°

- **Phase 2 (0.5-1.0s)**: Deep stretch. Back arches upward (cat back curve).
  - Body: arch upward (center lifts +4px), tail end of body lifts +6px
  - Front paws: slide further forward (+10px)
  - Back legs: straighten completely
  - Spine visible as arched back (draw as curved line on top of body)

- **Phase 3 (1.0-1.5s)**: Release. Body relaxes, cat settles into sitting posture.
  - Body: return to normal position and tilt
  - Legs: return to sit positions
  - Head: return to normal

**Sound**: Optional soft `trill` or `meow_short` at the end.

### C.2 Yawning Animation (`YAWN`)

**Trigger**: Random when waking from sleep (60% chance) or when energy < 30 and sitting (10% chance per check, checked every 30s).

**Duration**: 1.2 seconds (24 ticks)

**Visual elements**:
- **Phase 1 (0-0.3s)**: Mouth slowly opens. Eyes squint.
  - Mouth: a vertical ellipsis opens from 2px to 8px tall just below nose
  - Eyes: squint to thin arcs (like happy eyes but closing)
  - Head: tilts slightly back (+2px y)

- **Phase 2 (0.3-0.7s)**: Maximum yawn. Mouth wide open.
  - Mouth: 8px tall × 6px wide dark ellipse (tongue visible — tiny pink oval inside)
  - Eyes: fully closed (tight arcs)
  - Head: tilted back fully (+5px y)
  - Ears: flatten slightly (scale to 0.8)
  - Optional: tiny stretch of front legs

- **Phase 3 (0.7-1.2s)**: Mouth closes. Eyes open. Head returns.
  - Mouth: shrink from 8px to 0px
  - Eyes: transition from closed → normal open
  - Head: return to normal position

**Sound**: Soft `chirp`-like or a dedicated yawn audio.

### C.3 Grooming Behavior (`GROOM`)

**Trigger**: Random when sitting (5% per 10s), or when not interacted with for 60s while sitting (guaranteed after 60s idle).

**Duration**: 3-6 seconds (continuous cycle of lick → pause → reposition)

**Visual elements**:

**Groom Cycle** (loop 2-3 times per session):
1. **(0-0.3s)**: Cat looks at one front paw. Head rotates toward paw. Paw lifts slightly.
   - Front paw (whichever side cat is facing): lifts from ground by +10px y
   - Head: rotates toward that paw (-10° if lifting left, +10° if lifting right)

2. **(0.3-0.8s)**: Lick motion. Head lowers to meet lifted paw.
   - Head: moves down (-6px y) and toward paw
   - Lifted paw: higher (+15px y)
   - Mouth area: tiny open arc (2px)
   - Head bob: quick small oscillation (3 cycles over 0.5s) to simulate licking

3. **(0.8-1.0s)**: Reposition. Paw lowers. Head returns to neutral.
   - Everything returns to sit position

4. **(1.0-1.5s)**: Cat switches to other paw (mirror of steps 1-3, but shorter — 0.5s total)

5. **(1.5-2.5s)**: Face wash. Cat uses one paw to wipe across face/ear.
   - Paw: rises to face height (cx ± 5, head_y)
   - Head: tilts to meet paw
   - Paw moves in small arc across face area (simulating wiping motion)
   - Ear on that side: may bend slightly under paw pressure

6. **(2.5-3.0s)**: Return to normal sit posture.

**State transitions**: Grooming is a sub-behavior within SIT state. Set `cat["grooming"]` flag. Prevent other transitions during grooming.

**Sound**: Soft `purr`/`trill` (contentment).

### C.4 Scratching Behavior (`SCRATCH`)

**Trigger**: Random when sitting (3% per 15s), or after grooming (20%), or when boredom > 70 (15% per 10s while sitting).

**Duration**: 2.5 seconds

**Visual elements**:
- Cat stands up on hind legs slightly, leans forward, and rapidly scratches with front paws.
- **Phase 1 (0-0.3s)**: Cat rises slightly. Rear end stays low, front body lifts.
  - Body: tilt +15° forward, lift front end +4px
  - Front legs: straighten
  - Back legs: stay bent (like crouch)

- **Phase 2 (0.3-2.0s)**: Rapid alternating scratching motion.
  - Left front paw: extend forward and down (extend +8px x, +2px y)
  - Right front paw: same but alternating
  - Alternating cycle: 4-6 full alternations at 200ms each
  - Body: slight bounce with each scratch (2px body bob)
  - Head: lowered, focused on scratching surface
  - Tail: twitching or held straight back

- **Phase 3 (2.0-2.5s)**: Cat stops and returns to sitting.
  - Legs return to sit
  - Body returns to normal
  - Cat may look around afterward

**State**: `SCRATCH` — new state, can transition from SIT. On completion → SIT.

**Sound**: Optional scratch noise (if audio available). No vocalization.

### C.5 Tail Swishing (Annoyed/Focused)

**Not a full state** — a modifier on SIT, WALK, and CHASE states.

**Trigger conditions**:
- Mouse nearby but not interacting (distance 50-150px) for >5s → annoyed swish
- CHASE state — focused swish while tracking prey
- Boredom > 60 while sitting → impatient swish

**Visual**:
- Tail tip makes quick side-to-side motion (sinusoidal, 3Hz, ±10px amplitude)
- Replace the slow sit-tail animation with faster, sharper oscillations:
```python
tail_swish = math.sin(state.tail_phase * 3.0) * 10
# Tail drawn with lateral offset tail_swish at the tip
```
- The rest of the tail follows with slight lag (catenary curve effect)

**Duration**: As long as trigger condition persists. Decays over 3s after trigger ends.

### C.6 Ears Perking Up (Interested/Audio Attention)

**Not a full state** — a modifier on any state.

**Trigger conditions**:
- Mouse enters proximity (<150px) and cat is awake
- Mouse moves quickly nearby
- Any sound event (platform support needed)
- Cat playing/chasing

**Visual**:
- Both ears rotate toward the sound/mouse direction (up to ±15°)
- Ears scale up slightly (1.15×) — more alert appearance
- Inner ear may show more (ear drawn slightly wider)

**Implementation**: Modify `draw_ears()` to accept `ear_angle` and `ear_scale` parameters:
```python
def draw_ears(painter, cx, cy, state, head_y, scale=1.0, ear_angle=0):
    # ear_angle: rotation in degrees, positive = ears pointing right/forward
    # Apply rotation transform around each ear's base point
```
- `ear_angle` ranges from -15 (back, annoyed) to +15 (forward, interested)
- Default is 0 (neutral alert)
- Sleep: ears are relaxed (angle = 0, scale = 0.85)

### C.7 Looking Up (Head Tilt)

**Trigger**: Mouse passes above the cat's head (mouse_y < cat_y - 60). Cat tracks overhead movement.

**Duration**: As long as mouse is above. Decay 0.5s after mouse leaves area.

**Visual**:
- Head tilts up: head_y shifts up by 3-5px
- Eyes look up: pupil target shifts up by max 2px (in addition to normal tracking)
- Whiskers tilt slightly up
- If mouse stays overhead for >3s, cat may do a slow head turn tracking it

**Implementation**:
```python
if mouse_y < cat["y"] - 60:
    head_look_up = min((cat["y"] - 60 - mouse_y) / 100.0, 1.0)
else:
    head_look_up = max(0, head_look_up - dt / 0.5)  # decay
# Apply head_look_up to head_y, eye tracking
```

### C.8 Slow Blink (Cat "I Love You")

**Trigger**: Cat is sitting, well-fed (hunger < 30), and mouse is nearby (distance < 100px) for >3s without sudden movements. 15% chance per check (checked every 5s when conditions met).

**Duration**: 1.5 seconds (very slow blink cycle)

**Visual**:
- Eyes close very slowly (0.5s to close)
- Stay closed (0.5s)
- Open very slowly (0.5s)
- Unlike regular blinks (0.1s), this is deliberately slow and gentle
- May be accompanied by a slight head lowering

**Implementation**: Add `slow_blink` flag and timer to cat state. Override normal blink when active.

**Sound**: None (silent affection signal). Could trigger a soft `purr` if the sound system supports sustained sounds.

### C.9 Rolling Over (Trust/Belly Show) — `ROLL_OVER`

**Trigger**: Cat is sitting, well-fed (hunger < 20), energy > 70, and mouse has been within 60px for >8s. 5% chance when conditions met. Only when cat trusts owner (implemented as: no sudden approaches in last 120s).

**Duration**: 2.0 seconds

**Visual (three-phase roll)**:
- **Phase 1 (0-0.5s)**: Cat sits back and starts leaning to one side.
  - Body: tilts 30° to the side
  - Legs: splay outward from underneath
  - Head: follows body rotation

- **Phase 2 (0.5-1.2s)**: Full roll to side. Belly exposed.
  - Body: rotated 90° (side view becomes belly-up)
  - Instead of complex 3D rotation, **represent as:**
    - Body becomes a wider, flatter ellipse (body w: 44, h: 24, rotated so wider axis is horizontal)
    - Belly fill covers most of the visible area
    - Legs splay: front legs go up and forward (+8px x, -20px y from body center)
    - Back legs go up and back (-8px x, -20px y from body center)
    - Head: rotated 90° from upright — draw as a wider oval (r=14 → ellipse 18×10)
    - Eyes: both visible, looking slightly up and to the side
    - Tail: curves around the body

- **Phase 3 (1.2-2.0s)**: Cat rolls back to sitting.
  - Reverse of phase 1
  - Ends in normal sit position

**State**: `ROLL_OVER` — can only transition from SIT. On completion → SIT. After rolling over, cat may stretch.

**Sound**: Soft `trill` or purr.

### C.10 Play Bow (Play Invitation)

**Trigger**: Cat is sitting, energy > 60, boredom > 50, mouse is visible and moving nearby (<200px, speed > 100px/s). Also triggered if user does a "play gesture" (mouse rapidly moves away from cat then stops — simulates teasing). 

Also triggered automatically when transitioning from SIT to PLAY state.

**Duration**: 1.0 seconds. Then cat either engages in play (CHASE/PLAY) or returns to SIT.

**Visual**:
- Front legs stretch forward and down
- Chest lowers to the ground
- Rear stays up (butt higher than shoulders)
- Tail sticks straight up (excited)
- Head stays up, looking at target
- This is the classic cat play bow

**Coordinate positions** (relative to body center `(cx, cy)`):
- Body center: shifts down (+8px y) and slightly forward (+4px x)
- Front paws: extend to (-24, +14) and (+24, +14) — wide and forward
- Back paws: stay at (-12, +6) and (+12, +6) — ready to pounce
- Head: stays high at (0, -42) — looks up at play target
- Tail: straight up at (-16, -55) — tip may quiver

**Duration**: 1.0s hold, then either:
- Cat pounces (CHASE state) if mouse moves
- Cat stays in play bow and tail wags (PLAY state, inviting)
- Cat returns to sit if nothing happens

**Sound**: Playful `chirp`.

---

## D. Coat Color Options

### D.1 Configuration Structure

Replace the current `COAT_COLORS` flat list with a structured dictionary:

```python
from dataclasses import dataclass

@dataclass
class CoatColor:
    name: str                # Display name
    body: QColor             # Main body/fur color
    belly: QColor            # Belly/underside
    stripe: QColor | None    # Stripe color (None for solid coats)
    nose: QColor             # Nose color
    ear_inner: QColor        # Inner ear
    eye: QColor              # Eye/iris color
    paw: QColor              # Paw pads
    whisker: QColor          # Whisker color
    has_white_chin: bool     # Has white chin/chest patch?
    has_M_mark: bool         # Has forehead "M" marking?
    stripe_style: str        # "mackerel", "classic", "spotted", "none"
```

### D.2 Coat Definitions (7 Options)

```python
COAT_COLORS_STRUCTURED = [
    CoatColor(
        name="Orange Tabby",
        body=QColor(0xE8, 0x9B, 0x5D),
        belly=QColor(0xFC, 0xE6, 0xC9),
        stripe=QColor(0xC4, 0x7A, 0x3C),
        nose=QColor(0xF0, 0x80, 0x80),
        ear_inner=QColor(0xFF, 0xB6, 0xC1),
        eye=QColor(0x4C, 0xAF, 0x50),
        paw=QColor(0xD4, 0x95, 0x6A),
        whisker=QColor(0xD4, 0xD4, 0xD4),
        has_white_chin=True,
        has_M_mark=True,
        stripe_style="mackerel",
    ),
    CoatColor(
        name="Gray Tabby",
        body=QColor(0x7C, 0x8E, 0x9E),
        belly=QColor(0xD4, 0xD9, 0xDE),
        stripe=QColor(0x5A, 0x6B, 0x7A),
        nose=QColor(0xFF, 0x94, 0x94),
        ear_inner=QColor(0xFF, 0xB8, 0xC6),
        eye=QColor(0x6B, 0xA3, 0xD6),
        paw=QColor(0xCC, 0xD5, 0xDC),
        whisker=QColor(0xA8, 0xB0, 0xB8),
        has_white_chin=True,
        has_M_mark=True,
        stripe_style="classic",
    ),
    CoatColor(
        name="Tuxedo",
        body=QColor(0x2F, 0x2F, 0x2F),
        belly=QColor(0xFE, 0xFE, 0xFE),  # white belly
        stripe=None,
        nose=QColor(0x33, 0x33, 0x33),     # dark nose
        ear_inner=QColor(0x55, 0x55, 0x55),
        eye=QColor(0xE8, 0xD5, 0x3F),     # golden yellow
        paw=QColor(0xFE, 0xFE, 0xFE),     # white paws
        whisker=QColor(0xE0, 0xE0, 0xE0),
        has_white_chin=True,               # classic white chin/chest
        has_M_mark=False,
        stripe_style="none",
    ),
    CoatColor(
        name="Calico",
        body=QColor(0xFE, 0xFA, 0xF0),    # warm white base
        belly=QColor(0xFE, 0xFA, 0xF0),
        stripe=None,                       # patches instead of stripes
        nose=QColor(0xF0, 0x80, 0x80),
        ear_inner=QColor(0xFF, 0xB6, 0xC1),
        eye=QColor(0x8B, 0xC3, 0x4A),     # green
        paw=QColor(0xFE, 0xFA, 0xF0),
        whisker=QColor(0xD4, 0xD4, 0xD4),
        has_white_chin=True,
        has_M_mark=False,
        stripe_style="patch",
    ),
    CoatColor(
        name="Siamese",
        body=QColor(0xF5, 0xE6, 0xCC),    # warm cream body
        belly=QColor(0xFA, 0xF0, 0xDD),
        stripe=QColor(0x6B, 0x4E, 0x37),    # dark brown points
        nose=QColor(0x6B, 0x4E, 0x37),
        ear_inner=QColor(0x8B, 0x6E, 0x57),
        eye=QColor(0x4A, 0x90, 0xD9),        # vivid blue
        paw=QColor(0x6B, 0x4E, 0x37),        # dark paw pads
        whisker=QColor(0xF0, 0xF0, 0xF0),
        has_white_chin=False,
        has_M_mark=False,
        stripe_style="point",
    ),
    CoatColor(
        name="Solid Black",
        body=QColor(0x1A, 0x1A, 0x1A),
        belly=QColor(0x33, 0x33, 0x33),      # slightly lighter belly
        stripe=None,
        nose=QColor(0x44, 0x44, 0x44),
        ear_inner=QColor(0x55, 0x55, 0x55),
        eye=QColor(0xF0, 0xE6, 0x8C),        # amber/gold
        paw=QColor(0x44, 0x44, 0x44),
        whisker=QColor(0xBB, 0xBB, 0xBB),
        has_white_chin=False,
        has_M_mark=False,
        stripe_style="none",
    ),
    CoatColor(
        name="Tortoiseshell",
        body=QColor(0x2F, 0x2F, 0x2F),       # dark base
        belly=QColor(0x4A, 0x3A, 0x2A),
        stripe=QColor(0xCC, 0x7A, 0x3C),     # orange patches
        nose=QColor(0x80, 0x60, 0x60),
        ear_inner=QColor(0x8B, 0x6E, 0x57),
        eye=QColor(0xE8, 0xD5, 0x3F),        # golden
        paw=QColor(0x55, 0x44, 0x44),
        whisker=QColor(0xBB, 0xBB, 0xBB),
        has_white_chin=False,
        has_M_mark=False,
        stripe_style="patch",                # patchy swirled pattern
    ),
]
```

### D.3 Stripe Drawing by Style

Create a generic `draw_stripes(painter, cx, cy, state, coat)` function that dispatches by `stripe_style`:

| Style      | Method                                                       |
|------------|--------------------------------------------------------------|
| `mackerel` | Draw 7-8 vertical curved lines on body (Section B.2)         |
| `classic`  | Draw 3-4 bullseye/swirled shapes (concentric arcs) on sides  |
| `spotted`  | Draw 6-8 small ellipses in 2 rows (broken stripes)           |
| `patch`    | Draw 3-4 irregular large blobs (Calico/Tortie color patches) |
| `point`    | Draw dark color on: face mask, ears, paws, tail tip          |
| `none`     | Skip stripe drawing                                          |

**Patch pattern for Calico** (2-3 orange patches, 1-2 black patches over white base):
```python
patches = [
    # (cx_offset, cy_offset, w, h, color)
    (-8, -30, 18, 14, QColor(0xE8, 0x9B, 0x5D)),  # orange patch on shoulder
    (12, -24, 14, 12, QColor(0x2F, 0x2F, 0x2F)),   # black patch on back
    (-2, -38, 10, 8, QColor(0xE8, 0x9B, 0x5D)),    # small orange on top
]
for ox, oy, pw, ph, color in patches:
    p = QPainterPath()
    p.addEllipse(cx + ox, cy + oy, pw, ph)
    painter.fillPath(p, color)
```

**Point pattern for Siamese** (dark on face, ears, paw tips):
```python
# Dark face mask (oval over center of face)
mask = QPainterPath()
mask.addEllipse(cx - 6, head_y - 4, 12, 8)
painter.fillPath(mask, point_color)

# Dark ears — already handled by base ear drawing with point_color
# Dark tail tip — extra dark segment at tail end
```

---

## E. Implementation Notes for Coder

### E.1 New States to Add

| State         | Config Constant     | Description                          |
|---------------|---------------------|--------------------------------------|
| `STRETCH`     | `STATE_STRETCH`     | Stretching after waking up           |
| `GROOM`       | `STATE_GROOM`       | Grooming/fur-licking behavior        |
| `SCRATCH`     | `STATE_SCRATCH`     | Scratching ground/surface            |
| `ROLL_OVER`   | `STATE_ROLL_OVER`   | Rolling over to show belly           |
| `PLAY_BOW`    | `STATE_PLAY_BOW`    | Play bow invitation posture          |

### E.2 New Cat State Fields

```python
"stretch_timer": 0.0       # seconds into stretch animation
"grooming": False           # grooming flag
"groom_timer": 0.0          # seconds into grooming cycle
"groom_phase": 0            # which part: 0=paw lift, 1=lick, 2=switch, 3=face wash
"scratch_timer": 0.0        # seconds into scratch animation
"scratch_phase": 0          # which part of scratch
"roll_timer": 0.0           # seconds into roll-over
"roll_phase": 0             # 0=lean, 1=belly-up, 2=recover
"play_bow_timer": 0.0       # seconds in play bow
"tail_swish_active": False  # tail swishing flag
"tail_swish_intensity": 0.0 # 0-1 intensity of swishing
"ear_angle": 0.0            # -15 to +15 degrees
"head_look_up": 0.0         # 0-1 upward head tilt
"slow_blink_active": False  # slow blink in progress
"slow_blink_timer": 0.0     # seconds into slow blink
"slow_blink_phase": 0       # 0=closing, 1=closed, 2=opening
"coat_index": 0             # which coat color (index into COAT_COLORS_STRUCTURED)
```

### E.3 Flag for Preventing Multiple Behaviors

Add `cat["behavior_lock"]` — a string or None. When a behavior is active (STRETCH, GROOM, SCRATCH, ROLL_OVER, PLAY_BOW), set `behavior_lock` to that state name. The state transition system should skip checks while `behavior_lock` is set. The draw pipeline checks `behavior_lock` to choose the animation.

### E.4 New Config Constants

```python
# Behavior durations (seconds)
STRETCH_DURATION = 1.5
YAWN_DURATION = 1.2
GROOM_DURATION_MIN = 3.0
GROOM_DURATION_MAX = 6.0
SCRATCH_DURATION = 2.5
ROLL_OVER_DURATION = 2.0
PLAY_BOW_DURATION = 1.0
SLOW_BLINK_DURATION = 1.5

# Behavior trigger intervals (seconds)
GROOM_COOLDOWN = 30.0
SCRATCH_COOLDOWN = 20.0
ROLL_OVER_COOLDOWN = 120.0
PLAY_BOW_COOLDOWN = 15.0

# Gait
GAIT_FRAME_TIME = 0.2       # seconds per gait frame (8 frames = 1.6s cycle)
GAIT_BOB_AMPLITUDE = 2.0    # px body bob
GAIT_TILT_AMPLITUDE = 2.0   # degrees body tilt
```

### E.5 Draw Pipeline Changes

Update `window.py` draw methods:

1. **`_draw_sit()`**: Check `cat["behavior_lock"]` first. If lock is set, dispatch to the appropriate behavior draw function.
2. **`_draw_walk()`**: Replace 2-leg walk with 4-leg gait (Section A.3). Add body bob (A.4) and tail sway (A.5).
3. **Add `_draw_stretch()`**: Draw each stretch phase (C.1).
4. **Add `_draw_groom()`**: Draw grooming cycle (C.3).
5. **Add `_draw_scratch()`**: Draw scratch animation (C.4).
6. **Add `_draw_roll_over()`**: Draw roll-over (C.9). Requires drawing cat from "belly-up" perspective.
7. **Add `_draw_play_bow()`**: Draw play bow posture (C.10).

In `_draw_sleep()`: Check for slow blink transitions (though sleep eyes should be closed anyway).

### E.6 Engine Loop Changes

In `engine.py`'s main update loop:

1. After state transitions, before drawing: update behavior animations.
2. For each behavior lock, run the animation timer and phase logic.
3. When behavior timer expires, clear `behavior_lock`, set state to SIT.
4. Call `_check_behavior_triggers()` per cat to evaluate grooming, scratching, play bow, etc.
5. Add `_update_tail_swish()` — check conditions and set `tail_swish_active` + intensity.
6. Add `_update_ears()` — set `ear_angle` based on mouse proximity and direction.
7. Add `_update_head_look()` — check if mouse is above cat, set `head_look_up`.
8. Add `_update_slow_blink()` — check conditions and trigger slow blink.

### E.7 Modify `draw_ears()` to Accept `ear_angle`

```python
def draw_ears(painter, cx, cy, state, head_y, scale=1.0, ear_angle=0.0):
    """ear_angle: degrees, positive = forward/alert, negative = back/annoyed"""
    # Rotate ear triangles around their base points by ear_angle degrees
    painter.save()
    for side in (-1, 1):
        ear_base_x = cx + flip_x(side * EAR_OFFSET * scale, state.facing)
        ear_base_y = head_y - 2 * scale
        # Apply rotation
        painter.translate(ear_base_x, ear_base_y)
        painter.rotate(ear_angle * side)  # mirror for each side
        painter.translate(-ear_base_x, -ear_base_y)
        # ... draw ear as before ...
    painter.restore()
```

### E.8 Add `draw_yawn()` Animation to Head

Yawn affects head drawing only. The rest of the body stays in sit/walk pose.

```python
def draw_yawn(painter, cx, cy, head_y, state, yawn_timer, yawn_phase):
    """Draw open mouth and squinting eyes for yawn."""
    # Phase 0 (closing): mouth ellipse grows from 0 to 8px
    # Phase 1 (open): mouth at 8px, draw pink tongue oval inside
    # Phase 2 (recovering): mouth shrinks back to 0
```

### E.9 Stripe Opacity & Drawing Order

- Draw body fill first (body/base color)
- Draw belly fill (lighter color)
- Draw stripes over both (semi-overlapping body)
- Draw head, ears, eyes, nose, whiskers last (on top)

For tabbies: reduce stripe opacity slightly (alpha ~200/255) so they blend naturally with the body color rather than looking painted on top.

---

## Appendix: Quick Reference — All Color Hexes

| Part         | Orange Tabby | Gray Tabby  | Tuxedo    | Calico     | Siamese    | Black      | Tortie     |
|--------------|-------------|-------------|-----------|------------|------------|------------|------------|
| Body         | #E89B5D     | #7C8E9E     | #2F2F2F   | #FEFAF0    | #F5E6CC    | #1A1A1A    | #2F2F2F    |
| Belly        | #FCE6C9     | #D4D9DE     | #FEFEFE   | #FEFAF0    | #FAF0DD    | #333333    | #4A3A2A    |
| Stripe       | #C47A3C     | #5A6B7A     | N/A       | N/A        | #6B4E37    | N/A        | #CC7A3C    |
| Nose         | #F08080     | #FF9494     | #333333   | #F08080    | #6B4E37    | #444444    | #806060    |
| Ear inner    | #FFB6C1     | #FFB8C6     | #555555   | #FFB6C1    | #8B6E57    | #555555    | #8B6E57    |
| Eye          | #4CAF50     | #6BA3D6     | #E8D53F   | #8BC34A    | #4A90D9    | #F0E68C    | #E8D53F    |
| Paw pads     | #D4956A     | #CCD5DC     | #FEFEFE   | #FEFAF0    | #6B4E37    | #444444    | #554444    |
| Whisker      | #D4D4D4     | #A8B0B8     | #E0E0E0   | #D4D4D4    | #F0F0F0    | #BBBBBB    | #BBBBBB    |
| Chin patch   | Yes (white) | Yes (white) | Yes       | Yes        | No         | No         | No         |
| "M" mark    | Yes         | Yes         | No        | No         | No         | No         | No         |
| Stripe style | mackerel    | classic     | none      | patch      | point      | none       | patch      |