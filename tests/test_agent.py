"""
tests/test_agent.py — Tests for the AI cat agent integration.

Tests:
- CatAgent class with fallback behavior
- _execute_agent_action state translations
- Context building
- Action parsing
- End-to-end agent → engine flow
"""

import json
import math
import random
import time
from unittest.mock import MagicMock, patch

import pytest

from behavior.agent import (
    CatAgent,
    build_context,
    call_ollama,
    call_remote_api,
    parse_action,
    rule_based_action,
    SYSTEM_PROMPT,
)


# ── Mock State ────────────────────────────────────────────────────────

def make_cat(**overrides):
    """Create a test cat dict with defaults."""
    cat = {
        "id": 0,
        "x": 500.0,
        "y": 400.0,
        "state": "SIT",
        "facing": True,
        "coat": 0,
        "energy": 65.0,
        "hunger": 30.0,
        "boredom": 45.0,
        "at_home": False,
        "home_cooldown": 0.0,
        "home_linger": 0.0,
        "walk_duration": 0.0,
        "walk_elapsed": 0.0,
        "walk_vy": 0.0,
        "walk_accel": 0.0,
        "walk_pause": False,
        "walk_frame": 0,
        "walk_accum": 0.0,
        "last_interaction": time.time(),
        "purr_vibrate": 0.0,
        "reaction_type": None,
        "reaction_timer": 0.0,
        "blinking": False,
        "blink_timer": 0.0,
        "next_blink": 2.0,
        "toy_target": None,
        "toy_active": False,
        "toy_type": None,
        "toy_timer": 0.0,
        "chase_timeout": 0.0,
        "mouse_near": False,
        "_action_history": [],
    }
    cat.update(overrides)
    return cat


class MockState:
    """Minimal mock replacement for CatState for agent testing."""
    def __init__(self):
        self.cats = [make_cat()]
        self.screen_width = 1536
        self.screen_height = 816
        self.mouse_pos = (750.0, 400.0)
        self._mouse_distance = 150
        self._mouse_x = 750.0
        self._mouse_y = 400.0
        self.weather_condition = "sunny"
        self.click_through = False


# ── Context Builder Tests ─────────────────────────────────────────────

class TestContextBuilder:
    def test_build_context_includes_all_fields(self):
        cat = make_cat()
        state = MockState()
        ctx = build_context(cat, state)
        assert "15:59" in ctx or "Time:" in ctx
        assert "Energy:" in ctx
        assert "Hunger:" in ctx
        assert "Boredom:" in ctx
        assert "User:" in ctx
        assert "Proximity:" in ctx
        assert "Weather:" in ctx

    def test_context_shows_afk_after_long_inactivity(self):
        cat = make_cat(last_interaction=time.time() - 600)
        state = MockState()
        ctx = build_context(cat, state)
        assert "AFK" in ctx

    def test_context_shows_action_history(self):
        cat = make_cat(_action_history=["SIT", "PURR", "MEOW"])
        state = MockState()
        ctx = build_context(cat, state)
        assert "SIT" in ctx
        assert "PURR" in ctx

    def test_context_empty_history(self):
        cat = make_cat(_action_history=[])
        state = MockState()
        ctx = build_context(cat, state)
        assert "(no recent actions)" in ctx


# ── Action Parser Tests ───────────────────────────────────────────────

class TestActionParser:
    def test_parse_simple_actions(self):
        cases = [
            ("ACTION SIT", ("SIT", None)),
            ("ACTION SLEEP", ("SLEEP", None)),
            ("ACTION PURR", ("PURR", None)),
            ("ACTION CHASE", ("CHASE", None)),
            ("ACTION GROOM", ("GROOM", None)),
            ("ACTION STRETCH", ("STRETCH", None)),
            ("ACTION FOLLOW", ("FOLLOW", None)),
            ("ACTION HOME", ("HOME", None)),
            ("ACTION PLAYTOY", ("PLAYTOY", None)),
            ("ACTION IGNORE", ("IGNORE", None)),
            ("ACTION SLOWBLINK", ("SLOWBLINK", None)),
            ("ACTION SCRATCH", ("SCRATCH", None)),
        ]
        for inp, expected in cases:
            assert parse_action(inp) == expected, f"Failed: {inp}"

    def test_parse_walk_with_coords(self):
        result = parse_action("ACTION WALK 300 500")
        assert result[0] == "WALK"
        assert result[1]["x"] == 300.0
        assert result[1]["y"] == 500.0

    def test_parse_meow_with_type(self):
        result = parse_action("ACTION MEOW greeting")
        assert result[0] == "MEOW"
        assert result[1]["type"] == "greeting"

    def test_parse_case_insensitive(self):
        result = parse_action("  action sit  ")
        assert result == ("SIT", None)

    def test_parse_nonsense_returns_none(self):
        result = parse_action("do something random")
        assert result == ("NONE", None)

    def test_parse_empty_returns_none(self):
        result = parse_action("")
        assert result == ("NONE", None)

    def test_parse_none_returns_none(self):
        result = parse_action(None)
        assert result == ("NONE", None)


