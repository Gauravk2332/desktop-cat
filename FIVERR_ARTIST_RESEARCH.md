# FIVERR_ARTIST_RESEARCH.md — Desktop Cat Spritesheet Artists

**Status:** Web search blocked by Fiverr/DDG bot detection. Recommendations based on domain knowledge of Fiverr market landscape as of 2025-2026. Search was noted as unavailable but actionable recommendations follow.

**Note to Gk:** These are archetypes, not verified listings. I recommend Gk or Coder searches Fiverr directly from a normal browser to confirm current availability/pricing.

---

## Market Overview

Fiverr's 2D game art category has 3 tiers of relevant artists:

| Tier | Price Range | Delivery | Quality Level | Suitability |
|------|------------|----------|--------------|-------------|
| Budget | $15-30 | 2-3 days | Pixel art / cartoony | Low — wrong style |
| Mid | $40-80 | 3-7 days | Painterly, semi-realistic | **Best fit** — right balance |
| Premium | $100-200+ | 7-14 days | Studio-level, multiple revisions | Overkill for 400×400 sprites |

The master plan budgeted $30-50. This sits at the low-mid boundary. Expect to pay **$50-80** for a quality painterly spritesheet with the stripe consistency clause.

---

## Artist Archetypes (5 recommended to search)

### 1. Game Character Spritesheet Specialist (Best Fit)
- **Search terms:** "2D game character spritesheet" / "animal sprite animation"
- **Typical gig title:** "I will create 2D game spritesheet with idle walk and run animation"
- **Price range:** $40-80 per character (single pose sheet)
- **Delivery:** 4-7 days
- **Portfolio indicators:** Shows walking cycles (side view), multiple characters, consistent frame spacing
- **Stripe consistency:** Must explicitly ask — most use UV-unwrapped textures by hand, so stripe-wobble is a known issue
- **Rating check:** Look for 4.9+ with 50+ reviews mentioning "consistent" or "clean frames"
- **Strategy:** Find one with animal sprites in portfolio. Orange tabby is common enough.

### 2. Animal Character Illustrator
- **Search terms:** "cat illustration" / "animal character design"
- **Typical gig title:** "I will design cute animal characters for your game"
- **Price range:** $30-60
- **Delivery:** 2-5 days
- **Portfolio indicators:** Showcases cats, dogs, birds — painterly style, soft shading
- **Watch out:** Many do static illustrations, not frame-by-frame animation. Verify spritesheet experience.
- **Best for:** If you commission spritesheet frames as individual illustrations, then Coder stitches them. More expensive but higher quality control.

### 3. Sprite Sheet & Tileset Artist
- **Search terms:** "spritesheet and tileset" / "pixel art sprites"
- **Typical gig title:** "I will create pixel art spritesheet and tileset for your game"
- **Price range:** $25-50
- **Delivery:** 2-4 days
- **Portfolio indicators:** Shows side-scroller character sprites, often pixel art. Less relevant for painterly style.
- **Verdict:** Wrong aesthetic (pixel) but worth checking if any offer "semi-realistic" as an add-on. Some pixel artists can scale up to painterly.

### 4. 2D Animation Generalist
- **Search terms:** "2D animation frame by frame" / "character animation spritesheet"
- **Typical gig title:** "I will animate your character frame by frame"
- **Price range:** $50-120
- **Delivery:** 5-10 days
- **Portfolio indicators:** Quality frame-by-frame animation, smooth cycles, diverse styles
- **Best for:** An animator who can take an existing character design and produce frames. If you provide the cat design reference, they handle the animation.
- **Risk:** May not handle texture/stripe consistency across frames if they're purely animation-focused. Need to verify.

### 5. High-End Game Asset Artist (Premium)
- **Search terms:** "game assets" / "character design for games"
- **Typical gig title:** "I will design professional 2D game assets and characters"
- **Price range:** $100-200
- **Delivery:** 7-14 days
- **Portfolio indicators:** Portfolio-grade work, multiple styles, AAA-quality sprites
- **Verdict:** Over budget but worth considering if Phase 0+1 sprites are bundled as one $100-150 order for all 12 poses + transitions. Saves coordination cost.

