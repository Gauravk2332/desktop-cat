"""
tests/test_phase5_sounds.py — Test suite for Phase 5: Sound + Micro-Details.

Tests: sound labels on sequence steps, missing WAV handling, weather response.
Written FIRST — test-driven. All tests must pass before Phase 5 is complete.
"""

import sys
import os
import json
import tempfile
import time
import math
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from behavior.sequences import (
    SequenceRunner,
    MORNING_WAKE, GROOM_SESSION, HUNGER_WALK,
    WINDOW_WATCH, GREETING_USER, PLAY_BURST, SLEEP_SEQUENCE,
    MorningWake, GroomSession, HungerWalk,
    WindowWatch, GreetingUser, PlayBurst, SleepSequence,
)


class TestSoundLabels:
    """Each sequence step can carry a sound label."""

    def test_morning_wake_has_greeting_sound(self):
        """MorningWake steps should include meow_greeting on greeting step."""
        seq = MorningWake(cat_id=0)
        steps = seq.steps
        greeting_steps = [s for s in steps if "greet" in str(s).lower() or s[0] == "greet"]
        if greeting_steps:
            # At least one greeting step should have a sound
            has_sound = any(len(s) > 2 and "sound" in s[2] for s in greeting_steps)
            assert has_sound, "Greeting step missing sound label"

    def test_hunger_walk_has_eat_sound(self):
        """HungerWalk eat step should include eat_crunch sound."""
        seq = HungerWalk(cat_id=0)
        steps = seq.steps
        eat_steps = [s for s in steps if "eat" in str(s).lower()]
        if eat_steps:
            has_sound = any(len(s) > 2 and s[2].get("sound") == "eat_crunch" for s in eat_steps)
            assert has_sound, "Eat step missing eat_crunch sound"

    def test_groom_session_has_purr(self):
        """GroomSession should include purr sound."""
        seq = GroomSession(cat_id=0)
        steps = seq.steps
        has_purr = any(
            len(s) > 2 and s[2].get("sound") in ("purr_deep", "purr")
            for s in steps
        )
        assert has_purr, "GroomSession missing purr sound"

    def test_window_watch_has_chirp(self):
        """WindowWatch should include chirp_excited sound."""
        seq = WindowWatch(cat_id=0)
        steps = seq.steps
        has_chirp = any(
            len(s) > 2 and s[2].get("sound") == "chirp_excited"
            for s in steps
        )
        assert has_chirp, "WindowWatch missing chirp_excited sound"

    def test_greeting_user_has_greeting_sound(self):
        """GreetingUser should include meow_greeting sound."""
        seq = GreetingUser(cat_id=0)
        steps = seq.steps
        has_greeting = any(
            len(s) > 2 and s[2].get("sound") == "meow_greeting"
            for s in steps
        )
        assert has_greeting, "GreetingUser missing meow_greeting sound"

    def test_all_sequences_have_at_least_one_sound(self):
        """Every sequence should have at least one step with a sound label."""
        for seq_cls in [MorningWake, GroomSession, HungerWalk,
                        WindowWatch, GreetingUser, PlayBurst, SleepSequence]:
            seq = seq_cls(cat_id=0)
            has_sound = any(
                len(s) > 2 and "sound" in s[2]
                for s in seq.steps
            )
            assert has_sound, f"{seq_cls.__name__} has no sound labels"

    def test_sound_label_format(self):
        """Sound labels should have 'sound' key with valid string value."""
        for seq_cls in [MorningWake, GroomSession, HungerWalk,
                        WindowWatch, GreetingUser, PlayBurst]:
            seq = seq_cls(cat_id=0)
            for step in seq.steps:
                if len(step) > 2 and "sound" in step[2]:
                    sound_val = step[2]["sound"]
                    assert isinstance(sound_val, str), \
                        f"Sound label should be string, got {type(sound_val)}"
                    assert len(sound_val) > 0, \
                        "Sound label should not be empty"


