# Quality Checklist — Desktop Cat Spritesheet Acceptance

## Purpose

This checklist defines the 10-point acceptance gate for Fiverr deliverable `muse-cat-sprites-v1.0.zip`. Each test must pass before the deliverable is accepted.

**Decision**: Go / No-Go at the bottom.

---

## QC Environment

- View spritesheets at **100% zoom** in a PNG viewer with checkerboard background.
- Load into a test harness that overlays `eye_rect` coordinates as a red bounding box.
- Animate at specified frame rates (sit: 4 fps, walk: 12 fps, loaf: 4 fps).
- Measure colors with an eyedropper tool against sRGB hex targets.

---

## 1. Stripe Consistency Test

### Method
1. Open `cat_sit.png`. Identify the **same stripe** at the midpoint of the flank across all 4 frames.
2. Note its pixel position relative to anatomic landmarks (e.g., "the third vertical bar, centered between elbow and hip").
3. Repeat for `cat_walk.png` across all 12 frames.
4. Repeat for `cat_loaf.png` across all 4 frames.

### Pass Criteria
| Pose  | Must Pass                                          |
|-------|----------------------------------------------------|
| Sit   | All 4 frames: stripe position drifts ≤ 3 px from reference |
| Walk  | All 12 frames: stripe tracks with the flank skin, not the background. Drift across entire cycle ≤ 8 px cumulative (measured at stripe midpoint in canvas space, accounting for body displacement and spine flex) |
| Loaf  | All 4 frames: stripe position drifts ≤ 3 px from reference |

### Stripe Consistency Matrix

| Pose | Frame | Stripe #1 (dorsal) | Stripe #3 (mid-flank) | Stripe #5 (hip) | Tail ring #2 | Result |
|------|-------|-------------------|----------------------|----------------|-------------|--------|
| Sit  | 0     |                   |                      |                |             |        |
| Sit  | 1     |                   |                      |                |             |        |
| Sit  | 2     |                   |                      |                |             |        |
| Sit  | 3     |                   |                      |                |             |        |
| Walk | 0     |                   |                      |                |             |        |
| Walk | 1     |                   |                      |                |             |        |
| Walk | 2     |                   |                      |                |             |        |
| Walk | 3     |                   |                      |                |             |        |
| Walk | 4     |                   |                      |                |             |        |
| Walk | 5     |                   |                      |                |             |        |
| Walk | 6     |                   |                      |                |             |        |
| Walk | 7     |                   |                      |                |             |        |
| Walk | 8     |                   |                      |                |             |        |
| Walk | 9     |                   |                      |                |             |        |
| Walk | 10    |                   |                      |                |             |        |
| Walk | 11    |                   |                      |                |             |        |
| Loaf | 0     |                   |                      |                |             |        |
| Loaf | 1     |                   |                      |                |             |        |
| Loaf | 2     |                   |                      |                |             |        |
| Loaf | 3     |                   |                      |                |             |        |

*Fill PASS or FAIL per cell. If any cell FAIL, overall stripe consistency is FAIL.*

---

## 2. Frame Alignment Test

### Method
1. Check each frame's canvas boundaries. All spritesheet frames are exactly 400×400 px.
2. Verify the cat's **ground contact point** (lowest opaque pixel) is within 2 px of the same Y coordinate across all frames within a pose.
3. Check that the cat does not clip outside the canvas bounds.

### Pass Criteria
- Frame dimensions match spec (±0 px).
- Ground contact Y variance ≤ 2 px within a pose.
- No pixel data extends beyond 398,398 into the margin zone (last 2 px on any edge may be anti-alias fade only).

---

## 3. Color Accuracy

### Method
1. Sample 5 pixels from the base coat (`#E88D3B`) of the cat in frame 0 of each pose.
2. Sample 5 pixels from the stripe (`#C46A2A`).
3. Sample 3 pixels from the belly (`#F5DEB3`).
4. Sample 2 pixels from the eye (`#D4942B`).
5. Record hex values. Compare to target palette.

### Pass Criteria
| Color     | Target    | Tolerance (ΔE CIE76) | Notes                                |
|-----------|-----------|----------------------|--------------------------------------|
| Base      | `#E88D3B` | ≤ 8                  | Acceptable painterly variation       |
| Stripes   | `#C46A2A` | ≤ 8                  | Must remain distinct from base (>15 ΔE) |
| Belly     | `#F5DEB3` | ≤ 10                 | Slightly more variance permitted for warmth |
| Eye       | `#D4942B` | ≤ 5                  | Eye color must be tight              |
| Shadow    | `#2A1A0A` | ≤ 12                 | Blend-dependent, loose tolerance     |
| No blacks | —         | No pixel < 5% L\*    | Pure black (`#000000`) is forbidden  |

