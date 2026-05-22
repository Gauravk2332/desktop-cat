# RESEARCH_REAL_CAT.md — Exhaustive Cat Anatomy, Behavior & Simulation Reference

## 1. Orange Tabby: The Archetype

### 1.1 Coat Patterns
- **Mackerel tabby** (most common in orange): Vertical stripes down sides like a fish skeleton, M on forehead, necklaces, leg bracelets, ringed tail. Each stripe runs from spine down toward belly.
- **Classic/blotched tabby**: Swirling marble patterns on sides, bullseye target on flank, butterfly pattern over shoulders. Less common but striking.
- **Ticked tabby**: No stripes on body, but agouti banding on each hair — looks solid from distance but each hair has alternating light/dark bands.
- **Spotted tabby**: Broken mackerel stripes that form spots.

**Orange tabby specific:** Nearly all orange tabbies are mackerel pattern. The M on forehead is universal. Cheek stripes (two vertical on each cheek) and eyeliner (dark line around eyes) are defining features. Belly is always lighter — cream to pale orange. Nose is pink with dark outline. Paw pads are pink. Eye color ranges from amber to copper to green — most striking on orange is copper/amber.

### 1.2 Orange Tabby Genetics
- ~80% of orange tabbies are male (gene is sex-linked on X chromosome)
- "Orange cat energy" stereotype — friendlier, more food-motivated, more vocal, less strategic
- Famous orange tabbies: Garfield (classic pattern), Puss in Boots (mackerel), orange cats from meme culture