# ── Rule-Based Fallback Tests ─────────────────────────────────────────

class TestRuleFallback:
    def test_low_energy_goes_home(self):
        cat = make_cat(energy=10, hunger=20)
        action, params = rule_based_action(cat, MockState())
        assert action == "HOME"

    def test_high_hunger_goes_home(self):
        cat = make_cat(energy=80, hunger=90)
        action, params = rule_based_action(cat, MockState())
        assert action == "HOME"

    def test_bored_and_energetic_goes_chase(self):
        cat = make_cat(energy=75, hunger=20, boredom=50)
        action, params = rule_based_action(cat, MockState())
        assert action in ("CHASE", "WALK")

    def test_tired_cat_sleeps(self):
        cat = make_cat(energy=20, hunger=15)
        action, params = rule_based_action(cat, MockState())
        assert action == "HOME"

    def test_happy_cat_purrs_or_grooms(self):
        cat = make_cat(energy=60, hunger=30, boredom=20)
        action, params = rule_based_action(cat, MockState())
        assert action in ("PURR", "GROOM", "SIT")


# ── CatAgent Class Tests ─────────────────────────────────────────────

class TestCatAgent:
    def test_agent_initializes_with_fallback(self):
        agent = CatAgent(backend="ollama", decision_interval=0.1)
        assert agent.backend == "ollama"
        assert not agent.is_using_fallback

    def test_agent_fallback_on_ollama_unavailable(self):
        """When Ollama is unavailable, agent falls back to rules."""
        agent = CatAgent(backend="ollama", decision_interval=0.1,
                         max_failures=1)
        cat = make_cat(energy=10)
        state = MockState()
        action, params = agent.decide(cat, state)
        assert action in ("SIT", "HOME", "NONE")

    def test_agent_respects_decision_interval(self):
        """decide() should return the cached action if within interval."""
        agent = CatAgent(backend="ollama", decision_interval=60.0)
        cat = make_cat(energy=80)
        state = MockState()
        action1, _ = agent.decide(cat, state)
        action2, _ = agent.decide(cat, state)
        # Both should be the same (cached)
        assert action1 == action2


# ── Engine Integration Tests ─────────────────────────────────────────

class MockEngine:
    """Lightweight mock of engine for action testing (no PyQt dependency)."""
    def __init__(self):
        self._agent = None
        self.state = MagicMock()
        self.state.cats = []
        self.state.screen_width = 1536
        self.state.screen_height = 816
        self.state.mouse_pos = (750.0, 400.0)
        self.sound = MagicMock()

    def set_agent(self, agent):
        self._agent = agent
        for cat in self.state.cats:
            cat.setdefault("_action_history", [])

    def _execute_agent_action(self, cat, action, params, dt):
        """Inline copy of engine._execute_agent_action for testing."""
        if action == "NONE" or action == "IGNORE":
            return
        self._record_agent_action(cat, action)
        current_state = cat.get("state", "SIT")
        if action == "SIT":
            if current_state in ("WALK", "WANDER"):
                cat["state"] = "SIT"
                cat["walk_duration"] = 0.0
            elif current_state == "CHASE":
                cat["state"] = "SIT"
                cat["toy_target"] = None
        elif action == "WALK" and params:
            cat["walk_target_x"] = float(params.get("x", cat.get("x", 500)))
            cat["walk_target_y"] = float(params.get("y", cat.get("y", 400)))
            cat["walk_duration"] = 3.0
            cat["walk_elapsed"] = 0.0
            if current_state not in ("WALK", "WANDER"):
                cat["state"] = "WALK"
        elif action in ("HOME", "SLEEP"):
            if current_state != "SLEEP":
                cat["state"] = "GO_HOME" if not cat.get("at_home", False) else "SLEEP"
        elif action == "CHASE":
            cat["state"] = "CHASE"
            cat["toy_active"] = True
        elif action == "PURR":
            cat["purr_vibrate"] = 1.0
        elif action == "GROOM":
            cat["reaction_type"] = "groom"
            cat["reaction_timer"] = 2.0
        elif action == "STRETCH":
            cat["reaction_type"] = "stretch"
            cat["reaction_timer"] = 1.5
        elif action == "SLOWBLINK":
            cat["blinking"] = True
            cat["blink_timer"] = 0.0
            cat["next_blink"] = 3.0
        elif action == "SCRATCH":
            cat["reaction_type"] = "scratch"
            cat["reaction_timer"] = 1.5
        elif action == "PLAYTOY":
            cat["state"] = "PLAY"
            cat["toy_active"] = True
            cat["toy_type"] = "ball"
            cat["toy_timer"] = 3.0

    def _record_agent_action(self, cat, action):
        history = cat.get("_action_history", [])
        history.append(action)
        if len(history) > 10:
            history[:] = history[-10:]
        cat["_action_history"] = history


