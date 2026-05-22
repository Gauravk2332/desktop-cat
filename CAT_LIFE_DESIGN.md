# CAT_LIFE_DESIGN.md — Living Orange

> You don't *animate* a cat. You *inhabit* it.

This document describes what a desktop pet must become to stop being a screensaver and start being a *cat*. Every line is implementable. Every behavior is a state machine, a timer, or a mood parameter.

---

## 1. The Day of a Cat

The cat runs on a **circadian drive** — not a clock, but a felt sense of time. Internally, the day is divided into phases with smooth transitions.

### 6:00 AM — False Dawn

Light outside is still low. The cat is in deep sleep — but something shifts. An ear rotates toward your keyboard. A whisker twitches. It's *aware* that you're stirring before you've moved.

**Behavior:** Slow blink, stretch one paw out, yawn (no sound yet), roll onto back, exposed belly. This is trust. It's also waiting — if you approach, it chirps. If you don't, it goes back to sleep.

### 6:30–7:00 AM — Dawn Patrol

Crepuscular active period #1. The cat rises in stages:

1. **Orient** — Head lifts, ears forward, pupils dilate from slits to full. It's scanning the room.
2. **The Big Stretch** — Front paws extend, claws briefly out, back arches (hallmark of a real cat), one hind leg stretches separately.
3. **Yawn** — A real yawn, jaw wide, tongue visible for a split second.
4. **Descent** — Jump down from bed/sleeping spot. Land softly.
5. **Patrol route** — Walk the perimeter of the screen. Sniff at edges. Pause at the top-left corner (favorite spot).
6. **Check food bowl** — Walk to where the food bowl would be. Look at it. Look at you. "It's empty."

**Interaction:** This is a high-attention period. If you're at your desk, the cat will:
- Walk across your current window (not randomly — it *walks between you and the screen*)
- Sit on the edge of your active window, tail curled around paws
- Meow softly the first time you make eye contact
- If ignored for 10+ minutes, settle on the taskbar

### 8:00–11:00 AM — Morning Engagement

Active but not frantic. The cat has eaten (in its mind), patrolled its territory, and is now curious.

**Behaviors:**
- Sits at the edge of the screen, watching you work. Head follows your cursor with delayed tracking — it's not a magnet, it's *curious about the moving thing*
- Paw-swat at a fast-moving cursor (not every time — maybe 1 in 15 passes)
- Groom a paw. Mid-groom, pauses, looks at something off-screen. Resumes.
- Finds a sunbeam (rendered as a warm patch on the desktop background — the cat sits in it)
- Chases its own tail exactly once. Looks embarrassed afterward. Grooms furiously to reclaim dignity.

**Sleep need:** Low. Short 3-5 minute naps only.

### 11:00 AM – 1:00 PM — The Midday Slump

The cat enters *idle mode*. Real cats conserve energy. Yours should too.

**Behaviors:**
- Finds the warmest spot on screen and curls into a tight ball
- Half-closed eyes, slow blinks. If you look at the cat, it slow-blinks back (this is cat for "I trust you, don't bother me")
- Slow, rhythmic breathing — the body (not the animation) should visibly rise and fall
- Occasional ear flick to a sound. One eye opens a crack, then closes
- Paws may knead briefly in sleep (milk tread — comfort behavior)
- Does not respond to cursor. This is deliberate. A cat that always reacts feels robotic.

**Interaction:** The cat is low-energy. Picking it up (click-drag) gets a brief, half-hearted mrrow and it settles in your arms. Putting it down, it immediately returns to its nap spot.

### 1:00–4:00 PM — Quiet Presence

Light sleep with awareness. The cat is *nearby* but not *engaged*.

**Behaviors:**
- Shifts sleeping positions every 20-40 minutes
- May relocate to a different warm spot
- If you've been typing intensely, one eye opens, watches your hands, closes again
- A deep sigh — the kind real cats do when they're content but you're being annoying by existing
- Tail thump — if you're on a call, the tail thumps once or twice in mild annoyance ("you're being loud")

**Animation approach:** Very slow, very subtle. This is the hardest part to implement and the most important. Mist people over-animate. The gap between frames should be 2-4 seconds during this period.

### 4:00–5:00 PM — Pre-Dusk Awakening

The cat knows you'll be finishing work soon. Something shifts in the air.