### 1.3 Proportions (Domestic Shorthair)
- **Body length** (nose to tail base): 45-50cm (18-20")
- **Tail length**: 25-30cm (10-12") — roughly 55-65% of body length
- **Shoulder height**: 25-28cm (10-11")
- **Head**: roughly 8-10cm wide (round/soft triangular shape)
- **Ears**: 5-7cm tall, set at 45° from vertical, 2 ear-widths apart
- **Eye**: large relative to head, almond-shaped, iris takes up most of visible eye
- **Nose**: 1.5cm long, slight dip at bridge
- **Whiskers**: spread ~1.5x head width when relaxed, can flare forward to head width
- **Leg ratio**: front legs ~60% of body length, rear legs ~70% (cats are digitigrade — they walk on their toes)
- **Weight**: healthy ~4.5kg (10lb), chonky ~6-7kg (13-15lb)

### 1.4 Anatomical Landmarks (visible from side profile)
- **Scapula (shoulder blade)**: prominent ridge at top of front legs, visible as muscle bulge when walking
- **Hip joint**: rear of body, highest point of back when standing. Visible as rounded contour.
- **Spine line**: from base of neck to base of tail, slight upward arch at mid-back
- **Belly line**: from front legs to rear, slight upward tuck (primordial pouch sags slightly)
- **Flank**: side of torso between ribs and hip — visible as muscled curve
- **Chest**: front of ribcage, visible between front legs
- **Primordial pouch**: loose skin at belly — all cats have it, more pronounced in males. Sways when walking.

## 2. Cat Skeletal Structure (for Animation Reference)

### 2.1 Key Skeletal Landmarks
- **Skull**: short snout, large eye sockets, powerful jaw. From side: dome-shaped top, slight stop at nose bridge.
- **Cervical vertebrae**: 7 — very flexible for head rotation (180° each direction)
- **Thoracic vertebrae**: 13 — each with rib attached. Flexible spine allows back arch (the "Halloween cat" pose)
- **Lumbar vertebrae**: 7 — highly flexible, allows spine to curve and stretch during gallop
- **Sacral vertebrae**: 3 — fused, connects spine to pelvis
- **Caudal vertebrae**: 20-23 — the tail. Highly flexible, used for balance and communication
- **Clavicle**: vestigial (floating bone not attached to other bones) — allows cats to squeeze through tight spaces and always land on feet
- **Scapula**: elongated, not fused to ribcage — moves freely, key to feline fluid movement

### 2.2 Digitigrade Posture
Cats walk on their toes (digitigrade), not their whole foot (plantigrade like humans). The "wrist" (carpus) is the backward-bending joint above the paw. The "knee" (stifle) is the forward-bending joint hidden in the fur.

- Front leg joints: shoulder → elbow (backward) → wrist (forward) → paw
- Rear leg joints: hip → knee (forward) → ankle (backward) → paw

### 2.3 Muscle Groups Visible Through Fur
- **Trapezius**: ridge along top of neck and shoulders
- **Latissimus dorsi**: broad muscle across mid-back, visible when cat stretches
- **Gluteals**: powerful haunch muscles, give rear legs their bulk
- **Triceps**: rear of upper front leg
- **Biceps femoris**: rear thigh muscle, prominent during walking
- **Abdominals**: visible as belly line tuck

## 3. Cat Locomotion — Complete Movement Reference

### 3.1 Walk Gait (the 4-Beat Walk)
- **Pattern**: diagonal pairs move together (left front + right rear, then right front + left rear)
- **Timing for 12-frame cycle at 30fps**:
  - Frames 1-3: RF+LH move forward, LF+RH support weight
  - Frames 4-6: all four paws briefly on ground (support shift)
  - Frames 7-9: LF+RH move forward, RF+LH support weight
  - Frames 10-12: all four paws briefly on ground
- **Stance phase**: paw on ground ~60% of cycle
- **Swing phase**: paw in air ~40% of cycle
- **Overlap**: at least 2 paws always on ground (often 3), never all 4 off ground
- **Walk speed**: ~1-2 body lengths per second for casual walk

### 3.2 Walk Animations — Detailed Per-Frame (12-Frame Cycle)
- **Head bob**: head moves down ~2° during stance phase of front legs, up during swing. Most noticeable vertical movement at the nose.
- **Spine curve**: slight S-curve that shifts — when right front steps forward, spine curves slightly left. When left front steps forward, spine curves right. This lateral flex is what makes cat walk look fluid.
- **Tail counterbalance**: tail swings opposite to front body — when right front moves forward, tail swings slightly right (and vice versa). Tail also has it's own rhythm: a gentle S-wave propagating from base to tip.
- **Shoulder blade rotation**: scapula protracts (moves forward) when leg swings forward, retracts (moves back) when leg pushes off. Creates the "rolling shoulder" look.
- **Hip rotation**: pelvis rotates forward on the swing side, back on the stance side.

### 3.3 Trot (2-Beat Diagonal Gait)
- Faster than walk, used for purposeful movement across room
- Diagonal pairs move together (RF+LH, LF+RH) with a moment of suspension between
- Timing: 8-frame cycle at 30fps
  - Frames 1-3: RF+LH on ground, LF+RH in air
  - Frame 4: suspension (all paws off ground briefly)
  - Frames 5-7: LF+RH on ground, RF+LH in air
  - Frame 8: suspension
- Stance phase ~40%, swing phase ~60%
- Speed: ~2-4 body lengths per second

### 3.4 Gallop (3-Beat Asymmetrical Gait)
- Used for max speed chases
- Sequence: rear legs push (together or slightly staggered) → body extends → front legs reach → body tucks → repeat
- Full gallop cycle (8 frames at 30fps):
  - Frames 1-2: rear legs push off together
  - Frame 3: body fully extended, all paws off ground
  - Frames 4-5: front legs land in sequence (LF then RF or vice versa)
  - Frame 6: body tucks, rear legs come forward under body
  - Frame 7: rear legs land
  - Frame 8: coil to spring again
- Back arch in gallop: maximum flexion (back curves), maximum extension (back straightens)
- Speed: ~5-8 body lengths per second

### 3.5 Stalk/Creep Walk
- Slow, purposeful, low to ground
- Belly nearly touching ground, head low, ears swiveled forward
- Each paw placed deliberately — lifted high and placed silently
- Spread: 16+ frame cycle — extreme slow motion
- Tail: low, tip twitching, not swaying
- Butt wiggle before pounce: rear hips oscillate side to side 2-4 times

### 3.6 Jumping Mechanics
**Pre-jump (crouch/coil):**
1. Hind legs tuck under body (knees forward of hips)
2. Front legs straight, shoulders back
3. Head low, eyes fixed on target
4. Weight shifts rearward

**Launch (spring):**
1. Hind legs explode — hip, knee, ankle extend simultaneously
2. Body launches at 45° angle
3. Front legs lift off ground last
4. At peak height: body is fully extended, paws reaching forward

**Mid-air (tuck):**
1. To clear obstacles: front paws tuck under chin, rear paws tuck under body
2. To reach high surface: front paws reach up, body continues rising

**Landing:**
1. Front paws make contact first (~0.05s before rear)
2. Front legs absorb initial impact (elbows bend deeply)
3. Rear legs land slightly later, absorb second wave of impact
4. Spine flexes to absorb remaining shock
5. Whiskers point forward during jump, relax on landing

**Jump height**: a healthy cat can jump 5-6x its body length vertically (~1.5-2m).

### 3.7 Landing Mechanics (The Righting Reflex)
- When falling: cat senses orientation via vestibular system
- Rotates front half first (spine twists), then rear half follows
- Always lands with all 4 paws spread to absorb impact
- This is why low falls can be more dangerous (not enough time to right)

## 4. Cat Stationary Poses — Detailed

### 4.1 Sitting Positions
- **Alert sit**: legs parallel, paws together, back straight, head up, ears forward, tail curled around front paws or to side
- **Relaxed sit**: splayed slightly, one front paw tucked under, rear leg may show, head at normal level, eyes half-lidded
- **Loaf**: all 4 paws tucked under body, no legs visible, tail wrapped around. Looks like a furry bread loaf. Most compact.
- **Sphinx-like sit**: front paws extended forward, rear legs tucked, chest on ground. More like lying but with head up.

### 4.2 Lying Positions
- **Loaf (all paws tucked)**: classic loaf. Body oval, tail wrapped. Head may be up or resting on paws.
- **Side lie**: full body on one side, legs extended in front, belly exposed. Most relaxed sleep position.
- **Belly-up**: legs in air, head tilted back, full belly exposed. Extreme trust. Vulnerable position — only done when 100% safe.
- **Sprawl**: front paws forward, rear legs splayed back (frog legs), belly on cool surface. Summer heat position.
- **Curled**: nose touches tail in circle. Heat conservation. Tight curl = cold, loose curl = comfortable.

### 4.3 Sleeping Positions & REM
- **Curled tight**: light sleep or cold. Nose tucked into tail.
- **Side sprawl**: mid-depth sleep. Legs extended or gently twitching.
- **Full stretch**: deep REM sleep. Flat on side, legs twitching, whiskers flicking, ears twitching, tail tip twitching.
- **Loaf-sleep**: head resting on paws, eyes fully closed but still somewhat aware (can open instantly).
- **Breathing rate during sleep**: ~15-25 breaths/min for light sleep, 10-15 for deep sleep.
- **REM sleep**: ~5-10 min per cycle, intervals of ~20 min. Dreaming — see paw/kitten movements.

### 4.4 Grooming Positions
- **Paw licking**: one front leg raised at shoulder, head turns toward raised paw. Other three legs support weight.
- **Shoulder/chest licking**: head curled toward chest, neck bent. One paw may brace.
- **Flank licking**: head turns 90° to side, neck stretches. May shift weight for balance.
- **Rear leg grooming**: leg is fully extended and rotated outward (frog-leg position), head reaches over to lick. Looks awkward.
- **Belly grooming**: rolls to side, rear leg holds belly skin taut. Often follows with immediate kick reflex.
- **Tail grooming**: wraps tail around to front, holds with front paws, licks along length.
- **Full grooming sequence**: paw → face/ears → shoulder → flank → belly → rear → tail. Takes 10-20 minutes. Always followed by a shake.
- **Post-meal grooming**: starts immediately after eating, shorter sequence (face + paws).

## 5. Cat Behavior Ethogram — Exhaustive

### 5.1 SLEEP (30-50% of daily behavior for indoor cats)
| Subtype | Duration | Body | Eyes | Ears | Tail | Breathing |
|---------|----------|------|------|------|------|-----------|
| Light nap | 15-30 min | Loaf/curled | Closed or slits | Slightly swiveled | Still/tucked | Normal |
| Deep sleep | 45-90 min | Side lie/stretch | Closed, may twitch | Relaxed | Still | Slow |
| REM sleep | 5-10 min | Full stretch | Rapid movement under lids | Twitching | Tip twitch | Irregular |
| Torpor | 2-4 hours | Tight curl | Closed | Drop to sides | Nose-to-tail | Very slow |

**Trigger**: post-meal, boredom, comfort, warmth, after play, owner sleeping
**Exit**: sound, movement, hunger, cold, need to eliminate

### 5.2 WALK (2-5% of behavior)
| Subtype | Speed | Body height | Head | Tail | Purpose |
|---------|-------|-------------|------|------|---------|
| Casual walk | Slow | Normal | Level | Gently swaying | Exploring, moving to spot |
| Purposeful walk | Medium | Normal | Forward | Higher, tip curve | Going somewhere with intent |
| Patrol walk | Slow | Low | Sweeping left-right | Low, swaying | Territory inspection |
| Stalk | Very slow | Very low | Fixed on target | Low, tip twitch | Hunting |
| Trott | Fast | Slight forward | Forward | Aligned with spine | Quick transit |
| Gallop | Very fast | Extend/tuck cycle | Fixed | Trailing | Chase, prey, play |

### 5.3 SIT (20-30% of waking behavior)
- **Alert sit**: watching, waiting — ready to spring
- **Relaxed sit**: no immediate agenda, comfortable observation
- **Transition sit**: mid-sequence — deciding next action
- **Perch sit**: on narrow surface (window sill, desk edge, shelf) — paws together, back straighter

### 5.4 EAT/DRINK (2-5% of behavior)
**Eating:**
- Kibble: head down, bites individual pieces with side of mouth, crunches audibly
- Wet food: head lower, tongue laps, may use paw to scoop
- Pace: eats at medium speed, pauses periodically to look up and check surroundings
- Post-meal: immediately grooms face and paws

**Drinking:**
- Tongue laps at ~4 laps/second
- Tongue curls backward (backward-facing scoop), forms column of water
- Laps 10-20 times then pauses
- May dip paw and lick paw if water level is low
- Prefers moving water (fountains) — instinctive preference for fresh water

### 5.5 GROOM (5-15% of waking behavior)
- **Full groom session**: 10-20 min, progressive body coverage
- **Quick groom**: 30-60 seconds, face and chest only — after eating, after being pet
- **Stress grooming**: repetitive, focused on one spot (can lead to bald patches)
- **Allogrooming** (social): grooming another cat — usually head and neck (highest trust)
- **Self-grooming sequence**: paw → rub face/ears (wet paw then rub) → shoulder → flank → rear → tail → stand and shake

### 5.6 PLAY (5-10% of waking behavior)
- **Pounce**: crouch → butt wiggle (optional) → spring → land on target → bat with paws
- **Batting**: lying on back or side, batting target with one or both front paws
- **Chasing**: running after moving target (toy, laser, mouse cursor)
- **Bunny-kicking**: holds target with front paws, kicks with rear legs rapidly — instinctive prey-dispatch behavior
- **Stalk-and-ambush**: hides behind object, waits, then springs
- **Fetch**: some cats retrieve thrown objects (atypical, but occurs)
- **Play sequence**: stalk → pounce → bat → hold → bunny-kick → release → reset

### 5.7 STRETCH (1-2% of behavior)
- **Full stretch (downward dog)**: front legs extended forward, rear up, back arched — after sleep
- **Forward stretch**: front legs extended in front, rear legs planted, chest to ground — after lying
- **Side stretch**: cat on side, legs extend fully, spine curves — after side lie
- **Leg stretch**: one rear leg extends out to side, usually after sitting
- **Back arch (Halloween cat)**: along with puffed tail — fear/threat display
- **Yawn**: almost always accompanies a stretch. Mouth wide open, tongue curled. 2-3 seconds.

### 5.8 VOCALIZATIONS — 16+ Distinct Sounds
| Sound | Frequency (Hz) | Duration | Context |
|-------|---------------|----------|---------|
| Short meow | 300-500 rising | 0.3s | Greeting, request ("hi", "food?") |
| Long meow | 400-600 descending | 0.8-1.5s | Demand, complaint |
| Trill/chirrup | 400-700 rising | 0.3s | Happy greeting to owner |
| Purr | 25-150 Hz | Variable | Contentment (also stress/injury) |
| Hiss | Broad spectrum | 0.5-1s | Fear, threat |
| Spit | Explosive | 0.1s | Startle, strong threat |
| Growl | 80-150 Hz | 0.5-3s | Warning, escalate |
| Yowl | 400-800 Hz | 1-3s | Distress, mating call, loneliness |
| Chirp (bird-like) | 800-1500 Hz | 0.15s | Prey frustration, excitement |
| Chatter | Rapid teeth clicks | 0.3s | Frustrated watching (birds outside) |
| Scream | Harsh broad | 1-2s | Extreme fear/pain |
| Mew | High, quiet | 0.2s | Kitten call to mother |
| Caterwaul | Loud, howling | Long | Female in heat |
| Huff | Soft burst | 0.1s | Amused annoyance |
| Moan | Low sustained | 0.5s | Mild frustration |
| Silent meow | Format matched, no sound | 0.3s | Tactical request (cat learns to do this) |

### 5.9 AFFECTION/SOCIAL BEHAVIORS
- **Head bunting**: presses forehead/cheek against person or object — deposits scent from cheek glands (happy/social marking)
- **Body rubbing**: entire body length rub against legs/furniture — scent marking + greeting
- **Tail wrapping**: wraps tail around person's leg or another cat — "I'm here with you"
- **Kneading**: alternates front paws on soft surface — from kitten nursing behavior, comfort/trust
- **Slow blink**: eyes close halfway or fully, hold, open. "I trust you"
- **Following**: moves to same room as owner — companionship, not always food-related
- **Lap sitting**: chooses to sit on person — warmth + trust + bonding
- **Gazing**: soft eye contact, no tension — affection

### 5.10 TERRITORIAL Behaviors
- **Scratching**: vertical/horizontal surfaces. Front claws drag down. Multiple times daily. Marks territory visually + scent from paw pads.
- **Cheek rubbing**: chemical marking from glands on cheeks, chin, lips
- **Flank rubbing**: body brushing furniture, walls — scent marking along path
- **Urine spraying**: vertical surfaces. Both sexes. More common in unneutered males.
- **Midline patrol**: walks along specific path through territory — inspecting all corners

### 5.11 FEAR/THREAT Behaviors
| Level | Posture | Eyes | Ears | Tail | Voice |
|-------|---------|------|------|------|-------|
| Mild wariness | Crouched slightly | Normal | Forward/out | Low, still | Silent |
| Moderate fear | Crouched low | Wide, dilating | Sideways (airplane ears) | Low, tip flicking | Hiss possible |
| High fear | Arched back, puffed | Fully dilated | Flat back/body | Puffed (Halloween tail) | Hiss, growl |
| Panic | Fleeing | Wild | Flat | Tucked | Scream |
| Freeze | Statute-still | Wide, fixed | Back | Still | Silent |

### 5.12 CURIOSITY/INVESTIGATION
- Approach slowly → stop → sniff (nose twitching) → look around → paw touch → sniff again → decide
- Cat investigates any new object in its territory
- Hides initially with new objects, then approaches over time
- "If it fits, I sits" — cats sit in boxes, bags, circles on floor

## 6. Cat Senses — Detailed Reference

### 6.1 Vision
- **Field of view**: ~200° (human: 180°)
- **Binocular overlap**: ~130° (human: 120°) — good depth perception for close range
- **Low-light vision**: 6-8x better than humans — tapetum lucidum reflects light through retina twice
- **Color vision**: dichromatic — blue and green cones, no red cones. See blue-violet and yellow-green.
- **Visual acuity**: ~20/100 (much blurrier than humans at distance)
- **Motion detection**: 10-12x more sensitive than humans — can detect prey movements at 100m
- **Flicker fusion**: 70-80Hz (higher than humans' 50-60Hz) — see CRT screens as flickering
- **Near vision**: poor — can't focus on objects closer than ~25cm (why they sniff things)

### 6.2 Hearing
- **Frequency range**: 48 Hz – 85 kHz (humans: 20 Hz – 20 kHz)
- **Best sensitivity**: 200 Hz – 8 kHz (matches rodent vocalizations)
- **Ear rotation**: 180° independently — each ear can point in different direction
- **Sound localization**: accurate to 3-5° at 1m (humans: ~10°)
- **Hearing sensitivity**: can hear ultrasound (rodent communication)
- **Middle ear**: cats can hear 2 octaves higher than dogs

### 6.3 Smell
- **Olfactory epithelium**: ~20cm² (humans: 3-10cm²). Twice the surface area.
- **Number of olfactory receptors**: ~200 million (humans: ~5 million, dogs: ~300 million)
- **Scent glands locations**: 
  - Cheeks (temporal glands) — most used for marking
  - Chin (submental glands)
  - Lip corners (perioral glands)
  - Forehead
  - Tail base (supracaudal gland)
  - Paw pads (interdigital glands)
  - Anus (anal glands)
- **Flehmen response**: lifts upper lip to transfer scent molecules to vomeronasal organ (Jacobson's organ) — analyzes pheromones

### 6.4 Whiskers (Vibrissae)
- **Arrangement**: 4 rows on each side of muzzle (~24 total)
- **Above eyes**: 3-4 on each side (protective — triggers blink)
- **Chin**: 6-8 shorter whiskers
- **Back of front legs**: carpal whiskers for sensing prey nearby
- **Spread width**: ~1.5x body width when relaxed — used to gauge if cat can fit through openings
- **Positions**:
  - **Forward**: curiosity, hunting, interest — sweeps forward to sense things
  - **Relaxed**: slight forward, natural rest position
  - **Flattened**: fear, aggression, discomfort — pressed against face
- **Whisker fatigue**: overstimulation from constant touching — cats may avoid food bowls that hit whiskers

## 7. Circadian Rhythm & Daily Life Cycle

### 7.1 Crepuscular Activity Pattern (Dawn + Dusk)
- **Primary activity peaks**: sunrise (+/- 2h) and sunset (+/- 2h)
- **Secondary activity**: evening (after human comes home)
- **Lowest activity**: midday (12-3pm) and midnight-3am
- **Wild cat schedule**: hunt dawn → eat → groom → sleep → hunt dusk → eat → groom → sleep
- **Indoor cat adaptation**: shifts activity to align with owner's schedule

### 7.2 Typical Indoor Orange Tabby Day
| Time (24h) | Phase | Activity Level | Typical Behavior |
|------------|-------|---------------|------------------|
| 05:00-06:00 | Pre-dawn stir | Low-medium | Stretch, yawn, meow for food, patrol |
| 06:00-07:00 | Dawn peak | HIGH | Active play, food demand, window watching |
| 07:00-09:00 | Morning transition | Medium | Eat, groom thoroughly, find sunny spot |
| 09:00-12:00 | Morning nap | Low | Curled sleep in warm spot (sun beam) |
| 12:00-14:00 | Midday | Very low | Deep sleep, barely moves |
| 14:00-16:00 | Afternoon stir | Low-medium | Position change, look around, minor stretch |
| 16:00-17:00 | Pre-dusk | Medium | Wake fully, full stretch, blink, patrol |
| 17:00-18:00 | Dusk peak | HIGH | The "witching hour" — zoomies, chase, play maelstrom |
| 18:00-19:00 | Evening | Medium-High | Food interest, social time, lap sitting |
| 19:00-21:00 | Evening quiet | Medium | Groom, window watch, follow owner room to room |
| 21:00-22:00 | Wind-down | Low-Medium | Find sleep spot, knead bedding, curl up |
| 22:00-00:00 | Light sleep | Low | First sleep cycle, may wake briefly |
| 00:00-04:00 | Deep sleep | Very low | May wake once or twice for quick patrol/drink |
| 04:00-05:00 | Pre-dawn | Low | Position change, brief alertness |

### 7.3 Total Daily Time Budget (Indoor Cat)
| Activity | Percentage | Hours/day |
|----------|-----------|-----------|
| Sleep/nap | 50-60% | 12-15h |
| Groom | 10-15% | 2-4h |
| Patrol/explore | 5-10% | 1-2h |
| Eat/drink | 2-5% | 0.5-1h |
| Play | 3-10% | 0.5-2h |
| Watch/observe | 5-10% | 1-2h |
| Social (with owner) | 3-10% | 0.5-2h |
| Other (eliminate, scratch) | 1-3% | 15-30min |

## 8. The "Feel Alive" Checklist — What Makes a Virtual Cat Feel Real

### 8.1 Anticipation
Cat starts an action, pauses, changes mind. E.g., starts walking toward food bowl, stops halfway, sits, grooms, then continues.

### 8.2 Small Continuous Behaviors
Cats rarely do nothing. Even when "resting," they have micro-movements:
- Tail tip twitch every 5-10 seconds
- Ear rotation to track sounds every 3-10 seconds
- Whisker position change every 10-30 seconds
- Subtle breathing visible as body rise/fall
- Eye blink every 10-20 seconds (or slow blink every 20-40 seconds when relaxed)
- Head reposition every 1-5 minutes

### 8.3 Contextual Awareness
Cat should respond to what's happening:
- Rain outside → more likely to sleep, less likely to window-watch
- Owner using keyboard → may sit on desk near keyboard (warmth + attention)
- Owner on video call → may sit in front of camera (classic cat behavior)
- Time of day → dawn/dusk activity peaks
- Recent events → just ate → groom. Just woke → stretch. Just played → pant briefly then groom.

### 8.4 Habituation
If the cat sees the same thing repeatedly (a screensaver, a static desktop item), it should stop reacting to it after 2-3 times. Novelty gets attention.

### 8.5 Preference Formation
After 2-3 days:
- "Learns" where the sunny spot is (right side of desk at 10am)
- "Learns" where food appears (if user feeds at same spot)
- "Learns" owner's schedule (wakes up at 7am → starts being active at 6:45am)
- "Prefers" one sleeping spot over another

### 8.6 Comfort-Seeking
- Moves to warm areas (where the sun is, near a warm monitor, near the user)
- Moves to soft surfaces (if there's a blanket or soft object on desk)
- Avoids cold, drafts, noise
- Seeks high vantage points

### 8.7 Curiosity-Drive
- Investigates new objects placed on desktop (cursor, new window, download icon)
- Bats at moving objects (loading spinner, cursor, animated ad)
- Sits on paper/book/keyboard — if it's flat and in my spot, I sit

### 8.8 Transitions Between States
The in-between moments matter more than the states themselves:
- Sit → stand: front legs straighten first, rear legs follow, slight stretch mid-way
- Stand → walk: one paw lifts hesitantly, then commits
- Sleep → wake: eyes open slowly, blink once or twice, yawn, stretch front legs, stretch rear legs, sit up
- Walk → sit: pause, front paws step together, rear tucks, tail wraps
- Alert → relax: ears rotate from forward to side, eyes go from wide to half-lidded, body deflates slightly

---

**End of research document. This covers all major areas for building a realistic cat simulation.**
