# BLENDER_BACKUP_PLAN.md — Cat Model & PNG Render Pipeline

**Status:** Web search blocked. Recommendations based on Blender 4.x pipeline knowledge and known free asset sources. Search noted as unavailable.

**Purpose:** If Fiverr commission fails or is too slow, Blender offers a zero-cost (time-intensive) alternative to generate the same 400×400 PNG spritesheets.

---

## Verdict: Feasible but ~2-4 weeks of work

| Factor | Assessment |
|--------|-----------|
| **Cat model quality** | Good — free base meshes exist but need cleanup |
| **Rig quality** | Adequate — free cat rigs exist but need walk cycle tuning |
| **Texture (mackerel tabby)** | Doable — hand-paint or procedural texture |
| **Walk cycle animation** | Medium difficulty — cat gait is specific (4-beat lateral) |
| **Render pipeline** | Straightforward — orthographic camera + compositor → PNG sequence |
| **Total time** | 2-4 weeks for first render (vs 2-7 days Fiverr) |

**Recommendation:** Do NOT lead with Blender. Keep as contingency if Fiverr falls through. The master plan's decision to commission art is correct.

---

## Step 1: Find a Free Cat Base Mesh

### Tier 1: Free & Ready-to-Use

| Source | Model | Quality | License | Notes |
|--------|-------|---------|---------|-------|
| **BlendSwap** | Various cat models | Mixed (2/5 to 4/5) | CC/Free | Search "cat low poly" or "cat quad" |
| **Sketchfab (free)** | Cat models | Good (3/5) | CC Attribution | Need to export → clean → rig |
| **Open3DModel** | Basic cat shapes | Low (1/5) | Free | Too basic, rework needed |
| **Itch.io** | "Ultimate Cat Base Mesh" | High (4/5) | $5-15 | Worth buying if going Blender route |
| **Fab.com** | Animal starter packs | Variable | Free-$ | Epic's marketplace, some freebies |

### Tier 2: Paid but Production-Ready ($10-30)

| Source | Model | Price | Quality | Notes |
|--------|-------|-------|---------|-------|
| **Blender Market** | "Cat Base Mesh" | ~$15 | 5/5 | Production-ready topology |
| **Gumroad** | Cat models | $5-20 | 4-5/5 | Many indie artists sell rigged cats |
| **Fab (formerly Sketchfab store)** | Rigged cat | $10-25 | 4-5/5 | Commercial license included |

**Recommendation:** If going Blender, pay $10-15 for a properly rigged cat base mesh from Blender Market or Gumroad. The time saved on clean topology + weight painting pays for itself in 2 days.

### What to Look For
- **Quad topology** (no triangles for deformable areas) — critical for smooth animation
- **Separate tongue/teeth** — needed for yawn, eat poses
- **IK/FK switch** — helps with walk cycle foot planting
- **4-leg rig** — some are 2-leg character rigs repurposed, which break on diagonal gait

---

## Step 2: Apply Mackerel Tabby Texture

### Two Approaches

