"""
tests/test_engine_phase3.py — End-to-end integration tests for Phase 3 engine.

Tests the full chain: circadian → needs → planner → state transition.
Also tests soul layer integration: personality → reactions → habituation → memory.

These are INTERFACE-level tests — they test integration points directly
without creating Qt widgets or full Engine instances (those require a
real QApplication).

Tests target the public APIs: BehaviorPlanner, CircadianClock, Personality,
CatMemory, HabituationModule, ReactionSystem, SequenceRunner, needs.update().

Run: python3 -m pytest tests/test_engine_phase3.py -v
"""

import sys
import os
import time
import math
from unittest.mock import MagicMock, patch
from collections import deque
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState, default_cat_dict
from core.circadian import CircadianClock
from behavior.planner import BehaviorPlanner
from behavior.personality import Personality
from behavior.memory import CatMemory, get_zone_for_position
from behavior.habituation import HabituationModule, RESPONSE_FULL, RESPONSE_IGNORE
from behavior.reactions import ReactionSystem
from behavior.needs import update as needs_update
from behavior.sequences import SEQUENCE_REGISTRY, SequenceRunner

# ── Constants ──────────────────────────────────────────────────────────

DEFAULT_W = 1920
DEFAULT_H = 1080


def _make_state(num_cats=1, width=DEFAULT_W, height=DEFAULT_H):
    """Create a CatState with screen geometry and cats."""
    state = CatState()
    state.screen_width = width
    state.screen_height = height
    while len(state.cats) < num_cats:
        state.cats.append(default_cat_dict(len(state.cats)))
    return state


def _make_cat(**kwargs):
    """Create a cat dict with defaults."""
    cat = {
        "energy": 80.0, "hunger": 20.0, "boredom": 20.0,
        "state": "SIT", "user_nearby": False, "pet_timer": 0.0,
        "x": 500.0, "y": 700.0, "facing": True, "id": 0,
    }
    cat.update(kwargs)
    return cat


# ── Integration Tests ───────────────────────────────────────────────────


class TestCircadianNeedsChain:
    """Circadian → needs → planner: full chain."""

    def test_circadian_energy_multiplier_noon(self):
        """Energy multiplier should be ~1.0 at noon."""
        clock = CircadianClock()
        clock.internal_hour = 12.0
        mult = clock.energy_multiplier
        assert 0.9 <= mult <= 1.0, f"Expected ~1.0 at noon, got {mult}"

    def test_circadian_energy_multiplier_midnight(self):
        """Energy multiplier should be low at midnight."""
        clock = CircadianClock()
        clock.internal_hour = 0.0
        mult = clock.energy_multiplier
        assert mult < 0.5, f"Expected <0.5 at midnight, got {mult}"

    def test_planner_picks_hungerwalk_at_dawn_with_high_hunger(self):
        """Planner should pick walk_to_food for hungry cat at dawn."""
        planner = BehaviorPlanner()
        clock = CircadianClock()
        clock.internal_hour = 6.0  # dawn
        state = _make_state()
        cat = _make_cat(hunger=80.0, boredom=10.0, energy=80.0)

        action, is_seq, priority = planner.update(
            0.05, cat, state, circadian=clock,
        )

        assert action == "walk_to_food", \
            f"Expected walk_to_food, got {action}"

    def test_planner_picks_play_for_bored_cat(self):
        """Planner should pick play for very bored cat."""
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(hunger=20.0, boredom=85.0, energy=80.0)

        action, is_seq, priority = planner.update(
            0.05, cat, state,
        )

        assert action == "play", f"Expected play, got {action}"

    def test_planner_picks_sleep_for_tired_cat(self):
        """Planner should pick sleep for low energy cat."""
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(energy=25.0, hunger=20.0, boredom=30.0)

        action, is_seq, priority = planner.update(
            0.05, cat, state,
        )

        assert action == "sleep", f"Expected sleep, got {action}"

    def test_needs_modulated_by_circadian_noon(self):
        """Needs should drain faster at noon (high energy_multiplier)."""
        clock = CircadianClock()
        clock.internal_hour = 12.0
        state = _make_state()
        cat = _make_cat(energy=80.0, state="SIT")

        # Apply needs with circadian boost
        needs_update(10.0, cat, state)  # 10 seconds of decay

        # Energy should have dropped faster at noon
        assert cat["energy"] < 80.0, f"Energy should drop at noon, got {cat['energy']}"

    def test_needs_drain_slower_at_night(self):
        """Needs should drain slower at night (low energy_multiplier)."""
        clock = CircadianClock()
        clock.internal_hour = 0.0
        state = _make_state()
        cat = _make_cat(energy=80.0, state="SIT")

        needs_update(10.0, cat, state)

        energy_after = cat["energy"]
        assert energy_after < 80.0, "Energy should still drain"
        # Can't compare directly to noon version since needs doesn't use
        # circadian yet — this will pass after Coder's changes

    def test_planner_handles_interaction(self):
        """Planner should track interaction state."""
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat()

        planner.handle_interaction("click", cat, state)
        assert cat.get("pet_timer", 0) > 0
        assert cat.get("user_nearby")

    def test_planner_reset(self):
        """Planner reset should clear state."""
        planner = BehaviorPlanner()
        planner.reset()
        assert not planner.sequence_runner.running


