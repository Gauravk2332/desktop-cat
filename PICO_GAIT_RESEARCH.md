# Pico Gait Research: Cat Walk Cycle

## Sources Consulted

1. Wikipedia "Gait" — Quadrupedal gait classification, footfall patterns
2. Wikipedia "Cat anatomy" — Locomotion, digitigrade stance
3. Wikipedia "Horse gait" — Walk mechanics (reference for 4-beat gait)
4. Training knowledge: Biomechanics of feline locomotion, pixel art sprite conventions
5. General animation principles: Quadruped walk cycle timing (Richard Williams' Animator's Survival Kit reference)

---

## 1. Cat Walk Gait — Footfall Pattern

Cats use a **diagonal sequence walk** (as opposed to the lateral sequence walk used by dogs and horses).

**Footfall order (4 beats):**

```
Beat 1: Left Hind (LH) contacts ground
Beat 2: Right Front (RF) contacts ground  (LH + RF = supporting diagonal pair)
Beat 3: Right Hind (RH) contacts ground
Beat 4: Left Front (LF) contacts ground  (RH + LF = supporting diagonal pair)
```

**Key characteristic:** Diagonal pairs (LH+RF, RH+LF) move nearly together but with a slight 25% cycle offset — each of the 4 feet lands at a distinct time, creating a stable 4-beat rhythm.

**Phase relationships in 8-frame cycle:**
- LH phase: 0 (reference)
- RF phase: 2 (25% cycle = +2 frames)
- RH phase: 4 (50% cycle = +4 frames)
- LF phase: 6 (75% cycle = +6 frames)
- Each foot is on ground for ~5 frames (62.5% duty cycle), off ground for ~3 frames

---

## 2. Gait Cycle Frames

**Recommendation: 8 distinct frames** for smooth animation at 8-12 FPS.

- 4-frame cycle is too jumpy — legs appear to teleport
- 6-frame cycle is uneven for the 60/40 stance/swing split
- 8-frame cycle maps cleanly to the 4-beat footfall (each beat = 2 frames)

**Stance/swing timing per leg:**
- Stance (on ground): frames 1-5 (5 frames, ~62%)
- Swing (lifted): frames 6-8 (3 frames, ~38%)

---

## 3. Coordinate System

```
Screen coordinates: y increases downward
Cat faces: Right (+x)

Relative to BODY CENTER (0, 0):
  Front shoulder base:  (14, -4)   — towards head, above center
  Back hip base:       (-14, -4)   — towards tail, above center
  Head base:            (24, -6)
  Tail base:           (-24, -4)

All leg coordinates below are RELATIVE TO each leg's base (shoulder/hip).
```

**Leg segment lengths:**
- Upper segment (shoulder→elbow or hip→knee): 12px
- Lower segment (elbow→paw or knee→paw): 14px
- Effective ground reach from base: ~18-22px (varies with leg bend)

---

## 4. Eight-Frame Walk Cycle Table

### Legend
- **FL**: Front Left (near side)
- **FR**: Front Right (far side)
- **BL**: Back Left (near side)
- **BR**: Back Right (far side)
- All (x, y) pairs are **relative to leg base** (shoulder/hip)
- (↓) = paw on ground | (↑) = paw lifted in swing

---

### Frame 1 — Contact (LH + RF landing)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↑ swing reach | (-6, 5) | (10, 14) | Swing forward, paw approaching ground |
| FR | ↓ stance contact | (-3, 5) | (14, 20) | RF landing, reaching forward |
| BL | ↓ stance contact | (-3, 6) | (12, 20) | LH landing, reaching forward |
| BR | ↑ swing lift | (2, 6) | (-12, 16) | RH lifting off, swinging forward |

- **Body bob**: y = +1 (low, double support phase)
- **Head tilt**: 0° (level)
- **Tail sway**: -15° (slight swing toward tail side)

---

