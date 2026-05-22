# Phase 3: Weather Integration & Smart Needs System

## 1. Weather Integration

### API
- **Endpoint:** `https://wttr.in/{city}?format=j1` (free, no API key)
- **Cache:** Store raw JSON in-memory, re-fetch every `WEATHER_CACHE_MINUTES`
- **Rate limiting:** wttr.in allows ~1M requests/day — one call per 30min per instance is negligible

### Config Additions (`config.py`)

```python
# ─── Weather ──────────────────────────────────────────────────────────
WEATHER_CITY = "Mumbai"           # city name for wttr.in
WEATHER_CACHE_MINUTES = 30        # re-fetch interval
WEATHER_ENABLED = True            # toggle weather system on/off
```

### Derived Weather States

Map API `current_condition[0].weatherDesc` → internal state:

| API keyword | Internal state | Notes |
|---|---|---|
| "Sunny", "Clear" | `"sunny"` | |
| "Partly cloudy", "Overcast", "Cloudy" | `"cloudy"` | |
| "Light rain", "Rain", "Patchy rain", "Heavy rain", "Light drizzle", "Moderate rain" | `"rainy"` | |
| "Light snow", "Snow", "Heavy snow", "Blizzard" | `"snowy"` | |
| "Thunderstorm", "Thundery outbreaks" | `"stormy"` | |

Any unrecognised string → `"cloudy"` (safe neutral default).

### State Additions (`CatState`)

```python
# ── Weather ──
weather_condition: str = "cloudy"     # sunny|cloudy|rainy|snowy|stormy
weather_last_fetch: float = 0.0       # monotonic time of last fetch
weather_raw: dict | None = None       # cached raw JSON
```

### Cat Reactions by Weather

| Weather | Behavior modifiers |
|---|---|
| **sunny** | `ENERGY_DRAIN_SIT * 1.15` — more energy, wander chance +30%, playful transitions more likely |
| **cloudy** | Neutral — slight decrease in wander chance (-10%), slightly higher sleep chance |
| **rainy** | `ENERGY_DRAIN_SIT * 0.6` — sleep more, movement less, boredom increases 0.5x, wander nearly disabled |
| **snowy** | Curl up near hut — wander disabled entirely, sleep state preferred, stays near home |
| **stormy** | `ENERGY_DRAIN_ACTIVE * 0.3` — hide near hut, "alert" expression flashed periodically, no wander, no chase |

### Need Decay Modifiers by Weather

| Need | sunny | cloudy | rainy | snowy | stormy |
|---|---|---|---|---|---|
| energy drain | *1.15 | *1.0 | *0.6 | *0.4 | *0.3 |
| hunger drain | *1.1 | *1.0 | *0.8 | *0.7 | *0.6 |
| boredom increase | *1.0 | *0.9 | *0.5 | *0.3 | *0.2 |

Formula: `base_rate * weather_modifier * time_of_day_modifier`

### Implementation: `core/weather.py` (new file)

