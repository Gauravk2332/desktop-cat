# Research Brief: Building a Truly Realistic Cat Simulation

**Date:** 2026-05-22
**Status:** Complete
**Sources:** 12+ (papers, open-source projects, academic theses, game architecture docs)
**Confidence:** High on architecture recommendations, moderate on ethogram depth

---

## Executive Summary

Your current cat feels like a screensaver because it's a **reactive system**, not a **simulation**. Single LLM calls every 2s with no memory, no circadian rhythm, no planning, and no spatial awareness cannot produce lifelike behavior.

The fix: **Utility AI + Behavior Tree hybrid** for the core decision loop, with the LLM layered on top for creativity, novelty, and narrative. Pure LLM is too slow, too expensive, and too unpredictable for real-time cat behavior.

---

## 1. Best Approaches for Simulating Lifelike Animal Behavior

### The Four Contenders

| Approach | Best For | Weakness |
|----------|----------|----------|
| **Finite State Machine (FSM)** | Simple, linear behaviors (sleep→wake→eat) | Spaghetti at 15+ states |
| **Behavior Tree (BT)** | Complex hierarchies, modular, reusable | No built-in priority system |
| **Utility AI** | Multiple competing needs, weighted decisions | Can feel robotic without noise |
| **Goal-Oriented Action Planning (GOAP)** | Strategic sequences, emergent plans | Overkill for a desktop pet |

### Recommendation: Utility AI + Behavior Tree Hybrid

**Primary decision:** Utility AI scores all possible actions every tick based on needs + context + personality. This is what The Sims uses, and it's the right model for a cat that needs to balance hunger, energy, boredom, and social drive.

**Execution layer:** Behavior Tree handles *how* actions are performed once chosen. The BT contains sequences (e.g., WALK→SIT→GROOM), conditions (is player nearby?), and decorators (repeat grooming 3x).

**Why this beats pure FSM or pure LLM:**
- Utility AI naturally handles conflicting drives (hungry + tired → which wins?)
- Behavior trees make action sequences easy to author and debug
- Neither requires LLM latency for basic survival behavior
- LLM can be called sparingly for "creative" decisions (which toy to chase, how to react to a novel object)

**Confidence: 5/5.** This is well-established in game AI (The Sims, Halo, Last of Us).

### Literature Support

- **Sobrino (2024)** — *Artificial Intelligence and Life Simulation in Videogames* — Uses FSM for ants, BT for birds, Utility for mammals. Concludes hybrid architectures outperform single-model approaches for believable life simulation. [GitHub: DiegoSobrino/Artificial-Intelligence-and-Life-Simulation-In-Videogames]

- **Kindatechnical** — *Behavior Trees vs State Machines for Game AI* — "Modern game AI combines behavior trees for high-level decisions with utility AI for tactical choices and FSMs for animation states."

---

## 2. How Modern Digital Pet Games Implement Realistic Behavior

### Tamagotchi (1996+)
- **Architecture:** Simple need meters (hunger, happiness, discipline) ticking down
- **State machine with 3 stages:** Child → Teen → Adult
- **Key insight:** Consequences (death) create emotional investment. The "Tamagotchi Effect" — genuine distress at digital suffering
- **Limitation:** No memory, no personality. Every Tamagotchi is identical at start

### Nintendogs (2005)
- **Architecture:** Touch-driven interaction + need management
- **Key innovation:** Tactile petting via stylus → dopamine release
- **Learning:** Dog remembers tricks you teach it (simple associative memory)
- **Daily routine:** Walk schedule, feeding times

### The Sims (2000-2024)
- **Architecture:** **Utility AI** — every Sim computes a utility score for each possible action based on current needs and environment. Picks the highest.
- **Needs:** Hunger, Energy, Bladder, Social, Fun, Hygiene — each decays over time
- **Key innovation:** Personality traits modulate need decay rates and action preferences
- **Limitation:** Highly robotic without player input. Sims make "optimal" choices, not "characterful" ones.