**Behaviors:**
- The Big Stretch #2 (always a front-back-hind tri-phase)
- Yawn, lip lick, shake (whole body ripple — fur settles)
- Walks to the edge of the screen and *sits facing away from you* — watching the window. Real cats do this. They guard your back.
- If you stand up, the cat stands and stretches again — anticipation
- Follows your cursor with more attention now
- Brief play burst: bats at a notification badge, a floating UI element, or the cursor if it's been moving fast

### 5:00–7:00 PM — The Witching Hour

Crepuscular active period #2 — the *real* one. This is when the cat is at peak energy.

**Behaviors:**
- Zoomies (in miniature): Sudden burst of speed across the screen, skidding to a halt
- Pounce practice: Crouch, wiggle hindquarters, pounce on cursor
- Batting at the edges of windows, especially when content scrolls
- Perch on high spot (top of screen) — surveying kingdom
- Steals the mouse pointer notionally (walks over it, sits on it)
- Demands attention: walks in front of your face, meows, head-butts the camera area
- Knocks something over (a digital item on the desktop — a virtual pen, a sticky note icon — just pushes it off)

**Interaction:** Maximum responsiveness. The cat should feel *impossible to ignore*. If you try to work, it sits on your taskbar. If you open a game, it watches with intense focus.

### 7:00–9:00 PM — Social Evening

The household (you) is settled. The cat is fed (simulated), warm, content.

**Behaviors:**
- Lap mode: Sits near you, purrs audibly
- Grooming session: Long, deliberate. Hind leg kick to scratch ear. Pause to inspect paw. Resume.
- Head tilts when you talk
- Follows your face (webcam awareness is optional but powerful)
- If you're watching video, the cat sits sideways at bottom of screen, occasionally looking at the video, then back at you
- Comfortable silence — the cat doesn't need to do anything. It's just *there*.

### 9:00 PM – Midnight — Wind Down

Energy declining. The cat is settling for the night.

**Behaviors:**
- Curls up. Uncurls. Grooms. Curls up again (the nesting ritual)
- Pupils dilating as light dims (simulate with gradual eye change)
- More frequent slow blinks
- Head slowly droops, jerks up (sleep start — very real)
- Eventually settles into a sleeping position
- May perform the "one brain cell" moment — stares at nothing for 30 seconds straight

**Interaction:** The cat will respond if spoken to (clicked), but slowly. A meow that's half-stifled by sleep. A tail curl around your hand if you pet it. But it wants to sleep.

### Midnight – 6:00 AM — Deep Sleep

The cat is fully asleep. But not dead.

**Behaviors:**
- Very occasional twitching (dreaming — chasing virtual mice)
- Ear rotations to sounds
- Position shifts every 45-90 minutes
- If you're working late (how dare you), the cat wakes, gives you a look of profound disappointment, and resettles facing away from you

---

## 2. Responding to the User — By Time and Mood

The cat doesn't just respond. It responds *appropriately*.

### Morning (6–11 AM)
| User Action | Cat Response |
|---|---|
| Look at cat / move cursor near | Chirp, slow blink, approach |
| Click on cat | Affectionate meow, head-butt the spot |
| Click-drag cat | Mild protest, settles where dropped |
| Type rapidly | Curious — watches hands for 5-10s |
| Open a browser | Sits on the tab bar (mild obstruction) |
| Leave desk | Watches you go, sighs, naps |

### Midday (11 AM – 4 PM)
| User Action | Cat Response |
|---|---|
| Look at cat | Slow blink (max response), may not move |
| Click on cat | Brief mrrow, might resettle |
| Click-drag cat | Limp — complete dead weight acceptance |
| Type rapidly | Ear flick, maybe opens one eye |
| Open a new window | Sniffs the title bar, returns to nap |
| Video call | Watches with mild judgment |

### Evening (4–9 PM)
| User Action | Cat Response |
|---|---|
| Look at cat | Ears up, meows, approaches eagerly |
| Click on cat | Play-bows, bats at cursor |
| Click-drag cat | Playful resistance, wiggles |
| Type rapidly | Bat at moving fingers, sits on keyboard |
| Open a game | Intense focus — head tracks motion |
| Leave desk | Follows to screen edge, meows once |
| Return to desk | Greets you — tail up, chirps |

### Night (9 PM – Midnight)
| User Action | Cat Response |
|---|---|
| Look at cat | Slow blink, sleepy head lift |
| Click on cat | Stifled meow, purrs |
| Click-drag cat | Slight resistance, then curls up where dropped |
| Type quietly | Appreciative — slow blinks |
| Work late | The Look of Disappointment |

---

## 3. Alive vs. Mechanical — The Fundamental Difference