```python
"""
core/weather.py — Weather fetcher and state integrator.
Pulled by engine tick every WEATHER_CACHE_MINUTES.
"""
import json
import logging
import time
import urllib.request
import urllib.error
from datetime import datetime

import config

_WEATHER_CACHE = None
_WEATHER_CACHE_TIME = 0.0

def fetch_weather():
    """Fetch weather from wttr.in, return condition string."""
    global _WEATHER_CACHE, _WEATHER_CACHE_TIME
    
    now = time.monotonic()
    if now - _WEATHER_CACHE_TIME < config.WEATHER_CACHE_MINUTES * 60:
        return  # cache still fresh
    
    try:
        url = f"https://wttr.in/{config.WEATHER_CITY}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "desktop-cat/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError, ValueError) as e:
        logging.warning("weather fetch failed: %s", e)
        return
    
    _WEATHER_CACHE = data
    _WEATHER_CACHE_TIME = now

def get_weather_condition() -> str:
    """Return current derived weather condition string."""
    global _WEATHER_CACHE
    if not _WEATHER_CACHE:
        return "cloudy"
    
    try:
        desc = _WEATHER_CACHE["current_condition"][0]["weatherDesc"][0]["value"].lower()
    except (KeyError, IndexError):
        return "cloudy"
    
    # Map description to internal state
    clouds = {"partly cloudy", "overcast", "cloudy", "mist", "fog", "haze", "smoke"}
    rainy = {"light rain", "rain", "patchy rain", "heavy rain", "light drizzle",
             "moderate rain", "heavy rain", "light rain shower", "moderate or heavy rain shower",
             "torrential rain shower", "drizzle", "patchy light drizzle", "freezing drizzle"}
    snowy = {"light snow", "snow", "heavy snow", "blizzard", "patchy snow",
             "patchy light snow", "light snow showers", "moderate or heavy snow showers"}
    stormy = {"thunderstorm", "thundery outbreaks", "patchy light rain with thunder",
              "moderate or heavy rain with thunder", "patchy light snow with thunder"}
    sunny = {"sunny", "clear"}
    
    if desc in sunny:
        return "sunny"
    if desc in rainy:
        return "rainy"
    if desc in snowy:
        return "snowy"
    if desc in stormy:
        return "stormy"
    if desc in clouds:
        return "cloudy"
    
    return "cloudy"  # safe default

def get_weather_modifier(weather: str) -> dict:
    """Return dict of multipliers for this weather."""
    return {
        "sunny":  {"energy": 1.15, "hunger": 1.1, "boredom": 1.0, "wander": 1.3, "sleep": 0.8,  "chase": 1.2},
        "cloudy": {"energy": 1.0,  "hunger": 1.0, "boredom": 0.9, "wander": 0.9, "sleep": 1.1,  "chase": 0.9},
        "rainy":  {"energy": 0.6,  "hunger": 0.8, "boredom": 0.5, "wander": 0.1, "sleep": 1.4,  "chase": 0.2},
        "snowy":  {"energy": 0.4,  "hunger": 0.7, "boredom": 0.3, "wander": 0.0, "sleep": 1.6,  "chase": 0.0},
        "stormy": {"energy": 0.3,  "hunger": 0.6, "boredom": 0.2, "wander": 0.0, "sleep": 1.8,  "chase": 0.0},
    }.get(weather, {"energy": 1.0, "hunger": 1.0, "boredom": 1.0, "wander": 1.0, "sleep": 1.0, "chase": 1.0})

def update(state, dt: float) -> None:
    """Weather system tick. Call from engine systems loop."""
    fetch_weather()
    new_cond = get_weather_condition()
    if new_cond != state.weather_condition:
        state.weather_condition = new_cond
    state.weather_last_fetch = time.monotonic()

def get_weather_for_display(state) -> str:
    """Human-readable weather string for UI."""
    emoji_map = {
        "sunny": "☀️", "cloudy": "☁️", "rainy": "🌧️",
        "snowy": "❄️", "stormy": "⛈️"
    }
    e = emoji_map.get(state.weather_condition, "☁️")
    city = config.WEATHER_CITY
    cond = state.weather_condition.upper()
    return f"{e} {city}: {cond}"
```

### Integration Points

1. **`engine.py`** — Register `weather` system in `__init__`: `self.register("weather", weather)`
2. **`behavior/needs.py`** — Modify need decay rates using `weather.get_weather_modifier(state.weather_condition)`
3. **`behavior/transitions.py`** — Use weather modifiers: stormy/snowy → never wander, never chase; rainy → reduced wander
4. **`ui/settings.py`** — Add weather display row with city name and current condition

---

## 2. Smart Needs System

### Time-of-Day Multipliers (`config.py`)

```python
# ─── Smart Needs: Time-of-Day Multipliers ────────────────────────────
# Each entry: (start_hour, end_hour) -> {need: multiplier}
# Multipliers stack with weather modifiers via: base_rate * tod_mul * weather_mul
TIME_OF_DAY_MULTIPLIERS = {
    # Active hours — energy drains faster
    (6, 12):   {"energy": 2.0, "hunger": 1.0, "boredom": 1.2},
    # Meal times — hunger builds faster
    (7, 9):    {"energy": 1.5, "hunger": 1.5, "boredom": 1.0},
    (19, 21):  {"energy": 1.5, "hunger": 1.5, "boredom": 1.0},
    # Afternoon lull — cat naps
    (13, 16):  {"energy": 0.7, "hunger": 0.8, "boredom": 0.9},
    # Sleep hours — greatly reduced activity
    (22, 6):   {"energy": 0.3, "hunger": 0.4, "boredom": 0.5},
}

# ─── Keyboard Feed ─────────────────────────────────────────────────────
# Ctrl+F cycles through food options
FOOD_OPTIONS = ["fish", "treat", "milk"]
FOOD_HUNGER_REDUCTION = {"fish": 40.0, "treat": 20.0, "milk": 25.0}
```

### Priority Behavior Triggers

| Condition | Action | Priority |
|---|---|---|
| `hunger > 80` | Special "hungry" speech bubble (priority 5), meow sound, walks toward cat's bowl area | Critical |
| `energy < 20` | Auto-sleep anywhere (field sleep), override all other states | High |
| `boredom > 80` | Erratic walking pattern, sprite shakes/stutters, special "crazy" speech | Medium |
| `owner AFK > 5min` AND `state == SIT` | Boredom increases 2x faster | Medium |

### Implementation: Modified Need Decay in `behavior/needs.py`