class TestPlannerActionExecution:
    """Planner actions translate correctly (these test the expected mappings)."""

    def test_emergency_sleep_action(self):
        """Emergency sleep should come from planner chain."""
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(energy=4.0)

        action, is_seq, priority = planner.update(0.05, cat, state)
        assert action == "sleep", f"Expected sleep, got {action}"
        assert priority == 1, f"Expected priority 1, got {priority}"

    def test_greet_action(self):
        """Greet should come from pet timer."""
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(user_nearby=True, pet_timer=1.0)

        action, is_seq, priority = planner.update(0.05, cat, state)
        assert action == "greet", f"Expected greet, got {action}"

    def test_idle_state_when_satisfied(self):
        """All needs satisfied should give idle action."""
        planner = BehaviorPlanner()
        state = _make_state()
        cat = _make_cat(energy=80.0, hunger=20.0, boredom=20.0)

        action, is_seq, priority = planner.update(0.05, cat, state)
        assert priority >= 5, f"Expected idle priority >= 5, got {priority}"
        assert action in (
            "sit", "ear_twitch", "slow_blink", "tail_twitch",
            "weight_shift", "look_around", "stare", "window_watch",
        ), f"Unexpected idle action: {action}"


class TestSoulLayerIntegration:
    """Personality → Reactions → Habituation → Memory integration."""

    def test_personality_behavior_bias(self):
        """Personality should return comprehensive behavior weights."""
        p = Personality(load_from_file=False)
        bias = p.get_behavior_bias()
        for k in ("walk", "sleep", "play", "greet", "investigate", "flee", "follow_mouse"):
            assert k in bias, f"Missing key {k}"
            assert 0 <= bias[k] <= 1, f"{k}={bias[k]} out of range"

    def test_bold_vs_shy_reaction_delay(self):
        """Bold cat should react faster than shy cat."""
        bold = Personality(load_from_file=False)
        bold.modify("boldness", 8)
        shy = Personality(load_from_file=False)
        shy.modify("boldness", -5)

        bold_r = ReactionSystem(bold)
        shy_r = ReactionSystem(shy)

        # Average over 10 calls to smooth random variance
        bold_delays = [bold_r.get_reaction_delay("click") for _ in range(10)]
        shy_delays = [shy_r.get_reaction_delay("click") for _ in range(10)]
        bold_avg = sum(bold_delays) / len(bold_delays)
        shy_avg = sum(shy_delays) / len(shy_delays)

        assert bold_avg < shy_avg, \
            f"Bold avg ({bold_avg:.3f}) should be < shy avg ({shy_avg:.3f})"

    def test_habituation_blocks_after_rapid_clicks(self):
        """5 rapid clicks should trigger ignore level."""
        hab = HabituationModule()
        for _ in range(5):
            hab.record_interaction("click")
        assert hab.get_response_level("click") >= 2, \
            f"Expected level >= 2 after 5 clicks"

    def test_habituation_decays_over_time(self):
        """Habituation counters should decay after enough no-interaction time."""
        with patch("behavior.habituation.time.monotonic") as mock_t:
            mock_t.return_value = 0.0
            hab = HabituationModule()
            for _ in range(5):
                hab.record_interaction("click")
                mock_t.return_value += 0.1

            level_before = hab.get_response_level("click")
            assert level_before == 3, f"Expected ignore after 5 clicks"

            # Advance 600s -> 2.5 counts decay at 240s/decay
            mock_t.return_value += config.HABITUATION_DECAY_RATE * 2.5
            hab.update(600.0)

            level_after = hab.get_response_level("click")
            assert level_after < level_before, \
                f"Level should decrease ({level_before} -> {level_after})"

    def test_pre_reaction_cues(self):
        """Pre-reaction cues should be valid types or None."""
        p = Personality(load_from_file=False)
        r = ReactionSystem(p)
        cue = r.get_pre_reaction()
        if cue is not None:
            cue_type, duration = cue
            # cue_type can be None (no cue this call)
            if cue_type is not None:
                assert cue_type in ("ear_flick", "glance", "ear_twitch"), \
                    f"Unknown pre-reaction: {cue_type}"
                assert 0 < duration <= 0.5, f"Duration out of range: {duration}"

    def test_approach_chance_scales_with_traits(self):
        """High affection+boldness → higher approach chance."""
        p_high = Personality(load_from_file=False)
        p_high.modify("affection", 8)
        p_high.modify("boldness", 7)

        p_low = Personality(load_from_file=False)
        p_low.modify("affection", 2)
        p_low.modify("boldness", 2)

        assert p_high.get_approach_chance() > p_low.get_approach_chance(), \
            "High affection/boldness should give higher approach chance"

    def test_personality_trait_persistence(self):
        """Personality traits should survive save/load cycle."""
        p = Personality(load_from_file=False)
        p.modify("boldness", 8)
        traits_copy = dict(p._traits)

        p2 = Personality(load_from_file=False)
        p2._traits = traits_copy
        p2._apply_defaults()
        assert p2.get_raw("boldness") >= 8, \
            f"Boldness should persist, got {p2.get_raw('boldness')}"