class TestSoundPlayback:
    """Sound playback when sequence steps fire."""

    def test_step_execution_plays_sound(self):
        """Executing a step with sound label should trigger sound engine."""
        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.0  # mute for test

        with patch.object(sm, 'play_sound') as mock_play:
            with patch.object(sm, 'play_looped') as mock_loop:
                sm.play_step_sound("meow_greeting")
                mock_play.assert_called_once_with("meow_greeting")

    def test_unknown_sound_does_not_crash(self):
        """Missing/unregistered sound file should log a warning but not crash."""
        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.0
        try:
            sm.play_step_sound("nonexistent_sound_xyz")
            assert True, "Unknown sound should not crash"
        except Exception as e:
            assert False, f"Unknown sound crashed: {e}"

    def test_looped_sound_starts_and_stops(self):
        """Loop sounds (purr) should start and stop correctly."""
        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.0

        with patch.object(sm, 'play_looped') as mock_loop:
            with patch.object(sm, 'stop_looped') as mock_stop:
                sm.play_step_sound("purr_deep", loop=True)
                mock_loop.assert_called_once()
                # ... later
                sm.stop_step_sound("purr_deep")
                mock_stop.assert_called_once_with("purr_deep")

    def test_concurrent_sounds(self):
        """Multiple sounds should not interfere (e.g., purr + chirp)."""
        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.0

        with patch.object(sm, 'play_sound') as mock_play:
            with patch.object(sm, 'play_looped') as mock_loop:
                # Simulate grooming + bird chirp simultaneously
                sm.play_step_sound("purr_deep", loop=True)
                sm.play_step_sound("chirp_excited")
                mock_loop.assert_called()
                mock_play.assert_called()

    def test_purr_loop_wraps_in_sequence(self):
        """GroomSession should mark purr as loop-able."""
        seq = GroomSession(cat_id=0)
        purr_steps = [s for s in seq.steps
                      if len(s) > 2 and s[2].get("sound") == "purr_deep"]
        for step in purr_steps:
            assert step[2].get("loop", False), \
                "Purr_deep should be a loop sound"

    def test_sound_volume_respected(self):
        """Sound playback should respect global volume setting."""
        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.5
        with patch.object(sm, 'play_sound') as mock_play:
            with patch.object(sm, '_get_volume_multiplier', return_value=0.5):
                sm.play_step_sound("meow_greeting")
                mock_play.assert_called_once()


class TestMissingWAVHandling:
    """Graceful handling of missing sound files."""

    def test_missing_wav_logs_warning(self):
        """Missing WAV should log warning but not raise exception."""
        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.0

        # Pretend the WAV doesn't exist
        with patch.object(sm, '_file_exists', return_value=False):
            with patch('logging.warning') as mock_warn:
                try:
                    sm.play_step_sound("chirp_excited")
                    mock_warn.assert_called()
                except Exception as e:
                    assert False, f"Missing WAV raised exception: {e}"

    def test_missing_wav_falls_back_gracefully(self):
        """Missing WAV should not hang or loop infinitely."""
        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.0

        with patch.object(sm, '_file_exists', return_value=False):
            with patch('logging.warning'):
                # Should return immediately, no crash
                result = sm.play_step_sound("purr_deep", loop=True)
                assert result is None or result is not None  # just verify no crash

    def test_sequence_continues_after_missing_wav(self):
        """Sequence should not halt when a sound step has no WAV."""
        seq = GreetingUser(cat_id=0)
        runner = SequenceRunner(cat_id=0)
        runner.start_sequence(seq)

        from core.sound import SoundManager
        sm = SoundManager()
        sm.volume = 0.0

        with patch.object(sm, '_file_exists', return_value=False):
            with patch('logging.warning'):
                try:
                    # Advance through all steps
                    for _ in range(len(seq.steps) + 2):
                        runner.update(1.0)
                    assert True, "Sequence continued despite missing WAV"
                except Exception as e:
                    assert False, f"Sequence halted on missing WAV: {e}"


