# Fiverr Commission Brief: Orange Mackerel Tabby Cat Spritesheet

## Overview

Commission a **side-view orange mackerel tabby cat** spritesheet system for a desktop companion app. The cat is a semi-realistic painterly character — warm, stylized, but grounded in real feline anatomy. Delivery is a set of **horizontal strip spritesheets** (one per pose) with a companion `manifest.json`.

---

## Character Design

### Species & Morphology
- **Subject**: Adult domestic shorthair cat
- **Breed signature**: Orange mackerel tabby
- **View**: **Pure side profile** (sagittal plane). No foreshortening, no ¾ turns, no rotation.
- **Style**: Semi-realistic painterly. Soft brushwork, visible texture, no cel-shading, no hard vector outlines. Think *painterly illustration* — like pastel or digital oil.

### Color Palette (sRGB)

| Feature        | Hex       | Role                              |
|----------------|-----------|-----------------------------------|
| Base coat      | `#E88D3B` | Midtone body fur                  |
| Stripes        | `#C46A2A` | Mackerel stripe markings          |
| Belly/chest    | `#F5DEB3` | Soft warm cream, underside only   |
| Eyes           | `#D4942B` | Amber irises, warm golden         |
| Nose           | `#E57373` | Soft pink, small triangle         |
| Inner ear      | `#F8BBD0` | Pale pink blush, subtle           |
| Shadow         | `#2A1A0A` | 35% opacity multiply — deepest    |
| Outline (LOD)  | `#1A0F05` | 1px only at Small LOD (see LOD spec) |

> **Critical**: No pure black anywhere. All shadows and outlines derive from dark brown `#1A0F05`.

### Stripe Pattern — Mackerel Tabby
- **Dorsal stripe**: Single dark stripe runs along the spine from crown to tail base.
- **Vertical barring**: Thin, slightly curved vertical stripes descending from the dorsal stripe down the flanks. 6–8 bars visible in side view.
- **Leg barring**: 3–4 horizontal rings on each leg (like bracelets).
- **Tail**: Alternating rings, 6–8 total along length. Tip is dark.
- **Forehead "M"**: Classic tabby M marking on the brow — subtle, integrated into painterly strokes.
- **Chest**: Solid cream `#F5DEB3`, no stripes.
- **Belly**: Solid cream `#F5DEB3`, no stripes.
- **Stripe opacity**: 70–85% over base coat. Should feel painted, not stamped.

---

## CRITICAL: Stripe Consistency System

This is the **single most important technical requirement**. The cat appears across multiple poses and frames. **Stripes must track as though applied to a single 3D surface** — not re-drawn per frame.

### UV Map Convention (Mental Model)
Treat the cat's body as a 2D unwrapped texture:

```
Top (dorsal):    [head crown -> spine -> tail top]
Left flank:      [neck -> flank -> hip]
Right flank:     (not visible — side view only)
Underside:       [chin -> belly -> tail underside]
Legs:            [upper arm -> lower leg -> paw]
```

The stripes exist on this UV surface once. Every frame samples from it as the body deforms naturally.

### Frame-to-Frame Rules
1. A stripe visible at the midpoint of the flank in frame 5 must be at the *same anatomic position* in frame 6 — not drifting, not disappearing, not shifting color.
2. When limbs move (walk cycle), stripes on the limb rotate and translate with the bone. They do not slide independently.
3. Body stripes compress slightly when the spine curves (sit, loaf) and stretch when it extends (walk stride).
4. Tail stripes maintain spacing as the tail arcs; they are not evenly spaced in pixel space — they follow tail surface distance.

### Reference layout method
Sketch a **single orthographic reference** of the cat with all stripes mapped before animating any pose. Derive all frames from this reference. If stripes shift between frames in the same pose, the deliverable **fails acceptance**.

---

## Technical Specifications

### Frame Canvas
- **Size**: 400 × 400 pixels per frame
- **Format**: PNG with transparency (alpha channel)
- **DPI**: 72 (standard screen)
- **Color space**: sRGB
- **Max file size per spritesheet**: 2 MB

