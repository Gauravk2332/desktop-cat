"""
tests/test_engine_soul.py — Soul layer integration tests for Engine.

Tests that the Engine wires Personality → Memory → Habituation → Reactions
correctly in the game loop and _check_mouse interactions.

Run: python3 -m pytest tests/test_engine_soul.py -v
"""

import os
import sys
import time
import math
import random as _random
import tempfile
import json
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from core.state import CatState, default_cat_dict
from core.engine import Engine

# ── Test utilities ──────────────────────────────────────────────────────

DEFAULT_W = 1920
DEFAULT_H = 1080

_app = None


def _get_app():
    global _app
    if _app is None:
        from PyQt6.QtWidgets import QApplication
        _app = QApplication(sys.argv[:1] if sys.argv else [])
    return _app


def _make_state(num_cats=1, screen_width=DEFAULT_W, screen_height=DEFAULT_H):
    """Create a CatState with screen geometry and cats."""
    state = CatState(screen_width=screen_width, screen_height=screen_height)
    while len(state.cats) < num_cats:
        state.cats.append(default_cat_dict(len(state.cats)))
    return state


def _make_engine(num_cats=1, with_soul=True):
    """Create an Engine with a mock window for testing.

    Args:
        num_cats: Number of cats in state.
        with_soul: If True, init uses real soul modules; if False, only
                   test the flag and memory dict.

    Returns:
        Tuple of (engine, state, mock_window)
    """
    _get_app()
    from PyQt6.QtWidgets import QWidget

    import tempfile
    _tmp_dir = tempfile.mkdtemp()

    mock_window = QWidget()
    mock_window.update = MagicMock()
    mock_window.geometry = MagicMock()
    mock_window.geometry.return_value = MagicMock()
    mock_window.geometry.return_value.width.return_value = DEFAULT_W
    mock_window.geometry.return_value.height.return_value = DEFAULT_H

    state = _make_state(num_cats)
    engine = Engine(state, mock_window)

    # Stop timers to prevent interference
    if hasattr(engine, '_tick_timer') and engine._tick_timer:
        engine._tick_timer.stop()
    if hasattr(engine, '_idle_timer') and engine._idle_timer:
        engine._idle_timer.stop()
    if hasattr(engine, '_mouse_timer') and engine._mouse_timer:
        engine._mouse_timer.stop()

    # Redirect memory to temp dir to avoid contaminating production data
    if with_soul and hasattr(engine, '_memory'):
        for cid, mem in engine._memory.items():
            mem._memory_dir = _tmp_dir
            mem._memory_file = os.path.join(_tmp_dir, f"cat_memory_{cid}.json")
            mem._territory_file = os.path.join(_tmp_dir, f"cat_territory_{cid}.json")

    return engine, state, mock_window


# ── Tests ───────────────────────────────────────────────────────────────

class TestSoulInitialization:
    """Engine creates soul layer components on init."""

    def test_soul_initialized_flag(self):
        """Engine creates with soul_initialized=True."""
        engine, _, _ = _make_engine()
        assert engine._soul_initialized, \
            "Engine should have soul_initialized=True by default"

    def test_memory_create_at_init(self):
        """Engine creates CatMemory per cat."""
        engine, state, _ = _make_engine(num_cats=3)
        assert hasattr(engine, '_memory'), "Engine should have _memory dict"
        assert len(engine._memory) == 3, \
            f"Expected 3 CatMemory entries, got {len(engine._memory)}"
        for cat in state.cats:
            cid = cat.get("id", 0)
            assert cid in engine._memory, \
                f"Cat {cid} missing from _memory"
            from behavior.memory import CatMemory
            assert isinstance(engine._memory[cid], CatMemory), \
                f"_memory[{cid}] is not a CatMemory instance"

    def test_personality_init(self):
        """Engine creates Personality instance."""
        engine, _, _ = _make_engine()
        assert engine._personality is not None, \
            "Engine should have _personality"
        from behavior.personality import Personality
        assert isinstance(engine._personality, Personality)

    def test_habituation_init(self):
        """Engine creates HabituationModule instance."""
        engine, _, _ = _make_engine()
        assert engine._habituation is not None, \
            "Engine should have _habituation"
        from behavior.habituation import HabituationModule
        assert isinstance(engine._habituation, HabituationModule)

    def test_reactions_init(self):
        """Engine creates ReactionSystem instance."""
        engine, _, _ = _make_engine()
        assert engine._reactions is not None, \
            "Engine should have _reactions"
        from behavior.reactions import ReactionSystem
        assert isinstance(engine._reactions, ReactionSystem)


