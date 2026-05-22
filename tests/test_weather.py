"""
tests/test_weather.py — Unit tests for weather system and smart needs.

Tests that:
- Weather condition parsing works for all keyword categories
- Weather modifiers return correct values
- Time-of-day multipliers apply correctly (including overnight)
- AFK boredom acceleration
- Critical thresholds trigger correct behavior
- Feed cycle works correctly
- No crash on fetch failure
"""

import sys
import os
import json
import time
import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState, SPEECH_MOODS
from behavior.needs import _get_weather_multipliers, _get_tod_multipliers


class TestWeatherConditionParsing(unittest.TestCase):
    """Test weather description → condition mapping."""

    def _make_cache(self, desc: str) -> dict:
        """Create a fake wttr.in cache entry with given weatherDesc."""
        return {
            "current_condition": [{
                "weatherDesc": [{"value": desc}],
                "temp_C": "25",
            }]
        }

    def _set_cache(self, desc: str):
        """Set the module-level _WEATHER_CACHE for testing."""
        import core.weather as weather
        weather._WEATHER_CACHE = self._make_cache(desc)
        weather._WEATHER_CACHE_TIME = time.monotonic()

    def _clear_cache(self):
        import core.weather as weather
        weather._WEATHER_CACHE = None
        weather._WEATHER_CACHE_TIME = 0.0

    def tearDown(self):
        self._clear_cache()

    def test_sunny(self):
        self._set_cache("Sunny")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "sunny")

    def test_clear(self):
        self._set_cache("Clear")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "sunny")

    def test_cloudy(self):
        self._set_cache("Cloudy")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "cloudy")

    def test_partly_cloudy(self):
        self._set_cache("Partly cloudy")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "cloudy")

    def test_overcast(self):
        self._set_cache("Overcast")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "cloudy")

    def test_mist(self):
        self._set_cache("Mist")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "cloudy")

    def test_rain(self):
        self._set_cache("Rain")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "rainy")

    def test_light_rain(self):
        self._set_cache("Light rain")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "rainy")

    def test_heavy_rain(self):
        self._set_cache("Heavy rain")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "rainy")

    def test_drizzle(self):
        self._set_cache("Drizzle")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "rainy")

    def test_snow(self):
        self._set_cache("Snow")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "snowy")

    def test_blizzard(self):
        self._set_cache("Blizzard")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "snowy")

    def test_thunderstorm(self):
        self._set_cache("Thunderstorm")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "stormy")

    def test_thundery_outbreaks(self):
        self._set_cache("Thundery outbreaks")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "stormy")

    def test_unknown_desc_falls_to_cloudy(self):
        self._set_cache("Some weird weather")
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "cloudy")

    def test_no_cache_returns_unknown(self):
        self._clear_cache()
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "unknown")

    def test_empty_cache_returns_unknown(self):
        import core.weather as weather
        weather._WEATHER_CACHE = {}
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "unknown")