### Frame 2 — Weight Support (diagonal pair LH+RF supporting)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↑ mid-swing | (-4, 4) | (5, 12) | Forward swing continues |
| FR | ↓ stance | (-1, 5) | (8, 20) | Weight bearing, slightly back |
| BL | ↓ stance | (-1, 6) | (7, 20) | Weight bearing, slightly back |
| BR | ↑ mid-swing | (0, 5) | (-7, 14) | RH swinging forward |

- **Body bob**: y = 0 (neutral, body leveling)
- **Head tilt**: +2° (slight nod forward)
- **Tail sway**: -10°

---

### Frame 3 — Mid-Stance (diagonal pair LH+RF at vertical)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↑ forward reach | (-3, 2) | (14, 8) | Nearing full forward extension |
| FR | ↓ stance vertical | (0, 6) | (0, 20) | RF directly below shoulder |
| BL | ↓ stance vertical | (0, 7) | (0, 20) | LH directly below hip |
| BR | ↑ forward reach | (-2, 3) | (14, 10) | Swinging forward |

- **Body bob**: y = -2 (highest, inverted pendulum peak)
- **Head tilt**: +5° (slight upward tilt as body rises)
- **Tail sway**: -5°

---

### Frame 4 — Push-Off (diagonal pair LH+RF pushing back, RH+LF preparing to land)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↓ landing prep | (-12, 5) | (15, 22) | LF about to land |
| FR | ↓ push-off | (0, 7) | (-8, 20) | Pushing backward |
| BL | ↓ push-off | (0, 7) | (-8, 20) | Pushing backward |
| BR | ↓ landing prep | (-12, 5) | (16, 22) | RH about to land |

- **Body bob**: y = -1 (falling slightly)
- **Head tilt**: +3°
- **Tail sway**: 0° (centered)

---

### Frame 5 — Opposite Contact (RH + LF landing)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↓ stance contact | (-3, 5) | (14, 20) | LF landing, reaching forward |
| FR | ↑ swing lift | (6, 6) | (-12, 14) | RF lifting, swinging back-to-forward |
| BL | ↑ swing lift | (3, 5) | (-14, 16) | LH lifting, swinging back-to-forward |
| BR | ↓ stance contact | (-3, 6) | (12, 20) | RH landing, reaching forward |

- **Body bob**: y = +1 (low, double support phase)
- **Head tilt**: 0° (level)
- **Tail sway**: +15° (swung to opposite side)

---

### Frame 6 — Opposite Weight Support (diagonal pair RH+LF supporting)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↓ stance | (-1, 5) | (8, 20) | Weight bearing, slightly back |
| FR | ↑ mid-swing | (4, 4) | (-7, 12) | RF swinging forward |
| BL | ↑ mid-swing | (1, 5) | (-9, 14) | LH swinging forward |
| BR | ↓ stance | (-1, 6) | (7, 20) | Weight bearing, slightly back |

- **Body bob**: y = 0 (neutral)
- **Head tilt**: -2° (slight nod down)
- **Tail sway**: +10°

---

### Frame 7 — Opposite Mid-Stance (diagonal pair RH+LF at vertical)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↓ stance vertical | (0, 6) | (0, 20) | LF directly below shoulder |
| FR | ↑ forward reach | (3, 2) | (-14, 8) | Swinging far forward |
| BL | ↑ forward reach | (-2, 3) | (-14, 10) | Swinging forward |
| BR | ↓ stance vertical | (0, 7) | (0, 20) | RH directly below hip |

- **Body bob**: y = -2 (highest again)
- **Head tilt**: -5° (slight downward tilt)
- **Tail sway**: +5°

---

### Frame 8 — Opposite Push-Off (RH+LF pushing back, LH+RF preparing to land)

| Leg | Status | upper_end (x,y) | paw (x,y) | Notes |
|-----|--------|-----------------|-----------|-------|
| FL | ↓ push-off | (0, 7) | (-8, 20) | Pushing backward |
| FR | ↓ landing prep | (12, 5) | (-15, 22) | RF about to land |
| BL | ↓ landing prep | (3, 5) | (-16, 22) | LH about to land |
| BR | ↓ push-off | (0, 7) | (-8, 20) | Pushing backward |