### Color Sample Log

| Pose | Frame | Pixel | Sampled Hex | ΔE from Target | Pass? |
|------|-------|-------|-------------|----------------|-------|
| Sit  | 0     | Base 1 |             |                |       |
| Sit  | 0     | Stripe 1|             |                |       |
| Sit  | 0     | Belly 1|             |                |       |
| Walk | 0     | Base 1 |             |                |       |
| Walk | 0     | Eye 1  |             |                |       |
| Loaf | 0     | Base 1 |             |                |       |
| Loaf | 0     | Stripe 1|             |                |       |

---

## 4. Alpha Edges Check

### Method
1. View each spritesheet on a bright (#FFFFFF) and dark (#1A1A1A) background.
2. Check for:
   - **Fringe pixels**: Semi-transparent color residue at the boundary between opaque and transparent regions.
   - **Halo**: Light or dark rim around the cat's silhouette.
   - **Hard cut**: Abrupt alpha transition (0→255 in 1 px) where feathering is expected.

### Pass Criteria
- No visible fringe on either background at 100% zoom.
- Alpha transition from 255→0 spans ≥ 3 px (soft edge) and ≤ 8 px (no excessive glow).
- No pixel exceeds 50% alpha within 2 px of the frame edge (400,400 boundary).

---

## 5. eye_rect Coordinate Accuracy

### Method
1. Load `manifest.json`.
2. For each pose and frame, overlay a red bounding box at the declared `eye_rect` coordinates.
3. Verify:
   - Bounding box tightly contains the visible iris + pupil with ≤ 2 px margin on any side.
   - Box does not extend beyond the eye area into fur or eyelid.
   - `width` and `height` are consistent (±3 px) across frames within a pose (except blink frames, where height may be reduced).

### Pass Criteria
- All eye_rects pass visual overlay check.
- Non-blink frames: width variation ≤ 3 px, height variation ≤ 3 px within pose.
- Blink frames: height may be ≤ 60% of open height; width must remain within 3 px of open frames.

### eye_rect Audit Log

| Pose | Frame | Declared rect | Eye visible? | Tight fit? | Pass? |
|------|-------|--------------|--------------|------------|-------|
| Sit  | 0     | [165,115,30,18] |             |            |       |
| Sit  | 1     | [165,115,30,18] |             |            |       |
| Sit  | 2     | [165,118,30,14] |             |            |       |
| Sit  | 3     | [165,115,30,18] |             |            |       |
| Walk | 0     | [165,113,30,18] |             |            |       |
| Walk | 1     | [167,112,30,18] |             |            |       |
| Walk | 2     | [169,110,30,18] |             |            |       |
| Walk | 3     | [170,112,30,18] |             |            |       |
| Walk | 4     | [168,113,30,18] |             |            |       |
| Walk | 5     | [165,115,30,18] |             |            |       |
| Walk | 6     | [163,113,30,18] |             |            |       |
| Walk | 7     | [161,112,30,18] |             |            |       |
| Walk | 8     | [159,110,30,18] |             |            |       |
| Walk | 9     | [158,112,30,18] |             |            |       |
| Walk | 10    | [160,113,30,18] |             |            |       |
| Walk | 11    | [163,115,30,18] |             |            |       |
| Loaf | 0     | [170,145,28,16] |             |            |       |
| Loaf | 1     | [170,145,28,16] |             |            |       |
| Loaf | 2     | [170,148,28,12] |             |            |       |
| Loaf | 3     | [170,145,28,16] |             |            |       |

---

## 6. Walk Gait Anatomy

### Method
1. Animate `cat_walk.png` at 12 fps in a loop.
2. Observe the gait pattern frame-by-frame.

### Pass Criteria
- **Lateral walk**: Left front and right hind move together (frames 0–5), then right front and left hind (frames 6–11). Not a pace (same-side legs together).
- **Contact pattern**: Each foot has a clear contact and lift phase. No foot slides on ground without movement.
- **Spine wave**: The spine traces a gentle sine wave vertically (head bob) and laterally (body sway) across the cycle.
- **Tail follow-through**: Tail tip lags behind body movement by ~2 frames.
- **No float**: At least 2 feet contact the ground in every frame.
- **Stride length**: Front and hind paw advance covers 30–50 px per half-cycle (adjust proportionally to cat size).
- **Symmetry**: Frames 0 and 6 (mid-stride of each side) are roughly mirror images (vertical axis).

---

## 7. Head Proportion

### Method
1. Measure the head bounding box (ear tip to chin, nose to back of skull) in frame 0 of each pose.
2. Compare across poses.

### Pass Criteria
- Head width: 55–75 px (14–19% of 400 px canvas)
