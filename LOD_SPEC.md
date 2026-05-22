# LOD Specification — Desktop Cat Sprite

## Overview

The desktop cat renders at variable sizes depending on window dimensions, screen density, and user preference. This spec defines per-size rendering rules so the cat looks intentional at every scale — never muddy, never harsh, never lost.

Three LOD bands:

| LOD | Pixel Height | Label    |
|-----|-------------|----------|
| S   | 120–150 px  | Small    |
| M   | 150–250 px  | Medium   |
| L   | 250–350 px  | Large    |

Frames are always rendered from the same source spritesheets (400×400 px). The runtime scales them. These are *post-scale adjustments* applied in shader or compositing.

---

## LOD S — Small (120–150 px)

### Goal
Readability at a glance. The cat must remain recognizable as a cat with a clear silhouette, even on a taskbar or in a compact window.

### Adjustments

| Property | Value | Rationale |
|----------|-------|-----------|
| **Outline** | 1 px dark brown `#1A0F05` outer contour | Prevents the cat from blending into the background at small size. Painterly soft edges collapse at this scale. |
| **Contrast** | +15–20% (multiply contrast, not brightness) | Lost midtone separation needs recovery. |
| **Saturation** | +10% | Warms the orange and prevents desaturated mush. |
| **Stripe contrast** | +25% (stripes darken toward `#A8541E`) | Stripe separation collapses fastest at this LOD. Boost targeted to stripe pixels only. |
| **Eye prominence** | +20% iris brightness, catchlight → 3 px | Eyes are the character anchor. Enlarged catchlight maintains life. |
| **Shadow opacity** | 20% (down from 35%) | Heavy shadows at small scale turn into blobs. |
| **Sharpen** | None | Avoid ringing artifacts on thin geometry. |

### Shader / Compositing Notes
- Apply a 1 px morphological outline pass (erode alpha, then stroke composite).
- Contrast and saturation: standard HSL adjustment before tint pass.
- Stripe boost: multiply stripe pixels (from original source) by 1.25 in RGB.

---

## LOD M — Medium (150–250 px)

### Goal
Display the cat **as-drawn**. This is the artist's intended presentation — the sweet spot where painterly detail is fully visible without pixel peeping.

### Adjustments

| Property | Value |
|----------|-------|
| **Outline** | None. No outline pass. The cat breathes through its own value edges. |
| **Contrast** | None (0%). Keep original. |
| **Saturation** | None (0%). Keep original. |
| **Stripe contrast** | None. |
| **Eye prominence** | None. |
| **Shadow opacity** | Original 35%. |
| **Sharpen** | None. |

This LOD is the reference. All other LODs are derived from this baseline.

---

## LOD L — Large (250–350 px)

### Goal
Hold up to close inspection. At this scale, the user sees individual brush strokes. The cat should feel **rich and tactile** — like a framed print.

### Adjustments

| Property | Value | Rationale |
|----------|-------|-----------|
| **Outline** | None | Painterly style must not gain outlines at large size. |
| **Contrast** | +5% | Very gentle lift to compensate for perceived flatness when scaled up. |
| **Saturation** | None | Large size reveals the full palette already. |
| **Stripe contrast** | Check only. If stripe/base coat difference < 20% in L\* (CIELAB), boost to 20%. | Ensure stripes remain distinct. |
| **Eye prominence** | None | Eyes at this size are large enough. |
| **Shadow opacity** | 12–15% (down from 35%) | Full-opacity shadows at large scale look heavy and dirty in a painterly piece. Reduce for a softer, more illustrative feel. |
| **Sharpen** | Subtle unsharp mask: radius 0.5 px, amount 0.3, threshold 0 | Counteracts softness from bilinear upscale. Very subtle — must not introduce halos. |

### Stripe Contrast Check (CIELAB)
```
1. Convert stripe pixel and adjacent base-coat pixel to CIELAB
2. Compute ΔE* (CIE76)
3. If the stripe is base coat: ΔE threshold is 20
4. If ΔE < 20, boost stripe R/G/B values by factor = 20/ΔE, clamped to 1.5× max
```

---

## Crossfade Boundaries