### The Cat in Frame
- The cat should occupy **roughly 240–300 px** of the 400 px height (i.e., fills ~60–75% of frame height, centered).
- Leave padding for tail extension and ear tips (about 50 px margin on all sides).
- The cat faces **left** (standard for side-scrolling).

### Spritesheet Layout
- **Each pose is one horizontal strip**: frames laid left-to-right in a single PNG.
- Frame width = 400 px. Total spritesheet width = `400 × frame_count` px.
- Height remains 400 px.
- No padding or gutter between frames in the strip.

### Delivery Files

| File | Description |
|------|-------------|
| `cat_sit.png` | Sitting pose strip, 4 frames, 1600×400 px |
| `cat_walk.png` | Walk cycle strip, 12 frames, 4800×400 px |
| `cat_loaf.png` | Loaf pose strip, 4 frames, 1600×400 px |
| `manifest.json` | Metadata file (template below) |

---

## Phase 0 — Poses

### 1. Sit (4 frames)
- **Description**: Cat sitting with front legs straight, hind legs tucked, tail curled around.
- **Frames**: 1-2 soft idle (gentle head bob, ear flick), 3 blink, 4 return to idle.
- **Tail**: Wraps around front paws. Tip may twitch in frame 3.
- **Stripe visibility**: Full flank exposed; dorsal and vertical bars clearly visible.
- **Head**: Slightly raised, alert but relaxed.
- **eye_rect**: Centered in upper third of head. ~30×18 px per eye.

### 2. Walk (12 frames)
- **Description**: Full walk cycle at a casual pace.
- **Frames**: 12-frame cycle (6 frames per stride, mirrored).
  - Frames 1–6: Left front + right hind advance.
  - Frames 7–12: Right front + left hind advance.
- **Gait pattern**: Lateral walk (not pacing). Front paw lifts first, then hind on same side.
- **Head**: Subtle vertical bob — highest at mid-stride, lowest at double-support.
- **Tail**: Gentle S-curve sway counter to head movement.
- **Stripe tracking**: Limb stripes rotate with leg angle. Flank stripes stretch/compress with spine extension.
- **eye_rect**: Position shifts slightly with head bob — ~2 px vertical variance.

### 3. Loaf (4 frames)
- **Description**: Cat tucked into a "loaf" — paws tucked under body, compact oval silhouette.
- **Frames**: 1-2 relaxed loaf, 3 slow blink, 4 return to relaxed.
- **Tail**: Wrapped tight around body or tucked under. Only tip visible.
- **Stripe visibility**: Only dorsal stripe and top of flank bars visible. Belly and legs fully hidden.
- **Head**: Resting low, chin near paws. Ears relaxed, angled slightly outward.
- **eye_rect**: Lower in frame, partially occluded by brow fold in blink frame.
- **Challenge**: Communicating body volume through fur texture alone — few visible contours.

---

## Eye System

### Eye Window
Each frame declares an `eye_rect` — the bounding box of visible eye area (iris + pupil) in canvas coordinates.

- **Format**: `[x, y, width, height]` where (x, y) is top-left corner.
- **Frame canvas**: 400×400 px. Origin top-left.