```python
"""
behavior/needs.py — Need decay/recharge integrated with weather + time-of-day.
"""

import config
from datetime import datetime

def _get_tod_multipliers() -> dict:
    """Return combined time-of-day multipliers for current hour."""
    hour = datetime.now().hour
    result = {"energy": 1.0, "hunger": 1.0, "boredom": 1.0}
    
    for (start, end), mults in config.TIME_OF_DAY_MULTIPLIERS.items():
        # Handle overnight ranges (start > end, e.g. 22-6)
        if start <= end:
            if start <= hour < end:
                for k, v in mults.items():
                    result[k] *= v
        else:  # overnight
            if hour >= start or hour < end:
                for k, v in mults.items():
                    result[k] *= v
    
    return result

def _get_weather_multipliers(state) -> dict:
    """Delegate to weather module."""
    try:
        from core.weather import get_weather_modifier
        return get_weather_modifier(state.weather_condition)
    except (ImportError, AttributeError):
        return {"energy": 1.0, "hunger": 1.0, "boredom": 1.0}

def _needs_update(dt: float, state) -> None:
    """Full needs update with weather + time-of-day modifiers."""
    tod = _get_tod_multipliers()
    wea = _get_weather_multipliers(state)
    
    energy_mul = tod.get("energy", 1.0) * wea.get("energy", 1.0)
    hunger_mul = tod.get("hunger", 1.0) * wea.get("hunger", 1.0)
    boredom_mul = tod.get("boredom", 1.0) * wea.get("boredom", 1.0)
    
    # --- Energy ---
    if state.state == config.STATE_SLEEP:
        state.energy += config.ENERGY_RECHARGE_SLEEP * dt
        if state.deep_sleep:
            state.energy += config.ENERGY_RECHARGE_SLEEP * 0.5 * dt  # slower deep sleep recharge? Actually: keep same
    elif state.state in (config.STATE_WALK, config.STATE_WANDER, config.STATE_CHASE, config.STATE_PLAY):
        state.energy -= config.ENERGY_DRAIN_ACTIVE * dt * energy_mul
    else:
        state.energy -= config.ENERGY_DRAIN_SIT * dt * energy_mul
    
    # --- Hunger ---
    state.hunger += config.HUNGER_DRAIN * dt * hunger_mul
    
    # --- Boredom ---
    if state.state == config.STATE_SLEEP:
        state.boredom = max(0.0, state.boredom - 0.01 * dt)
    elif state.state in (config.STATE_WALK, config.STATE_WANDER, config.STATE_CHASE, config.STATE_PLAY):
        state.boredom = max(0.0, state.boredom - 0.005 * dt)
    else:  # SIT or idle
        state.boredom += config.BOREDOM_INCREASE_SIT * dt * boredom_mul
    
    # --- AFK boredom acceleration ---
    if state.state == config.STATE_SIT and _is_owner_afk(state):
        state.boredom += config.BOREDOM_INCREASE_SIT * dt * boredom_mul  # effectively 2x on SIT

def _is_owner_afk(state) -> bool:
    """Check if owner hasn't interacted in 5+ minutes."""
    import time
    return (time.monotonic() - state.last_interaction) > 300  # 5 min

def _check_critical_triggers(state) -> None:
    """Check hunger > 80, energy < 20, boredom > 80."""
    # Priority 5: hunger > 80 — urgent meow
    if state.hunger > 80 and state.speech_cooldown <= 0:
        if state.speech.get("text") is None:
            from core.state import SPEECH_MOODS
            import random as _r
            mood = SPEECH_MOODS.get("hungry")
            if mood:
                text = _r.choice(mood["texts"])
                # Force display regardless of priority
                state.speech["text"] = text
                state.speech["emoji"] = mood["emoji"]
                state.speech["timer"] = config.SPEECH_DISPLAY + 1.0
                state.speech["fading"] = False
                state.speech["opacity"] = 0.0
                state.speech_cooldown = 10.0
        # Also play meow sound
        try:
            from core.sound import SoundManager
            SoundManager().play("meow_long")
        except Exception:
            pass
        state.hunger_urgent = True
    else:
        state.hunger_urgent = False
    
    # Priority High: energy < 20 — auto-sleep anywhere
    if state.energy < 20 and state.state != config.STATE_SLEEP:
        state.state = config.STATE_SLEEP
        state.sleep_breath = 0.0
        state.zzz_particles = []
        # If at_home is True, keep it; otherwise set to False (field sleep)
        state.at_home = False
    
    # Medium: boredom > 80 — erratic behavior
    if state.boredom > 80 and state.state == config.STATE_SIT:
        # Erratic walk trigger
        import random as _r
        if _r.random() < 0.1:  # 10% chance per tick to go erratic
            _trigger_erratic(state)
    
    # Medium: energy < 30 — sleepy expression
    if state.energy < 30:
        state.expr_target = config.EXPR_SLEEPY

def _trigger_erratic(state) -> None:
    """Trigger erratic walking pattern when bored."""
    import random as _r
    state.state = config.STATE_WALK
    state.walk_duration = _r.uniform(0.3, 1.0)  # short, jerky walks
    state.walk_elapsed = 0.0
    state.walk_accel = 2.0  # fast accel for jerky movement
    state.facing = _r.choice([True, False])
    state.expression = "crazy"
    
    if state.speech_cooldown <= 0:
        texts = ["!!", "argh", "bored!", "ughh"]
        state.speech["text"] = _r.choice(texts)
        state.speech["emoji"] = "😵"
        state.speech["timer"] = config.SPEECH_DISPLAY
        state.speech["fading"] = False
        state.speech["opacity"] = 0.0
        state.speech_cooldown = 15.0

def update(dt: float, state) -> None:
    """Main needs update — call from engine tick."""
    _needs_update(dt, state)
    _check_critical_triggers(state)
    
    # Add hunger_urgent flag to state if not present
    if not hasattr(state, 'hunger_urgent'):
        state.hunger_urgent = False
```

