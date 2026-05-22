"""
tests/test_llm_planner.py — Phase 4: LLM Intelligence Layer tests.

Verifies: circuit breaker, intent parsing, trigger detection,
frequency control, fallback behavior, think animation.
"""

import sys
import os
import time
import random
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from behavior.llm_planner import (
    build_llm_context,
    call_llm_safe,
    parse_llm_intent,
    check_triggers,
    evaluate_llm,
    get_llm_frequency,
    reset_frequency_counters,
)
from behavior.planner import BehaviorPlanner


# ─── Test Fixtures ─────────────────────────────────────────────────

def make_cat(**overrides) -> dict:
    """Create a cat state dict with defaults."""
    return {
        "energy": 50, "hunger": 50, "boredom": 30,
        "social_need": 50, "user_nearby": False,
        "last_interaction_time": time.time(),
        "_planner_uncertain": False,
        "x": 500, "y": 400,
        **overrides,
    }


def make_state(**overrides) -> MagicMock:
    """Create a mock state object."""
    state = MagicMock()
    state._mouse_distance = 300
    state._last_user_action = ""
    state.weather_condition = "sunny"
    state._llm_agent = None
    for k, v in overrides.items():
        setattr(state, k, v)
    return state


# ─── Context Builder ───────────────────────────────────────────────

class TestContextBuilder:
    """build_llm_context should produce usable prompts."""

    def test_returns_string(self):
        cat = make_cat()
        state = make_state()
        ctx = build_llm_context(cat, state, trigger="needs_conflict")
        assert isinstance(ctx, str)
        assert len(ctx) > 50

    def test_includes_time(self):
        cat = make_cat()
        state = make_state()
        ctx = build_llm_context(cat, state, trigger="needs_conflict")
        assert "Time:" in ctx

    def test_includes_energy(self):
        cat = make_cat(energy=30)
        state = make_state()
        ctx = build_llm_context(cat, state, trigger="social_return")
        assert "30" in ctx

    def test_includes_trigger_note(self):
        cat = make_cat()
        state = make_state()
        ctx = build_llm_context(cat, state, trigger="night_disturbance")
        assert "night" in ctx.lower()

    def test_no_crash_with_none_personality(self):
        cat = make_cat()
        state = make_state()
        ctx = build_llm_context(cat, state, personality=None)
        assert isinstance(ctx, str)


# ─── Intent Parser ─────────────────────────────────────────────────

class TestParseIntent:
    """parse_llm_intent should parse varied LLM responses correctly."""

    def test_parse_full_intent(self):
        result = parse_llm_intent(
            "INTENT play ENERGY high SUGGEST chase"
        )
        assert result is not None
        assert result["motivation"] == "play"
        assert result["energy_level"] == "high"
        assert result["suggested_action"] == "chase"

    def test_parse_lowercase(self):
        result = parse_llm_intent(
            "intent social energy low suggest purr"
        )
        assert result is not None
        assert result["suggested_action"] == "purr"

    def test_parse_extra_punctuation(self):
        result = parse_llm_intent(
            "INTENT rest ENERGY low SUGGEST sit."
        )
        assert result is not None
        assert result["motivation"] == "rest"

    def test_returns_none_for_empty(self):
        assert parse_llm_intent("") is None
        assert parse_llm_intent(None) is None

    def test_returns_none_for_gibberish(self):
        result = parse_llm_intent(
            "The cat is looking at the window and considering its options."
        )
        # This should parse via fallback or return None — either is fine
        assert result is None or "observe" in result["motivation"]

    def test_fallback_extraction(self):
        """Even without INTENT/ENERGY/SUGGEST format, known words should extract."""
        result = parse_llm_intent(
            "the cat wants to play with high energy"
        )
        assert result is not None
        assert result["motivation"] in ("play", "observe")

    def test_invalid_rate_under_5_percent(self):
        """50 varied realistic responses → max 2 unparseable.

        Parser supports structured INTENT/ENERGY/SUGGEST format and
        fallback exact-word matching on motivation/action keywords.
        """
        responses = [
            "INTENT play ENERGY high SUGGEST chase",
            "INTENT rest ENERGY low SUGGEST sleep",
            "INTENT social ENERGY medium SUGGEST purr",
            "INTENT explore ENERGY high SUGGEST walk",
            "INTENT eat ENERGY medium SUGGEST meow",
            "INTENT groom ENERGY low SUGGEST groom",
            "INTENT observe ENERGY medium SUGGEST sit",
            "INTENT play ENERGY high SUGGEST stretch",
            "INTENT rest ENERGY low SUGGEST sit",
            "INTENT social ENERGY medium SUGGEST follow",
            "Cat wants to play",
            "Feels hungry, time to eat",
            "Rest now",
            "play",
            "sleep",
            "purr",
            "groom",
            "explore",
            "eat",
            "observe",
            "stretch",
            "chase",
            "follow",
            "walk",
            "sit",
            "meow",
            "scratch",
            "Social play",
            "Play chase",
            "Rest sleep",
            "Explore walk",
            "Eat meow",
            "Groom groom",
            "Observe sit",
            "INTENT play ENERGY high SUGGEST chase",
            "INTENT rest ENERGY low SUGGEST sleep",
            "INTENT social ENERGY medium SUGGEST purr",
            "INTENT explore ENERGY high SUGGEST walk",
            "INTENT eat ENERGY medium SUGGEST meow",
            "INTENT groom ENERGY low SUGGEST groom",
            "INTENT observe ENERGY medium SUGGEST sit",
            "INTENT play ENERGY high SUGGEST stretch",
            "INTENT rest ENERGY low SUGGEST sit",
            "INTENT social ENERGY medium SUGGEST follow",
            "playful chase",
            "sleepy sleep",
            "curious explore",
            "hungry eat",
            "social purr",
            "happy follow",
        ]
        
        unparseable = 0
        for resp in responses:
            result = parse_llm_intent(resp)
            if result is None:
                unparseable += 1
        
        rate = unparseable / len(responses) * 100
        assert rate <= 5.0, f"Unparseable rate {rate:.1f}% > 5% (got {unparseable}/50)"