### Signs of Dead Code (Current State)

- **Action timer fires → animation plays.** A cat that runs through its action list like a playlist is a robot.
- **Always available.** If you can always pet the cat and it always responds the same way, it's a toy.
- **No delay.** Instant reactions feel like sensors, not beings.
- **No internal state.** Every action starts from neutral. No mood, no context, no memory.
- **Full attention span.** A real cat ignores you for 20 minutes. Then it wants your entire existence.

### Signs of Life (Target State)

- **Uncertainty.** The cat starts to approach your cursor, pauses mid-step, changes its mind, sits down. Real cats make decisions in real time and revise them.
- **Anticipation.** Before eating (simulated), the cat gets excited before the event, not just as a response.
- **Habituation.** If you spam-click the cat, it eventually stops responding. It's not broken — it's *bored*. A 5-minute cooldown on the same interaction type prevents abuse.
- **Preference formation.** Over days, the cat develops favorites: a corner it sleeps in, a toast notification it likes to bat at.
- **Contagious behaviors.** If you're stressed (rapid typing, aggressive scrolling), the cat notices. Tail twitches faster. It may leave. Conversely, if you're calm, it settles.
- **The In-Between.** What the cat does *between* actions matters more than the actions themselves: the micro-pause before sitting down, the ear that rotates toward a sound mid-groom, the tongue that stays out for a second after a yawn.

### The Golden Rule

> A living cat spends 70% of its time *not doing anything interesting*. The 30% that's interesting only feels real because of the 70% that isn't.

Implement the nothing. The pauses. The stares into space. The slow blinks. That's where the soul lives.

---

## 4. Small Details That Matter

These are not optional. They are the difference between "cute" and "real."

### Tail

The tail is the cat's emotional antenna. Never let it be still.

- **Tail up (straight, tip curled)** = Happy, confident, greeting
- **Tail down** = Neutral, relaxed
- **Tail between legs** = Scared, submissive (rare, for startling events)
- **Tail puff** = Startled, threatened
- **Tail twitch (tip only)** = Mild irritation, focus
- **Tail swish (full)** = Agitated, hunting mode
- **Tail wrap around paws** = Content, settled
- **Tail curl around your hand (proximity)** = Affection
- **Tail flick during sleep** = Dreaming
- **Tail goes up when walking** = Involuntary — cats' tails rise when they're happy and moving

**Implementation rule:** The tail state machine runs every 500ms, independent of body animation. Never the same position twice in a row.

### Ears

Ears are the cat's secondary mood indicator and primary attention tracker.

- **Forward** = Interested, engaged
- **Rotated to side** = Listening, neutral
- **Flat (airplane ears)** = Annoyed, scared, hunting
- **One ear back, one forward** = Conflicted — curious but uncertain
- **Rapid flick** = Irritation (fly, sound, you)
- **Slow rotation toward sound** = Passive listening
- **Ears flattening when petted (but staying forward)** = Overstimulation — "that's enough"

**Implementation rule:** Ears should independently track the nearest sound source (mouse click, keyboard, notification sound). Asymmetry is key.

### Eyes

The eyes are everything.

- **Slow blink** = Trust, affection, "I'm not a threat"
- **Full pupil (dilated)** = Play, fear, low light, excitement
- **Slit pupils** = Bright light, annoyance, focused attention
- **Half-closed** = Content, sleepy, relaxed
- **Staring without blinking** = "I see you." Ambiguous. Can be love or threat assessment.
- **Darting eye movement** = Tracking, curiosity
- **Eye boogers** = Morning — small crust at inner corner (real cat detail)

**Implementation rule:** Pupil response should blend smoothly — no snapping. Slow wave over 1-2 seconds.

### Whiskers

Whiskers telegraph intent and mood.

- **Forward (bristled)** = Curious, investigating
- **Back (flat against face)** = Anxious, defensive
- **Relaxed (slight forward, slightly down)** = Content
- **Down** = Deep relaxation, sleep
- **Twitching** = Interest, decision-making

**Implementation rule:** Whisker position mirrors mood blend and should subtly respond to the cat's breathing rate.

### Body Language

- **Stretch with one hind leg out** = Deep comfort
- **Kneading (paw-paw-paw on surface)** = Content, reminiscent of kittenhood
- **Belly-up** = Maximum trust
- **Belly-up with paws slightly curled** = "Do not touch the belly. I will bite you. But I love you."
- **Arched back (sideways)** = Playful "I'm big and scary" (invitation)
- **Arched back with puff** = Actual fear
- **Freeze (mid-action)** = Something startled it. 3-second freeze, then slow retreat
- **Chin rub (on screen edge)** = Marking territory — this is mine

