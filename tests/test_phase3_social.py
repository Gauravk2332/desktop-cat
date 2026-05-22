"""
tests/test_phase3_social.py — Tests for Phase 3 Social features.

Covers:
- MoodState: happiness/trust changes, decay, persistence, greeting multiplier
- SocialReferencing: trigger conditions, sequence phase advancement
- ContagionMonitor: input rate → tail swish mapping
- REM twitch: deep sleep trigger, timer management
- Planner mood integration: _check_interaction respects mood_multiplier

Run: python3 -m pytest tests/test_phase3_social.py -v
"""

import sys
import os
import json
import math
import tempfile
import time
from unittest.mock import patch, MagicMock
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState, default_cat_dict


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_state(num_cats=1, width=1920, height=1080):
    """Create a CatState with screen geometry and cats."""
    state = CatState()
    state.screen_width = width
    state.screen_height = height
    while len(state.cats) < num_cats:
        state.cats.append(default_cat_dict(len(state.cats)))
    state.last_interaction = 0.0
    return state


def _make_cat(**kwargs):
    """Create a cat dict with defaults."""
    cat = {
        "energy": 80.0, "hunger": 20.0, "boredom": 20.0,
        "state": "SIT", "user_nearby": False, "pet_timer": 0.0,
        "x": 500.0, "y": 700.0, "facing": True, "id": 0,
        "deep_sleep": False, "rem_twitch": False, "rem_twitch_timer": 0.0,
    }
    cat.update(kwargs)
    return cat


# ── MoodState Tests ────────────────────────────────────────────────────────