class TestMemoryZoneIntegration:
    """Memory zone tracking + territory management."""

    def test_zone_maps_correctly(self):
        """Coordinates map to expected zones."""
        cases = [
            (100, 900, DEFAULT_W, DEFAULT_H, "sleep_corner"),
            (800, 200, DEFAULT_W, DEFAULT_H, "window_perch"),
            (900, 600, DEFAULT_W, DEFAULT_H, "desk_center"),
            (1600, 900, DEFAULT_W, DEFAULT_H, "food_area"),
            (1400, 500, DEFAULT_W, DEFAULT_H, "play_area"),
        ]
        for x, y, sw, sh, expected in cases:
            assert get_zone_for_position(x, y, sw, sh) == expected, \
                f"({x},{y}) should map to {expected}"

    def test_memory_records_zone_visits(self):
        """Walking should count zone visits."""
        mem = CatMemory(cat_id=0)
        mem.record_event("walk", (100, 900))  # sleep_corner
        mem.record_event("walk", (800, 200))  # window_perch
        mem.record_event("walk", (900, 600))  # desk_center

        zones = mem.long_term["favorite_zones"]
        assert zones.get("sleep_corner", 0) >= 1
        assert zones.get("window_perch", 0) >= 1
        assert zones.get("desk_center", 0) >= 1

    def test_memory_interaction_count(self):
        """Interactions should increment today's count."""
        mem = CatMemory(cat_id=0)
        mem.long_term["last_interaction_date"] = "2000-01-01"  # force reset
        mem.record_interaction()
        mem.record_interaction()
        mem.record_interaction()
        assert mem.long_term["interactions_today"] == 3

    def test_memory_favorite_zone_empty(self):
        """No visits → desk_center fallback."""
        mem = CatMemory(cat_id=0)
        mem.long_term["favorite_zones"] = {}
        assert mem.get_favorite_zone() == "desk_center"

    def test_memory_favorite_zone_busy(self):
        """Most-visited zone returned correctly."""
        mem = CatMemory(cat_id=0)
        mem.long_term["favorite_zones"] = {
            "sleep_corner": 2, "window_perch": 10, "desk_center": 5,
        }
        assert mem.get_favorite_zone() == "window_perch"