class TestEngineAgentIntegration:
    @pytest.fixture
    def engine(self):
        return MockEngine()

    def test_set_agent(self, engine):
        agent = CatAgent(backend="ollama")
        engine.set_agent(agent)
        assert engine._agent is not None

    def test_execute_sit_from_walk(self, engine):
        cat = make_cat(state="WALK")
        engine._execute_agent_action(cat, "SIT", None, 0.016)
        assert cat["state"] == "SIT"

    def test_execute_walk_sets_target(self, engine):
        cat = make_cat(state="SIT")
        engine._execute_agent_action(cat, "WALK", {"x": 800, "y": 500}, 0.016)
        assert cat["state"] == "WALK"
        assert cat["walk_target_x"] == 800.0
        assert cat["walk_target_y"] == 500.0

    def test_execute_home_or_sleep(self, engine):
        cat = make_cat(state="SIT", at_home=True)
        engine._execute_agent_action(cat, "SLEEP", None, 0.016)
        assert cat["state"] == "SLEEP"

    def test_execute_home_when_not_at_home(self, engine):
        cat = make_cat(state="SIT", at_home=False)
        engine._execute_agent_action(cat, "SLEEP", None, 0.016)
        assert cat["state"] == "GO_HOME"

    def test_execute_chase_sets_toy(self, engine):
        cat = make_cat(state="SIT")
        engine._execute_agent_action(cat, "CHASE", None, 0.016)
        assert cat["state"] == "CHASE"
        assert cat["toy_active"]

    def test_execute_purr(self, engine):
        cat = make_cat(state="SIT")
        engine._execute_agent_action(cat, "PURR", None, 0.016)
        assert cat["purr_vibrate"] > 0

    def test_execute_groom(self, engine):
        cat = make_cat()
        engine._execute_agent_action(cat, "GROOM", None, 0.016)
        assert cat["reaction_type"] == "groom"
        assert cat["reaction_timer"] > 0

    def test_execute_stretch(self, engine):
        cat = make_cat()
        engine._execute_agent_action(cat, "STRETCH", None, 0.016)
        assert cat["reaction_type"] == "stretch"

    def test_execute_slowblink(self, engine):
        cat = make_cat()
        engine._execute_agent_action(cat, "SLOWBLINK", None, 0.016)
        assert cat["blinking"]

    def test_execute_none_does_nothing(self, engine):
        cat = make_cat(state="SIT")
        engine._execute_agent_action(cat, "NONE", None, 0.016)
        assert cat["state"] == "SIT"

    def test_execute_ignore_does_nothing(self, engine):
        cat = make_cat(state="SIT")
        engine._execute_agent_action(cat, "IGNORE", None, 0.016)
        assert cat["state"] == "SIT"

    def test_record_action_history(self, engine):
        cat = make_cat()
        engine._record_agent_action(cat, "CHASE")
        engine._record_agent_action(cat, "SIT")
        assert len(cat["_action_history"]) == 2
        assert cat["_action_history"][0] == "CHASE"
        assert cat["_action_history"][1] == "SIT"

    def test_action_history_max_10(self, engine):
        cat = make_cat()
        for i in range(15):
            engine._record_agent_action(cat, f"ACTION_{i}")
        assert len(cat["_action_history"]) == 10
        assert cat["_action_history"][0] == "ACTION_5"
        assert cat["_action_history"][-1] == "ACTION_14"

    def test_playtoy_sets_toy_state(self, engine):
        cat = make_cat(state="SIT")
        engine._execute_agent_action(cat, "PLAYTOY", None, 0.016)
        assert cat["state"] == "PLAY"
        assert cat["toy_active"]
        assert cat["toy_type"] == "ball"


# ── LLM Caller Tests (mock) ──────────────────────────────────────────

class TestLLMCallers:
    def test_call_ollama_returns_none_on_failure(self):
        """Should return None gracefully when Ollama is unreachable."""
        result = call_ollama("test context", host="localhost:0", timeout=0.5)
        assert result is None

    def test_call_remote_api_returns_none_without_credentials(self):
        result = call_remote_api("test context", "", "")
        assert result is None