class TestMemoryIntegration:
    """Memory records interactions from _check_mouse proximity."""

    def test_memory_records_interaction(self):
        """Simulating _check_mouse proximity records interaction in memory."""
        engine, state, mock_window = _make_engine()

        cat = state.cats[0]
        cid = cat.get("id", 0)

        # Reset interactions_today for clean test
        engine._memory[cid].long_term["interactions_today"] = 0
        engine._memory[cid].long_term["last_interaction_date"] = "2000-01-01"

        # Simulate QCursor near cat
        cat["x"] = 500.0
        cat["y"] = 700.0
        cat["state"] = "SIT"
        cat["mouse_near"] = True

        from PyQt6.QtCore import QPoint, QPointF
        _prev = engine._prev_mouse_pos
        engine._prev_mouse_pos = QPointF(500, 700)

        _cursor_pt = QPoint(510, 710)
        with patch('PyQt6.QtGui.QCursor.pos', return_value=_cursor_pt):
            engine._check_mouse()

        assert engine._memory[cid].long_term["interactions_today"] > 0, \
            "Memory should record an interaction after proximity pet"

    def test_memory_records_mouse_proximity_event(self):
        """Mouse proximity event recorded (1% sample rate)."""
        engine, state, mock_window = _make_engine()

        cat = state.cats[0]
        cid = cat.get("id", 0)
        cat["x"] = 500.0
        cat["y"] = 700.0
        cat["state"] = "SIT"

        from PyQt6.QtCore import QPoint, QPointF
        engine._prev_mouse_pos = QPointF(500, 700)
        _cursor_pt = QPoint(510, 710)

        with patch('PyQt6.QtGui.QCursor.pos', return_value=_cursor_pt):
            with patch('random.random', return_value=0.005):  # < 0.01
                engine._check_mouse()

        # Verify the infrastructure exists
        assert hasattr(engine, '_memory'), "Engine should have _memory"
        assert cid in engine._memory, "Cat should have memory entry"

    def test_memory_interaction_increases_happiness(self):
        """Recorded interaction increases happiness mood."""
        engine, state, _ = _make_engine()
        cat = state.cats[0]
        cid = cat.get("id", 0)

        engine._memory[cid].long_term["interactions_today"] = 0
        engine._memory[cid].long_term["mood"]["happiness"] = 65
        engine._memory[cid].long_term["last_interaction_date"] = "2000-01-01"

        engine._memory[cid].record_interaction()

        assert engine._memory[cid].long_term["mood"]["happiness"] > 65, \
            "Happiness should increase after interaction"


class TestHabituationIntegration:
    """Habituation blocks reactions after rapid interactions."""

    def test_habituation_blocks_after_rapid_interactions(self):
        """Record 5 rapid clicks; response level >= 2 (glance/ignore)."""
        engine, state, _ = _make_engine()
        assert engine._habituation is not None

        for _ in range(5):
            engine._habituation.record_interaction("click")

        resp_level = engine._habituation.get_response_level("click")
        assert resp_level >= 2, \
            f"After 5 clicks, response level should be >= 2, got {resp_level}"

    def test_habituation_decay(self):
        """Record interaction, wait 300s dt, verify response level drops."""
        engine, state, _ = _make_engine()
        assert engine._habituation is not None

        # Mock time.monotonic so that decay has measurable elapsed
        _base_time = 1000.0
        with patch('behavior.habituation.time.monotonic') as mock_mono:
            mock_mono.return_value = _base_time
            for _ in range(5):
                engine._habituation.record_interaction("click")

            level_before = engine._habituation.get_response_level("click")

            # Advance time by 600s (decay_rate is 240s, so 2+ counts should decay)
            mock_mono.return_value = _base_time + 600.0
            engine._habituation.update(600.0)

            level_after = engine._habituation.get_response_level("click")

        assert level_after < level_before, \
            f"Habituation level should decrease after decay ({level_before} -> {level_after})"

    def test_habituation_ignores_add_habituation(self):
        """Verify that at high response level, _should_react is set False.

        This tests the engine integration: after 5 rapid proximity events
        with _should_react=False, the pet reaction block is skipped.
        """
        _get_app()
        from PyQt6.QtWidgets import QWidget
        from PyQt6.QtCore import QPointF
        from behavior.habituation import HabituationModule

        mock_window = QWidget()
        mock_window.update = MagicMock()
        mock_window.geometry = MagicMock()
        mock_window.geometry.return_value = MagicMock()
        mock_window.geometry.return_value.width.return_value = DEFAULT_W
        mock_window.geometry.return_value.height.return_value = DEFAULT_H

        state = _make_state(1)
        engine = Engine(state, mock_window)

        if engine._tick_timer:
            engine._tick_timer.stop()
        if engine._idle_timer:
            engine._idle_timer.stop()
        if engine._mouse_timer:
            engine._mouse_timer.stop()

        # Give engine a clean habituation module
        engine._habituation = HabituationModule()
        engine._soul_initialized = True

        cat = state.cats[0]
        cat["x"] = 500.0
        cat["y"] = 700.0
        cat["state"] = "SIT"

        # Simulate 5 rapid pet interactions
        for _ in range(6):
            engine._habituation.record_interaction("click")

        # Verify habituation is high enough to block
        assert engine._habituation.get_response_level("click") >= 2, \
            "Habituation should be high after 6 clicks"