### Animal Crossing: New Horizons (2020)
- **Architecture:** Time-based schedules per villager + random variation
- **Circadian rhythm:** Each villager follows a daily schedule (wake hours, activity periods)
- **Personality types:** 8 personality types with distinct dialogue pools
- **Memory:** Villagers remember gifts and interactions
- **Key insight:** Making villagers *mildly inconvenient* (showing up when you don't need them) makes them feel more real

### AIdorable (2024, Generation 4 AI pet)
- **Architecture:** LLM personality engine + memory vector DB
- **Unique personality** develops from interaction history
- **Emotional memory:** Remembers past interactions, references them
- **Developmental milestones:** Triggered by care patterns, not timers
- **Key insight:** The shift from cortisol-based attachment (fear of death) to oxytocin-based (nurturing bond)

### Key Takeaway for Your Cat
- **Needs are table stakes.** Every virtual pet since 1996 has them.
- **Personality is the differentiator.** Why does MY cat act differently from yours?
- **Memory separates simulation from routine.** If the cat can't remember you, it's a robot.
- **Slight unpredictability creates life.** 100% deterministic behavior feels dead.

---

## 3. Academic Work on Animal Behavior Simulation in Games/AI

### Key Papers

**1. Stanford "Generative Agents" (Park et al., 2023)**
- *"Generative Agents: Interactive Simulacra of Human Behavior"*
- 25 LLM-powered agents living in a simulated world
- **Memory stream:** Every experience → summarized → stored → recalled for decision-making
- **Reflection:** Agents periodically synthesize memories into higher-level insights
- **Planning:** Agents plan their day based on memories and current state
- **Relevance for cat simulation:** The memory stream architecture maps perfectly — cat remembers where food bowl is, which spots are sunny, where you usually sit. LLM call frequency: ~1/min, not 2/sec.
- [arXiv: 2304.03442]

**2. Survey on LLM-Based Game Agents (Hu et al., 2024)**
- *arXiv:2404.02039* — Unified reference architecture for LLM agents
- **Three core components:** Memory (short + long-term), Reasoning (planning + reflection), Perception-Action (sensors + actuation)
- **Six game genres mapped** to agent requirements
- **Key finding:** LLM agents excel at open-ended reasoning but struggle with real-time control. Hybrid systems outperform pure LLM.
- [arXiv: 2404.02039]

**3. Sobrino's Academic Thesis (2024)**
- Systematic comparison of 6 AI techniques for life simulation: FSM, Steering Behaviors, Behavior Trees, Reinforcement Learning, GOAP, Fuzzy Logic, Utility Maximization
- 6 experiments: ants (FSM), birds (BT), fish (steering), mammals (hybrid), city simulation, plant growth
- **Conclusion:** Each technique has a niche. Hybrid architectures that match technique to behavioral domain produce the most realistic results.
- [GitHub: DiegoSobrino/Artificial-Intelligence-and-Life-Simulation-In-Videogames]

---

## 4. Implementing Key Simulation Systems

### 4.1 Circadian Rhythm

Cats are **crepuscular** — most active at dawn and dusk. This is hardwired.

**Proposed implementation:**

```
circadian_rhythm = {
    phase: String,           // "deep_sleep" | "light_sleep" | "drowsy" | "alert" | "active" | "hunting" | "playful"
    energy_modifier: Float,  // 0.0 - 1.5 multiplier on energy decay
    activity_preference: Map<String, Float>  // modifies utility scores per action
}
```

**Daily cycle for a domestic cat (synthesized from ethology sources):**

| Time (window) | Phase | Dominant Behaviors |
|---------------|-------|-------------------|
| 04:00-06:00 | Dawn active peak | Hunting, patrolling, high energy |
| 06:00-08:00 | Morning routine | Meowing for food, eating, brief play |
| 08:00-11:00 | Morning nap | Light sleep, sunbeam-seeking |
| 11:00-13:00 | Afternoon sleepy | Deep sleep, minimal movement |
| 13:00-15:00 | Midday lazy | Drowsy, occasional stretching, repositioning |
| 15:00-17:00 | Late afternoon | Grooming, brief exploration |
| 17:00-19:00 | Dusk active peak | Hunting, play, zoomies, patrolling |
| 19:00-22:00 | Evening social | Near owner, purring, lap time, eating |
| 22:00-04:00 | Night | Intermittent sleep, short active bursts, silent patrol |

**Key:** The cat should NOT always sleep at night. Real cats wake up multiple times. At least 3-4 activity bursts during the night of 15-30 minutes each.

**Confidence: 4/5.** Based on ethology literature. Exact timing varies by individual cat and household.

### 4.2 Memory System

Your cat needs three memory layers:

**Short-term (working memory):** Last 30-60 seconds. What just happened, where did that sound come from, was that a toy?

**Episodic (medium-term):** Last few hours. Where did I leave the toy? Did the human just walk in?

**Long-term:** Persistent across sessions. Favorite spots (sunbeam by window at 2pm), routines (human comes home at 6pm), object associations (red dot = laser pointer = fun), person identification (this human = food giver).

**Recommended implementation (adapted from Generative Agents):**

```
// Memory entry structure
{
    timestamp: int64,
    type: "event" | "observation" | "reflection",
    content: string,
    emotional_valence: float (-1 to 1),
    location: vector2d,
    importance: float (0-1),  // decays but never reaches 0
    tags: ["food", "human", "toy", "danger", "comfort"]
}
```

**Storage:**
- SQLite / JSON file for persistence (lightweight, no server needed)
- In-memory recent buffer for short-term
- Periodic summarization (every hour of sim time) of episodic into long-term

**Recall mechanics:**
- **Spatial:** Entering a region triggers associated memories ("I found food here yesterday")
- **Temporal:** Time of day triggers routine memories
- **Cued:** Seeing the red dot triggers play excitement
- **Decay:** Unreinforced memories fade over days of sim time

**Confidence: 5/5.** This maps directly from Generative Agents and is straightforward to implement.

### 4.3 Personality Traits

**Five traits for your cat simulation (adapted from feline temperament research):**

| Trait | Low End | High End | Effects |
|-------|---------|----------|---------|
| **Boldness** | Timid, hides | Confident, explores | New object reaction, approach distance |
| **Sociability** | Aloof, solitary | Affectionate, follows | Time near human, purr frequency, lap-seeking |
| **Playfulness** | Sedate, lazy | Energetic, playful | Toy interaction duration, zoomie triggers |
| **Neophobia** | Accepts change | Fears novelty | Reaction to new objects, furniture changes |
| **Vocalness** | Silent | Meowy, chatty | Meow frequency, volume, variation |

**How traits work:**
- Each trait is a float 0.0-1.0 initialized with distribution (normal + some random shift)
- Traits modify utility scores: a bold cat gets +0.3 utility on EXPLORE actions, a timid cat gets -0.5
- Traits affect need decay rates: playful cat's boredom decays 2x faster
- Traits can **drift slowly** over time based on experience (a cat that successfully hunts gets slightly bolder)

**Confidence: 4/5.** Trait dimensions are from feline personality research. The specific implementation numbers need tuning.

### 4.4 Spatial Awareness & Territory

Cats have excellent spatial memory and are territorial animals.

**Spatial map structure:**

```
// Grid or sparse graph of known locations
{
    type: "territory_center" | "resting_spot" | "food_station" | "water_station" |
          "litter_area" | "sunbeam" | "vantage_point" | "hiding_spot" | "toy_location",
    position: vector2d,
    last_visited: int64,
    visit_count: int,
    preference: float (0-1),
    time_bias: [24 floats, one per hour]  // when is this spot best?
}
```

**Territory behavior:**
- Cat patrols territory edges periodically (slow walk, sniffing)
- Marks territory by rubbing (virtually — triggers rubbing animation in certain spots)
- Shows comfort in known areas (relaxed posture), alert in unknown
- Has favorite spots that change with time of day (sunbeam tracking!)

**Object permanence:**
- If a toy moves behind furniture, cat remembers it exists and may investigate
- If human leaves room, cat knows they still exist (doesn't just switch to idle)
- If food bowl is empty but cat was fed there yesterday, returns to check

**Confidence: 4/5.** Object permanence is known from cat cognition research. Implementation is straightforward game AI.

### 4.5 Learning

Simple reinforcement learning for:
- **Operant conditioning:** If human gives treats when cat meows at food bowl, meow frequency increases
- **Avoidance:** If human reacts negatively to clawing furniture, probability decreases (or cat learns to do it when human isn't watching!)
- **Social learning:** Cat watches where other cats (if any) find food

**Implementation:** Simple Q-learning or even just weighted probability counters.

```
// Learned associations
{
    cue: string,        // "owner_in_kitchen"
    action: string,     // "meow_at_food_bowl"
    outcome: string,    // "got_treat"
    strength: float,    // -1 to 1, updated on each occurrence
    trials: int
}
```

**Confidence: 3/5.** Real cats are capable of all of these. Simple q-learning approximates this well enough for a desktop pet.

---

## 5. The Right Way to Use LLMs

### DON'T: LLM as Core Decision Engine

Your current architecture (LLM call every 2s deciding actions) has fundamental problems:

1. **Latency:** A real cat responds in milliseconds. A 500ms-2s LLM call makes every action feel delayed and deliberate.
2. **Lack of subtlety:** LLMs think in language, not in continuous motion. A real cat's ear twitch, tail flick, and head rotation communicate more than any text output.
3. **Cost:** 30 LLM calls/minute = ~1800/hour = unsustainable
4. **No embodied sense:** LLMs don't understand physics, spatial relationships, or proprioception without massive prompt engineering.

### DO: LLM as Creative Layer on Top of a Rule System

**Recommended architecture:**

```
┌─────────────────────────────────────────────────────┐
│                    LLM Layer                        │
│  (called every 30-120 seconds, or on trigger)       │
│  - Novel object reaction (what IS this thing?)      │
│  - Play sequence variation (which toy, what order?) │
│  - Narrative generation (journal entry)             │
└──────────────────┬──────────────────────────────────┘
                   │ decides "which flavor" of action
┌──────────────────▼──────────────────────────────────┐
│              Utility AI Layer                       │
│  (called every tick, ~500ms)                        │
│  - Scores all actions by need + circadian + context │
│  - Applies personality modifiers                    │
│  - Picks best action                                │
└──────────────────┬──────────────────────────────────┘
                   │ picks "what to do"
┌──────────────────▼──────────────────────────────────┐
│            Behavior Tree Layer                      │
│  (executes current action)                          │
│  - Sequences, conditions, loops for animation       │
│  - Reads/writes blackboard (needs, position, etc.)  │
└──────────────────┬──────────────────────────────────┘
                   │ controls animation
┌──────────────────▼──────────────────────────────────┐
│              Animation/Movement Layer               │
│  (continuous, physics-driven)                       │
│  - Smooth movement, transitions, blend trees        │
└─────────────────────────────────────────────────────┘
```

**When to call the LLM (single cat):**

| Trigger | Purpose | Frequency |
|---------|---------|-----------|
| Novel object appears | "What would this cat think?" | Rare (new item placed) |
| Cat has been idle 5+ min | "Suggest a rare/creative behavior" | Every 5-10 min |
| Human interacts | "How does this cat respond right now?" | On interaction |
| Day summary | "Generate journal entry" | Once per sim day |
| Personality drift | "Given recent events, update trait slightly" | Once per sim day |
| Play sequence start | "What's the play pattern this time?" | Every 2-3 min of play |

**Total: ~1-3 LLM calls per minute.** Not 30.

**Prompt design for cat LLM:**

```
You are a [bold/playful/shy] cat named [name].
Current time: [time of day]. You feel: [hungry/tired/bored/content].
You are in: [location]. [human] is [nearby/away/sleeping].
Recent events: [2-3 most salient memories].
Your energy: [0-100]. Hunger: [0-100]. Boredom: [0-100].

The highest-priority action from your instinct system is: [action].
But you can add creativity to HOW you perform it, or suggest an alternative
if something truly interesting is happening.

Respond with:
- action: [action name]
- variation: [how to do it differently]
- expressiveness: [tail position, ear position, vocalization]
```

**Confidence: 5/5.** This hybrid architecture is the consensus from all sources surveyed: Generative Agents, LLM Game Agent Survey, AI Tamago, and industry practice.

### Case Study: AI Tamago

[AI Tamago](https://github.com/ykhli/AI-tamago) is the closest open-source implementation to what you need:
- Local LLM via Ollama (or OpenAI/Replicate)
- Langchain.js orchestration
- Supabase pgvector for memory (embeddings via Transformer.js/all-MiniLM-L6-v2)
- Inngest for scheduled game state ticks
- Full compatibility with your stack

Their architecture: LLM generates "thoughts" and "feelings" every cycle → stored in vector DB → retrieved on triggers → influences next decisions. But it's still primarily LLM-driven, which is why it remains somewhat slow and deliberate.

---

## 6. How Real Cats Behave: Behavioral Ethogram for Simulation

### Comprehensive Cat Behavior Catalog

This ethogram is synthesized from the International Cat Care ethogram, the ASPCA Cat Behavior guidelines, and feline behavioral ecology research. Each behavior is listed with triggers, typical duration, posture, and simulation implications.

#### Maintenance Behaviors

| Behavior | Triggers | Duration | Sequence | Simulation Note |
|----------|----------|----------|----------|-----------------|
| **Sleep** | Low energy, post-meal, circadian trough | 15min-2h per bout, 12-16h/day total | Find spot → circle 3x → curl → sleep → ears twitch periodically | Not always deep. Simulate 70% light, 30% deep. REM cycling (eye/whisker twitches) |
| **Groom** | After eating, after sleep, idle, stress | 5-30 min per session | Lick paw → rub face → lick chest → flank → tail | Incomplete grooming is stress signal. Interruptible. |
| **Eat** | Hunger > 70, food visible | 2-10 min | Approach → sniff → eat → walk away | Small meals, multiple per day (not 2 big ones). Usually after hunting sequence. |
| **Drink** | Thirst | 30-60 seconds | Approach water → lap → pause → lap | Cats prefer running water (moving water = safer). Fresh water important. |
| **Eliminate** | Bladder/bowel pressure | 30-60 seconds | Dig → squat → eliminate → cover → sniff → leave | Litter box aversion = stress. Burying = submissive. Not burying = territorial. |
| **Stretch** | After sleep, after long sit | 5-10 seconds | Front paws extend, chest lowers, tail up | Often followed by yawn. |

#### Locomotor Behaviors

| Behavior | Triggers | Duration | Sequence | Simulation Note |
|----------|----------|----------|----------|-----------------|
| **Walk** | Exploration, patrol, travel | Variable | Slow, deliberate, tail up in comfort, tail low in uncertainty | Head swiveling. Occasional pause to sniff. |
| **Sit** | Watch, wait, indecision | 30sec-10min | Hind legs tuck, front straight | Alert posture. Ears swivel. |
| **Lie down** | Comfort, warmth, watch | Variable | Chest down, paws tucked (loaf) or stretched | Loaf = relaxed. Sphinx = alert. Side = deep comfort. |
| **Pace** | Boredom, stress, confined | Minutes to hours | Back and forth, same path | **Stress indicator.** Stop if given stimulation. |
| **Zooomies** | Burst energy, dusk/dawn, after bathroom | 1-5 minutes | Explosive run, sudden direction changes, skid stops | Usually after elimination or long rest. FRAP (Frenetic Random Activity Periods). |
| **Climb** | Vertical exploration, escape, vantage | Variable | Jump → claw into surface → ascend | Climbing up is easy. Getting down is hard. |
| **Jump** | Access surface, chase | <1 second | Crouch → coil → launch | Hind legs provide power. 6x body length horizontal. |
| **Perch** | Territory viewing, surveillance | 15min-3h | High vantage, alert but relaxed | Cats are both predator AND prey. Vantage points = safety. |

#### Social/Communicative Behaviors

| Behavior | Triggers | Duration | Sequence | Simulation Note |
|----------|----------|----------|----------|-----------------|
| **Head bunting** | Affection, marking | 2-5 seconds | Push forehead/cheek into human/object | Pheromone deposition. Temporal/scent glands on forehead. |
| **Rubbing** | Greeting, marking | 2-5 seconds | Flank/tail rub against legs | Same purpose. Routines around known objects. |
| **Purring** | Contentment, greeting, nursing, pain | Variable | Rhythmic vibration 25-150 Hz | Not always happy. Also self-soothing in pain/stress. |
| **Kneading** | Comfort, nursing memory, relaxation | 1-5 minutes | Alternating paw presses, rhythmic | Associated with kittenhood nursing. Comfort behavior. |
| **Slow blink** | Trust, contentment | 2-5 seconds | Eyes half-close slowly | "Cat kiss." Sign of trust. Reciprocate for bonding simulation. |
| **Tail up** | Greeting, happiness, confidence | Variable | Tail vertical, tip may curve | "I'm friendly" — universal cat signal. |
| **Tail flick** | Irritation, indecision | <1 second | Quick flick of tail tip | Warning sign before more aggressive response. |
| **Ears back/forward** | Mood indicator | Continuous | Forward = interested. Back = annoyed. Sideways = anxious. | Crucial for emotional state tracking. |
| **Hiss** | Fear, threat, warning | 1-3 seconds | Mouth open, teeth visible, forced exhalation | Last warning before swat/flee. |
| **Chirp/trill** | Greeting, attention-seeking, watching prey | 1-2 seconds | Rising pitch, question-like | Friendly greeting. Also predator frustration (watching birds through window). |
| **Meow** | Human-directed communication | Variable | Various pitches and rhythms | Adult cats don't meow at other cats. Meowing is exclusively human-directed. |

#### Hunting/Predatory Behaviors

| Behavior | Triggers | Duration | Sequence | Simulation Note |
|----------|----------|----------|----------|-----------------|
| **Stalk** | Prey detected, toy spotted | 30sec-5min | Low posture → slow step → pause → slow step | Hind legs lower, belly near ground. Tail twitches. |
| **Pounce** | Prey in range | <1 second | Coiled hind legs → sudden forward launch | Forepaws land first. |
| **Bat/pat** | Moving object, curiosity | 2-30 seconds | Paw lifts, taps object | Testing if object is alive. |
| **Grasp/bite** | Prey caught | Variable | Forepaws hold, hind paws kick (bunny kick), bite neck | Play vs. real hunting distinction is important. |
| **Toy carry** | Successful hunt, play | Variable | Pick up and carry in mouth, may "present" to owner | Gift-giving behavior. High trust signal. |
| **Toy toss** | Boredom, practice | 1-3 min | Pick up → toss → chase → pounce | Self-play hunting practice. |
| **Watching (window/outdoors)** | Visual stimulation | 5-30 min | Still, eyes tracking, subtle tail tip twitch, chirping | Often the "chirp" vocalization accompanies bird-watching. |

#### Territorial/Environmental Behaviors

| Behavior | Triggers | Duration | Sequence | Simulation Note |
|----------|----------|----------|----------|-----------------|
| **Scent marking** | New object, territory patrol, stress | 2-5 seconds | Rub cheek/chin/flank on surface | Multiple scent glands. |
| **Scratching** | Nail maintenance, territory marking, stretching | 10-30 seconds | Front claws extend, drag down surface | Both visual and scent (scent glands in paws). |
| **Patrol** | Territory ownership, boredom | 5-15 min | Walk perimeter of territory, sniff, pause, mark | Regular circuit. More frequent if new cat outside. |
| **Investigating** | Novel object, new scent, sound | 30sec-10min | Approach slowly → sniff → retreat → return | Neophobia vs. curiosity tug-of-war. |
| **Hiding** | Fear, stress, need for security, illness | Minutes to hours | Dark enclosed space, curled tight | Critical sign of stress or illness if prolonged. |

#### Play Behaviors (kitten and adult)

| Behavior | Triggers | Duration | Sequence | Simulation Note |
|----------|----------|----------|----------|-----------------|
| **Object play** | Moving toy, laser, crumpled paper | 5-20 min per bout | Stalk → pounce → bat → chase | Simulates hunting. Most common play. |
| **Social play** | Another cat, human hand | 5-15 min | Ambush → pounce → wrestle → chase | Kittens learn bite inhibition. |
| **Exploration** | New environment, new object | 10-30 min | Sniff → investigate → small movements | Information gathering. |
| **Hide and ambush** | Predatory play | 5-10 min | Hide behind object → crouch → wait → pounce at passing target | Independent play. |

### Behavioral Sequencing

Cats don't do isolated behaviors. They run **sequences**:

1. **Sleep-wake-transition:** Sleep → ears twitch → eyes open → stretch → yawn → sit → groom face → look around → decide next action
2. **Hunger chain:** Wake → stretch → patrol to food area → sniff bowl → meow (if human nearby) → eat → groom → find sunbeam → sleep
3. **Play sequence:** Watch prey → stalk → freeze → pounce → bat → capture → bunny kick → toss → repeat (or eat if real prey)
4. **Greeting sequence:** Hear human → ears forward → tail up → approach (walk/run) → rub legs → head bunt → purr → maybe flop for belly rubs

**Important:** The LLM at the top of the architecture selects *which sequence variant* to run. The Utility AI picks *which sequence* to run. The BT handles *execution of the sequence*.

---

## 7. Proposed Architecture: The Full System

### Phase 1: Foundation (1-2 weeks)

```
┌─────────────────────────────────────────────────────────┐
│ TICK LOOP (every 500ms)                                 │
├─────────────────────────────────────────────────────────┤
│ 1. Update needs                                          │
│    - hunger -= time_decay * circadian_modifier           │
│    - energy += resting_rate if sleeping else -= decay    │
│    - boredom += time_decay * activity_modifier           │
│    - social += need_for_attention * proximity_modifier   │
│                                                          │
│ 2. Check interrupts                                      │
│    - Human interaction? (mouse hover/click)             │
│    - Novel object?                                       │
│    - Sound/event?                                        │
│                                                          │
│ 3. Utility AI scores all actions                         │
│    - Each action gets utility = base_priority            │
│      + need_score * need_weight                          │
│      + personality_bias                                  │
│      + circadian_bias                                    │
│      + environmental_score (is food nearby? is sun out?) │
│      + memory_score (was this rewarding?)                │
│      + random_variation (±0-15%)                         │
│                                                          │
│ 4. Execute selected action via Behavior Tree             │
│    - Sequence nodes for multi-step actions               │
│    - Condition nodes for interruptibility                │
│    - Decorator nodes for repetition/variation            │
│                                                          │
│ 5. Update memory                                         │
│    - Record current state + action + outcome             │
│    - Update spatial map                                  │
│    - Queue periodic summary for LLM                      │
│                                                          │
│ 6. Update animation state                                │
│    - Blend animations based on action + posture          │
│    - Update tail, ear, eye state for expressiveness      │
└─────────────────────────────────────────────────────────┘
```

### Phase 2: Memory & LLM Layer (1 week)

- Add vector DB (Chroma or SQLite-vss — both local, no server)
- Implement Generative Agents-style memory stream
- LLM called on triggers only (3-5 calls/min max)
- Personality drift system

### Phase 3: Circadian & Territory (1 week)

- Time-of-day system tied to system clock (or accelerated for testing)
- Sunbeam tracking (calculate window positions via time + window angle config)
- Patrol routes and territory map
- Favorite spot learning

### Phase 4: Learning & Polish (1 week)

- Operant conditioning (meow-for-treat, scratch-for-attention)
- Social learning (observe owner patterns, predict routines)
- Journal generation (LLM summarizes day's events)
- Personality visualization (subtle differences in how cat holds tail, ear angles, movement speed)

### What to Remove

**Phase it out:**
- LLM call every 2s → Immediate migration to 500ms Utility AI with LLM on triggers
- Single action selection → Behavior Tree hierarchy for execution
- No memory → Memory stream (start simple, in-memory dictionary)

---

## Recommended Tools & Libraries

| Need | Option | Why |
|------|--------|-----|
| **Utility AI** | Custom (50 lines of Python) | Too simple for a library. Formula: `score(need) * weight * personality * circadian` |
| **Behavior Tree** | py_trees (Python) or custom | py_trees is mature, MIT licensed. Or write your own (100 lines for basic nodes) |
| **Memory** | SQLite + JSON | No server. Serialize to file on save. |
| **Vector DB for memories** | Chroma (local, embedded) | No server. Works with all-MiniLM-L6-v2. |
| **LLM orchestration** | Langchain or direct API | Langchain if you want flexibility. Direct API if you want speed. |
| **LLM client** | DeepSeek proxy (same as current) | Keep your existing setup. Just change calling frequency. |
| **Embeddings** | all-MiniLM-L6-v2 (via sentence-transformers) | 384-dim, fast, local. Good enough for cat memories. |

---

## Open Questions (Should be tested)

1. **LLM trigger timing:** What's the minimum interval before the cat feels "dumb"? 30s? 60s? 120s?
2. **Need decay rates:** What makes the cat feel alive but not needy? Test hunger decay for "feeds itself" vs. "always hungry" balance.
3. **Randomness amount:** How much noise in utility scoring produces lifelike unpredictability without feeling erratic? Start at 10% noise.
4. **Memory decay:** How long should a cat remember a person? A food location? A toy? Real cats: months to years for people, days for toy locations.
5. **Circadian phase shift:** Should the cat's rhythm adapt to the owner's schedule (real cats do this — they learn when you wake up)?

---

## References

1. Park, J.S., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." arXiv:2304.03442.
2. Hu, S., et al. (2024). "A Survey on Large Language Model-Based Game Agents." arXiv:2404.02039.
3. Sobrino, D. (2024). "Artificial Intelligence and Life Simulation in Videogames." GitHub: DiegoSobrino/Artificial-Intelligence-and-Life-Simulation-In-Videogames.
4. Bandai Namco. (1996-2024). Tamagotchi series. Need-meter architecture with life-cycle states.
5. Nintendo EAD. (2005). Nintendogs. Touch-driven pet simulation with trick learning.
6. Maxis/Electronic Arts. (2000-2024). The Sims. Utility AI architecture for autonomous agents.
7. Nintendo EPD. (2020). Animal Crossing: New Horizons. Circadian schedule + personality system.
8. Bungie. (2004-2007). Halo 2/3. First major AAA use of behavior trees in game AI.
9. Monolith Productions. (2005). F.E.A.R. GOAP (Goal-Oriented Action Planning) for tactical squad combat.
10. Khli, Y. (2023). AI Tamago. GitHub: ykhli/AI-tamago. LLM-driven virtual pet with memory.
11. International Cat Care. (2018). "Domestic Cat Ethogram." Standardized behavioral catalog for cats.
12. AIdorable. (2026). "From Tamagotchi to AI: The Complete Evolution of Virtual Pets (1996-2026)."