### Eye States (Phase 0 only uses neutral-open)
- **Neutral-open**: Iris fully visible, pupil circular, slight highlight catchlight (1–2 px white dot at 10 o'clock).
- **(Future) Blink/half-close**: Partial upper lid occlusion.
- **(Future) Alert**: Wider, larger highlight.

### Color
- Iris: Amber `#D4942B`
- Pupil: Near-black `#1A1005`
- Sclera: Not visible (cat eyes are mostly iris when open)
- Catchlight: Pure white, ~2 px, upper-left quadrant of iris

### Coordinates per frame (to be completed by artist)

```json
// cat_sit.png (example)
"eye_rects": {
  "frame_0": [165, 115, 30, 18],
  "frame_1": [165, 115, 30, 18],
  "frame_2": [165, 118, 30, 14],
  "frame_3": [165, 115, 30, 18]
}
```

> Replace values with actual frame measurements. Both eyes use the same dimensions (side view overlaps them).

---

## Lighting & Shading

### Light Source
- **Position**: Upper-left, 45° downward angle.
- **Type**: Soft studio light — no harsh shadows, no rim light.
- **Shadow**: Warm dark brown `#2A1A0A` at 35% opacity multiply. Falls on the lower-right of the body.
- **Highlight**: Subtle warm glow on dorsal ridge, crown, and top of head. Not glossy.

### Shading Rules
1. Underside (belly, chin, inner legs) is in shadow from self-occlusion.
2. The area under the tail where it meets the body is deepest shadow.
3. No hard outline — the cat is defined by value contrast against background, not a line.
4. Fur texture: subtle directional strokes visible at native resolution. Not photo-realistic, not flat.
5. Animated frames maintain consistent lighting: shadows do not jump or shift between frames within a pose.

---

## Deliverable Format

### Spritesheet Files
- PNG-24 with full alpha transparency
- Named per table above
- Pixels must be cleanly opaque or transparent — no semi-transparent fringe pixels at frame edges

### manifest.json Template

```json
{
  "sprite": "Muse Desktop Cat v1.0",
  "author": "[Artist name]",
  "character": "orange_mackerel_tabby",
  "view": "side",
  "style": "semi-realistic_painterly",
  "frame_size": { "width": 400, "height": 400 },
  "poses": {
    "sit": {
      "file": "cat_sit.png",
      "frames": 4,
      "frame_rate": 4,
      "loop": true,
      "eye_rects": {
        "frame_0": [165, 115, 30, 18],
        "frame_1": [165, 115, 30, 18],
        "frame_2": [165, 118, 30, 14],
        "frame_3": [165, 115, 30, 18]
      }
    },
    "walk": {
      "file": "cat_walk.png",
      "frames": 12,
      "frame_rate": 12,
      "loop": true,
      "eye_rects": {
        "frame_0": [165, 113, 30, 18],
        "frame_1": [167, 112, 30, 18],
        "frame_2": [169, 110, 30, 18],
        "frame_3": [170, 112, 30, 18],
        "frame_4": [168, 113, 30, 18],
        "frame_5": [165, 115, 30, 18],
        "frame_6": [163, 113, 30, 18],
        "frame_7": [161, 112, 30, 18],
        "frame_8": [159, 110, 30, 18],
        "frame_9": [158, 112, 30, 18],
        "frame_10": [160, 113, 30, 18],
        "frame_11": [163, 115, 30, 18]
      }
    },
    "loaf": {
      "file": "cat_loaf.png",
      "frames": 4,
      "frame_rate": 4,
      "loop": true,
      "eye_rects": {
        "frame_0": [170, 145, 28, 16],
        "frame_1": [170, 145, 28, 16],
        "frame_2": [170, 148, 28, 12],
        "frame_3": [170, 145, 28, 16]
      }
    }
  },
  "palette": {
    "base": "#E88D3B",
    "stripes": "#C46A2A",
    "belly": "#F5DEB3",
    "eyes": "#D4942B",
    "nose": "#E57373",
    "inner_ear": "#F8BBD0",
    "shadow": "#2A1A0A",
    "outline_lod_small": "#1A0F05"
  },
  "lod_spec": "LOD_SPEC.md"
}
```

### Delivery Format
- **One ZIP archive** containing all spritesheets + manifest.json
- ZIP name: `muse-cat-sprites-v1.0.zip`
- File naming: lowercase, underscore-separated, no spaces

---

## Timeline & Revisions

- Include **1 preliminary sketch** of the cat in sit pose (line art + flat color) for stripe pattern sign-off before full production.
- After approval:
  - Sit: 3 days
  - Walk: 5 days
  - Loaf: 3 days
  - Polish & manifest: 2 days
- **One round of revisions per pose** included in the price.

---

## Do Not

- Do not add background elements, floor shadows, or ground planes.
- Do not rotate or transform the cat in 3D space — side view only.
- Do not use hard-edged line art or vector outlines (except Small LOD per LOD spec).
- Do not vary palette between frames — color consistency is mandatory.
- Do not deliver individual frame files — only horizontal strip spritesheets.
- Do not embed metadata or ICC profiles in the PNG.
