"""
tests/test_sequences.py — Tests for behavior/sequences.py

Verifies:
1. All sequences have valid step schemas
2. SequenceRunner cycles through steps
3. Interruptibility checking
4. Sequence completion detection
5. get_progress tracking
6. Force-stop
7. Trigger registration and matching
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from behavior.sequences import (
    SEQUENCE_REGISTRY,
    SequenceRunner,
    register_trigger,
    get_best_sequence,
)


def test_all_sequences_have_valid_steps():
    """All sequences should have steps with action, duration, can_interrupt."""
    for name, steps in SEQUENCE_REGISTRY.items():
        assert len(steps) > 0, f"Sequence {name} is empty"
        for i, step in enumerate(steps):
            assert "action" in step, \
                f"{name}[{i}]: missing 'action'"
            assert "duration" in step, \
                f"{name}[{i}]: missing 'duration'"
            assert "can_interrupt" in step, \
                f"{name}[{i}]: missing 'can_interrupt'"
            assert isinstance(step["duration"], (int, float)), \
                f"{name}[{i}]: duration not numeric"
            assert step["duration"] > 0, \
                f"{name}[{i}]: duration must be > 0"
            assert isinstance(step["can_interrupt"], bool), \
                f"{name}[{i}]: can_interrupt must be bool"


def test_runner_steps_through():
    """SequenceRunner should cycle through all steps."""
    runner = SequenceRunner()
    steps = [{"action": "a", "duration": 0.1, "can_interrupt": True},
             {"action": "b", "duration": 0.1, "can_interrupt": True},
             {"action": "c", "duration": 0.1, "can_interrupt": True}]

    runner.start("test_seq", steps)
    assert runner.running
    assert runner.name == "test_seq"
    assert runner.current_action == "a"

    actions = []
    for _ in range(30):
        action = runner.update(0.05)
        if action:
            actions.append(action)

    assert not runner.running, "Sequence should have completed"
    assert actions.count("a") > 0
    assert actions.count("b") > 0
    assert actions.count("c") > 0


def test_runner_completes():
    """Runner should report completed after all steps."""
    runner = SequenceRunner()
    steps = [{"action": "x", "duration": 0.05, "can_interrupt": True}]

    runner.start("short", steps)
    assert runner.running

    for _ in range(10):
        runner.update(0.05)

    assert not runner.running, "Short sequence should have completed"


def test_interruptible_check():
    """Runner should correctly report interruptibility."""
    runner = SequenceRunner()
    steps = [{"action": "interruptible", "duration": 5.0, "can_interrupt": True},
             {"action": "critical", "duration": 5.0, "can_interrupt": False}]

    runner.start("test", steps)
    assert runner.is_interruptible(), "First step should be interruptible"

    # Advance past first step
    runner.step_timer = 5.1
    runner.update(0.0)
    assert not runner.is_interruptible(), \
        "Second step (critical) should NOT be interruptible"


def test_force_stop():
    """Force-stop should halt sequence immediately."""
    runner = SequenceRunner()
    steps = [{"action": "a", "duration": 10.0, "can_interrupt": True}]

    runner.start("test", steps)
    assert runner.running

    runner.stop()
    assert not runner.running
    assert runner.current_action == ""


def test_progress():
    """get_progress should track through 0.0-1.0."""
    runner = SequenceRunner()
    steps = [{"action": "a", "duration": 1.0, "can_interrupt": True},
             {"action": "b", "duration": 1.0, "can_interrupt": True}]

    runner.start("test", steps)
    progress = runner.get_progress()
    assert 0.0 <= progress < 0.5, \
        f"Early progress should be < 0.5, got {progress}"

    # Advance to middle
    runner.step_timer = 0.5
    progress = runner.get_progress()
    assert 0.0 < progress < 0.6, \
        f"Mid progress should be ~0.25, got {progress}"

    # Complete
    runner.step_index = len(steps)
    assert runner.get_progress() >= 1.0, \
        "Progress should be 1.0 when complete"


def test_default_sequence_runner_state():
    """Fresh SequenceRunner should not be running."""
    runner = SequenceRunner()
    assert not runner.running
    assert runner.current_action == ""
    assert runner.get_current_step() is None


def test_get_current_step():
    """get_current_step returns correct step dict."""
    runner = SequenceRunner()
    steps = [{"action": "test_action", "duration": 1.0, "can_interrupt": True}]
    runner.start("test", steps)

    step = runner.get_current_step()
    assert step is not None
    assert step["action"] == "test_action"
    assert step["duration"] == 1.0


def test_trigger_registration():
    """Triggers should register and sort by priority."""
    # Clear triggers
    from behavior.sequences import _SEQUENCE_TRIGGERS
    _SEQUENCE_TRIGGERS.clear()

    def always_true(cat, state):
        return True

    def always_false(cat, state):
        return False

    register_trigger("Contemplation", 5, always_true)
    register_trigger("TheStare", 1, always_false)

    triggers = _SEQUENCE_TRIGGERS
    assert len(triggers) == 2
    assert triggers[0][0] == 1, "Priority 1 should be first"
    assert triggers[1][0] == 5, "Priority 5 should be second"


def test_get_best_sequence():
    """get_best_sequence should return highest-priority matching sequence."""
    from behavior.sequences import _SEQUENCE_TRIGGERS
    _SEQUENCE_TRIGGERS.clear()

    def energy_low(cat, state):
        return cat.get("energy", 100) < 50

    def hunger_high(cat, state):
        return cat.get("hunger", 0) > 60

    register_trigger("SleepSequence", 3, energy_low)
    register_trigger("HungerWalk", 2, hunger_high)

    cat_energy_low_only = {"energy": 30, "hunger": 10}
    result = get_best_sequence(cat_energy_low_only, None)
    assert result is not None
    # SleepSequence has higher priority (3) than HungerWalk (2)
    # But HungerWalk at priority 2 is checked first
    # Wait — HungerWalk condition (hunger > 60) is False, so SleepSequence should match
    assert result[0]["action"] in ("lie_down",), \
        f"Expected sleep sequence, got {result[0]['action']}"


def test_high_priority_wins():
    """When both conditions match, highest priority (lowest number) wins."""
    from behavior.sequences import _SEQUENCE_TRIGGERS
    _SEQUENCE_TRIGGERS.clear()

    def always_true(cat, state):
        return True

    register_trigger("PlayBurst", 5, always_true)
    register_trigger("TheStare", 1, always_true)  # Higher priority

    result = get_best_sequence({}, None)
    assert result is not None
    assert result[0]["action"] == "freeze", \
        f"Expected TheStare (freeze), got {result[0]['action']}"


if __name__ == "__main__":
    tests = [
        test_all_sequences_have_valid_steps,
        test_runner_steps_through,
        test_runner_completes,
        test_interruptible_check,
        test_force_stop,
        test_progress,
        test_default_sequence_runner_state,
        test_get_current_step,
        test_trigger_registration,
        test_get_best_sequence,
        test_high_priority_wins,
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
            import traceback
            print(f"  [FAIL] {test.__name__}: {e}")
            traceback.print_exc()
    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