When the cat resizes across LOD boundaries, apply a **smooth crossfade** over a 10 px height window to prevent visual pops.

### Crossfade Windows

| From → To | Window | Blend |
|-----------|--------|-------|
| S → M     | 145–155 px | Linear lerp all adjustment parameters over the window. At 145 px: full S settings. At 155 px: full M settings. |
| M → L     | 245–255 px | Same. At 245 px: full M. At 255 px: full L. |
| S → L     | (never direct — always passes through M via crossfade cascade) | |

### Crossfade Formula
```glsl
float t = clamp((currentHeight - windowStart) / (windowEnd - windowStart), 0.0, 1.0);
// t=0 at lower band, t=1 at upper band
// Lerp each adjustment parameter linearly by t
contrast = mix(contrast_lower, contrast_upper, t);
outlineWidth = mix(outlineWidth_lower, outlineWidth_upper, t);
// ... etc for all parameters
```

---

## Eye Compositing Per LOD

Eyes are composited as a **separate pass** over the body sprite (see `FIVERR_BRIEF.md` eye_rect system). LOD affects the composite:

| LOD | Eye Scale | Eye Treatment |
|-----|-----------|---------------|
| S   | 0.85×     | Slightly enlarge iris relative to head to maintain readability. Boost catchlight to 3 px. |
| M   | 1.0×      | As-drawn. |
| L   | 1.0×      | As-drawn. Add subtle specular detail (secondary catchlight, 1 px, lower-right). |

### Implementation
- Eye sprites are pre-rendered at 400×400 resolution.
- At render time, the eye_rect for the current frame is scaled by the overall cat size.
- LOD S: after scaling, apply a 0.85 multiplier to the iris rect, centered on its original center, to slightly enlarge the visible iris relative to the head.
- Catchlight size: S = 3 px, M = 2 px, L = 2 px primary + 1 px secondary.

---

## Pipeline Reference

```
Source PNG (400×400)
        │
        ▼
    Scale to target height (bilinear)
        │
        ├── LOD S ──► Outline pass → HSL adjust → Stripe boost → Eye composite
        │
        ├── LOD M ──► (passthrough) → Eye composite
        │
        └── LOD L ──► Shadow reduce → Unsharp mask → Stripe check → Eye composite
                              │
                              ▼
                        Output frame
```

---

## Presets (Recommended Defaults)

| Context               | LOD | Height | Rationale |
|-----------------------|-----|--------|-----------|
| Taskbar / compact     | S   | 128 px | Fits standard taskbar. |
| Widget / HUD          | S   | 144 px | Slightly larger for glanceability. |
| Default desktop       | M   | 192 px | Standard small-window companion. |
| Large desktop / focus | M   | 224 px | Comfortable reading size. |
| Presentation / stream | L   | 300 px | Showcasing the cat's detail. |
| Max pop-out           | L   | 336 px | Largest before exceeds frame. |

Size is configurable by the user. These are the runtime defaults.

---

## Edge Cases

1. **Below 120 px**: Cat should not render below 120 px. Hide or show a simplified icon (paw print silhouette, 32×32 px).
2. **Between band values (e.g., 147 px)**: Crossfade is active. Do not snap.
3. **Non-integer scaling**: Always round the final composited image to nearest integer dimensions. Avoid sub-pixel rendering on the outline pass.
4. **High DPI (Retina)**: Render at 2× the logical LOD height, then downscale. This applies crossfade at the logical height boundaries, not the pixel-doubled height.
5. **Animation during resize**: Crossfade should complete within 150 ms of resize end. Do not animate LOD transitions frame-by-frame in the walk cycle.

---

## Summary Table

| LOD | Height   | Outline | Contrast | Saturation | Stripe | Eye       | Shadow | Sharpen |
|-----|----------|---------|----------|------------|--------|-----------|--------|---------|
| S   | 120–150  | 1 px    | +18%     | +10%       | +25%   | +20%, 3px | 20%    | None    |
| M   | 150–250  | None    | 0%       | 0%         | 0%     | As-drawn  | 35%    | None    |
| L   | 250–350  | None    | +5%      | 0%         | Check  | 2nd spec  | 13%    | 0.3/0.5 |