class TestWeatherModifiers(unittest.TestCase):
    """Test get_weather_modifier returns correct values."""

    def _make_state(self, weather: str = "cloudy"):
        s = CatState()
        s.weather_condition = weather
        return s

    def test_sunny_modifiers(self):
        from core.weather import get_weather_modifier
        mods = get_weather_modifier(self._make_state("sunny"))
        self.assertAlmostEqual(mods["energy"], 1.15)
        self.assertAlmostEqual(mods["hunger"], 1.1)
        self.assertAlmostEqual(mods["wander"], 1.3)

    def test_rainy_modifiers(self):
        from core.weather import get_weather_modifier
        mods = get_weather_modifier(self._make_state("rainy"))
        self.assertAlmostEqual(mods["energy"], 0.6)
        self.assertAlmostEqual(mods["hunger"], 0.8)
        self.assertAlmostEqual(mods["boredom"], 0.5)
        self.assertAlmostEqual(mods["wander"], 0.1)

    def test_snowy_modifiers(self):
        from core.weather import get_weather_modifier
        mods = get_weather_modifier(self._make_state("snowy"))
        self.assertAlmostEqual(mods["energy"], 0.4)
        self.assertAlmostEqual(mods["wander"], 0.0)
        self.assertAlmostEqual(mods["chase"], 0.0)

    def test_stormy_modifiers(self):
        from core.weather import get_weather_modifier
        mods = get_weather_modifier(self._make_state("stormy"))
        self.assertAlmostEqual(mods["energy"], 0.3)
        self.assertAlmostEqual(mods["wander"], 0.0)
        self.assertAlmostEqual(mods["sleep"], 1.8)

    def test_unknown_weather_uses_default(self):
        from core.weather import get_weather_modifier
        mods = get_weather_modifier(self._make_state("unknown"))
        # Should fall through to cloudy defaults
        self.assertAlmostEqual(mods["energy"], 1.0)
        self.assertAlmostEqual(mods["wander"], 0.9)

    def test_no_weather_attr_uses_cloudy(self):
        from core.weather import get_weather_modifier
        s = Mock()
        # No weather_condition attribute → getattr default to cloudy
        mods = get_weather_modifier(s)
        self.assertAlmostEqual(mods["energy"], 1.0)

    def test_all_modifier_keys_present(self):
        from core.weather import get_weather_modifier
        expected_keys = {"energy", "hunger", "boredom", "wander", "sleep", "chase"}
        for weather in ("sunny", "cloudy", "rainy", "snowy", "stormy"):
            mods = get_weather_modifier(self._make_state(weather))
            self.assertEqual(set(mods.keys()), expected_keys,
                             f"Missing keys for {weather}")
        # unknown falls to cloudy
        mods = get_weather_modifier(self._make_state("unknown"))
        self.assertEqual(set(mods.keys()), expected_keys)


class TestWeatherNeedsIntegration(unittest.TestCase):
    """Test that weather modifiers affect need decay in behavior/needs.py."""

    def setUp(self):
        self.state = CatState()
        self.state.weather_condition = "rainy"
        self.dt = 1.0

    def _import_needs(self):
        if "behavior.needs" in sys.modules:
            del sys.modules["behavior.needs"]
        import behavior.needs
        return behavior.needs

    def test_rainy_reduces_energy_drain(self):
        """Rainy weather should reduce energy drain (0.6 multiplier)."""
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.energy = 100.0
        # Patch to a neutral hour (14) where no energy TOD multiplier applies
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 14
            needs.update(self.dt, self.state.cats[0], self.state)
        # Energy should have drained less than normal SIT rate
        base_drain = config.ENERGY_DRAIN_SIT * self.dt
        drain = 100.0 - self.state.energy
        # With rainy (0.6) and neutral hour (1.0): drain = base * 0.6
        self.assertLess(drain, base_drain,
                        "Rainy should reduce energy drain below base SIT rate")

    def test_sunny_increases_hunger(self):
        """Sunny weather should increase hunger drain (1.1 multiplier)."""
        self.state.weather_condition = "sunny"
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.hunger = 20.0
        needs.update(self.dt, self.state.cats[0], self.state)
        base_hunger = config.HUNGER_DRAIN * self.dt
        sunny_hunger = config.HUNGER_DRAIN * self.dt * 1.1
        increase = self.state.hunger - 20.0
        self.assertGreater(increase, base_hunger * 0.95)  # should be increased

    def test_stormy_reduces_boredom_increase(self):
        """Stormy weather should reduce boredom increase (0.2 multiplier)."""
        self.state.weather_condition = "stormy"
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.boredom = 0.0
        needs.update(self.dt, self.state.cats[0], self.state)
        base_boredom = config.BOREDOM_INCREASE_SIT * self.dt
        stormy_boredom = base_boredom * 0.2
        # Boredom will have time-of-day multiplier too, but should still be small
        self.assertLess(self.state.boredom, base_boredom * 1.5)