---

## Recommended Search Strategy

### Primary Query
```
"2D character spritesheet" + "animal" + "frame by frame"
```

### Filter Criteria
1. **Level 2 Seller or Top Rated Seller** (not New Seller — too much risk)
2. **Portfolio includes side-view animal walk cycles** (non-negotiable)
3. **Reviews mention "consistent across frames" or "clean animation"**
4. **Response rate > 95%** (communication matters for stripe consistency)
5. **Accepts revisions** (minimum 2 rounds for stripe correction)

### What to Look for in Portfolio
- Side-view cat or dog animation loops
- Painterly/soft style (not pixel, not vector flat, not hyper-realistic)
- Consistent character proportions across frames
- Clean frame separation (no smearing across frame boundaries)

---

## Pricing Estimate (Multiple Quotes)

Given the 12 poses + 6 transitions + overlays from the master plan, here's the likely cost breakdown:

| Scenario | Poses | Sheet Style | Est. Cost | Timeline |
|----------|-------|-------------|-----------|----------|
| Phase 0 only (sit, walk, loaf) | 3 poses | One sheet | $30-45 | 3-5 days |
| Phase 1 full (all 12 + transitions) | 12+6 | Multiple sheets | $120-200 | 2-3 weeks |
| Split across 2 artists | 2 bundles | Per-artist | $80-120 | 1-2 weeks |
| Single artist, bundle deal | All | Negotiated | $100-150 | 2 weeks |

**Recommendation:** Commission Phase 0 (3 poses) from one artist as a test. If quality is good, order Phase 1 from same artist. This mitigates R3 and R6 risks from the risk register.

---

## Contract Must-Haves

These clauses are critical (from MASTER_PLAN_FINAL.md risk register):

1. **Stripe consistency:** "Stripe UV mapping must be consistent across all frames. Stripes must not wobble, shift, or change shape independently of the cat's body."
2. **Frame size:** "All frames must be exactly 400×400 pixels PNG with transparency"
3. **Eye rects:** "Provide eye_rect coordinates (x, y, width, height) for each frame specifying the eye region"
4. **Color spec:** "Base #E88D3B, stripes #C46A2A, belly/chest/snout #F5DEB3, eyes amber #D4942B"
5. **Revisions:** Minimum 2 rounds for stripe/anatomy correction
6. **Review step:** "First draft of 3 frames for review before completing full spritesheet"

---

## Fallback: If Fiverr Doesn't Work

| Option | Cost | Time | Quality |
|--------|------|------|---------|
| ArtStation/DeviantArt commission | $60-150 | 1-3 weeks | Higher (pro illustrators) |
| Itch.io asset packs (pre-made) | $5-15 | Immediate | Good but generic cat |
| Blender render pipeline | $0 (time) | 2-4 weeks | Good with effort |
| AI-generated + manual cleanup | $0 | 2-3 days | Risky — stripe consistency poor |

**Recommendation order:** Fiverr → ArtStation/DeviantArt → Blender → Itch.io pack → AI

---

## Ready-to-Paste Brief for Fiverr Artist

> "I need a horizontal spritesheet for an orange mackerel tabby cat, side view, soft painterly style. All frames: 400×400px PNG with transparency. Critical: consistent stripe UV-mapping across ALL frames — stripes must not wobble or shift independently of the body.
>
> **Color:** base #E88D3B, stripes #C46A2A, belly/chest/snout #F5DEB3, eyes amber #D4942B.
> **Lighting:** Upper-left key at 45°. No hard outlines.
> **Eyes:** Neutral open state. Provide eye_rect coordinates per frame (pupil/iris composited at runtime).
>
> **Phase 0 (test):** Sit-breathing (4 frames), walk (12 frame cycle), loaf (4 frames) = 20 frames total.
>
> **Full scope (after test):** Same cat, all 12 poses + 6 transition strips + overlays (tail, ears). Happy to negotiate bundle pricing after the test delivery is approved."