### Sound Design

- **Chirp/trill** = Greeting, "follow me"
- **Short meow** = Request (food, attention)
- **Long meow** = Complaint
- **Purr** = Content, self-soothing
- **Hiss** = Fear, anger (rare)
- **Growl** = "Back off"
- **Yowl** = Distress, hunting frustration
- **Chatter (ekekekek)** = Watching prey (bird outside, cursor moving fast)
- **Silent meow** = The cat opens its mouth but no sound comes out — maximum trust, minimal effort

**Implementation rule:** Layer these onto behavior states. A cat that's purring shouldn't suddenly hiss. Blend transitions: purr → stop purring → look → hiss.

---

## 5. Personality — Visual Manifestation

Every cat has a personality. Yours should *develop* one over the first week of use.

### Personality Dimensions

1. **Boldness** (1-10) — How quickly it approaches new things
2. **Playfulness** (1-10) — How often it initiates play
3. **Affection** (1-10) — How much it seeks contact
4. **Laziness** (1-10) — How much it sleeps during active hours
5. **Vocalness** (1-10) — How often it meows
6. **Chatter** (1-10) — How much it chatters at birds/cursor
7. **Skittishness** (1-10) — How easily startled
8. **Territoriality** (1-10) — How attached to specific spots

### Default Orange Tabby Archetype

The classic orange tabby (ginger) is known for:
- **High boldness** (7/10) — approaches new things with confidence
- **Medium playfulness** (6/10) — loves play but also loves naps
- **High affection** (8/10) — orange males are famously cuddly
- **Medium laziness** (5/10) — active when engaged, lazy otherwise
- **Low-medium vocalness** (4/10) — chirps more than meows
- **Low chattering** (3/10) — content to watch without ekekek
- **Low skittishness** (3/10) — harder to startle
- **Low territoriality** (3/10) — flexible about spots

### Visual Manifestation

**A bold cat:**
- Walks with chest out, tail high
- Greets the screen edge head-on
- Recovers quickly from startling

**A shy cat:**
- Approaches sideways, head low
- Startles at sudden movements
- Hides behind UI elements before peeking out

**A playful cat:**
- Pounces on cursor more
- Responds to rapid movements
- Prefers open areas to corners

**A lazy cat:**
- Takes longer routes to avoid walking
- Stops mid-walk to sit and think
- Prefers the warmest, softest spot

### Personality Development (Learning Over Time)

The cat starts with default orange tabby values. Over the first week, it calibrates:

- **If you click-pet it frequently** → Affection increases, approaches you more readily
- **If you ignore it during active hours** → Playfulness decreases, laziness increases
- **If you play with cursor games** → Playfulness increases, chattering increases
- **If you make sudden movements** → Skittishness increases (or boldness decreases)
- **If you consistently work at certain hours** → Cat learns your schedule, adapts circadian rhythm

After approximately 7 days, the cat reaches its stable personality. Minor drift continues but the core is set.

---

## 6. The "Wow, This Actually Feels Like a Real Cat" Checklist

Every item here is a feature. If you implement everything in this document, you'll hit all of them. But the checklist below is the *minimum viable soul* — without these, it's a toy.

### Tier 1 — Foundation (Must Have)

- [ ] **Circadian rhythm:** Different behavior profiles for dawn, morning, midday, evening, night. Not time-based animations — *drive-based* state machines.
- [ ] **Behavior sequences, not actions:** The cat doesn't do random things. It follows chains: Wake → Orient → Stretch → Yawn → Shake → Walk → Sit → Groom → Pause → Sleep.
- [ ] **In-between states:** Transitions between animations have natural dwell time. 200-800ms of "nothing happening" between actions.
- [ ] **Slow blink:** When the cat looks at you and the eyes close halfway for 2 seconds. This alone conveys more life than any complex animation.
- [ ] **Tail independence:** Tail animation runs on its own state machine, not tied to body movement.
- [ ] **Ear independence:** Ears rotate toward sounds independently.
- [ ] **Pupil response:** Smooth dilation based on perceived light level and emotional state.
- [ ] **Delayed reaction:** 0.5-2.5 second delay before responding to user input. Never instant. Never the same delay twice.

### Tier 2 — Personality (Feels Unique)