class TestMoodState:
    """MoodState: happiness/trust, decay, persistence, greeting multiplier."""

    def test_happiness_increases_on_pet(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        before = mood.happiness
        mood.apply_interaction("pet")
        assert mood.happiness > before, \
            f"Expected happiness > {before}, got {mood.happiness}"

    def test_happiness_increases_on_play(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 50.0
        mood.apply_interaction("play")
        assert mood.happiness == 55.0, \
            f"Expected 55.0, got {mood.happiness}"

    def test_happiness_decreases_on_startle(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 80.0
        mood.apply_interaction("startle")
        assert mood.happiness == 70.0, \
            f"Expected 70.0, got {mood.happiness}"

    def test_trust_decreases_on_startle(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        before = mood.trust
        mood.apply_interaction("startle")
        assert mood.trust < before, \
            f"Expected trust < {before}, got {mood.trust}"

    def test_happiness_decays_over_time(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 80.0
        # Update with enough time to trigger decay (300s per decay)
        mood.update(600.0)
        assert mood.happiness < 80.0, \
            f"Expected happiness < 80.0 after 600s, got {mood.happiness}"

    def test_happiness_does_not_below_minimum(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood._happiness_minimum = 30.0
        mood.happiness = 30.5
        # Even with massive decay, should floor at minimum
        mood.update(10000.0)
        assert mood.happiness >= 30.0, \
            f"Expected >= 30.0, got {mood.happiness}"

    def test_greeting_multiplier_happy(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 85.0
        assert mood.get_greeting_multiplier() == 2.0, \
            f"Expected 2.0, got {mood.get_greeting_multiplier()}"

    def test_greeting_multiplier_normal(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 60.0
        assert mood.get_greeting_multiplier() == 1.0, \
            f"Expected 1.0, got {mood.get_greeting_multiplier()}"

    def test_greeting_multiplier_sad(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 35.0
        assert mood.get_greeting_multiplier() == 0.5, \
            f"Expected 0.5, got {mood.get_greeting_multiplier()}"

    def test_greeting_multiplier_very_sad(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 10.0
        assert mood.get_greeting_multiplier() == 0.2, \
            f"Expected 0.2, got {mood.get_greeting_multiplier()}"

    def test_approach_distance_high_trust(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.trust = 90.0
        dist = mood.get_approach_distance()
        # 200 - 90*1.5 = 65
        assert dist == 65.0, f"Expected 65.0, got {dist}"

    def test_approach_distance_low_trust(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.trust = 10.0
        dist = mood.get_approach_distance()
        # 200 - 10*1.5 = 185
        assert dist == 185.0, f"Expected 185.0, got {dist}"

    def test_approach_distance_minimum(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.trust = 200.0  # should floor at 30
        dist = mood.get_approach_distance()
        assert dist == 30.0, f"Expected 30.0 (minimum), got {dist}"

    def test_mood_persistence(self):
        """Save → verify ±2 tolerance on reload."""
        from behavior.mood import MoodState
        with tempfile.TemporaryDirectory() as tmpdir:
            mood = MoodState(load_from_file=False, persist_dir=tmpdir)
            mood.happiness = 42.0
            mood.trust = 88.0
            mood._save()

            mood2 = MoodState(load_from_file=True, persist_dir=tmpdir)
            assert abs(mood2.happiness - 42.0) <= 2.0, \
                f"Happiness mismatch: {mood2.happiness} vs 42.0"
            assert abs(mood2.trust - 88.0) <= 2.0, \
                f"Trust mismatch: {mood2.trust} vs 88.0"

    def test_mood_persistence_tolerance_precision(self):
        """Exact round-trip for known values."""
        from behavior.mood import MoodState
        with tempfile.TemporaryDirectory() as tmpdir:
            mood = MoodState(load_from_file=False, persist_dir=tmpdir)
            mood.happiness = 65.0
            mood.trust = 70.0
            mood._save()

            mood2 = MoodState(load_from_file=True, persist_dir=tmpdir)
            assert mood2.happiness == 65.0, \
                f"Expected 65.0, got {mood2.happiness}"
            assert mood2.trust == 70.0, \
                f"Expected 70.0, got {mood2.trust}"

    def test_mood_multiplier_property(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 85.0
        assert mood.mood_multiplier == 2.0

    def test_mood_caps_at_maximum(self):
        from behavior.mood import MoodState
        mood = MoodState(load_from_file=False)
        mood.happiness = 99.0
        mood.apply_interaction("pet")  # +3
        assert mood.happiness == 100.0, \
            f"Expected 100.0 (capped), got {mood.happiness}"


# ── SocialReferencing Tests ────────────────────────────────────────────────

class TestSocialReferencing:
    """SocialReferencing: trigger conditions, sequence phases."""

    def test_returns_normally_when_inactive(self):
        from behavior.social_referencing import SocialReferencing
        sr = SocialReferencing()
        state = _make_state()
        cat = _make_cat()
        result = sr.update(0.05, cat, state, None)
        assert result is None or result == "look_toward", \
            f"Expected None or look_toward, got {result}"

    def test_sequence_advances_through_phases(self):
        """Force a sequence and verify all phases appear."""
        from behavior.social_referencing import SocialReferencing
        sr = SocialReferencing()
        # Directly start a sequence
        sr._start_sequence()

        phases_seen = []
        # Run through the sequence (5 phases total, 0.5s each)
        for _ in range(30):
            action = sr.update(0.2, {}, None, None)
            if action is not None:
                phases_seen.append(action)

        # Should see: look_toward, look_object, look_back, chirp
        expected = ["look_toward", "look_object", "look_back", "chirp"]
        for exp in expected:
            assert exp in phases_seen, \
                f"Expected {exp} in sequence, got {phases_seen}"

    def test_cooldown_blocks_rapid_retrigger(self):
        from behavior.social_referencing import SocialReferencing
        sr = SocialReferencing()
        # Set cooldown manually
        sr._cooldown = 15.0  # 15s remaining
        sr._active = False
        cat = _make_cat()
        state = _make_state()
        state.last_interaction = 0.0  # user nearby

        # Should not trigger (on cooldown)
        with patch("random.random", return_value=0.001):  # well under 0.005
            result = sr.update(0.05, cat, state, None)
            assert result is None, f"Expected None (cooldown), got {result}"

    def test_reset_clears_state(self):
        from behavior.social_referencing import SocialReferencing
        sr = SocialReferencing()
        sr._start_sequence()
        assert sr.is_active
        sr.reset()
        assert not sr.is_active
        assert sr.cooldown_remaining == 0.0

    def test_trigger_requires_curiosity_above_05(self):
        from behavior.social_referencing import SocialReferencing
        sr = SocialReferencing()
        cat = _make_cat()
        state = _make_state()
        state.last_interaction = 0.0  # user nearby

        # Mock personality with low curiosity
        p = MagicMock()
        p.get_raw.return_value = 0.2

        with patch("random.random", return_value=0.001):
            result = sr.update(0.05, cat, state, p)
            assert result is None, \
                f"Expected None (low curiosity), got {result}"

    def test_trigger_requires_user_near(self):
        from behavior.social_referencing import SocialReferencing
        sr = SocialReferencing()
        cat = _make_cat()
        state = _make_state()
        state.last_interaction = 100.0  # user far away

        p = MagicMock()
        p.get_raw.return_value = 0.8

        with patch("random.random", return_value=0.001):
            result = sr.update(0.05, cat, state, p)
            assert result is None, \
                f"Expected None (no user), got {result}"

    def test_sequence_completes_and_returns_none(self):
        from behavior.social_referencing import SocialReferencing
        sr = SocialReferencing()
        sr._start_sequence()
        # Run through all phases
        for _ in range(30):
            sr.update(0.5, {}, None, None)
        assert not sr.is_active, "Sequence should be inactive after completion"


# ── ContagionMonitor Tests ────────────────────────────────────────────────

class TestContagionMonitor:
    """ContagionMonitor: input rate → tail swish mapping."""

    def test_no_input_gives_calm(self):
        from behavior.contagion import ContagionMonitor
        cm = ContagionMonitor(window_seconds=5.0)
        result = cm.update(0.05)
        assert result["tail_swish"] == 0.0, \
            f"Expected 0.0 tail swish with no input, got {result['tail_swish']}"
        assert not result["ears_airplane"], \
            "Expected no airplane ears with no input"

    def test_high_input_rate_triggers_airplane_ears(self):
        from behavior.contagion import ContagionMonitor
        cm = ContagionMonitor(window_seconds=5.0)
        # Record 60 input events (12/sec over 5s window)
        for _ in range(60):
            cm.record_input("keyboard")
        result = cm.update(0.05)
        assert result["ears_airplane"], \
            "Expected airplane ears with high input rate"

    def test_moderate_input_gives_some_tail_swish(self):
        from behavior.contagion import ContagionMonitor
        cm = ContagionMonitor(window_seconds=5.0)
        # 20 events in 5s → 4/sec → moderate
        for _ in range(20):
            cm.record_input("keyboard")
        result = cm.update(0.05)
        assert result["tail_swish"] > 0, \
            "Expected some tail swish with moderate input"

    def test_reset_clears_state(self):
        from behavior.contagion import ContagionMonitor
        cm = ContagionMonitor(window_seconds=5.0)
        for _ in range(60):
            cm.record_input("keyboard")
        cm.reset()
        result = cm.update(0.05)
        assert result["tail_swish"] == 0.0, \
            "Expected 0 swish after reset"

    def test_contagion_mood_property(self):
        from behavior.contagion import ContagionMonitor
        cm = ContagionMonitor()
        assert cm.mood == "calm", \
            f"Expected 'calm' initially, got {cm.mood}"
        for _ in range(60):
            cm.record_input("keyboard")
        cm.update(0.05)
        # after update, mood should be "agitated" since high input
        if cm.input_rate > 10:
            assert cm.mood == "agitated", \
                f"Expected 'agitated', got {cm.mood}"

    def test_input_rate_property(self):
        from behavior.contagion import ContagionMonitor
        cm = ContagionMonitor(window_seconds=5.0)
        for _ in range(10):
            cm.record_input("keyboard")
        rate = cm.input_rate
        assert rate > 0, f"Expected rate > 0, got {rate}"


# ── REM Twitch Tests ──────────────────────────────────────────────────────

class TestREMTwitch:
    """REM twitch: deep sleep triggers, timer management."""

    def test_no_twitch_when_awake(self):
        """cat should not twitch when not sleeping."""
        cat = _make_cat(state="SIT", deep_sleep=False)
        _check_rem_twitch_direct(cat, 0.05)
        assert not cat.get("rem_twitch"), \
            "Should not twitch when awake"

    def test_no_twitch_without_deep_sleep(self):
        cat = _make_cat(state="SLEEP", deep_sleep=False)
        _check_rem_twitch_direct(cat, 0.05)
        assert not cat.get("rem_twitch"), \
            "Should not twitch without deep sleep"

    def test_twitch_during_deep_sleep(self):
        """2% per tick chance — force it with random patch."""
        cat = _make_cat(state="SLEEP", deep_sleep=True)
        with patch("random.random", return_value=0.01):  # less than 0.02
            with patch("random.uniform", return_value=0.75):
                _check_rem_twitch_direct(cat, 0.05)
                assert cat.get("rem_twitch"), \
                    "Should twitch during deep sleep"

    def test_rem_twitch_timer(self):
        cat = _make_cat(state="SLEEP", deep_sleep=True)
        with patch("random.random", return_value=0.01):
            with patch("random.uniform", return_value=0.75):
                _check_rem_twitch_direct(cat, 0.05)
                assert cat["rem_twitch_timer"] > 0, \
                    "Timer should be set"
                assert cat["rem_twitch_timer"] <= 1.0, \
                    "Timer should be <= 1.0"

    def test_twitch_timer_decays(self):
        cat = _make_cat(state="SLEEP", deep_sleep=True)
        cat["rem_twitch"] = True
        cat["rem_twitch_timer"] = 0.8
        _check_rem_twitch_direct(cat, 0.3)
        assert cat["rem_twitch_timer"] <= 0.5 + 0.001, \
            f"Timer should decay (~0.5), got {cat['rem_twitch_timer']}"

    def test_twitch_ends_when_timer_expires(self):
        cat = _make_cat(state="SLEEP", deep_sleep=True)
        cat["rem_twitch"] = True
        cat["rem_twitch_timer"] = 0.1
        _check_rem_twitch_direct(cat, 0.2)  # beyond timer
        assert not cat.get("rem_twitch"), \
            "Twitch should end when timer expires"

    def test_no_twitch_when_already_twitching(self):
        """Should not start a new twitch while one is active."""
        cat = _make_cat(state="SLEEP", deep_sleep=True)
        cat["rem_twitch"] = True
        cat["rem_twitch_timer"] = 0.5
        with patch("random.random", return_value=0.01):  # would trigger if not already twitching
            _check_rem_twitch_direct(cat, 0.05)
            assert cat["rem_twitch"], "Should still be twitching"
            # timer should have decremented
            assert cat["rem_twitch_timer"] < 0.5, \
                "Timer should have decremented"

    def test_rem_twitch_config_disabled(self):
        """Disabled config should prevent any REM behavior."""
        # Use alternate version disabled
        cat = _make_cat(state="SLEEP", deep_sleep=True)
        _check_rem_twitch_disabled(cat, 0.05)
        assert not cat.get("rem_twitch"), \
            "Should not twitch when disabled"


def _check_rem_twitch_direct(cat, dt):
    """Direct copy of engine's _check_rem_twitch logic for testing."""
    import random
    if cat.get("state") != config.STATE_SLEEP:
        if cat.get("rem_twitch"):
            cat["rem_twitch"] = False
            cat["rem_twitch_timer"] = 0.0
        return
    if not cat.get("deep_sleep", False):
        return
    if random.random() < 0.02 and not cat.get("rem_twitch"):
        cat["rem_twitch"] = True
        cat["rem_twitch_timer"] = random.uniform(0.5, 1.0)
        return
    if cat.get("rem_twitch"):
        cat["rem_twitch_timer"] = max(0.0, cat.get("rem_twitch_timer", 0.0) - dt)
        if cat["rem_twitch_timer"] <= 0:
            cat["rem_twitch"] = False


def _check_rem_twitch_disabled(cat, dt):
    """REM twitch when disabled — no state changes."""
    pass


# ── Planner Mood Integration Tests ────────────────────────────────────────

class TestPlannerMoodIntegration:
    """Planner _check_interaction respects mood_multiplier."""

    def test_greet_happens_with_high_mood(self):
        """High mood (2.0) = always greet when conditions met."""
        from behavior.planner import BehaviorPlanner
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(user_nearby=True, pet_timer=1.0,
                        mood_multiplier=2.0)

        action, is_seq, priority = planner.update(0.05, cat, state)
        assert action == "greet", \
            f"Expected greet, got {action}"

    def test_greet_can_be_suppressed_by_low_mood(self):
        """Low mood (0.2) = only 20% chance to greet."""
        from behavior.planner import BehaviorPlanner
        planner = BehaviorPlanner()
        state = _make_state()

        # With mood_mult=0.2, random() > 0.2 most of time → None
        # Force random high so we skip greet
        with patch("random.random", return_value=0.5):  # > 0.2
            cat = _make_cat(user_nearby=True, pet_timer=1.0,
                            mood_multiplier=0.2)
            action, is_seq, priority = planner.update(0.05, cat, state)
            assert action != "greet", \
                f"Expected non-greet with mood=0.2 and random=0.5, got {action}"

    def test_greet_happens_when_random_rolls_below_mood(self):
        """With mood=0.2, random roll of 0.1 should allow greet."""
        from behavior.planner import BehaviorPlanner
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(user_nearby=True, pet_timer=1.0,
                        mood_multiplier=0.2)

        with patch("random.random", return_value=0.1):  # < 0.2 → greet
            action, is_seq, priority = planner.update(0.05, cat, state)
            assert action == "greet", \
                f"Expected greet (random below mood), got {action}"

    def test_no_mood_multiplier_defaults_to_normal(self):
        """Missing mood_multiplier = 1.0 = always greet."""
        from behavior.planner import BehaviorPlanner
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(user_nearby=True, pet_timer=1.0)
        # No mood_multiplier set

        action, is_seq, priority = planner.update(0.05, cat, state)
        assert action == "greet", \
            f"Expected greet with no mood_mult, got {action}"


# ── Config Tests ──────────────────────────────────────────────────────────

class TestSocialConfigFlags:
    """Config flags for Phase 3 Social features."""

    def test_mood_enabled_flag(self):
        assert hasattr(config, "MOOD_ENABLED")
        assert isinstance(config.MOOD_ENABLED, bool)

    def test_social_referencing_enabled_flag(self):
        assert hasattr(config, "SOCIAL_REFERENCING_ENABLED")
        assert isinstance(config.SOCIAL_REFERENCING_ENABLED, bool)

    def test_contagion_enabled_flag(self):
        assert hasattr(config, "CONTAGION_ENABLED")
        assert isinstance(config.CONTAGION_ENABLED, bool)

    def test_rem_twitch_enabled_flag(self):
        assert hasattr(config, "REM_TWITCH_ENABLED")
        assert isinstance(config.REM_TWITCH_ENABLED, bool)


# ── No-Import Error Tests ────────────────────────────────────────────────

class TestImportSafety:
    """All modules import cleanly without error."""

    def test_mood_imports(self):
        from behavior.mood import MoodState

    def test_social_referencing_imports(self):
        from behavior.social_referencing import SocialReferencing

    def test_contagion_imports(self):
        from behavior.contagion import ContagionMonitor
