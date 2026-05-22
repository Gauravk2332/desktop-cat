"""
core/weather.py — Weather fetcher and state integrator.

Pulled from engine tick. No external dependencies beyond stdlib.
Fetches from wttr.in (free, no API key).
"""

import json
import logging
import time
import urllib.request
import urllib.error


# ── Internal cache ───────────────────────────────────────────────────

_WEATHER_CACHE = None       # dict | None  — raw JSON from wttr.in
_WEATHER_CACHE_TIME = 0.0   # monotonic time of last successful fetch

logger = logging.getLogger(__name__)


def fetch_weather(city: str = "Mumbai") -> dict | None:
    """Fetch weather JSON from wttr.in and return parsed dict.

    Uses module-level cache; returns None if fetch fails on all retries.
    The caller is responsible for checking WEATHER_CACHE_INTERVAL.
    """
    global _WEATHER_CACHE, _WEATHER_CACHE_TIME

    import config

    url = f"https://wttr.in/{city}?format=j1"
    last_error = None

    for attempt in range(config.WEATHER_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "desktop-cat/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.JSONDecodeError, OSError, ValueError) as e:
            last_error = e
            if attempt < config.WEATHER_RETRIES - 1:
                time.sleep(config.WEATHER_RETRY_DELAY)
            continue

        _WEATHER_CACHE = data
        _WEATHER_CACHE_TIME = time.monotonic()
        return data

    logger.warning("Weather fetch failed after %d retries: %s",
                   config.WEATHER_RETRIES, last_error)
    return None


def get_weather_condition() -> str:
    """Return current derived weather condition string.

    Reads from internal cache. Returns 'unknown' on no data or parse error.
    """
    global _WEATHER_CACHE
    if not _WEATHER_CACHE:
        return "unknown"

    try:
        desc = _WEATHER_CACHE["current_condition"][0]["weatherDesc"][0]["value"].lower()
    except (KeyError, IndexError, TypeError):
        return "unknown"

    # Keyword sets — order matters: check specific before generic
    sunny    = {"sunny", "clear"}
    cloudy   = {"partly cloudy", "overcast", "cloudy", "mist", "fog", "haze",
                "smoke", "fair", "mostly cloudy", "partly sunny"}
    rainy    = {"light rain", "rain", "patchy rain", "heavy rain", "light drizzle",
                "moderate rain", "torrential rain", "drizzle",
                "patchy light drizzle", "freezing drizzle",
                "light rain shower", "moderate or heavy rain shower",
                "torrential rain shower", "light freezing rain",
                "moderate or heavy freezing rain", "patchy light rain"}
    snowy    = {"light snow", "snow", "heavy snow", "blizzard", "patchy snow",
                "patchy light snow", "light snow showers",
                "moderate or heavy snow showers", "patchy moderate snow",
                "ice pellets", "light ice pellets", "moderate or heavy ice pellets"}
    stormy   = {"thunderstorm", "thundery outbreaks",
                "patchy light rain with thunder",
                "moderate or heavy rain with thunder",
                "patchy light snow with thunder",
                "moderate or heavy snow with thunder"}

    if desc in sunny:
        return "sunny"
    if desc in rainy:
        return "rainy"
    if desc in snowy:
        return "snowy"
    if desc in stormy:
        return "stormy"
    if desc in cloudy:
        return "cloudy"

    return "cloudy"  # safe neutral default for unrecognised strings


def get_weather_modifier(state) -> dict:
    """Return weather modifier dict for the given cat state.

    Returns dict with keys: energy, hunger, boredom, wander, sleep, chase.
    Values are multipliers applied to base rates.
    """
    weather = getattr(state, "weather_condition", "cloudy")
    modifiers = {
        "sunny":  {"energy": 1.15, "hunger": 1.1,  "boredom": 1.0,
                   "wander": 1.3,  "sleep": 0.8,   "chase": 1.2},
        "cloudy": {"energy": 1.0,  "hunger": 1.0,  "boredom": 0.9,
                   "wander": 0.9,  "sleep": 1.1,   "chase": 0.9},
        "rainy":  {"energy": 0.6,  "hunger": 0.8,  "boredom": 0.5,
                   "wander": 0.1,  "sleep": 1.4,   "chase": 0.2},
        "snowy":  {"energy": 0.4,  "hunger": 0.7,  "boredom": 0.3,
                   "wander": 0.0,  "sleep": 1.6,   "chase": 0.0},
        "stormy": {"energy": 0.3,  "hunger": 0.6,  "boredom": 0.2,
                   "wander": 0.0,  "sleep": 1.8,   "chase": 0.0},
    }
    return modifiers.get(weather, modifiers["cloudy"])


def update(dt: float, state) -> None:
    """Weather system tick. Call from engine systems loop (dt, state).

    Fetches weather if cache is stale, updates state.weather_condition.
    """
    import config

    now = time.monotonic()
    interval = config.WEATHER_CACHE_INTERVAL

    if now - state.weather_last_fetch >= interval:
        fetch_weather(config.WEATHER_CITY)
        new_cond = get_weather_condition()
        state.weather_condition = new_cond
        state.weather_last_fetch = now

        # Also store temp if available
        try:
            if _WEATHER_CACHE:
                state.weather_temp = int(_WEATHER_CACHE["current_condition"][0]["temp_C"])
        except (KeyError, IndexError, TypeError, ValueError):
            pass


def get_weather_for_display(state) -> str:
    """Human-readable weather string for UI."""
    import config
    emoji_map = {
        "sunny": "☀️", "cloudy": "☁️", "rainy": "🌧️",
        "snowy": "❄️", "stormy": "⛈️", "unknown": "❓",
    }
    e = emoji_map.get(state.weather_condition, "☁️")
    city = config.WEATHER_CITY
    cond = state.weather_condition.upper()
    temp = getattr(state, "weather_temp", None)
    if temp is not None:
        return f"{e} {city}: {cond} {temp}°C"
    return f"{e} {city}: {cond}"