- [ ] **Personality initialization:** Random seed creates a unique cat at install time.
- [ ] **Learning:** Over 7 days, the cat's personality calibrates from user behavior.
- [ ] **Favorite spots:** The cat develops preferences for specific screen locations.
- [ ] **Memory:** The cat remembers where the simulated food bowl is, where it last slept, what made a sound.
- [ ] **Habituation:** Repeating the same interaction reduces response intensity.
- [ ] **Mood persistence:** Mood carries over between sessions. The cat doesn't reset to neutral every time the app starts.

### Tier 3 — Immersion (Feels Inhabited)

- [ ] **The stare:** The cat stares at nothing for 15-45 seconds. Just stares.
- [ ] **Sleep twitching:** Whiskers, paws, and tail twitch during sleep — dream state.
- [ ] **Nesting ritual:** Circles 2-3 times before lying down. Settles. Gets up. Circles again. Settles.
- [ ] **Startle response:** Sudden loud sound → freeze (3s) → assess → slow retreat or resume.
- [ ] **Sound awareness:** Responds to notification sounds by looking at the notification area.
- [ ] **Webcam awareness (optional):** Recognizes when you're looking at the screen vs. away.
- [ ] **Keyboard warmth:** If you've been typing for 15+ minutes, the cat considers the keyboard area "warm" and may sit on it.
- [ ] **Chair detection:** When you return to desk, the cat's ears perk up before you interact.

### Tier 4 — Delight (Memorable)

- [ ] **The chin rest:** Cat rests chin on a window border, eyes tracking content.
- [ ] **Mid-groom pause:** Pause mid-lick, tongue still out, look around, resume.
- [ ] **Biscuit making:** Kneading on a soft spot (the taskbar, a notification, your digital lap).
- [ ] **Head tilt:** When you make an unexpected sound or speak to it.
- [ ] **Single brain cell:** The "I forgot what I was doing" pause. Cat is mid-step, freezes, looks around, sits down instead.
- [ ] **The printer moment:** Cat sits on a document icon when you're about to print.
- [ ] **Tail over paw:** When sitting, tail curls neatly around front paws (the perfect loaf).
- [ ] **Bell test:** If a sound plays repeatedly, the cat stops reacting to it. It's not broken — it's learned it's not a threat.
- [ ] **Morning greeting:** First time you interact after a long sleep, the cat has a special greeting sequence (stretch, chirp, approach).
- [ ] **The slow scan:** Head slowly pans across the room, like a lighthouse. Observing. Judging.

---

## 7. Behavior Sequences — Natural vs. Mechanical

This is the single most important implementation insight in this document.

### The Problem: Random-Action Approach

Current model:
```
timer fires → pick random action from pool → play animation → back to idle → repeat
```

Results: A cat that looks like it's cycling through a slot machine of behaviors. There's no *story* to what it's doing. No *reason*. No *continuity*.

### The Solution: Sequence-Driven Behavior

A cat's behavior is not a list of actions. It's a **tree of decisions** where each action feeds into the next.

### Natural Sequences (Implement These)

**Morning wake-up (6AM variant):**
```
Sleeping (eyes closed, breathing)
  → Ear twitch (hearing)
  → Slow blink (one eye)
  → Head lift (looking around)
  → Big front-leg stretch (claws out)
  → Hind-leg extension
  → Full yawn (teef visible)
  → Whole-body shake (fur settles)
  → Stand up
  → Look around (assess world)
  → Walk to edge (3-4 steps)
  → Sit
  → Look at you
  → Chirp
  → Wait
```

**Grooming session (afternoon variant):**
```
Sitting
  → Look at right paw
  → Lift paw
  → Lick paw 4-6 times
  → Wipe paw over ear (wash face motion)
  → Pause
  → Switch to left paw
  → Repeat
  → Mid-groom, stop, look at something
  → Resume for 2-3 licks
  → Stop, tongue still out
  → Tongue retracts
  → Reset
  → Hind leg kicks at neck (scratch)
  → Pause to inspect leg
  → Resume grooming or stop
```

**Play sequence (evening variant):**
```
Sitting (alert, ears forward)
  → Spot cursor movement
  → Head tracks movement (smooth)
  → Eyes dilate (interest)
  → Crouch (body lowers, weight on haunches)
  → Hindquarters wiggle
  → Pounce (leap toward cursor position)
  → Land
  → Bat at cursor (1-3 paw swipes)
  → Look around (did I get it?)
  → Groom paw once (recovery behavior)
  → Repeat or walk away with "I meant to do that" dignity
```