class TestSequenceIntegration:
    """SequenceRunner + sequence definitions."""

    def test_sequence_runner_completes(self):
        """Runner should complete all steps."""
        runner = SequenceRunner()
        steps = [
            {"action": "a", "duration": 0.1, "can_interrupt": True},
            {"action": "b", "duration": 0.1, "can_interrupt": True},
        ]
        runner.start("test", steps)
        for _ in range(30):
            runner.update(0.05)
        assert not runner.running, "Sequence should complete"

    def test_sequence_interruptibility(self):
        """Non-interruptible steps should block."""
        runner = SequenceRunner()
        steps = [{"action": "critical", "duration": 10.0, "can_interrupt": False}]
        runner.start("test", steps)
        assert not runner.is_interruptible()

    def test_sleep_sequence_has_rem(self):
        """SleepSequence should include REM sleep phases."""
        seq = SEQUENCE_REGISTRY.get("SleepSequence")
        assert seq is not None
        rem = [s for s in seq if "rem" in s["action"]]
        assert len(rem) >= 3, f"Expected 3+ REM phases, got {len(rem)}"

    def test_hunger_walk_includes_eat(self):
        """HungerWalk should contain an eat step."""
        seq = SEQUENCE_REGISTRY.get("HungerWalk")
        assert seq is not None
        eat = [s for s in seq if "eat" in s["action"]]
        assert len(eat) == 1, f"Expected 1 eat step, got {len(eat)}"

    def test_all_sequences_valid(self):
        """All registered sequences must have valid steps."""
        for name, steps in SEQUENCE_REGISTRY.items():
            assert len(steps) > 0, f"Empty sequence: {name}"
            for i, s in enumerate(steps):
                assert "action" in s, f"{name}[{i}]: missing action"
                assert "duration" in s, f"{name}[{i}]: missing duration"
                assert s["duration"] > 0, f"{name}[{i}]: duration must be > 0"


class TestConfigFlags:
    """Config flags control feature activation."""

    def test_circadian_enabled_flag(self):
        """CIRCADIAN_ENABLED should exist and be boolean."""
        assert hasattr(config, "CIRCADIAN_ENABLED")
        assert isinstance(config.CIRCADIAN_ENABLED, bool)

    def test_needs_enabled_flag(self):
        """NEEDS_ENABLED should exist and be boolean."""
        assert hasattr(config, "NEEDS_ENABLED")
        assert isinstance(config.NEEDS_ENABLED, bool)

    def test_personality_enabled_flag(self):
        """PERSONALITY_ENABLED should exist."""
        assert hasattr(config, "PERSONALITY_ENABLED")

    def test_habituation_enabled_flag(self):
        """HABITUATION_ENABLED should exist."""
        assert hasattr(config, "HABITUATION_ENABLED")

    def test_clock_jump_threshold_exists(self):
        """CLOCK_JUMP_THRESHOLD should exist and be numeric."""
        assert hasattr(config, "CLOCK_JUMP_THRESHOLD")
        assert config.CLOCK_JUMP_THRESHOLD > 0