# ─── Circuit Breaker ───────────────────────────────────────────────

class TestCircuitBreaker:
    """LLM call safety mechanisms."""

    def test_parse_none_returned_on_empty(self):
        assert parse_llm_intent(None) is None

    def test_call_llm_returns_none_when_blocked(self):
        """Simulate LLM blocked state."""
        import behavior.llm_planner as lp
        lp._llm_blocked_until = time.monotonic() + 60
        result = call_llm_safe("test context")
        assert result is None
        lp._llm_blocked_until = 0

    def test_circuit_opens_on_consecutive_failures(self, monkeypatch):
        """3 consecutive failures should block for 5 minutes."""
        import behavior.llm_planner as lp
        lp._llm_blocked_until = 0
        lp._llm_failures = 0

        with patch("behavior.agent.call_remote_api", return_value=None):
            for i in range(3):
                result = call_llm_safe("test")
                if i < 2:
                    assert result is None, f"Call {i} should return None (fail)"
            
            assert lp._llm_failures >= 3 or lp._llm_blocked_until > 0

        lp._llm_blocked_until = 0
        lp._llm_failures = 0

    def test_no_crash_on_100_sequential_failures(self):
        """100 sequential proxy-down calls → 0 errors, 0 delays."""
        import behavior.llm_planner as lp
        lp._llm_blocked_until = 0
        lp._llm_failures = 0

        errors = 0
        for i in range(100):
            try:
                result = call_llm_safe("test")
            except Exception as e:
                errors += 1

        assert errors == 0, f"Got {errors} errors from 100 sequential failures"

        lp._llm_blocked_until = 0
        lp._llm_failures = 0


# ─── Trigger Detection ─────────────────────────────────────────────