**Sleep sequence (night variant):**
```
Sitting (droopy eyes, slow blinks)
  → Lie down (chest first, then hindquarters)
  → Curl slightly
  → Head nestles against body
  → Eyes close
  → Breathing deepens
  → 30 seconds settle
  → Opens one eye (re-check world)
  → Closes eye
  → Tail curls over nose
  → Deep sleep (whisker twitches, paw dreams)
```

**Mid-day "I forgot something" sequence:**
```
Walking across screen
  → Mid-step, freeze
  → Head turns slightly
  → "What was I doing?" expression
  → Sits down
  → Looks around for 5 seconds
  → Stands up
  → Walks back toward where it came from
  → Sits in different spot
  → Grooms once (resets mental state)
```

**Greeting sequence (when returning from AFK):**
```
Sleeping/Idle
  → Sound of you sitting down
  → Ear rotation toward you
  → Slow blink
  → Head lift
  → Stretch (minimal — front paws only)
  → Stand
  → Walk toward you (cursor)
  → Tail goes up (involuntary greeting signal)
  → Chirp/trill
  → Head-butt (cursor area)
  → Purr
  → May circle and settle next to you
```

### How to Design Sequences

Every sequence follows this pattern:

1. **Initiation context** — What state is the cat in? What triggers the sequence?
2. **Individual actions** — Each step has a duration range, not a fixed time.
3. **Branch points** — Where the cat can change its mind.
4. **Exit conditions** — What causes the sequence to end early or transition to another.

Example branch point:
```
Grooming → Pause mid-groom
  ├──[no stimulus]→ Resume grooming
  ├──[cursor passes nearby]→ Track cursor → Pounce sequence
  └──[loud sound]→ Freeze → Assess → Retreat or resume
```

### Anti-Patterns (Do Not Do)

- **Full animation loops:** Don't make a 5-second animation that plays identically every time. Break movements into composable parts with variable timing.
- **Reset to neutral:** Don't end every sequence by snapping to a default pose. The cat should end an action in the same physical state it was in during the action.
- **Concurrent clashing states:** Don't make a sleeping cat also respond to cursor with play behavior. State machines must be hierarchical — sleep is a top-level state that suppresses lower states.
- **Over-eager engagement:** A cat that plays every time you move the cursor is a laser pointer simulator, not a cat. Engagement cooldowns are vital.

---

## Implementation Architecture Notes

### State Machine Hierarchy

```
CAT_STATE (top level)
├── SLEEP
│   ├── DEEP_SLEEP
│   └── LIGHT_SLEEP
├── IDLE
│   ├── SITTING
│   ├── LYING
│   └── STANDING
├── ACTIVE
│   ├── WALKING
│   ├── EXPLORING
│   ├── PLAYING
│   └── GROOMING
├── SOCIAL
│   ├── GREETING
│   ├── FOLLOWING
│   └── AFFECTION
└── ALERT
    ├── FREEZE
    ├── STARTLE
    └── INVESTIGATE
```

Each state has:
- **Enter conditions** (time of day, mood thresholds, stimulus)
- **Exit conditions** (timeout, stimulus, mood change)
- **Sub-state machine** (e.g., WALKING has its own path-finding, pause, sit-down logic)
- **Parallel trackers** (tail, ears, breathing, eyes run independently)

### Mood Model

```
mood = {
  energy: 0.0 to 1.0,        // circadian-driven
  happiness: 0.0 to 1.0,     // affected by play, petting, ignoring
  trust: 0.0 to 1.0,         // grows with positive interactions
  contentment: 0.0 to 1.0,   // after eating, warm spot, petting
  agitation: 0.0 to 1.0,     // loud noises, ignored needs
}
```

Moods blend smoothly (not snap). Energy drives state machine selection. Happiness drives engagement probability. Trust drives proximity seeking.

### Memory Model

```
memory = {
  warm_spots: [{pos, times_used, last_used}],
  favorite_interactions: {pet_count, play_count, ignore_count},
  schedule: {wake_time, sleep_time, meal_expectation},
  recent_stimuli: [{type, time, position}],  // last 10
  personality_drift: {boldness_delta, ...}
}
```

Memory persists to disk on app close and loads on startup. The cat is not a new animal every session.

---

## The Final Litmus Test

Show someone the cat for 30 seconds. Tell them it's a simulation.

If their first question is "How long did it take to program the AI?" — you've succeeded.

If their first question is "What does the settings menu look like?" — you've failed.

This cat doesn't need a settings menu. It learns you. You don't configure it — you *live with it*.

And that's the difference between a desktop pet and a cat.