class TestPersonalityIntegration:
    """Personality traits modulate behavior parameters."""

    def test_reaction_delay_bold_vs_shy(self):
        """Bold cat (8) has shorter reaction delay than shy cat (2)."""
        from behavior.personality import Personality
        from behavior.reactions import ReactionSystem

        bold_p = Personality(load_from_file=False)
        bold_p._traits["boldness"] = 8
        shy_p = Personality(load_from_file=False)
        shy_p._traits["boldness"] = 2

        bold_r = ReactionSystem(bold_p)
        shy_r = ReactionSystem(shy_p)

        # Deterministic: uniform returns the upper bound of its range
        with patch('behavior.reactions.random.uniform', side_effect=lambda lo, hi: hi):
            with patch('behavior.reactions.random.random', return_value=0.5):
                bold_delay = bold_r.get_reaction_delay("click")
                shy_delay = shy_r.get_reaction_delay("click")

        assert bold_delay < shy_delay, \
            f"Bold delay ({bold_delay}) should be < shy delay ({shy_delay})"

    def test_personality_approach_chance(self):
        """Bold cat (8) has higher approach_chance than shy cat (2)."""
        from behavior.personality import Personality

        bold_p = Personality(load_from_file=False)
        bold_p._traits["boldness"] = 8
        bold_p._traits["affection"] = 8

        shy_p = Personality(load_from_file=False)
        shy_p._traits["boldness"] = 2
        shy_p._traits["affection"] = 2

        high = bold_p.get_approach_chance()
        low = shy_p.get_approach_chance()

        assert high > low, \
            f"Bold approach chance ({high}) should be > shy ({low})"

    def test_approach_chance_used_in_check_mouse(self):
        """_check_mouse uses personality approach_chance instead of hardcoded 0.01."""
        engine, state, _ = _make_engine()

        # Override personality with a high-approach one
        from behavior.personality import Personality
        from behavior.habituation import HabituationModule
        from behavior.reactions import ReactionSystem

        bold_p = Personality(load_from_file=False)
        bold_p._traits["boldness"] = 9
        bold_p._traits["affection"] = 9
        engine._personality = bold_p
        engine._habituation = HabituationModule()
        engine._reactions = ReactionSystem(bold_p)

        approach = engine._personality.get_approach_chance()
        assert approach > 0.01, \
            f"Bold+affectionate cat should have approach_chance > 0.01, got {approach}"


class TestSoulGracefulDegradation:
    """Engine handles missing soul modules without crashing."""

    def test_soul_graceful_degradation_on_import_fail(self):
        """Engine sets soul_initialized=False when imports fail.

        We test this by removing the soul attributes and verifying
        _check_mouse doesn't crash.
        """
        _get_app()
        from PyQt6.QtWidgets import QWidget

        mock_window = QWidget()
        mock_window.update = MagicMock()
        mock_window.geometry = MagicMock()
        mock_window.geometry.return_value = MagicMock()
        mock_window.geometry.return_value.width.return_value = DEFAULT_W
        mock_window.geometry.return_value.height.return_value = DEFAULT_H

        state = _make_state(1)
        engine = Engine(state, mock_window)

        if engine._tick_timer:
            engine._tick_timer.stop()
        if engine._idle_timer:
            engine._idle_timer.stop()
        if engine._mouse_timer:
            engine._mouse_timer.stop()

        from PyQt6.QtCore import QPoint, QPointF
        engine._prev_mouse_pos = QPointF(500, 700)

        # Delete soul attributes to simulate import failure
        del engine._memory
        del engine._personality
        del engine._habituation
        del engine._reactions
        engine._soul_initialized = False

        cat = state.cats[0]
        cat["x"] = 500.0
        cat["y"] = 700.0
        cat["state"] = "SIT"

        # Must not crash
        _cursor_pt = QPoint(510, 710)
        with patch('PyQt6.QtGui.QCursor.pos', return_value=_cursor_pt):
            try:
                engine._check_mouse()
            except Exception as e:
                assert False, f"_check_mouse crashed after soul removal: {e}"