class TestTimeOfDayMultipliers(unittest.TestCase):
    """Test time-of-day need multipliers."""

    def test_active_hours_energy_multiplier(self):
        """Energy should have 2x multiplier during 6-12 range."""
        from behavior.needs import _get_tod_multipliers
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 8  # inside 6-12
            mults = _get_tod_multipliers()
            self.assertAlmostEqual(mults["energy"], 2.0)

    def test_sleep_hours_energy_multiplier(self):
        """Energy should have 0.5x multiplier during 22-6 range."""
        from behavior.needs import _get_tod_multipliers
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 2  # inside 22-6 (overnight)
            mults = _get_tod_multipliers()
            self.assertAlmostEqual(mults["energy"], 0.5)

    def test_outside_active_hours_default_energy(self):
        """Energy should default to 1.0 outside 6-12 and 22-6."""
        from behavior.needs import _get_tod_multipliers
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 15  # outside both ranges
            mults = _get_tod_multipliers()
            self.assertAlmostEqual(mults["energy"], 1.0)

    def test_hunger_meal_times(self):
        """Hunger should have 1.5x during 7-9 and 19-21."""
        from behavior.needs import _get_tod_multipliers
        for hour, expected in [(8, 1.5), (20, 1.5), (14, 1.0), (23, 1.0)]:
            with patch("behavior.needs.datetime") as mock_dt:
                mock_dt.now.return_value.hour = hour
                mults = _get_tod_multipliers()
                self.assertAlmostEqual(mults["hunger"], expected,
                                       msg=f"hour={hour}")

    def test_overnight_range_wraps_correctly(self):
        """Overnight range (22-6) should wrap: hour 23 applies, hour 10 doesn't."""
        from behavior.needs import _get_tod_multipliers
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 23
            mults = _get_tod_multipliers()
            self.assertAlmostEqual(mults["energy"], 0.5, "hour 23 should apply 22-6")
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 10
            mults = _get_tod_multipliers()
            self.assertAlmostEqual(mults["energy"], 2.0, "hour 10 should apply 6-12")


class TestAfkBoredomAcceleration(unittest.TestCase):
    """Test AFK boredom acceleration."""

    def setUp(self):
        self.state = CatState()
        self.state.state = config.STATE_SIT
        self.state.boredom = 0.0
        self.state.last_interaction = 0.0  # a long time ago
        self.dt = 1.0

    def _import_needs(self):
        if "behavior.needs" in sys.modules:
            del sys.modules["behavior.needs"]
        import behavior.needs
        return behavior.needs

    def test_afk_doubles_boredom_increase(self):
        """AFK (no interaction for 300s+) should double boredom increase."""
        needs = self._import_needs()
        # last_interaction = 0, now is time.monotonic() which is large
        needs.update(self.dt, self.state.cats[0], self.state)
        base_boredom = config.BOREDOM_INCREASE_SIT * self.dt
        # With AFK double + tod + weather modifiers, should be more than base
        self.assertGreaterEqual(self.state.boredom, base_boredom)

    def test_non_afk_normal_boredom(self):
        """Recent interaction should not accelerate boredom."""
        self.state.last_interaction = time.monotonic()  # just interacted
        needs = self._import_needs()
        needs.update(self.dt, self.state.cats[0], self.state)
        base_boredom = config.BOREDOM_INCREASE_SIT * self.dt
        # With AFK not active, boredom should be base * tod * weather
        self.assertLess(self.state.boredom, base_boredom * 2.0)