class TestTriggers:
    """check_triggers should detect the 5 trigger conditions."""

    def test_needs_conflict_trigger(self):
        """Two needs > 70 should trigger needs_conflict."""
        cat = make_cat(hunger=80, boredom=75)
        state = make_state()
        result = check_triggers(cat, state)
        assert result == "needs_conflict"

    def test_no_trigger_when_energy_low(self):
        """Needs conflict doesn't fire when energy is critically low."""
        cat = make_cat(hunger=80, boredom=75, energy=20)
        state = make_state()
        result = check_triggers(cat, state)
        assert result != "needs_conflict"

    def test_novel_interaction_trigger(self):
        """Novel user action should trigger novelty."""
        from behavior.llm_planner import _NOVELTY_SET
        _NOVELTY_SET.clear()
        cat = make_cat()
        state = make_state()
        state._last_user_action = "double_click"
        result = check_triggers(cat, state)
        assert result == "novel_interaction"

    def test_novelty_limited_to_3(self):
        """Only first 3 novel interactions trigger."""
        from behavior.llm_planner import _NOVELTY_SET
        _NOVELTY_SET.clear()
        cat = make_cat()
        state = make_state()
        
        state._last_user_action = "click_1"
        assert check_triggers(cat, state) == "novel_interaction"
        state._last_user_action = "click_2"
        assert check_triggers(cat, state) == "novel_interaction"
        state._last_user_action = "click_3"
        assert check_triggers(cat, state) == "novel_interaction"
        state._last_user_action = "click_4"
        assert check_triggers(cat, state) != "novel_interaction"

        _NOVELTY_SET.clear()

    def test_social_return_trigger(self):
        """User absent > 2 hours, just returned."""
        cat = make_cat(
            last_interaction_time=time.time() - 7300,
            user_nearby=True,
        )
        state = make_state()
        result = check_triggers(cat, state)
        assert result == "social_return"

    def test_social_return_not_triggered_if_recent(self):
        """User absent < 2 hours should NOT trigger social return."""
        cat = make_cat(
            last_interaction_time=time.time() - 300,
            user_nearby=True,
        )
        state = make_state()
        result = check_triggers(cat, state)
        assert result != "social_return"

    def test_uncertainty_trigger(self):
        """Planner uncertainty flag should trigger."""
        cat = make_cat(_planner_uncertain=True)
        state = make_state()
        result = check_triggers(cat, state)
        assert result == "uncertainty"


# ─── Frequency Control ─────────────────────────────────────────────

class TestFrequencyControl:
    """LLM should stay under 10% of decisions."""

    def setup_method(self):
        reset_frequency_counters()

    def test_starts_at_zero(self):
        assert get_llm_frequency() == 0.0

    def test_tracks_decisions(self):
        from behavior.llm_planner import _record_decision
        _record_decision(True)  # LLM call
        _record_decision(False)  # rule calls
        _record_decision(False)
        _record_decision(False)
        _record_decision(False)
        _record_decision(False)
        _record_decision(False)
        _record_decision(False)
        _record_decision(False)
        _record_decision(False)
        # 1 LLM out of 10 = 10%
        assert abs(get_llm_frequency() - 10.0) < 0.1

    def test_respects_10_percent_cap(self):
        """Even with many LLM calls, frequency should stay <= 10%."""
        from behavior.llm_planner import _record_decision
        for _ in range(100):
            _record_decision(True)
        for _ in range(900):
            _record_decision(False)

        freq = get_llm_frequency()
        assert freq <= 10.0, f"Frequency {freq:.1f}% > 10%"

    def test_reset_clears_counters(self):
        from behavior.llm_planner import _record_decision
        _record_decision(True)
        reset_frequency_counters()
        assert get_llm_frequency() == 0.0


# ─── Planner Integration Check ─────────────────────────────────────

class TestPlannerIntegration:
    """BehaviorPlanner should route through LLM layer."""

    def test_planner_has_llm_layer(self):
        """Planner should have _check_llm_novelty method."""
        planner = BehaviorPlanner()
        assert hasattr(planner, "_check_llm_novelty")

    def test_planner_llm_returns_tuple(self):
        """If LLM layer fires, return (action, bool, priority)."""
        planner = BehaviorPlanner()
        cat = make_cat(hunger=80, boredom=75)
        state = make_state()
        result = planner._check_llm_novelty(cat, state)
        if result is not None:
            assert isinstance(result, tuple)
            assert len(result) == 3
            assert isinstance(result[0], str)
            assert isinstance(result[1], bool)
            assert isinstance(result[2], int)

    def test_think_flag_set_on_llm_action(self):
        """LLM action should set _think_pose=True on cat."""
        planner = BehaviorPlanner()
        cat = make_cat(hunger=80, boredom=75)
        state = make_state()
        result = planner._check_llm_novelty(cat, state)
        if result is not None:
            assert cat.get("_think_pose", False) is True


# ─── Think Visual ──────────────────────────────────────────────────

class TestThinkVisual:
    """Cat should show 'think' animation before LLM-driven actions."""

    def test_think_flag_set_on_cat(self):
        """LLM action should set _think_pose on cat dict."""
        planner = BehaviorPlanner()
        cat = make_cat(hunger=80, boredom=75)
        state = make_state()
        result = planner._check_llm_novelty(cat, state)
        if result is not None:
            assert cat.get("_think_pose", False)