- **Body bob**: y = -1 (falling)
- **Head tilt**: -3°
- **Tail sway**: 0° (centered, return to start)

---

## 5. Body Movement Summary

| Frame | Body bob y | Head tilt | Tail sway | Supporting diagonal |
|-------|-----------|-----------|---|---------------------|
| 1     | +1        | 0°        | -15°      | LH+RF contact       |
| 2     | 0         | +2°       | -10°      | LH+RF support       |
| 3     | -2        | +5°       | -5°       | LH+RF mid-stance    |
| 4     | -1        | +3°       | 0°        | LH+RF push-off      |
| 5     | +1        | 0°        | +15°      | RH+LF contact       |
| 6     | 0         | -2°       | +10°      | RH+LF support       |
| 7     | -2        | -5°       | +5°       | RH+LF mid-stance    |
| 8     | -1        | -3°       | 0°        | RH+LF push-off      |

**Body bob amplitude:** ~3px peak-to-peak (ranges from y=-2 to y=+1)

**Head movement:** Head tilts in the direction of forward motion — slightly up during LH+RF support, slightly down during RH+LF support. Overall stays quite level; the bob is more of a gentle undulation.

**Tail movement:** The tail acts as a counterbalance. It swings toward the side of the forward-reaching front leg:
- When RF is reaching forward (frames 1-4): tail swings left/negative (-15° to 0°)
- When LF is reaching forward (frames 5-8): tail swings right/positive (+15° to 0°)
- The tail motion is a smooth sine wave oscillator, not jerky

---

## 6. Speed & Timing

| Parameter | Value | Notes |
|-----------|-------|-------|
| Walk cycle duration | ~0.6-0.8 sec per full cycle | Slow casual cat walk |
| Frames per cycle | 8 | Smooth loop |
| Frame rate | 10-12 FPS | Ideal for cartoon walk |
| Steps per second | ~2.5-3.3 | 8 frames / (10-12 FPS) inverted |
| Body forward speed (px/s) | ~8-12 px/s at cycle rate | Tune to desired visual speed |
| Ground speed per stride | ~5-8 px | Distance body travels per cycle |

**For a slow, casual walk:** Use 12 FPS with 8 frames = 0.67s per cycle. This gives a relaxed, unhurried gait appropriate for a desktop cat.

---

## 7. Implementation Notes for PyQt6

### Diagonal pairing reminder
```
Diagonal Pair A: LH (Back Left) + RF (Front Right) — move together
Diagonal Pair B: RH (Back Right) + LF (Front Left) — move together
They are 4 frames out of phase (half cycle apart)
```

### Ground collision
- When a paw's y reaches ~20 relative to its base, it's "on the ground"
- The cat's body should be drawn so the base y positions place paws at the intended ground level
- Body bob shifts everything: when bob is -2 (up), legs need to reach slightly further down

### Recommended easing
- Use sinusoidal easing for paw swing motion (smooth acceleration/deceleration)
- Body bob should use a smooth sine wave: `bob_y = amplitude * sin(phase)`

### Leg rendering order (z-index)
1. Far-side legs (FR, BR) — drawn first (behind body)
2. Body — drawn next
3. Near-side legs (FL, BL) — drawn last (in front of body)

### Debug visualization
- Draw small circles at each joint (base, upper_end, paw)
- Draw lines connecting the joints
- Color-code diagonal pairs (Pair A = green, Pair B = blue)

---

## 8. References for Further Reading

- Hildebrand, M. (1989). "Vertebrate locomotion — gait classification". *BioScience* 39(11): 764-765.
- Wikipedia: "Gait" — Quadrupedal gait classification and footfall patterns
- Wikipedia: "Cat anatomy" — Locomotion section, digitigrade stance
- Richard Williams (2001). *The Animator's Survival Kit* — Quadruped walk cycle principles
- Pixel art sprite references: OpenGameArt "LPC Cat", Itch.io cat sprite packs