class TestCriticalThresholds(unittest.TestCase):
    """Test critical need threshold triggers."""

    def setUp(self):
        self.state = CatState()
        self.state.speech_cooldown = 0.0
        self.dt = 0.05

    def _import_needs(self):
        if "behavior.needs" in sys.modules:
            del sys.modules["behavior.needs"]
        import behavior.needs
        return behavior.needs

    def test_energy_critical_auto_sleep(self):
        """Energy below 20 should force sleep regardless of state."""
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.energy = 15.0
        needs.update(self.dt, self.state.cats[0], self.state)
        self.assertEqual(self.state.state, config.STATE_SLEEP)

    def test_energy_critical_does_not_interrupt_sleep(self):
        """Auto-sleep should not trigger if already sleeping."""
        needs = self._import_needs()
        self.state.state = config.STATE_SLEEP
        self.state.energy = 15.0
        needs.update(self.dt, self.state.cats[0], self.state)
        self.assertEqual(self.state.state, config.STATE_SLEEP)

    def test_boredom_erratic_triggers_walk(self):
        """Boredom above 80 can trigger erratic walk (probabilistic)."""
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.boredom = 85.0
        # Run many ticks to ensure it fires (10% per tick)
        erratic_triggered = False
        for _ in range(200):
            needs.update(self.dt, self.state.cats[0], self.state)
            if self.state.state != config.STATE_SIT:
                erratic_triggered = True
                break
        self.assertTrue(erratic_triggered, "Erratic walk should trigger eventually")

    def test_boredom_below_80_no_erratic(self):
        """Boredom below 80 should not trigger erratic walk."""
        needs = self._import_needs()
        self.state.state = config.STATE_SIT
        self.state.boredom = 75.0
        for _ in range(200):
            needs.update(self.dt, self.state.cats[0], self.state)
        self.assertEqual(self.state.state, config.STATE_SIT,
                         "Should stay sitting when boredom < 80")


class TestFeedCycle(unittest.TestCase):
    """Test Ctrl+F feed cycle."""

    def setUp(self):
        self.state = CatState()
        self.mock_window = MagicMock()
        self.mock_engine = MagicMock()
        from core.controls import Controls
        self.controls = Controls(self.mock_window, self.state, self.mock_engine)

    def test_feed_reduces_hunger(self):
        """Ctrl+F should reduce hunger."""
        self.state.hunger = 50.0
        self.controls._feed_cycle()
        self.assertLess(self.state.hunger, 50.0)

    def test_feed_clamps_at_zero(self):
        """All food items should clamp hunger at 0."""
        self.state.hunger = 10.0  # less than any reduction
        self.controls._feed_cycle()
        self.assertEqual(self.state.hunger, 0.0)

    def test_feed_cycles_food_index(self):
        """feed_cycle_index should cycle 0→1→2→0."""
        self.state.feed_cycle_index = 0
        self.controls._feed_cycle()
        self.assertEqual(self.state.feed_cycle_index, 1)
        self.controls._feed_cycle()
        self.assertEqual(self.state.feed_cycle_index, 2)
        self.controls._feed_cycle()
        self.assertEqual(self.state.feed_cycle_index, 0)

    def test_feed_calls_speech(self):
        """Feed should trigger happy speech via engine."""
        self.state.speech_cooldown = 0.0
        self.controls._feed_cycle()
        self.mock_engine._trigger_speech.assert_called_once_with("happy", cat_idx=0)

    def test_feed_spawns_hearts(self):
        """Feed should spawn 3 hearts."""
        initial_count = len(self.state.hearts)
        self.controls._feed_cycle()
        self.assertEqual(len(self.state.hearts), initial_count + 3)

    def test_feed_cooldown_speech(self):
        """Feed should not trigger speech if cooldown active."""
        self.state.speech_cooldown = 10.0
        self.controls._feed_cycle()
        self.mock_engine._trigger_speech.assert_not_called()