### Keyboard Feed: Ctrl+F Handler

Add in `ui/controls.py`:

```python
def _on_ctrl_f(self):
    """Cycle through food options and feed the cat."""
    s = self.state
    if not hasattr(self, '_food_index'):
        self._food_index = 0
    
    food = config.FOOD_OPTIONS[self._food_index]
    self._food_index = (self._food_index + 1) % len(config.FOOD_OPTIONS)
    
    reduction = config.FOOD_HUNGER_REDUCTION.get(food, 20.0)
    s.hunger = max(0.0, s.hunger - reduction)
    
    # Trigger happy speech
    if s.speech_cooldown <= 0:
        from core.state import SPEECH_MOODS
        import random as _r
        mood = SPEECH_MOODS.get("happy")
        if mood:
            s.speech["text"] = _r.choice(mood["texts"])
            s.speech["emoji"] = mood["emoji"]
            s.speech["timer"] = config.SPEECH_DISPLAY
            s.speech["fading"] = False
            s.speech["opacity"] = 0.0
            s.speech_cooldown = 3.0
    
    # Show food type in tray notification
    print(f"🐱 Fed {food} (-{reduction:.0f} hunger)")
    
    # Spawn hearts
    from core.navigation import _spawn_hearts
    _spawn_hearts(s, count=3)
```

### State Additions

```python
# ── Smart Needs ──
hunger_urgent: bool = False  # True when hunger > 80
```

### Files Changed Summary

| File | Change |
|---|---|
| `config.py` | Add `WEATHER_*`, `TIME_OF_DAY_MULTIPLIERS`, `FOOD_*` constants |
| `core/weather.py` | **NEW** — fetch, cache, derive condition, modifiers |
| `core/state.py` | Add `weather_condition`, `weather_last_fetch`, `weather_raw`, `hunger_urgent` |
| `behavior/needs.py` | Rewrite `update()` to apply weather + time-of-day modifiers, add critical triggers, AFK detection |
| `behavior/transitions.py` | Apply weather modifiers to wander/sleep/chase chances |
| `ui/controls.py` | Add Ctrl+F keyboard feed handler |
| `engine.py` | Register `weather` system in systems OrderedDict |

### Test Plan (213 baseline → ~240)

- `test_weather_condition_parsing` — 7 weather keywords map correctly
- `test_weather_modifier_values` — Each weather returns correct modifier dict
- `test_tod_multiplier_active_hours` — Energy 2x at 8am
- `test_tod_multiplier_sleep_hours` — Energy 0.3x at 2am
- `test_tod_overnight_range` — 22-6 range wraps correctly
- `test_tod_stacked_mults` — (7,9) overlaps (6,12): energy *= 2.0 * 1.5
- `test_critical_hunger_triggers_speech` — hunger > 80 forces speech
- `test_critical_energy_triggers_sleep` — energy < 20 forces sleep
- `test_critical_boredom_triggers_erratic` — boredom > 80 can trigger erratic walk
- `test_afk_boredom_acceleration` — 5min+ no interaction doubles boredom
- `test_keyboard_feed_reduces_hunger` — Ctrl+F applies correct reduction
- `test_cyle_food_options` — Ctrl+F cycles fish→treat→milk→fish
- `test_needs_stay_clamped_after_multipliers` — 0-100 range maintained
- `test_weather_integration_pipeline` — fetch → cache → condition → modifiers flows end-to-end
- `test_weather_no_internet_fallback` — fetch failure falls back to cloudy
- `test_weather_need_compound_modifiers` — Rainy + night = energy 0.6*0.3 = 0.18x
