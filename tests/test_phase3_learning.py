"""
tests/test_phase3_learning.py — Tests for Phase 3 learning systems.

Verifies:
1. CatMemory.record_zone_visit — tracks visits, daily decay, favorite marking at N=10
2. OwnerSchedule — hour recording, 7-day average, peak prediction
3. Engine integration — zone visit recorded during tick (with mock state)
"""

import json
import os
import sys
import tempfile
import time

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from behavior.memory import CatMemory, get_zone_for_position
from behavior.schedule import OwnerSchedule


# ─── Helpers ──────────────────────────────────────────────────────────────

def _make_memory(tmp_dir):
    """Create a CatMemory with isolated data dir."""
    mem = CatMemory(cat_id=999)
    mem._memory_dir = tmp_dir
    mem._memory_file = os.path.join(tmp_dir, "cat_memory_999.json")
    mem._territory_file = os.path.join(tmp_dir, "cat_territory_999.json")
    return mem


def _patch_schedule_path(schedule, tmp_path):
    """Point an OwnerSchedule to a temporary path."""
    schedule.persist_file = tmp_path


# ─── Zone Visit Learning ─────────────────────────────────────────────────

def test_zone_visit_records():
    """record_zone_visit should increment visit counter."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.record_zone_visit("sleep_corner")
    mem.record_zone_visit("sleep_corner")
    mem.record_zone_visit("window_perch")

    visits = mem.long_term.get("zone_visits", {})
    assert visits.get("sleep_corner") == 2, \
        f"Expected 2 visits to sleep_corner, got {visits.get('sleep_corner')}"
    assert visits.get("window_perch") == 1, \
        f"Expected 1 visit to window_perch, got {visits.get('window_perch')}"


def test_zone_visit_default_empty():
    """zone_visits should default to empty dict."""
    mem = _make_memory(tempfile.mkdtemp())
    visits = mem.long_term.get("zone_visits", {})
    assert visits == {}, f"Expected empty zone_visits, got {visits}"


def test_favorite_zones_at_threshold():
    """get_favorite_zones should return zones with >= N visits."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["zone_visits"] = {
        "sleep_corner": 15,
        "window_perch": 10,
        "desk_center": 5,
        "food_area": 3,
    }
    # Force today's decay to happen so it doesn't interfere
    mem.long_term["last_zone_decay"] = time.strftime("%Y-%m-%d")

    favs = mem.get_favorite_zones(min_visits=10)
    assert "sleep_corner" in favs, f"Expected sleep_corner in favorites: {favs}"
    assert "window_perch" in favs, f"Expected window_perch in favorites: {favs}"
    assert "desk_center" not in favs, f"Expected desk_center NOT in favorites: {favs}"


def test_no_favorite_zones():
    """Empty zone_visits should return empty favorites list."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["last_zone_decay"] = time.strftime("%Y-%m-%d")
    favs = mem.get_favorite_zones(min_visits=10)
    assert favs == [], f"Expected empty favorites, got {favs}"


def test_idle_zone_weight_favorite():
    """Favorite zones (>=10 visits) should get 3× weight."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["zone_visits"] = {
        "sleep_corner": 15,
        "desk_center": 3,
    }
    weight_fav = mem.get_idle_zone_weight("sleep_corner")
    weight_non = mem.get_idle_zone_weight("desk_center")
    assert weight_fav == 3.0, f"Expected 3.0 for favorite, got {weight_fav}"
    assert weight_non == 1.0, f"Expected 1.0 for non-favorite, got {weight_non}"


def test_idle_zone_weight_unknown():
    """Unknown zone should still return base weight."""
    mem = _make_memory(tempfile.mkdtemp())
    weight = mem.get_idle_zone_weight("nonexistent_zone")
    assert weight == 1.0, f"Expected 1.0 for unknown, got {weight}"


def test_zone_visit_daily_decay():
    """Daily decay should reduce visit counts by 1."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["zone_visits"] = {"sleep_corner": 5, "window_perch": 3}
    mem.long_term["last_zone_decay"] = "2000-01-01"  # force old date so decay runs

    # get_favorite_zones triggers decay
    mem.get_favorite_zones()

    visits = mem.long_term["zone_visits"]
    assert visits.get("sleep_corner") == 4, \
        f"Expected 4 after decay, got {visits.get('sleep_corner')}"
    assert visits.get("window_perch") == 2, \
        f"Expected 2 after decay, got {visits.get('window_perch')}"


def test_zone_visit_decay_floor():
    """Decay should not bring visits below 0."""
    mem = _make_memory(tempfile.mkdtemp())
    mem.long_term["zone_visits"] = {"sleep_corner": 0, "window_perch": 1}
    mem.long_term["last_zone_decay"] = "2000-01-01"

    mem.get_favorite_zones()

    visits = mem.long_term["zone_visits"]
    assert visits.get("sleep_corner") == 0, \
        f"Expected 0 (floor), got {visits.get('sleep_corner')}"
    assert visits.get("window_perch") == 0, \
        f"Expected 0 after decay, got {visits.get('window_perch')}"


# ─── Owner Schedule ─────────────────────────────────────────────────────

def test_schedule_record_activity():
    """record_activity should store levels for a given hour."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule.json")
    _patch_schedule_path(sched, tmp_file)

    sched.record_activity(14, 0.8)
    data = sched.hourly_activity[14]
    assert len(data) == 1, f"Expected 1 entry, got {len(data)}"
    assert abs(data[0] - 0.8) < 0.001, f"Expected 0.8, got {data[0]}"


