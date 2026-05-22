"""
tests/test_memory.py — Tests for behavior/memory.py

Verifies:
1. Short-term event deque (maxlen 20)
2. Long-term JSON persistence (atomic write)
3. Territory zone mapping
4. Activity tracking (hourly rolling average)
5. Mood changes from interactions
6. Favorite zone calculation
"""

import json
import os
import sys
import tempfile
import time

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from behavior.memory import CatMemory, get_zone_for_position
from collections import deque


def _make_memory(tmp_dir):
    """Create a CatMemory with isolated data dir."""
    mem = CatMemory(cat_id=999)
    mem._memory_dir = tmp_dir
    mem._memory_file = os.path.join(tmp_dir, "cat_memory_999.json")
    mem._territory_file = os.path.join(tmp_dir, "cat_territory_999.json")
    return mem


def test_short_term_maxlen():
    """Short-term deque should max at 20 events."""
    mem = _make_memory(tempfile.mkdtemp())
    for i in range(25):
        mem.record_event(f"event_{i}", (100, 100))
    assert len(mem.short_term) == 20, \
        f"Expected 20 events, got {len(mem.short_term)}"


def test_short_term_most_recent():
    """Short-term should keep the last 20 events."""
    mem = _make_memory(tempfile.mkdtemp())
    for i in range(25):
        mem.record_event(f"event_{i}", (100, 100))
    recent = mem.get_recent_events(3)
    assert recent[-1]["type"] == "event_24", \
        f"Expected event_24, got {recent[-1]['type']}"
    assert recent[-2]["type"] == "event_23"
    assert recent[-3]["type"] == "event_22"


def test_zone_mapping():
    """Test territory zone mapping from coordinates."""
    test_cases = [
        (100, 900, 1920, 1080, "sleep_corner"),      # bottom-left
        (800, 200, 1920, 1080, "window_perch"),       # top-center
        (900, 600, 1920, 1080, "desk_center"),        # center area
        (1600, 900, 1920, 1080, "food_area"),         # bottom-right
        (1400, 500, 1920, 1080, "play_area"),         # center-right
    ]
    for x, y, sw, sh, expected in test_cases:
        zone = get_zone_for_position(x, y, sw, sh)
        assert zone == expected, \
            f"({x},{y}) on {sw}x{sh}: expected {expected}, got {zone}"


def test_favorite_zone():
    """Most-visited zone should be returned."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["favorite_zones"] = {
        "sleep_corner": 5,
        "window_perch": 20,
        "desk_center": 3,
    }
    fav = mem.get_favorite_zone()
    assert fav == "window_perch", f"Expected window_perch, got {fav}"


def test_empty_favorite_zone():
    """Fallback when no zones recorded."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["favorite_zones"] = {}
    fav = mem.get_favorite_zone()
    assert fav == "desk_center", f"Expected desk_center fallback, got {fav}"


def test_interaction_increases_mood():
    """User interaction should increase happiness and trust."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["mood"]["happiness"] = 50
    mem.long_term["mood"]["trust"] = 60

    mem.record_interaction()

    assert mem.long_term["mood"]["happiness"] > 50, \
        f"Happiness should increase: {mem.long_term['mood']['happiness']}"
    assert mem.long_term["mood"]["trust"] > 60, \
        f"Trust should increase: {mem.long_term['mood']['trust']}"


def test_interaction_today_count():
    """Interaction count resets daily but increments correctly."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["last_interaction_date"] = "2000-01-01"  # force old date

    mem.record_interaction()
    assert mem.long_term["interactions_today"] == 1, \
        f"Expected 1 interaction, got {mem.long_term['interactions_today']}"

    mem.record_interaction()
    assert mem.long_term["interactions_today"] == 2


def test_activity_hourly():
    """Activity tracking stores rolling average."""
    mem = _make_memory(tempfile.mkdtemp())

    mem.record_activity(14, 1.0)
    val = mem.get_activity_at_hour(14)
    assert val > 0, f"Activity at hour 14 should be > 0, got {val}"
    # First recording: 0 * 0.7 + 1.0 * 0.3 = 0.3
    assert abs(val - 0.3) < 0.01, \
        f"Expected ~0.3 after first record, got {val}"


def test_activity_default_zero():
    """Default activity for unrecorded hour is 0."""
    mem = _make_memory(tempfile.mkdtemp())
    val = mem.get_activity_at_hour(3)
    assert val == 0.0, f"Expected 0.0 for unrecorded hour, got {val}"


def test_json_persistence():
    """Long-term memory saves and loads correctly."""
    tmp_dir = tempfile.mkdtemp()
    # Build paths before creating instance
    mem_file = os.path.join(tmp_dir, "cat_memory_888.json")
    terr_file = os.path.join(tmp_dir, "cat_territory_888.json")

    mem = CatMemory(cat_id=888)
    mem._memory_dir = tmp_dir
    mem._memory_file = mem_file
    mem._territory_file = terr_file
    # Reload from empty (file doesn't exist yet)
    mem.long_term = mem._load_json(mem_file, mem._default_memory())
    assert mem.long_term["mood"]["happiness"] == 65, "Default should be 65"

    # Write
    mem.long_term["mood"]["happiness"] = 88
    mem.save()

    # Read (fresh load)
    mem2 = CatMemory(cat_id=888)
    mem2._memory_dir = tmp_dir
    mem2._memory_file = mem_file
    mem2.long_term = mem2._load_json(mem2._memory_file, mem2._default_memory())
    assert mem2.long_term["mood"]["happiness"] == 88, \
        f"Expected 88 after reload, got {mem2.long_term['mood']['happiness']}"


def test_territory_stale():
    """Territory mark should be stale after max_age."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.update_territory_mark("sleep_corner")
    # Just marked — should not be stale
    assert not mem.is_territory_stale("sleep_corner", max_age=3600.0), \
        "Fresh mark should not be stale"


def test_unknown_zone_default():
    """Unknown position maps to litter_corner."""
    zone = get_zone_for_position(0, 0, 0, 0)
    assert zone == "unknown", f"Expected 'unknown' for 0-sized screen, got {zone}"


if __name__ == "__main__":
    tests = [
        test_short_term_maxlen,
        test_short_term_most_recent,
        test_zone_mapping,
        test_favorite_zone,
        test_empty_favorite_zone,
        test_interaction_increases_mood,
        test_interaction_today_count,
        test_activity_hourly,
        test_activity_default_zero,
        test_json_persistence,
        test_territory_stale,
        test_unknown_zone_default,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  [PASS] {test.__name__}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {test.__name__}: {e}")
    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