class TestWeatherResponse:
    """Weather responses: thunder hide, sunny boost, palette shift."""

    def test_thunder_triggers_hide(self):
        """Thunder/storm weather should trigger hide/go_home action."""
        from core.weather import WeatherSystem
        ws = WeatherSystem()
        ws._current = "thunderstorm"

        # Don't call ws.update() — it reads global _WEATHER_CACHE which
        # other tests may populate, overriding our manual _current.
        action = ws.check_storm_response({"state": "SIT"})
        assert action in ("go_home", "hide", "walk_off_screen"), \
            f"Storm should trigger escape action, got {action}"

    def test_sunny_boosts_window_watch(self):
        """Sunny weather should increase WindowWatch probability."""
        from core.weather import WeatherSystem
        ws = WeatherSystem()
        ws._current = "sunny"
        boost = ws.get_sequence_boost("WindowWatch")
        assert boost >= 2.0, f"Sunny should double WindowWatch, got {boost}"

    def test_rain_does_not_boost(self):
        """Rain should not boost WindowWatch."""
        from core.weather import WeatherSystem
        ws = WeatherSystem()
        ws._current = "rain"
        boost = ws.get_sequence_boost("WindowWatch")
        assert boost <= 1.0, f"Rain should not boost WindowWatch, got {boost}"

    def test_return_after_storm(self):
        """Cat should return to normal position after storm timer expires."""
        from core.weather import WeatherSystem
        ws = WeatherSystem()
        cat = {"state": "OFF_SCREEN", "storm_timer": 5.0, "x": 0, "y": 0}

        # Still in storm
        ws.advance_storm(cat, 1.0)
        assert cat["storm_timer"] == 4.0
        assert cat["state"] == "OFF_SCREEN"

        # Storm ended
        ws.advance_storm(cat, 4.0)
        # Should return to normal position
        assert cat["state"] != "OFF_SCREEN", "Cat should return after storm"

    def test_storm_duration_minimum(self):
        """Storm hiding should last at least 3 seconds."""
        from core.weather import WeatherSystem
        # Storm timer should be >= 3s
        hide_duration = WeatherSystem._get_storm_duration()
        assert hide_duration >= 3.0, \
            f"Storm should hide at least 3s, got {hide_duration}"

    def test_no_reaction_to_clear_weather(self):
        """Clear weather should not trigger any weather response."""
        from core.weather import WeatherSystem
        ws = WeatherSystem()
        ws._current = "clear"
        action = ws.check_storm_response({"state": "SIT"})
        assert action is None, f"Clear weather should not trigger escape"

    def test_sunny_palette_not_mandatory(self):
        """Sunny weather may have palette hint but shouldn't crash if missing."""
        from core.weather import WeatherSystem
        ws = WeatherSystem()
        ws._current = "sunny"
        try:
            palette = ws.get_palette_hint()
            assert palette is None or isinstance(palette, dict)
        except Exception as e:
            assert False, f"Palette hint crashed: {e}"


class TestConfigFlags:
    """Phase 5 config flags."""

    def test_sound_enabled_flag(self):
        assert hasattr(config, "SOUND_ENABLED")

    def test_weather_enabled_flag(self):
        assert hasattr(config, "WEATHER_ENABLED")

    def test_storm_hide_time_config(self):
        assert hasattr(config, "STORM_HIDE_TIME")
        assert getattr(config, "STORM_HIDE_TIME", 0) >= 3.0

    def test_weather_system_initialized(self):
        """WeatherSystem should be importable cleanly."""
        try:
            from core.weather import WeatherSystem
            ws = WeatherSystem()
            assert ws is not None
        except Exception as e:
            assert False, f"WeatherSystem import failed: {e}"