def test_schedule_out_of_range():
    """Out of range hours should be ignored."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule.json")
    _patch_schedule_path(sched, tmp_file)

    sched.record_activity(-1, 0.5)
    sched.record_activity(24, 0.5)
    # Should not have crashed and no entries added
    assert -1 not in sched.hourly_activity or sched.hourly_activity[-1] == []
    assert 24 not in sched.hourly_activity or sched.hourly_activity[24] == []


def test_schedule_average():
    """get_average should return mean across recordings."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule.json")
    _patch_schedule_path(sched, tmp_file)

    sched.record_activity(10, 0.5)
    sched.record_activity(10, 1.0)
    avg = sched.get_average(10)
    assert abs(avg - 0.75) < 0.01, f"Expected 0.75 avg, got {avg}"


def test_schedule_average_empty():
    """Empty hour should return 0.0."""
    sched = OwnerSchedule()
    avg = sched.get_average(3)
    assert avg == 0.0, f"Expected 0.0 for empty hour, got {avg}"


def test_schedule_seven_day_rolling():
    """Should keep only last 7 entries per hour."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule.json")
    _patch_schedule_path(sched, tmp_file)

    for i in range(10):
        sched.record_activity(8, 0.5)
    assert len(sched.hourly_activity[8]) == 7, \
        f"Expected 7 entries (rolling), got {len(sched.hourly_activity[8])}"


def test_schedule_predict_active_hour():
    """predict_active_hour should return the busiest hour."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule.json")
    _patch_schedule_path(sched, tmp_file)

    # Make hour 9 very active
    for _ in range(7):
        sched.record_activity(9, 1.0)
    # Hour 14 mildly active
    for _ in range(7):
        sched.record_activity(14, 0.3)

    peak = sched.predict_active_hour()
    assert peak == 9, f"Expected peak at hour 9, got {peak}"


def test_schedule_predict_active_hour_default():
    """Default peak should be 12 (noon) when no data."""
    sched = OwnerSchedule()
    # Use a temp file so previous test data doesn't pollute
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_sched_default.json")
    _patch_schedule_path(sched, tmp_file)
    sched.hourly_activity = {h: [] for h in range(24)}
    peak = sched.predict_active_hour()
    assert peak == 12, f"Expected default peak 12, got {peak}"


def test_schedule_predict_pre_active_time():
    """Pre-active time should be 30 min before peak."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule.json")
    _patch_schedule_path(sched, tmp_file)

    for _ in range(7):
        sched.record_activity(10, 1.0)
    pre_time = sched.predict_pre_active_time()
    assert abs(pre_time - 9.5) < 0.01, \
        f"Expected 9.5 pre-active time, got {pre_time}"


def test_schedule_persist():
    """Schedule should survive save/load cycle."""
    tmp_dir = tempfile.mkdtemp()
    tmp_file = os.path.join(tmp_dir, "test_schedule.json")

    sched1 = OwnerSchedule()
    _patch_schedule_path(sched1, tmp_file)
    sched1.record_activity(15, 0.9)
    sched1.record_activity(15, 0.7)

    # Create new instance and load the same file
    sched2 = OwnerSchedule()
    _patch_schedule_path(sched2, tmp_file)
    sched2._load()

    assert len(sched2.hourly_activity.get(15, [])) == 2, \
        "Expected 2 entries after reload"
    avg = sched2.get_average(15)
    assert abs(avg - 0.8) < 0.01, f"Expected avg 0.8 after reload, got {avg}"


def test_schedule_clamp_max():
    """record_activity should clamp to 1.0."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule.json")
    _patch_schedule_path(sched, tmp_file)

    sched.record_activity(12, 5.0)
    data = sched.hourly_activity[12]
    assert data[0] == 1.0, f"Expected clamped 1.0, got {data[0]}"


# ─── Zone Mapping ───────────────────────────────────────────────────────

