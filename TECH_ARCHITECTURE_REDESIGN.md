# Technical Architecture: Desktop Cat Redesign

**Goal:** Transform a screensaver with random actions into a cat that feels genuinely alive — with circadian rhythm, memory, personality, behavioral sequences, territory, and learning.

**Target engine:** PyQt6 overlay, 33fps tick-based, single-process, Windows 11.

---

## Table of Contents

1. [Circadian Rhythm Architecture](#1-circadian-rhythm-architecture)
2. [Cat Memory System](#2-cat-memory-system)
3. [Behavioral Sequences](#3-behavioral-sequences)
4. [Personality Data Model](#4-personality-data-model)
5. [Behavior Planner](#5-behavior-planner)
6. [Render Pipeline: Smoother Transitions](#6-render-pipeline-smoother-transitions)
7. [Territory & Favorite Spots](#7-territory--favorite-spots)
8. [Circadian Effects](#8-circadian-effects)
9. [PyQt6 Constraints & Feasibility](#9-pyqt6-constraints--feasibility)
10. [File Organization & Integration Plan](#10-file-organization--integration-plan)

---

## 1. Circadian Rhythm Architecture

### Current Problem
The existing code has time-of-day awareness (NEED_TIME_MULTIPLIERS, transitions.py dawn/dusk checks) but it's scattered across three files with inconsistent logic. There's no single clock driving behavior.

### Proposed: Hybrid Tick-Event Architecture

Keep the 33fps tick for physics/animation. Add a **circadian clock** that broadcasts phase changes as events.

```
┌──────────────────────────────────────┐
│           CircadianClock             │
│  ├─ phase: DAWN / DAY / DUSK / NIGHT │
│  ├─ internal_hour: 0-24 (float)      │
│  ├─ day_length: 24.0 (configurable)  │
│  ├─ events: phase_change Signal      │
│  └─ update(dt) → checks transitions  │
└──────────────┬───────────────────────┘
               │ events (phase_change)
               ▼
┌──────────────────────────────────────┐
│         BehaviorPlanner              │
│  ├─ reads circadian phase            │
│  ├─ schedules sequences              │
│  └─ sets internal_state.phase        │
└──────────────────────────────────────┘
               │ reads
               ▼
┌──────────────────────────────────────┐
│         Engine (every tick)          │
│  ├─ CircadianClock.update(dt)        │
│  ├─ BehaviorPlanner.update(dt)       │
│  ├─ Needs.update(dt, cat, state)     │
│  ├─ Transitions.update(dt, cat, st)  │
│  ├─ Navigation.update(dt, cat, st)   │
│  └─ Painter.update()                 │
└──────────────────────────────────────┘
```

### CircadianClock Implementation

```python
# behavior/circadian.py

import time
from enum import Enum
from dataclasses import dataclass

class CircadianPhase(Enum):
    DAWN     = "dawn"      # 5:00-7:00 — crepuscular peak 1
    MORNING  = "morning"   # 7:00-12:00
    MIDDAY   = "midday"    # 12:00-17:00 — siesta
    DUSK     = "dusk"      # 17:00-19:00 — crepuscular peak 2
    EVENING  = "evening"   # 19:00-22:00
    NIGHT    = "night"     # 22:00-5:00  — deep sleep

@dataclass
class CircadianParams:
    """Scalars applied per phase. Behavior planner reads these."""
    energy_regen_rate: float     # e.g. 1.5x at night
    energy_drain_rate: float     # e.g. 2.0x during dawn/dusk
    wander_chance: float         # e.g. 3.0x at dawn/dusk
    sleep_chance: float          # e.g. 4.0x at night
    play_chance: float           # e.g. 2.0x during dusk
    hunt_chance: float           # e.g. 2.5x at dawn
    vocal_frequency: float       # e.g. 0.5x at night (quiet)
    curiosity_mult: float        # e.g. 1.5x at dawn/dusk

class CircadianClock:
    """
    Drives all time-dependent behavior. Maps real or simulated time
    to circadian phases with smooth transitions.
    
    Key feature: supports simulated accelerated time for testing,
    and real-time mode for production.
    """
    
    def __init__(self, state, time_source: str = "real", 
                 time_scale: float = 1.0,
                 custom_hour: float = None):
        """
        time_source: "real" | "simulated"
        time_scale: 1.0 = real-time, 2.0 = 2x speed (for testing)
        custom_hour: override hour (0-24) for simulated mode
        """
        self.state = state
        self.time_source = time_source
        self.time_scale = time_scale
        self._internal_hour = custom_hour or self._real_hour()
        self._phase = self._compute_phase(self._internal_hour)
        self._accum = 0.0
        
        # Phase effect params (computed at phase change)
        self.params = self._phase_params(self._phase)
    
    def update(self, dt: float):
        """Advance clock. dt is real wall-clock seconds."""
        effective_dt = dt * self.time_scale
        self._accum += effective_dt
        
        # Advance internal hour
        self._internal_hour += effective_dt / 3600.0
        if self._internal_hour >= 24.0:
            self._internal_hour -= 24.0
        
        new_phase = self._compute_phase(self._internal_hour)
        if new_phase != self._phase:
            old = self._phase
            self._phase = new_phase
            self.params = self._phase_params(new_phase)
            # Emit event for behavior planner
            self._on_phase_change(old, new_phase)
    
    def _compute_phase(self, hour: float) -> CircadianPhase:
        """Map 0-24 hour to phase."""
        if 5.0 <= hour < 7.0:
            return CircadianPhase.DAWN
        elif 7.0 <= hour < 12.0:
            return CircadianPhase.MORNING
        elif 12.0 <= hour < 17.0:
            return CircadianPhase.MIDDAY
        elif 17.0 <= hour < 19.0:
            return CircadianPhase.DUSK
        elif 19.0 <= hour < 22.0:
            return CircadianPhase.EVENING
        else:
            return CircadianPhase.NIGHT
    
    def _phase_params(self, phase: CircadianPhase) -> CircadianParams:
        params = {
            CircadianPhase.DAWN:    CircadianParams(0.6, 1.8, 3.0, 0.2, 1.5, 2.5, 1.2, 1.5),
            CircadianPhase.MORNING: CircadianParams(0.8, 1.0, 1.5, 0.5, 1.2, 1.0, 1.0, 1.0),
            CircadianPhase.MIDDAY:  CircadianParams(1.0, 0.5, 0.3, 0.8, 0.3, 0.2, 0.8, 0.5),
            CircadianPhase.DUSK:    CircadianParams(0.6, 1.8, 2.5, 0.3, 2.0, 1.5, 1.1, 1.3),
            CircadianPhase.EVENING: CircadianParams(0.8, 1.2, 1.0, 0.6, 1.0, 0.8, 0.9, 0.8),
            CircadianPhase.NIGHT:   CircadianParams(1.5, 0.3, 0.1, 4.0, 0.1, 0.1, 0.3, 0.3),
        }
        return params[phase]
```

### What Changes in the Engine Tick

```python
# In Engine.__init__:
self.circadian = CircadianClock(state)

# In Engine._on_tick():
self.circadian.update(dt)  # ← new: step 1 before everything else

# Needs system now reads circadian.params instead of ad-hoc hour checks
# Transitions.py reads circadian.params for wander/sleep/play chances
```

### Config Changes

```python
# config.py additions:
CIRCADIAN_TIME_SOURCE = "real"    # "real" | "simulated"
CIRCADIAN_TIME_SCALE = 1.0        # 2.0 = double-speed for testing
```

**Why this works with the tick architecture:** The circadian clock is O(1) per tick — a few float ops and one phase comparison. Zero overhead. The real cost is in the behavior planner that reads it, which runs at ~1Hz.

---

## 2. Cat Memory System

### Current Problem
Zero memory. The cat acts on current needs + random LLM prompt. Each decision is a blank slate. A cat that just ate should remember being fed and not beg. A cat that was just petted should remember affection.

### Architecture: Short-Term + Long-Term Memory

```
┌──────────────────────────────┐
│       ShortTermMemory        │  ← in-dict, last ~5 min
│  ├─ last N actions           │
│  ├─ recent interactions      │
│  ├─ recent locations visited │
│  └─ recent sounds/events     │
├──────────────────────────────┤
│       LongTermMemory         │  ← SQLite, persisted across sessions
│  ├─ daily patterns           │
│  ├─ user habits learned      │
│  ├─ preferred spots          │
│  ├─ mood baselines           │
│  └─ associative learning     │
└──────────────────────────────┘
```

### Short-Term Memory (in RAM, on cat dict)

```python
# Added to default_cat_dict():
"short_term": {
    "recent_actions": [],          # deque(maxlen=20): [(timestamp, action, detail)]
    "recent_locations": [],        # deque(maxlen=15): [(timestamp, x, y)]
    "last_interaction_type": None, # "pet" | "feed" | "play" | "wake" | None
    "last_interaction_time": 0.0,
    "last_meal_time": 0.0,        # timestamp of last feed
    "recent_sounds": [],           # deque(maxlen=10): [(timestamp, sound_name)]
    "attention_calls": 0,          # how many times user called/clicked recently
    "recent_user_proximity": [],   # deque(maxlen=5): [(timestamp, "near"|"far")] 
    "emotional_state": {           # decaying emotional state
        "contentment": 50.0,       # 0-100, decays over time
        "frustration": 0.0,        # 0-100, builds from unmet needs
        "excitement": 0.0,         # 0-100, spikes from play/chase
    },
}
```

Short-term memory decays naturally — old entries age out of the deque.

### Long-Term Memory (SQLite)

```python
# behavior/memory.py

import sqlite3
import json
import os
from datetime import datetime, timedelta

MEMORY_DB_PATH = os.path.join(config.STATE_DIR, "cat_memory.db")

# Schema:
#
# cat_memories:
#   id INTEGER PRIMARY KEY
#   cat_id INTEGER
#   memory_type TEXT          -- "spot" | "habit" | "user_pattern" | "mood_baseline" | "association"
#   key TEXT                  -- e.g. "favorite_spot_1" 
#   value TEXT                -- JSON-encoded data
#   confidence REAL           -- 0.0 to 1.0, how confident in this memory
#   created_at TEXT           -- ISO timestamp
#   updated_at TEXT           -- ISO timestamp
#   access_count INTEGER      -- how many times this memory was read
#
# cat_daily_stats:
#   id INTEGER PRIMARY KEY
#   cat_id INTEGER
#   date TEXT                  -- "2026-05-22"
#   total_sleep_min REAL
#   total_walk_min REAL
#   total_play_min REAL
#   total_sit_min REAL
#   meal_count INTEGER
#   pet_count INTEGER
#   avg_energy REAL
#   avg_boredom REAL
#   avg_hunger REAL

class CatMemory:
    """Persistent memory for one cat. Thread-safe via SQLite WAL mode."""
    
    def __init__(self, cat_id: int):
        self.cat_id = cat_id
        self._conn = sqlite3.connect(MEMORY_DB_PATH, timeout=1.0)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=OFF")
        self._init_tables()
    
    def _init_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS cat_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cat_id INTEGER NOT NULL,
                memory_type TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                UNIQUE(cat_id, memory_type, key)
            );
            CREATE TABLE IF NOT EXISTS cat_daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cat_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                UNIQUE(cat_id, date, metric)
            );
            CREATE INDEX IF NOT EXISTS idx_mem_type ON cat_memories(cat_id, memory_type);
        """)
    
    def remember(self, memory_type: str, key: str, value, confidence: float = 0.5):
        """Store or update a memory."""
        now = datetime.now().isoformat()
        value_json = json.dumps(value) if not isinstance(value, str) else value
        self._conn.execute("""
            INSERT INTO cat_memories (cat_id, memory_type, key, value, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cat_id, memory_type, key) DO UPDATE SET
                value = excluded.value,
                confidence = (confidence + excluded.confidence) / 2,
                updated_at = excluded.updated_at,
                access_count = access_count + 1
        """, (self.cat_id, memory_type, key, value_json, confidence, now, now))
        self._conn.commit()
    
    def recall(self, memory_type: str, key: str = None, min_confidence: float = 0.3):
        """Retrieve memory. Returns list of (key, value, confidence) tuples."""
        if key:
            rows = self._conn.execute("""
                SELECT key, value, confidence FROM cat_memories
                WHERE cat_id = ? AND memory_type = ? AND key = ? AND confidence >= ?
            """, (self.cat_id, memory_type, key, min_confidence)).fetchall()
        else:
            rows = self._conn.execute("""
                SELECT key, value, confidence FROM cat_memories
                WHERE cat_id = ? AND memory_type = ? AND confidence >= ?
                ORDER BY access_count DESC, confidence DESC
                LIMIT 20
            """, (self.cat_id, memory_type, min_confidence)).fetchall()
        
        result = []
        for r in rows:
            try:
                val = json.loads(r[1])
            except (json.JSONDecodeError, TypeError):
                val = r[1]
            result.append((r[0], val, r[2]))
        return result
    
    def record_daily(self, metric: str, value: float):
        """Accumulate a daily stat metric."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._conn.execute("""
            INSERT INTO cat_daily_stats (cat_id, date, metric, value)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cat_id, date, metric) DO UPDATE SET
                value = value + excluded.value
        """, (self.cat_id, today, metric, value))
        self._conn.commit()
    
    def get_daily_summary(self) -> dict:
        """Return today's stats as {metric: value}."""
        today = datetime.now().strftime("%Y-%m-%d")
        rows = self._conn.execute("""
            SELECT metric, value FROM cat_daily_stats
            WHERE cat_id = ? AND date = ?
        """, (self.cat_id, today)).fetchall()
        return {r[0]: r[1] for r in rows}
    
    def close(self):
        self._conn.close()
```

### What Gets Remembered (Automatic Triggers)

| Event | Memory Type | Key | Value |
|-------|-------------|-----|-------|
| Cat sits at same spot 3+ times/day | "spot" | f"favorite_{n}" | (x, y, visit_count) |
| User feeds cat | "user_pattern" | "feeding_time" | hour_of_day (averaged) |
| User goes AFK for >30min | "user_pattern" | "afk_habit" | time_of_day |
| Cat is petted repeatedly | "user_pattern" | "pet_sessions" | frequency, avg_duration |
| Cat played with toy at spot | "association" | "play_spot" | (x, y) coordinates |
| Cat woke up at same time 3+ days | "habit" | "wake_time" | hour of day |
| Cat chased something at location | "association" | "prey_spot" | (x, y) coordinates |

### Integration with LLM Agent

```python
# In build_context():
def build_context(cat: dict, state, circadian: CircadianClock, memory: CatMemory) -> str:
    """Enhanced context with memory and circadian awareness."""
    
    # ... existing context ...
    
    # Add memory-informed context
    daily = memory.get_daily_summary()
    favorite_spots = memory.recall("spot", min_confidence=0.6)
    
    lines = [
        # ... existing lines ...
        f"Circadian phase: {circadian._phase.value}",
        f"Internal time: {circadian._internal_hour:.1f}h",
        f"Today: slept {daily.get('sleep_min', 0):.0f}min, "
        f"played {daily.get('play_min', 0):.0f}min, "
        f"ate {int(daily.get('meal_count', 0))} times",
    ]
    
    if favorite_spots:
        spots = [f"({s[1][0]:.0f}, {s[1][1]:.0f})" for s in favorite_spots[:3]]
        lines.append(f"Favorite spots: {', '.join(spots)}")
    
    return "\n".join(lines)
```

---

## 3. Behavioral Sequences

### Current Problem
Random single actions. Cat walks, sits, walks, sleeps — no narrative. Real cats have sequences: wake → stretch → yawn → walk to bowl → eat → groom → walk to window → sit → sleep.

### Implementation: Sequence Planner

```python
# behavior/sequences.py

from typing import List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

class SequenceState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"

@dataclass
class SequenceStep:
    name: str                       # "stretch"
    action: str                     # "STRETCH"
    params: dict = None             # {"duration": 2.0}
    duration: float = 2.0           # seconds to complete
    can_interrupt: bool = False     # can user petting abort this step?
    on_start: Callable = None       # called when step begins
    on_complete: Callable = None    # called when step finishes

@dataclass
class Sequence:
    """A named behavioral sequence."""
    name: str                       # "morning_routine"
    trigger: str                    # "on_wake" | "on_arrive_home" | "after_meal" | "time_of_day"
    priority: int                   # 0-10, higher = more important
    steps: List[SequenceStep]
    cooldown: float = 120.0         # min seconds between repetitions
    circadian_phase: str = None     # optional: only run during this phase

# ── Built-in Sequences ──────────────────────────────────────────

WAKE_UP_SEQUENCE = Sequence(
    name="wake_up",
    trigger="on_wake",
    priority=5,
    steps=[
        SequenceStep("yawn", "YAWN", {"duration": 0.8}, can_interrupt=True),
        SequenceStep("stretch_front", "STRETCH_FRONT", {"duration": 1.5}, can_interrupt=True),
        SequenceStep("stretch_back", "STRETCH_BACK", {"duration": 1.5}, can_interrupt=True),
        SequenceStep("sit_up", "SIT", {"duration": 1.0}),
    ],
    cooldown=300.0,  # 5 min between full wake sequences
    circadian_phase=None,
)

EAT_SEQUENCE = Sequence(
    name="eat",
    trigger="on_feed",
    priority=8,  # high priority — eating is important
    steps=[
        SequenceStep("walk_to_bowl", "WALK", {"x": "bowl_x", "y": "bowl_y"}, 
                      duration=3.0, can_interrupt=False),
        SequenceStep("eat", "EAT", {"duration": 4.0}, can_interrupt=False),
        SequenceStep("lick_paws", "GROOM", {"duration": 2.0}, can_interrupt=True),
        SequenceStep("look_up", "SIT", {"duration": 2.0}, can_interrupt=True),
    ],
    cooldown=60.0,
)

GROOM_SEQUENCE = Sequence(
    name="full_groom",
    trigger="time_of_day",  # runs ~3x per day naturally
    priority=2,
    steps=[
        SequenceStep("lick_paw", "LICK_PAW", {"duration": 3.0}),
        SequenceStep("wipe_face", "WIPE_FACE", {"duration": 2.0}),
        SequenceStep("lick_chest", "LICK_CHEST", {"duration": 4.0}),
        SequenceStep("lick_flank", "LICK_FLANK", {"duration": 3.0}),
        SequenceStep("pause", "SIT", {"duration": 2.0}),
        SequenceStep("lick_tail", "LICK_TAIL", {"duration": 3.0}),
    ],
    cooldown=3600.0,  # 1 hour between full grooms
)

HUNT_PLAY_SEQUENCE = Sequence(
    name="hunt_play",
    trigger="time_of_day",  # dawn/dusk
    priority=4,
    steps=[
        SequenceStep("stalk", "STALK", {"duration": 2.0}),
        SequenceStep("pounce", "POUNCE", {"duration": 0.5}),
        SequenceStep("bat", "BAT", {"duration": 1.0}),
        SequenceStep("watch", "SIT", {"duration": 3.0}),
    ],
    cooldown=600.0,  # 10 min
)

NAP_SEQUENCE = Sequence(
    name="nap_prep",
    trigger="on_sleep",
    priority=3,
    steps=[
        SequenceStep("circle", "CIRCLE_BED", {"duration": 2.0}),
        SequenceStep("knead", "KNEAD", {"duration": 3.0}),
        SequenceStep("curl", "SLEEP", {"duration": 0.5}),
    ],
    cooldown=600.0,
)

# ── Sequence Manager ─────────────────────────────────────────────

class SequenceManager:
    """
    Manages which sequence is running and advances through steps.
    
    Replaces the simple state machine for sequence-driven behavior.
    Idle behavior still uses the planner/machine for non-sequence actions.
    """
    
    def __init__(self):
        self.active_sequence: Optional[Sequence] = None
        self.current_step_idx: int = 0
        self.step_elapsed: float = 0.0
        self.state: SequenceState = SequenceState.IDLE
        self.last_sequence_time: dict = {}  # sequence_name → last run timestamp
        self._step_cooldowns: dict = {}      # step_name → cooldown remaining
    
    def start_sequence(self, sequence: Sequence):
        """Begin running a sequence. Interrupts current sequence."""
        if self.state == SequenceState.RUNNING:
            self.abort("interrupted by new sequence")
        self.active_sequence = sequence
        self.current_step_idx = 0
        self.step_elapsed = 0.0
        self.state = SequenceState.RUNNING
        self.last_sequence_time[sequence.name] = time.monotonic()
    
    def update(self, dt: float, cat: dict, state) -> tuple:
        """
        Advance sequence. Returns (action, params) for the current step,
        or None if no sequence is active.
        
        Called by the behavior planner. If a sequence is active, its action
        takes priority over the state machine.
        """
        if self.state != SequenceState.RUNNING or self.active_sequence is None:
            return None
        
        seq = self.active_sequence
        step = seq.steps[self.current_step_idx]
        self.step_elapsed += dt
        
        # Check if step duration completed
        if self.step_elapsed >= step.duration:
            self.current_step_idx += 1
            self.step_elapsed = 0.0
            
            # Check if sequence finished
            if self.current_step_idx >= len(seq.steps):
                self.state = SequenceState.COMPLETED
                self.active_sequence = None
                return ("SIT", None)  # graceful end
            
            step = seq.steps[self.current_step_idx]
        
        # Resolve dynamic params (e.g., "bowl_x" → actual coordinate)
        resolved_params = self._resolve_params(step.params, cat, state)
        
        return (step.action, resolved_params)
    
    def can_interrupt(self) -> bool:
        """Can the current sequence be interrupted by user interaction?"""
        if self.active_sequence is None:
            return True
        step = self.active_sequence.steps[self.current_step_idx]
        return step.can_interrupt
    
    def abort(self, reason: str = "unknown"):
        """Abort the current sequence."""
        if self.active_sequence:
            self.active_sequence = None
            self.current_step_idx = 0
            self.step_elapsed = 0.0
            self.state = SequenceState.ABORTED
    
    def _resolve_params(self, params: dict, cat: dict, state) -> dict:
        """Replace symbolic references like 'bowl_x' with actual values."""
        if params is None:
            return None
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str) and v == "bowl_x":
                resolved[k] = cat.get("x", 500.0)
            elif isinstance(v, str) and v == "bowl_y":
                resolved[k] = cat.get("y", 700.0)
            else:
                resolved[k] = v
        return resolved
```

### Sequence Selection Logic

```python
# In BehaviorPlanner.decide():

def _select_sequence(self, cat: dict, circadian: CircadianClock, 
                     short_term: dict) -> Optional[Sequence]:
    """Choose the best sequence to run right now."""
    
    now = time.monotonic()
    candidates = []
    
    # 1. Event-triggered sequences (highest priority)
    if cat.get("_just_ate", False):
        candidates.append(EAT_SEQUENCE)
    
    if short_term.get("last_interaction_type") == "wake":
        candidates.append(WAKE_UP_SEQUENCE)
    
    # 2. Time-triggered sequences
    phase = circadian._phase
    if phase in (CircadianPhase.DAWN, CircadianPhase.DUSK):
        candidates.append(HUNT_PLAY_SEQUENCE)
    
    # 3. Need-driven sequences
    if cat.get("boredom", 0) > 70:
        candidates.append(HUNT_PLAY_SEQUENCE)
    if cat.get("energy", 80) > 70 and cat.get("boredom", 0) > 50:
        candidates.append(HUNT_PLAY_SEQUENCE)
    
    # 4. Maintenance sequences (low priority, check cooldown)
    if self._sequence_cooldown_ok("full_groom"):
        candidates.append(GROOM_SEQUENCE)
    
    # 5. Filter by cooldown
    available = [s for s in candidates 
                 if self._sequence_cooldown_ok(s.name)]
    
    if not available:
        return None
    
    # Pick highest priority
    return max(available, key=lambda s: s.priority)
```

### New Actions Required for Sequences

These need new rendering code:

| Action | Description | Est. Work |
|--------|-------------|-----------|
| `YAWN` | Mouth opens wide, eyes squint, head tilts back | Small (modify head draw) |
| `STRETCH_FRONT` | Front legs extend forward, body elongates, butt up | Medium (new pose) |
| `STRETCH_BACK` | Back legs extend one at a time | Medium (new leg anim) |
| `LICK_PAW` | Paw lifts to mouth, tongue motion | Medium (new paw+head anim) |
| `WIPE_FACE` | Wet paw wipes over ear/face | Medium |
| `LICK_CHEST` | Head down to chest, tongue visible | Small |
| `LICK_FLANK` | Twist head to side, lick flank | Medium |
| `LICK_TAIL` | Head turns back, tail brought forward | Medium |
| `CIRCLE_BED` | Walk in tight circle before lying down | Small (reuse walk) |
| `KNEAD` | Alternating paw presses, purr | Small (new animation) |
| `STALK` | Low crouch, slow creeping walk | Medium (new walk pose) |
| `POUNCE` | Jump forward with front paws extended | Medium (new pose) |
| `BAT` | Paw swat at toy, claws out | Small (new arm anim) |
| `EAT` | Head down, chewing motion | Small (modify head draw) |

### Sequence Priority Rules

1. **Safety sequences** (fear/hiss/growl) interrupt everything — priority 10
2. **Hunger sequences** (walk to bowl → eat) — priority 8, uninterruptible during eating
3. **Wake sequences** (stretch → yawn) — priority 5
4. **Play sequences** (stalk → pounce → bat) — priority 4
5. **Maintenance** (groom, nap) — priority 2-3
6. **Random walk** — no sequence, fall through to state machine

---

## 4. Personality Data Model

### Current Problem
No personality. Every cat behaves identically. The prompt in agent.py describes "curious but easily bored" but it's just text — no actual traits.

### Implementation: Trait Vector System

```python
# behavior/personality.py

from dataclasses import dataclass, field
from typing import Dict
import random
import json
import os

# Big 5 for cats (adapted — validated against cat behavior research)
# Each trait is 0.0 to 1.0

TRAIT_LABELS = {
    "confidence": {
        "low": "Timid — hides, startles easily",
        "high": "Bold — approaches new things, doesn't flee",
    },
    "sociability": {
        "low": "Aloof — independent, seeks solitude",
        "high": "Affectionate — seeks contact, purrs readily",
    },
    "playfulness": {
        "low": "Sedate — prefers lounging over playing",
        "high": "Energetic — initiates play, chases everything",
    },
    "curiosity": {
        "low": "Incurious — ignores novelty, stays in comfort zone",
        "high": "Inquisitive — investigates every change",
    },
    "vocalness": {
        "low": "Quiet — rarely meows, communicates by presence",
        "high": "Chatty — meows, trills, chirps frequently",
    },
    "agreeableness": {
        "low": "Grumpy — hisses, swats when annoyed",
        "high": "Easygoing — tolerates handling, adapts well",
    },
    "neatness": {
        "low": "Messy — doesn't groom much, tolerates mess",
        "high": "Fastidious — grooms frequently, precise",
    },
    "food_motivation": {
        "low": "Picky eater — eats when hungry, indifferent to treats",
        "high": "Food-driven — meows for food, linked to feeding time",
    },
}

@dataclass
class Personality:
    """Per-cat personality trait vector."""
    confidence: float = 0.5         # boldness, fear response
    sociability: float = 0.5        # affection, contact-seeking
    playfulness: float = 0.5        # play drive
    curiosity: float = 0.5          # novelty-seeking
    vocalness: float = 0.5          # vocalization frequency
    agreeableness: float = 0.5      # tolerance, patience
    neatness: float = 0.5           # grooming frequency
    food_motivation: float = 0.5    # food drive
    
    def clamp(self):
        """Ensure all traits are 0-1."""
        for attr in self.__dataclass_fields__:
            v = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, v)))
    
    def to_dict(self):
        return {f: getattr(self, f) for f in self.__dataclass_fields__}
    
    @classmethod
    def random(cls):
        """Generate a random cat personality (realistic distribution)."""
        import random
        p = cls()
        for attr in p.__dataclass_fields__:
            # Use normal distribution centered on 0.5
            v = random.gauss(0.5, 0.2)
            setattr(p, attr, max(0.0, min(1.0, v)))
        return p

    @classmethod
    def from_name(cls, name: str):
        """Get personality from a named archetype."""
        ARCHETYPES = {
            "mellow_lap_cat": cls(confidence=0.7, sociability=0.9, playfulness=0.3,
                                    curiosity=0.4, vocalness=0.3, agreeableness=0.9,
                                    neatness=0.6, food_motivation=0.5),
            "curious_explorer": cls(confidence=0.8, sociability=0.5, playfulness=0.7,
                                     curiosity=0.9, vocalness=0.4, agreeableness=0.6,
                                     neatness=0.3, food_motivation=0.4),
            "grumpy_queen": cls(confidence=0.6, sociability=0.2, playfulness=0.3,
                                 curiosity=0.4, vocalness=0.6, agreeableness=0.2,
                                 neatness=0.8, food_motivation=0.7),
            "playful_kitten": cls(confidence=0.5, sociability=0.8, playfulness=0.95,
                                   curiosity=0.8, vocalness=0.5, agreeableness=0.7,
                                   neatness=0.2, food_motivation=0.6),
            "shy_wallflower": cls(confidence=0.2, sociability=0.3, playfulness=0.4,
                                   curiosity=0.3, vocalness=0.2, agreeableness=0.7,
                                   neatness=0.5, food_motivation=0.3),
        }
        return ARCHETYPES.get(name, cls())


# ── Personality Effects on Behavior ──────────────────────────
# These functions map personality traits to behavior modifiers.
# Each returns a multiplier applied to the base probability/config value.


def fear_response(p: Personality) -> float:
    """Multiplier for flee/hide threshold (lower = more fearful)."""
    # Low confidence = more fearful = lower threshold
    return 0.3 + p.confidence * 0.7


def affection_chance(p: Personality) -> float:
    """Chance to seek user contact when idle."""
    return p.sociability * 0.08  # max ~8% per tick check


def play_initiative(p: Personality) -> float:
    """Chance to start playing when energy > 50."""
    return p.playfulness * 0.03


def grooming_frequency(p: Personality) -> float:
    """Base interval in seconds between grooming sessions."""
    # Low neatness = grooms less often
    return 120.0 + (1.0 - p.neatness) * 480.0  # 120-600s interval


def vocalization_rate(p: Personality) -> float:
    """Seconds between voluntary vocalizations."""
    return 30.0 + (1.0 - p.vocalness) * 270.0  # 30-300s


def explore_radius(p: Personality) -> float:
    """How far from comfortable spots the cat will explore."""
    return 100.0 + p.confidence * 300.0 + p.curiosity * 200.0


def tolerance_time(p: Personality) -> float:
    """Seconds of petting before cat walks away."""
    return 1.0 + p.agreeableness * 9.0  # 1-10s


def food_urgency(p: Personality) -> float:
    """Hunger threshold for vocal demands."""
    return 100.0 - p.food_motivation * 50.0  # 50-100 range


# ── Persistence ──────────────────────────────────────────────

def save_personality(personality: Personality, cat_id: int):
    """Save personality to disk."""
    path = os.path.join(config.STATE_DIR, f"personality_{cat_id}.json")
    with open(path, "w") as f:
        json.dump(personality.to_dict(), f)


def load_personality(cat_id: int) -> Personality:
    """Load personality from disk, or generate random if not found."""
    path = os.path.join(config.STATE_DIR, f"personality_{cat_id}.json")
    try:
        with open(path) as f:
            data = json.load(f)
        return Personality(**data)
    except (FileNotFoundError, json.JSONDecodeError):
        p = Personality.random()
        save_personality(p, cat_id)
        return p


---

## 5. Behavior Planner

### Current Problem
Two competing decision systems:
1. Hardcoded state machine (transitions.py) runs every tick
2. LLM agent (agent.py) runs every ~2s in a background thread

Both make independent decisions. The LLM often overrides the state machine mid-stride, creating jarring transitions. Neither has awareness of sequences, memory, or personality.

### Proposed: Unified BehaviorPlanner

```python
# behavior/planner.py

"""
Unified behavior planner that replaces the split between transitions.py
and agent.py for the core decision loop.

Architecture:
  1. Every tick, check critical needs (emergency override)
  2. If sequence is active, advance it (highest priority)
  3. If user is interacting, handle interaction (medium priority)
  4. Otherwise, use the state machine with circadian + personality + memory
  5. LLM is consulted for novelty detection (rare, ~every 30s)
"""

from typing import Optional, Tuple
from dataclasses import dataclass
import random

import config
from behavior.sequences import Sequence, SequenceManager, SequenceState
from behavior.personality import Personality
from behavior.circadian import CircadianClock, CircadianPhase


@dataclass
class Decision:
    """A single decision output by the planner."""
    action: str
    params: dict = None
    source: str = "state_machine"  # "sequence" | "interaction" | "state_machine" | "llm" | "emergency"


class BehaviorPlanner:
    """
    Central decision-maker. Runs every tick, returns one action.
    
    Priority order:
      1. Emergency overrides (critical needs)
      2. Active sequence advancement
      3. Interaction handling (user proximity)
      4. State machine (transitions.py stripped down)
      5. LLM consultation (periodic novelty)
    """
    
    def __init__(self, state, personality: Personality, 
                 circadian: CircadianClock, memory=None):
        self.state = state
        self.personality = personality
        self.circadian = circadian
        self.memory = memory
        self.sequence_mgr = SequenceManager()
        self._llm_cooldown = 0.0
        self._llm_interval = 30.0  # LLM consulted every 30s, not every 2s
        self._last_action = ("SIT", None)
    
    def decide(self, dt: float, cat: dict) -> Decision:
        """
        Main decision entry point. Returns one action with params.
        Called every tick. Never blocks.
        """
        # 1. Emergency override — critical needs always win
        emergency = self._check_emergency(cat)
        if emergency:
            return emergency
        
        # 2. Active sequence — sequences cannot be interrupted by state machine
        if self.sequence_mgr.state == SequenceState.RUNNING:
            seq_action = self.sequence_mgr.update(dt, cat, self.state)
            if seq_action is not None:
                return Decision(seq_action[0], seq_action[1], source="sequence")
        
        # 3. Interaction handling — user is nearby
        if self._is_user_interacting(cat):
            interaction = self._handle_interaction(cat)
            if interaction:
                return interaction
        
        # 4. State machine (simplified from transitions.py)
        machine_action = self._state_machine_step(dt, cat)
        if machine_action:
            return machine_action
        
        # 5. Periodic LLM consultation for novelty (replaces agent.py)
        self._llm_cooldown -= dt
        if self._llm_cooldown <= 0:
            self._llm_cooldown = self._llm_interval
            llm_action = self._ask_llm(cat)
            if llm_action:
                return llm_action
        
        # Fallback
        return Decision("SIT", None, source="fallback")
    
    def _check_emergency(self, cat: dict) -> Optional[Decision]:
        """Critical need overrides. These fire immediately."""
        if cat["energy"] < 15 and cat["state"] != config.STATE_SLEEP:
            self.sequence_mgr.abort("emergency: low energy")
            return Decision("HOME", None, source="emergency")
        if cat["hunger"] > 85:
            self.sequence_mgr.abort("emergency: hunger")
            return Decision("HOME", None, source="emergency")
        return None
    
    def _is_user_interacting(self, cat: dict) -> bool:
        """Is the user currently interacting with this cat?"""
        mouse_near = cat.get("mouse_near", False)
        # High consecutive pets means active petting
        consec = cat.get("consecutive_pets", 0)
        return mouse_near or consec > 0
    
    def _handle_interaction(self, cat: dict) -> Optional[Decision]:
        """Respond to user interaction based on personality."""
        consec = cat.get("consecutive_pets", 0)
        tolerance = behavior.personality.tolerance_time(self.personality)
        
        # Cat has been petted enough — walks away
        if consec >= int(tolerance * 2):
            cat["consecutive_pets"] = 0
            angle = random.uniform(0, 360)
            dx = math.cos(math.radians(angle)) * 100
            nx = cat["x"] + dx
            return Decision("WALK", {"x": nx, "y": cat["y"]}, source="interaction")
        
        # Otherwise, purr or slow blink
        if random.random() < self.personality.sociability:
            return Decision("PURR", None, source="interaction")
        return Decision("SLOWBLINK", None, source="interaction")
    
    def _state_machine_step(self, dt: float, cat: dict) -> Optional[Decision]:
        """
        Simplified state machine. Replaces transitions.py.
        Uses circadian phase + personality to weight decisions.
        """
        phase = self.circadian._phase
        p = self.personality
        
        # Periodically try to start a sequence
        if self.sequence_mgr.state == SequenceState.IDLE:
            seq = self._select_appropriate_sequence(cat)
            if seq is not None:
                self.sequence_mgr.start_sequence(seq)
                return Decision(seq.steps[0].action, seq.steps[0].params, 
                               source="sequence")
        
        # Fall through to existing state transitions (read from transitions.py)
        # but with personality-weighted probabilities
        # ... existing state machine logic ...
        return None
    
    def _select_appropriate_sequence(self, cat: dict) -> Optional[Sequence]:
        """Choose a sequence based on cat state + personality + time."""
        from behavior.sequences import (
            WAKE_UP_SEQUENCE, EAT_SEQUENCE, GROOM_SEQUENCE,
            HUNT_PLAY_SEQUENCE, NAP_SEQUENCE
        )
        
        phase = self.circadian._phase
        p = self.personality
        
        # Dawn/dusk: hunt-play sequence (crepuscular instinct)
        if phase in (CircadianPhase.DAWN, CircadianPhase.DUSK):
            if random.random() < p.playfulness * 0.02:
                return HUNT_PLAY_SEQUENCE
        
        # Midday: grooming
        if phase == CircadianPhase.MIDDAY:
            if random.random() < p.neatness * 0.01:
                return GROOM_SEQUENCE
        
        # Night: sleep
        if phase == CircadianPhase.NIGHT:
            if random.random() < 0.01:
                return NAP_SEQUENCE
        
        return None
    
    def _ask_llm(self, cat: dict) -> Optional[Decision]:
        """
        Consult LLM for novel actions. Called rarely (~every 30s).
        Returns None if LLM is unavailable or suggests nothing new.
        """
        # Only consult LLM for novelty when cat is idle
        if cat["state"] != "SIT":
            return None
        # ... existing LLM call, but as a LOW-PRIORITY novelty source ...
        return None
```

### Planner Priority Chain Visualization

```
Every tick (33fps):
  ├─ Emergency? → HOME / SLEEP
  ├─ Sequence active? → advance step
  ├─ User interacting? → interaction response
  │   └─ Petted too long? → walk away (personality-based)
  ├─ Time for sequence? → start appropriate sequence
  ├─ State machine → sit/walk/sleep/chase
  └─ LLM cool expired? → ask for novelty (~30s)
       └─ LLM busy? → return last action
```

---

## 6. Render Pipeline: Smoother Transitions

### Current Problem
State transitions are instant — cat teleports from WALK to SIT between 2 frames. No blend, no morph. Tails snap to new position. Eyes pop between expressions.

### Targets for Smoothing

| Transition | Current | Target |
|-----------|---------|--------|
| Walk → Sit | Teleport, frame N+1 | Decel over 0.3s, body settles |
| Sit → Walk | Instant acceleration | Lean forward, then walk |
| Sit → Sleep | Instant curl | Circle first, then curl |
| Expression change | Snapped | Eased over 0.2s |
| Blink | 150ms hard | 100ms ease-in-out |

### Implementation: Interpolation System

```python
# animation/interpolate.py

from dataclasses import dataclass
from typing import Dict, Any
import math


@dataclass
class AnimatedProp:
    """A smoothly animating numeric value."""
    current: float
    target: float
    velocity: float = 0.0
    easing: str = "smooth"  # "smooth" | "spring" | "overshoot" | "bounce"
    spring_tension: float = 200.0
    spring_damping: float = 15.0

    def update(self, dt: float):
        """Spring-physics based interpolation."""
        diff = self.target - self.current
        if abs(diff) < 0.001 and abs(self.velocity) < 0.001:
            self.current = self.target
            self.velocity = 0.0
            return
        
        if self.easing == "spring":
            force = diff * self.spring_tension
            damping = self.velocity * self.spring_damping
            accel = force - damping
            self.velocity += accel * dt
            self.current += self.velocity * dt
        elif self.easing == "smooth":
            self.current += diff * min(1.0, dt * 8.0)
        elif self.easing == "overshoot":
            self.current += diff * min(1.0, dt * 10.0)
            if abs(diff) < 5.0:
                self.current = self.target  # snap at end


class CatAnimator:
    """
    Manages smoothly animated properties for one cat.
    
    Instead of directly writing to cat dict, writes to animated props
    that smoothly track targets. Drawing code reads animated values.
    """
    
    def __init__(self):
        # Body position (for decel/accel)
        self.body_y = AnimatedProp(0.0, 0.0, easing="spring")
        self.body_tilt = AnimatedProp(0.0, 0.0, easing="smooth")
        
        # Tail (continuous, always smooth)
        self.tail_angle = AnimatedProp(0.0, 0.0, easing="smooth")
        
        # Expression morphing
        self.eye_width = AnimatedProp(4.0, 4.0, easing="smooth")
        self.eye_height = AnimatedProp(4.0, 4.0, easing="smooth")
        self.pupil_width = AnimatedProp(2.5, 2.5, easing="smooth")
        self.pupil_height = AnimatedProp(2.5, 2.5, easing="smooth")
        self.pupil_x = AnimatedProp(0.0, 0.0, easing="smooth")
        self.pupil_y = AnimatedProp(0.0, 0.0, easing="smooth")
        
        # Head tracking (smooth rotation toward target)
        self.head_angle = AnimatedProp(0.0, 0.0, easing="spring",
                                       spring_tension=100.0, spring_damping=12.0)
        
        # Posture blend (0 = sitting, 1 = walking, 2 = sleeping, etc.)
        self.posture_blend = AnimatedProp(0.0, 0.0, easing="smooth")
    
    def update(self, dt: float):
        """Tick all animated properties."""
        for attr in self.__dict__.values():
            if isinstance(attr, AnimatedProp):
                attr.update(dt)
```

### State Transition Blending

```python
# In Engine._on_tick, replace:
#   cat["state"] = "SIT"  # instant
# With:
#   cat["_pending_state"] = "SIT"
#   cat["_transition_progress"] += dt / transition_duration

# In drawing code, blend between poses during transitions:
#   blend = cat["_transition_progress"]  # 0.0 → 1.0
#   if blend < 1.0:
#       draw_pose_blend(painter, cx, cy, cat, old_pose, new_pose, blend)
#   else:
#       draw_pose(painter, cx, cy, cat, new_pose)
```

This is implemented as a **transition state** on the cat dict:

```python
# Added to default_cat_dict():
"transition": {
    "active": False,         # True during a blend
    "from_state": None,       # "WALK", "SIT", etc.
    "to_state": None,
    "progress": 0.0,         # 0.0 → 1.0
    "duration": 0.3,         # seconds (configurable per transition type)
    "init_y": None,          # y at transition start (for smooth y changes)
}
```

### Easing Curves (New)

```python
# animation/easing.py

import math

def ease_in_out(t: float) -> float:
    """Smooth step. t in [0, 1]."""
    return t * t * (3.0 - 2.0 * t)

def ease_out(t: float) -> float:
    """Fast start, slow end."""
    return 1.0 - (1.0 - t) * (1.0 - t)

def ease_in(t: float) -> float:
    """Slow start, fast end."""
    return t * t

def ease_out_back(t: float) -> float:
    """Overshoot slightly at end (good for head turns)."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0)**3 + c1 * (t - 1.0)**2

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t
```

### Smoother Gait Animation

Current gait is 8 frames with hard frame switches. Improvement:
- Interpolate between gait frames using elapsed time within the step
- Body bob becomes a continuous sine wave instead of a table lookup
- Tail sway becomes continuous sinusoidal

```python
# In legs.py, replace GAIT_FRAMES_4LEG lookup with:

def get_gait_position(walk_elapsed: float) -> dict:
    """
    Continuous gait using sinusoidal leg cycles.
    Returns leg positions for all 4 legs.
    """
    # Trot: diagonal pairs move together
    # Front-right + back-left are in phase
    # Front-left + back-right are in opposite phase
    phase = walk_elapsed * 8.0 * math.pi  # Full cycle in ~0.785s at 2 steps/sec
    
    return {
        "fl": {
            "lift": max(0.0, math.sin(phase + math.pi)),  # 0 = ground, 1 = max lift
            "reach": math.cos(phase + math.pi),            # -1 to 1, forward/back
        },
        "fr": {
            "lift": max(0.0, math.sin(phase)),
            "reach": math.cos(phase),
        },
        "bl": {
            "lift": max(0.0, math.sin(phase)),
            "reach": math.cos(phase),
        },
        "br": {
            "lift": max(0.0, math.sin(phase + math.pi)),
            "reach": math.cos(phase + math.pi),
        },
    }
```

---

## 7. Territory & Favorite Spots

### Current Problem
Cat has no memory of locations. It walks randomly within screen bounds. No favorite window, no preferred rug, no territory.

### Implementation: Zone Map

```python
# behavior/territory.py

from dataclasses import dataclass
from typing import List, Optional
import random
import time


@dataclass
class Zone:
    """A named area on screen."""
    name: str                    # "window" | "bed" | "rug" | "owner_keyboard"
    center_x: float
    center_y: float
    radius: float                # px — how far from center counts as "in zone"
    category: str = "general"    # "comfort" | "high_ground" | "warm" | "play" | "observation"
    cooldown: float = 0.0        # seconds left until cat can use this zone again
    visit_count: int = 0         # how many times cat has been here
    last_visit: float = 0.0      # timestamp
    
    def contains(self, x: float, y: float) -> bool:
        return math.hypot(x - self.center_x, y - self.center_y) <= self.radius


class Territory:
    """
    Manages the cat's known zones and favorite spots.
    Learns new zones from cat behavior + memory recall.
    """
    
    def __init__(self, state, memory: CatMemory = None):
        self.state = state
        self.memory = memory
        self.zones: List[Zone] = self._init_default_zones()
        # Dynamic zones learned from behavior
        self._discovered_spots: List[Zone] = []
        # Track where cat spends time
        self._location_log: List[tuple] = []  # [(timestamp, x, y), ...]
    
    def _init_default_zones(self) -> List[Zone]:
        """Default zones based on screen layout."""
        sw = self.state.screen_width
        sh = self.state.screen_height
        return [
            Zone("home_hut", sw - 50, sh - 50, 60, "comfort"),
            Zone("bottom_left", 100, sh - 50, 80, "general"),
            Zone("bottom_center", sw // 2, sh - 50, 100, "general"),
            Zone("bottom_right", sw - 150, sh - 50, 80, "general"),
        ]
    
    def update(self, dt: float, cat: dict):
        """
        Tick territory system.
        - Decay zone cooldowns
        - Log cat position for spot discovery
        - Periodically discover new favorite spots
        """
        for zone in self.zones + self._discovered_spots:
            zone.cooldown = max(0.0, zone.cooldown - dt)
        
        # Log position every ~10s
        self._location_accum += dt
        if self._location_accum >= 10.0:
            self._location_accum = 0.0
            self._location_log.append((time.monotonic(), cat["x"], cat["y"]))
            if len(self._location_log) > 500:
                self._location_log = self._location_log[-500:]
            self._try_discover_spot()
    
    def _try_discover_spot(self):
        """Analyze location log to find frequently visited spots."""
        # Simple: if cat sits in same area >5 times in last hour, it's a spot
        from collections import Counter
        recent = [p for p in self._location_log 
                  if p[0] > time.monotonic() - 3600]
        
        # Bin positions into 50px grid cells
        bins = Counter()
        for ts, x, y in recent:
            bx = int(x // 50) * 50 + 25
            by = int(y // 50) * 50 + 25
            bins[(bx, by)] += 1
        
        for (bx, by), count in bins.items():
            if count >= 5:  # visited 5+ times
                existing = any(z.contains(bx, by) for z in self.zones + self._discovered_spots)
                if not existing:
                    zone = Zone(f"spot_{len(self._discovered_spots)}", 
                               bx, by, 40, "general")
                    self._discovered_spots.append(zone)
                    # Save to long-term memory
                    if self.memory:
                        self.memory.remember("spot", zone.name, 
                                           (bx, by), min(1.0, count / 10.0))
    
    def get_nearby_zone(self, x: float, y: float) -> Optional[Zone]:
        """Find the zone closest to (x, y) within its radius."""
        for zone in self.zones + self._discovered_spots:
            if zone.contains(x, y):
                return zone
        return None
    
    def get_available_zone(self, cat_x: float, cat_y: float, 
                           preference: str = None) -> Optional[Zone]:
        """
        Get a zone the cat can walk to.
        preference: "comfort" | "warm" | "play" | "observation"
        """
        candidates = [z for z in self.zones + self._discovered_spots 
                      if z.cooldown <= 0.0]
        if preference:
            candidates = [z for z in candidates if z.category == preference]
        
        # Prefer zones farther from current position (exploration)
        if candidates:
            # Weight: 70% farthest, 30% favorite
            candidates.sort(key=lambda z: -math.hypot(z.center_x - cat_x, 
                                                      z.center_y - cat_y))
            return candidates[0]
        return None
```

### How Territory Feeds the Behavior Planner

```python
# In _state_machine_step or _select_appropriate_sequence:

# If cat is sitting and wants to explore:
target_zone = self.territory.get_available_zone(cat["x"], cat["y"], 
                                                 preference="observation")
if target_zone:
    return Decision("WALK", {"x": target_zone.center_x, "y": target_zone.center_y})

# If cat has a favorite spot that's not on cooldown:
fav = self.territory.get_available_zone(cat["x"], cat["y"], preference="comfort")
if fav:
    return Decision("HOME", None)  # or WALK to favorite spot
```

---

## 8. Circadian Effects

### Effects on Needs

| Circadian Phase | Energy Drain | Energy Recharge | Hunger Rate | Boredom Rate |
|-----------------|-------------|-----------------|-------------|-------------|
| DAWN (5-7)      | 1.8x        | 0.6x            | 1.2x        | 0.5x        |
| MORNING (7-12)  | 1.0x        | 0.8x            | 1.0x        | 1.0x        |
| MIDDAY (12-17)  | 0.5x        | 1.0x            | 0.7x        | 0.5x        |
| DUSK (17-19)    | 1.8x        | 0.6x            | 1.2x        | 0.5x        |
| EVENING (19-22) | 1.2x        | 0.8x            | 1.0x        | 1.2x        |
| NIGHT (22-5)    | 0.3x        | 1.5x            | 0.3x        | 0.1x        |

### Effects on Behavior Probabilities

| Behavior | DAWN | MORNING | MIDDAY | DUSK | EVENING | NIGHT |
|----------|------|---------|--------|------|---------|-------|
| Wander   | 3.0x | 1.5x    | 0.3x   | 2.5x | 1.0x    | 0.1x  |
| Sleep    | 0.2x | 0.5x    | 1.5x   | 0.3x | 0.6x    | 4.0x  |
| Play     | 2.0x | 1.2x    | 0.3x   | 2.5x | 1.5x    | 0.1x  |
| Hunt     | 2.5x | 1.0x    | 0.2x   | 2.0x | 0.5x    | 0.05x |
| Groom    | 0.5x | 1.0x    | 2.0x   | 0.5x | 1.5x    | 0.5x  |
| Vocalize | 1.2x | 1.0x    | 0.8x   | 1.1x | 1.0x    | 0.3x  |
| Explore  | 1.5x | 1.0x    | 0.5x   | 1.3x | 0.8x    | 0.3x  |

### Implementation in Needs & Transitions

```python
# In needs.py update():
# Replace ad-hoc time-of-day multipliers with circadian.params

phase = self.circadian._phase
params = self.circadian.params

if cur_state in (WALK, WANDER, CHASE, PLAY):
    drain = ENERGY_DRAIN_ACTIVE * dt * params.energy_drain_rate
elif cur_state == SLEEP:
    recharge = ENERGY_RECHARGE_SLEEP * dt * params.energy_regen_rate

# In transitions.py:
# Replace _walk_chance_per_tick, _home_chance_per_tick,
# _wander_chance_per_tick with single method that reads params

def _get_behavior_chance(cat, state, circadian: CircadianClock, 
                         behavior_type: str) -> float:
    """
    Unified behavior chance calculator.
    behavior_type: "wander" | "sleep" | "play" | "groom" | "vocalize"
    """
    chance_mult = {
        "wander": circadian.params.wander_chance,
        "sleep": circadian.params.sleep_chance,
        "play": circadian.params.play_chance,
        "hunt": circadian.params.hunt_chance,
    }.get(behavior_type, 1.0)
    
    # Personality modifier
    p = personality
    if behavior_type == "play":
        chance_mult *= p.playfulness
    elif behavior_type == "sleep":
        chance_mult *= (1.0 - p.playfulness * 0.5)
    elif behavior_type == "wander":
        chance_mult *= (p.confidence * 0.5 + p.curiosity * 0.5)
    
    return base_chance * chance_mult
```

### Effects on Sleep Behavior

Cats are crepuscular — most active at dawn/dusk, sleep through middle of day and night.

```python
# In transitions.py _update_sit():

# Dawn/dusk: hard to fall asleep
sleep_chance = circadian.params.sleep_chance  # 0.1x - 4.0x
if random.random() > sleep_chance:
    return  # skip sleep check

# Night: deep sleep (harder to wake)
if circadian._phase == CircadianPhase.NIGHT:
    cat["deep_sleep"] = True
    cat["wake_difficulty"] = 5.0  # seconds of persistent petting to wake

# Midday: catnap (light sleep, wakes easily)
if circadian._phase == CircadianPhase.MIDDAY:
    cat["deep_sleep"] = False
    cat["max_nap_duration"] = 900.0  # 15 min max nap
```

### Lighting Effects (Visual)

```python
# In window.py paintEvent:

phase = self.engine.circadian._phase

if phase == CircadianPhase.NIGHT:
    # Dim everything slightly (screen-wide overlay)
    painter.fillRect(rect, QColor(0, 0, 0, 40))  # slight darkness
    # Cat's eyes glow slightly
    cat["eye_glow"] = True
elif phase == CircadianPhase.DAWN:
    # Warm orange tint
    painter.fillRect(rect, QColor(255, 200, 150, 15))
elif phase == CircadianPhase.DUSK:
    # Warm red-gold tint
    painter.fillRect(rect, QColor(255, 180, 100, 20))
```

---

## 9. PyQt6 Constraints & Feasibility

### What's Feasible (Within PyQt6 + 33fps Tick)

| Feature | Feasibility | Cost | Notes |
|---------|-------------|------|-------|
| 20+ animation states | ✅ Feasible | Low | Each state is just a different draw function path |
| Multi-stage sequences | ✅ Feasible | Low | Just string of actions; engine already handles action dispatch |
| Spring-physics interpolation | ✅ Feasible | Low | ~200 float ops per cat per tick |
| Expression morphing | ✅ Feasible | Low | Blend between EXPR dicts over time |
| SQLite memory | ✅ Feasible | Medium | WAL mode, async writes, <1ms per query |
| Territory zones | ✅ Feasible | Low | Just coordinate checks (O(n) per tick) |
| Personality vector | ✅ Feasible | Zero | Pure data, no runtime cost |
| Circadian clock | ✅ Feasible | Zero | O(1) per tick |
| Continuous gait (sine-based) | ✅ Feasible | Low | ~50 float ops per tick |
| Lighting overlay (night tint) | ✅ Feasible | Low | Single fillRect → GPU |
| LLM novelty (~30s) | ✅ Feasible | Low | Same architecture as current agent, but 15x less frequent |

### What's NOT Feasible (or Very Expensive)

| Feature | Reason | Alternative |
|---------|--------|-------------|
| Real-time pathfinding (A*) | Too expensive at 33fps with PyQt6 overlay | Use zone-to-zone direct walk with margin checks (current approach) |
| Physics-based fur | CPU-bound, QPainter can't do it | Keep current silhouette + stripe approach |
| 3D rendered cat | Qt3D + OpenGL is heavy for overlay | Stick with 2D QPainter — it's charm |
| Speech-to-text | API latency kills the smooth feel | Keep current speech bubble system |
| Continuous real-time audio analysis | Too heavy for overlay process | Keep event-driven vocalization system |
| Machine learning on-laptop | CPU/GPU contention with games/work | Keep LLM calls external/rare |
| Real-time ragdoll physics | Overkill for a desktop companion | Sequence-based animations are sufficient |

### Performance Budget (33fps → 30ms per frame)

| System | Current Cost | Target Cost | Headroom |
|--------|-------------|-------------|----------|
| Needs update (all cats) | ~0.05ms | ~0.| Needs update (all cats) | ~0.05ms | ~0.1ms | 29.9ms |
| Circadian update | — | ~0.002ms | 29.9ms |
| Sequence manager | — | ~0.05ms | 29.85ms |
| Territory update | — | ~0.1ms | 29.75ms |
| Memory logging | — | ~0.1ms | 29.65ms |
| Animation interpolators | — | ~0.05ms | 29.6ms |
| State transitions | — | ~0.02ms | 29.58ms |
| LLM context build (~30s) | ~5ms | ~5ms | Same |
| Drawing (all cats) | ~2-5ms | ~2-5ms | Same |
| **Total budget** | **~10ms** | **~12ms** | **~18ms headroom** |

**Key insight**: The new architecture adds ~2ms per frame in overhead. At 30ms budget per frame (33fps), we have 18ms headroom. The heavy lifting (memory writes, LLM calls) is done asynchronously or at low frequency.

### Audio Changes (Sound System)

Current: 18 WAV files, event-driven vocalization, `winsound`/`qmediaplayer` backends.

Future: Extend vocalizations to be **personality-aware**:
- Vocalization rate comes from personality (chatty cat meows 10x more)
- Circadian phase suppresses nighttime vocalizations
- Sequence-managed sounds: purr during knead, meow during eat anticipation

No changes needed to the audio backend — just how sounds are triggered.

---

## 10. File Organization & Integration Plan

### New Files

```
behavior/
├── circadian.py      CIRCUMPLEX  ← CircadianClock class
├── personality.py     PERSONALITY ← Personality dataclass + archetypes + effects
├── sequences.py       SEQUENTIAL  ← Sequence, SequenceStep, SequenceManager
├── memory.py          MEMORY      ← CatMemory (SQLite persistence)
├── territory.py       TERRITORY   ← Zone, Territory classes
├── planner.py         PLANNER     ← BehaviorPlanner (unified decision maker)
└── agent.py           MODIFY      ← Strip down to LLM novelty wrapper

animation/
├── interpolate.py     INTERPOLATE ← CatAnimator, AnimatedProp
├── easing.py          EASING      ← Easing functions (ease_in_out, lerp, etc.)
└── breathe.py         NO CHANGE   ← Keep existing

behavior/transitions.py  MODIFY ← Simplify, delegate to planner
behavior/needs.py        MODIFY ← Add circadian multiplier integration
core/engine.py           MODIFY ← Add circadian clock init + update call
core/state.py            MODIFY ← Add new cat dict fields
config.py                MODIFY ← Add new constants
cat/*.py                 NO CHANGE ← Add new pose draw functions as needed
```

### Existing Files to Modify

| File | Change | Effort |
|------|--------|--------|
| `core/engine.py` | Add `CircadianClock.__init__()`, call `circadian.update(dt)` at start of tick | Small |
| `core/state.py` | Add default cat dict keys for short-term memory, transition state, personality ref | Small |
| `behavior/agent.py` | Strip down to LLM novelty wrapper, reduce interval from 2s to 30s | Medium |
| `behavior/transitions.py` | Remove ad-hoc time-of-day checks, delegate to planner, add personality weighting | Medium |
| `behavior/needs.py` | Read circadian params for drain/recharge multipliers | Small |
| `config.py` | Add circadian constants, sequence config, territory defaults | Small |
| `core/window.py` | Add per-cat `CatAnimator` instance, draw from animated values | Medium |

### Integration Steps (Ordered)

**Phase 1: Data Layer** (N+ files, zero behavioral change)
1. Create `behavior/personality.py` — trait vector, load/save, archetypes
2. Create `behavior/circadian.py` — clock, phase enum, params
3. Create `behavior/memory.py` — SQLite CRUD, daily stats
4. Modify `core/state.py` — add short-term memory dict to default cat state
5. Modify `config.py` — add new constants

**Phase 2: Animation Layer** (N files, zero behavioral change — visual only)
6. Create `animation/interpolate.py` — `AnimatedProp`, `CatAnimator`
7. Create `animation/easing.py` — easing functions
8. Add transition state to cat dict + blending in draw pipeline
9. Implement continuous gait (sine-based leg animation)

**Phase 3: Planner Overhaul** (replaces existing transitions + agent)
10. Create `behavior/sequences.py` — `Sequence`, `SequenceStep`, `SequenceManager`
11. Create `behavior/territory.py` — zones, spot discovery
12. Create `behavior/planner.py` — unified `BehaviorPlanner`
13. Modify `behavior/transitions.py` — strip down, delegate to planner
14. Modify `behavior/agent.py` — strip down to novelty-only LLM wrapper

**Phase 4: Integration**
15. Wire `BehaviorPlanner` into `Engine._on_tick()`
16. Wire `CatAnimator` into draw pipeline (`window.py`)
17. Wire `CatMemory` into `agent.py` context builder
18. Wire `Territory` into `BehaviorPlanner._state_machine_step()`
19. Wire lighting effects into `paintEvent()`

**Phase 5: Polish & Tuning**
20. Tune personality archetypes against real cat behavior
21. Tune circadian phase transition timing
22. Tune sequence cooldowns for natural pacing
23. Add new pose draw functions (stretch, lick, knead, stalk, pounce)
24. Test all sequences with each personality archetype

### Rollback Strategy

Each phase is independently testable:
- **Phase 1**: Cat still behaves identically, personality file is created on disk ✓
- **Phase 2**: Animations smooth out, no behavior change ✓
- **Phase 3**: If planner has bugs, revert to old transitions.py + agent.py path via config flag
- **Phase 4**: Integration is just wiring — comment one line to disconnect

```python
# config.py — feature flags for safe rollout
ENABLE_CIRCADIAN = True
ENABLE_PERSONALITY = True
ENABLE_MEMORY = True
ENABLE_SEQUENCES = True
ENABLE_BEHAVIOR_PLANNER = True    # Falls back to transitions.py + agent.py
ENABLE_SMOOTH_TRANSITIONS = True
ENABLE_TERRITORY = True
```

All new features can be toggled off in config.py if anything goes wrong. Each system reads its own flag and gracefully degrades.

---

## Summary: What Each Research Question Answers

| Question | Where Answered |
|----------|---------------|
| Circadian rhythm architecture | Section 1 — hybrid tick/event with CircadianClock |
| Cat memory | Section 2 — short-term (dict) + long-term (SQLite) |
| Behavioral sequences | Section 3 — Sequence + SequenceManager with step advancement |
| Personality data model | Section 4 — 8-trait vector from cat behavior research |
| Behavior planner | Section 5 — unified planner with 5-step priority chain |
| Smoother render pipeline | Section 6 — spring-physics CatAnimator + transition blending |
| Territory and spots | Section 7 — Zone map with automatic spot discovery |
| Circadian effects | Section 8 — multiplied needs/behavior/lighting per phase |
| PyQt6 constraints | Section 9 — all features feasible within 33fps budget |

---

*End of Architecture Document*