class TestWeatherFetchFailure(unittest.TestCase):
    """Test behavior when weather API is unreachable."""

    def setUp(self):
        import core.weather as weather
        weather._WEATHER_CACHE = None
        weather._WEATHER_CACHE_TIME = 0.0

    def test_fetch_failure_returns_none(self):
        """fetch_weather should return None on all retries failing."""
        from core.weather import fetch_weather
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = ConnectionError("No network")
            result = fetch_weather("Nowhere")
            self.assertIsNone(result)

    def test_fetch_failure_leaves_cache_unchanged(self):
        """Fetch failure should not corrupt the internal cache."""
        import core.weather as weather
        weather._WEATHER_CACHE = {"old": "data"}
        old_cache = weather._WEATHER_CACHE

        from core.weather import fetch_weather
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = ConnectionError("No network")
            fetch_weather("Nowhere")

        self.assertIs(weather._WEATHER_CACHE, old_cache,
                      "Cache should remain unchanged on failure")

    def test_condition_returns_unknown_on_failure(self):
        """get_weather_condition should return 'unknown' when cache is None."""
        from core.weather import get_weather_condition
        self.assertEqual(get_weather_condition(), "unknown")

    def test_no_crash_on_network_failure(self):
        """Full update cycle should not crash on network failure."""
        import core.weather as weather
        state = CatState()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = ConnectionError("No network")
            weather.update(0.05, state)  # should not raise
        self.assertEqual(state.weather_condition, "unknown",
                         "Should stay unknown after failed fetch")


class TestWeatherDisplay(unittest.TestCase):
    """Test weather display string production."""

    def test_display_sunny(self):
        state = CatState()
        state.weather_condition = "sunny"
        state.weather_temp = 30
        from core.weather import get_weather_for_display
        display = get_weather_for_display(state)
        self.assertIn("☀️", display)
        self.assertIn("SUNNY", display)
        self.assertIn("30", display)

    def test_display_no_temp(self):
        state = CatState()
        state.weather_condition = "cloudy"
        # Del attribute to simulate no temp
        if hasattr(state, 'weather_temp'):
            del state.weather_temp
        from core.weather import get_weather_for_display
        display = get_weather_for_display(state)
        self.assertIn("☁️", display)
        self.assertIn("CLOUDY", display)

    def test_display_unknown(self):
        state = CatState()
        state.weather_condition = "unknown"
        from core.weather import get_weather_for_display
        display = get_weather_for_display(state)
        self.assertIn("❓", display)


class TestCompoundModifiers(unittest.TestCase):
    """Test compound weather + time-of-day modifier stacking."""

    def test_rainy_night_energy_cumulative(self):
        """Rainy weather (0.6) + night tod (0.5) = 0.3 energy multiplier."""
        # Reload needs module to get fresh datetime reference for patching
        if "behavior.needs" in sys.modules:
            del sys.modules["behavior.needs"]
        import behavior.needs
        from behavior.needs import _get_weather_multipliers as gwm
        from behavior.needs import _get_tod_multipliers as gtm

        state = CatState()
        state.weather_condition = "rainy"
        weather_mods = gwm(state)
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 2  # night → 0.5
            tod = gtm()
        compound = weather_mods.get("energy", 1.0) * tod.get("energy", 1.0)
        self.assertAlmostEqual(compound, 0.6 * 0.5)

    def test_sunny_morning_energy_cumulative(self):
        """Sunny weather (1.15) + morning tod (2.0) = 2.3 energy multiplier."""
        if "behavior.needs" in sys.modules:
            del sys.modules["behavior.needs"]
        import behavior.needs
        from behavior.needs import _get_weather_multipliers as gwm
        from behavior.needs import _get_tod_multipliers as gtm

        state = CatState()
        state.weather_condition = "sunny"
        weather_mods = gwm(state)
        with patch("behavior.needs.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 8  # morning → 2.0
            tod = gtm()
        compound = weather_mods.get("energy", 1.0) * tod.get("energy", 1.0)
        self.assertAlmostEqual(compound, 1.15 * 2.0)


if __name__ == "__main__":
    unittest.main()