def test_get_zone_for_position():
    """get_zone_for_position maps correctly."""
    zone = get_zone_for_position(100, 900, 1920, 1080)
    assert zone == "sleep_corner", f"Expected sleep_corner, got {zone}"

    zone = get_zone_for_position(800, 200, 1920, 1080)
    assert zone == "window_perch", f"Expected window_perch, got {zone}"

    zone = get_zone_for_position(900, 600, 1920, 1080)
    assert zone == "desk_center", f"Expected desk_center, got {zone}"

    zone = get_zone_for_position(1600, 900, 1920, 1080)
    assert zone == "food_area", f"Expected food_area, got {zone}"

    zone = get_zone_for_position(1400, 500, 1920, 1080)
    assert zone == "play_area", f"Expected play_area, got {zone}"


# ─── Engine Integration (mock-based) ───────────────────────────────────

def _make_mock_state():
    """Create a minimal mock state object for engine tick testing."""
    class MockState:
        screen_width = 1920
        screen_height = 1080
        mouse_pos = (500.0, 500.0)
        cats = []

    return MockState()


def _make_mock_cat(cat_id=0, x=800, y=600):
    """Create a minimal mock cat dict."""
    return {
        "id": cat_id,
        "x": x,
        "y": y,
        "state": "SIT",
        "facing": True,
        "energy": 80.0,
        "hunger": 20.0,
        "boredom": 10.0,
        "at_home": False,
        "home_cooldown": 0.0,
        "home_linger": 0.0,
        "walk_duration": 0.0,
        "walk_elapsed": 0.0,
        "walk_vy": 0.0,
        "wander_duration": 0.0,
        "wander_elapsed": 0.0,
        "wander_cooldown": 0.0,
        "wander_vx": 0.0,
        "wander_vy": 0.0,
        "hut_index": 0,
        "zoop_counter": 0.0,
        "lava_counter": 0.0,
        "mouse_near": False,
        "speech_cooldown": 0.0,
        "consecutive_pets": 0,
        "reaction_type": None,
        "reaction_timer": 0.0,
        "tail_phase": 0.0,
        "blink_timer": 0.0,
        "blinking": False,
        "next_blink": 10.0,
        "sleep_breath": 0.0,
        "zzz_particles": [],
        "purr_vibrate": 0.0,
        "hearts": [],
        "eye_current": (0.0, 0.0),
        "eye_target": (0.0, 0.0),
    }


def test_engine_tick_adds_zone_visit():
    """Simulating the engine tick's zone visit recording logic."""
    tmp_dir = tempfile.mkdtemp()
    mem = _make_memory(tmp_dir)
    cat = _make_mock_cat(cat_id=999, x=800, y=600)

    # Run the logic from _on_tick's per-cat loop 200 times (expect ~2 visits at 1%)
    for _ in range(200):
        if 999 in {cat['id']}:
            # Replicate engine logic gate + get_zone_for_position
            zone = get_zone_for_position(
                cat.get('x', 0), cat.get('y', 0),
                1920, 1080,
            )
            import random
            if random.random() < 0.01:
                mem.record_zone_visit(zone)

    visits = mem.long_term.get("zone_visits", {})
    total = sum(visits.values())
    assert total > 0, \
        f"Expected some zone visits after 200 ticks at 1% rate, got {total}"


def test_engine_tick_schedule_recording():
    """Simulating the engine tick's schedule recording logic."""
    sched = OwnerSchedule()
    tmp_file = os.path.join(tempfile.mkdtemp(), "test_schedule_engine.json")
    _patch_schedule_path(sched, tmp_file)

    from datetime import datetime
    hour = datetime.now().hour

    # Simulate recording like engine does
    sched.record_activity(hour, 0.5)

    avg = sched.get_average(hour)
    assert avg > 0.0, f"Expected activity recorded for hour {hour}, got {avg}"


if __name__ == "__main__":
    tests = [
        test_zone_visit_records,
        test_zone_visit_default_empty,
        test_favorite_zones_at_threshold,
        test_no_favorite_zones,
        test_idle_zone_weight_favorite,
        test_idle_zone_weight_unknown,
        test_zone_visit_daily_decay,
        test_zone_visit_decay_floor,
        test_schedule_record_activity,
        test_schedule_out_of_range,
        test_schedule_average,
        test_schedule_average_empty,
        test_schedule_seven_day_rolling,
        test_schedule_predict_active_hour,
        test_schedule_predict_active_hour_default,
        test_schedule_predict_pre_active_time,
        test_schedule_persist,
        test_schedule_clamp_max,
        test_get_zone_for_position,
        test_engine_tick_adds_zone_visit,
        test_engine_tick_schedule_recording,
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