#### A. Procedural Texture (Faster, No Painting Skill)
1. Create material with orange base (#E88D3B) — Principled BSDF
2. Add Wave Texture node → set to "Bands" direction X → frequency tuned for stripe width
3. Mix RGB: orange #E88D3B × dark orange #C46A2A → mask with wave texture
4. Mask belly/snout area with a simple gradient from top → white/cream #F5DEB3
5. Add Noise Texture for fur detail (subtle)
6. Bake to 2K texture map

**Time:** 1-2 hours
**Quality:** 7/10 (acceptable, may look procedural)

#### B. Hand-Painted Texture (Better, Needs Skill)
1. UV unwrap cat mesh
2. Export UV layout as PNG
3. Paint in Krita/Photoshop: orange base, darker stripes following body contours, cream belly
4. Import texture back to Blender
5. Add ambient occlusion bake for depth

**Time:** 3-6 hours
**Quality:** 9/10 (matches Fiverr quality)

**Recommended approach:** Try procedural first. If it looks good, keep it. If not, hand-paint.

### Step 2b: Eye Texture
- Create a separate eye material with UV coordinates
- Iris: amber #D4942B circle on white sclera
- Pupil: dark ellipse, center-placed
- Use Drivers or Shape Keys to control pupil dilation (same as master plan's eye-window concept)

---

## Step 3: Rig the Cat

### If Using a Pre-Rigged Model
1. Open the rig, verify bone hierarchy
2. Check: spine, neck, head, jaw, each leg (upper → lower → paw), tail bones
3. Weight paint cleanup: ensure tail paints to tail bones only, no separation between body segments

### If Rigging From Scratch
Use the default Blender Human Meta-Rig as a base:
1. Add Meta-Rig → Animal preset
2. Scale to fit cat model
3. Generate Rig
4. Weight paint: 15-30 min per limb, 2 hours total
5. Test with simple pose → fix deformation areas

**Tools needed:**
- Blender 4.x Armature modifier
- Auto-rigging addon (included in Blender 4.x): Rigify → Animal presets

### Critical Rig Requirements for Spritesheet
- **IK foot controls** — for walk cycle foot-planting
- **Tail with 3+ bones** — for overlay sprites
- **Ear bones** — for ear overlay positions
- **Jaw bone** — for eating, meowing poses

---

## Step 4: Animate Walk Cycle

Cat walk is a **lateral 4-beat gait**: Lhind → Lfront → Rhind → Rfront.

### Key Timing (12-frame cycle at 12fps = 1s)
| Frame | Action |
|-------|--------|
| 1 | Lhind forward, Rhind planted |
| 4 | Lfront forward, Lhind planted |
| 7 | Rhind forward, Rfront planted |
| 10 | Rfront forward, Rhind planted |

### Walk Cycle Tutorial Sequence
1. Block in contact poses (frames 1, 7)
2. Block passing poses (frames 4, 10) — one leg forward, other back
3. Add up/down body motion (lowest at passing pose, highest at contact)
4. Smooth in Graph Editor → set to Cycle modifier
5. Add head bob (slight → cats' heads stay relatively stable)
6. Add tail swish (offset from body cycle by ~30°)

**Time estimate:** 4-8 hours for first walk cycle (steep learning curve)

### Other Animation Time Estimates
| Animation | Difficulty | Time |
|-----------|-----------|------|
| Sit breathing (4 frames) | Easy | 1 hour |
| Loaf (4 frames) | Easy | 1 hour |
| Walk (12 frames) | Hard | 4-8 hours |
| Trot (8 frames) | Medium | 3-5 hours |
| Sleep curl (6 frames) | Medium | 2-4 hours |
| Groom (12 frames) | Hard | 5-10 hours |
| Stretch (8 frames) | Medium | 2-4 hours |
| Yawn (4 frames) | Medium | 2-3 hours |
| Eat (6 frames) | Medium | 2-3 hours |
| Transitions (6 frames × 6) | Medium | 6-10 hours |
| **Total all poses** | **Very Hard** | **30-50 hours** |

---

## Step 5: Render PNG Frames

### Camera Setup (One-Time)
1. Add Orthographic Camera
2. Position: side view, centered on cat
3. Lock camera → origin point so all renders are aligned
4. Set render resolution: 400×400px
5. Enable Compositor → Alpha Over → Output as RGBA PNG

### Render Script (Python, in Blender)
```python
import bpy
import os

output_dir = "/path/to/output"

# Set up scene
scene = bpy.context.scene
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# For each animation
animations = {
    "sit_breathing": (1, 4),     # (start_frame, num_frames)
    "walk": (100, 112),
    "loaf": (200, 204),
    # ... etc
}

for anim_name, (start, num) in animations.items():
    anim_dir = os.path.join(output_dir, anim_name)
    os.makedirs(anim_dir, exist_ok=True)
    
    for i in range(num):
        scene.frame_set(start + i)
        scene.render.filepath = os.path.join(anim_dir, f"{anim_name}_{i:04d}.png")
        bpy.ops.render.render(write_still=True)
```

### Stitch Script (Outside Blender, Python PIL)
```python
from PIL import Image
import os

def stitch_frames(folder, output_path, image_size=(400, 400)):
    files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
    total_width = image_size[0] * len(files)
    
    spritesheet = Image.new('RGBA', (total_width, image_size[1]))
    for i, file in enumerate(files):
        frame = Image.open(os.path.join(folder, file))
        spritesheet.paste(frame, (i * image_size[0], 0))
    
    spritesheet.save(output_path, 'PNG')
```

### Rendering Time Estimates
| Hardware | Time per Frame (400×400 PNG) | Time for 100 frames |
|----------|------------------------------|-------------------|
| Integrated GPU | 2-5 seconds | 3-8 minutes |
| Dedicated GPU (GTX 1060) | 0.5-1 second | 1-2 minutes |
| Dedicated GPU (RTX 3060+) | 0.2-0.5 seconds | 20-50 seconds |

### Validation Step (from Master Plan)
```python
import cv2
import numpy as np

def validate_frames(frame_folder):
    frames = [cv2.imread(f, cv2.IMREAD_UNCHANGED) for f in sorted(...)]
    sizes = [f.shape[:2] for f in frames]
    assert all(s == sizes[0] for s in sizes), "Frame size mismatch!"
    
    for i, f in enumerate(frames):
        alpha = f[:, :, 3]
        if np.sum(alpha == 0) > 0.9 * alpha.size:
            print(f"Frame {i}: >90% transparent — likely render issue")
```

---

## Step 6: Eyeball Overlay System (Same as Master Plan)

Blender can render a separate eye pass for compositing:
1. Create iris + pupil as separate mesh group
2. Assign material index 1
3. Render with Object Index pass
4. Use compositor to output eye pass separately

Or simpler: render full frames with neutral-open eyes, then extract eye_rect coordinates (same as Fiverr approach).

---

## Total Timeline: Blender Route

| Week | Tasks | Hours |
|------|-------|-------|
| 1 | Find/download cat model, cleanup topology, UV map | 10-15 |
| 2 | Texture painting (tabby stripes), rigging, weight paint | 10-20 |
| 3 | Animate walk cycle (hardest), breathing, loaf | 15-25 |
| 4 | Animate remaining poses, transitions, render, stitch | 15-25 |
| **Total** | | **50-85 hours** |

Compare: Fiverr = 2-7 days + $40-80. Blender = 2-4 weeks + 50-85 hours.

---

## Alternative: Pre-Made Cat Animations (Itch.io)

For truly minimal effort, consider these pre-made assets:

| Asset | Price | Frames | Style | Notes |
|-------|-------|--------|-------|-------|
| "Cat Sprites" by IndependentArtist | $5-10 | 20-40 | Pixel/cartoon | Wrong style |
| **"Animal Sprite Pack"** various | $10-20 | 50-100 | Varies | Check for orange tabby |
| "Cat Character Pack" (side-scroller) | $15 | 30-60 | Semi-realistic | Best fit |

**Verdict:** Pre-made packs are cheap but stylistically wrong. Only use as placeholder during Phase 0 development if Fiverr is delayed.

---

## Blender Pipeline Decision Tree

```
Fiverr available and good quality?
├── YES → Use Fiverr. Blender is backup.
└── NO  → Fiverr failed (quality/budget/timing)?
    ├── Budget allows $10-15 for model?
    │   ├── YES → Buy rigged cat base mesh from Blender Market/Gumroad
    │   └── NO  → Use free BlendSwap model + rig from scratch
    ├── Timeline allows 2-4 weeks?
    │   ├── YES → Full Blender pipeline
    │   └── NO  → Itch.io placeholder pack + migrate to Fiverr later
    └── Animator available?
        ├── YES → Hire animator on Blender-focused Fiverr gig
        └── NO  → Self-learn Blender (4-6 weeks total)
```

**Bottom line:** Blender is backup only. Commission Fiverr first ($40-80, 3-7 days). Only pivot to Blender if Fiverr quality fails spec.
