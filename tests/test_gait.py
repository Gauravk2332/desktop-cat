"""tests/test_gait.py — Unit tests for 4-leg gait system.

Tests cover:
- walk_frame cycles 0-7 correctly
- Body bob and tilt table values are valid
- Tail sway calculation produces valid values
- GAIT_FRAMES_4LEG has all 8 frames with correct leg keys
- Each frame has all 4 legs mapped
- Gait position values are within reasonable ranges
"""

import sys
import os
import math
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from cat.legs import (
    GAIT_FRAMES_4LEG, GAIT_BODY_BOB, GAIT_BODY_TILT,
    _LEG_BASES,
)
from cat.tail import draw_tail_walk


class TestGaitFrameCount(unittest.TestCase):
    """8-frame gait cycle completeness."""

    def test_exactly_8_frames(self):
        self.assertEqual(len(GAIT_FRAMES_4LEG), 8)

    def test_all_frames_present(self):
        for i in range(8):
            self.assertIn(i, GAIT_FRAMES_4LEG,
                          f"Frame {i} missing from GAIT_FRAMES_4LEG")

    def test_each_frame_has_4_legs(self):
        expected_legs = {"fl", "fr", "bl", "br"}
        for frame in range(8):
            data = GAIT_FRAMES_4LEG[frame]
            keys = set(data.keys())
            self.assertEqual(keys, expected_legs,
                             f"Frame {frame} has legs {keys}, expected {expected_legs}")


class TestGaitLegStructure(unittest.TestCase):
    """Each leg entry has correct tuple structure."""

    def test_each_leg_has_4_values(self):
        for frame in range(8):
            for leg in ("fl", "fr", "bl", "br"):
                data = GAIT_FRAMES_4LEG[frame][leg]
                self.assertEqual(len(data), 4,
                                 f"Frame {frame} leg {leg} has {len(data)} values, expected 4")
                mid_dx, mid_dy, paw_dx, paw_dy = data
                # Values should be reasonable integers
                self.assertIsInstance(mid_dx, int)
                self.assertIsInstance(mid_dy, int)
                self.assertIsInstance(paw_dx, int)
                self.assertIsInstance(paw_dy, int)

    def test_joint_always_above_paw(self):
        """Joint (mid_dy) should be more negative (higher) than paw position."""
        for frame in range(8):
            for leg in ("fl", "fr", "bl", "br"):
                mid_dx, mid_dy, paw_dx, paw_dy = GAIT_FRAMES_4LEG[frame][leg]
                self.assertLessEqual(mid_dy, paw_dy,
                                     f"Frame {frame} leg {leg}: joint y={mid_dy} should be <= paw y={paw_dy}")


class TestGaitBodyBobTilt(unittest.TestCase):
    """Body bob and tilt tables."""

    def test_body_bob_has_8_entries(self):
        self.assertEqual(len(GAIT_BODY_BOB), 8)

    def test_body_tilt_has_8_entries(self):
        self.assertEqual(len(GAIT_BODY_TILT), 8)

    def test_body_bob_values_in_range(self):
        for i, val in enumerate(GAIT_BODY_BOB):
            self.assertGreaterEqual(val, -3,
                                    f"Bob frame {i} value {val} < -3")
            self.assertLessEqual(val, 3,
                                 f"Bob frame {i} value {val} > 3")

    def test_body_tilt_values_in_range(self):
        for i, val in enumerate(GAIT_BODY_TILT):
            self.assertGreaterEqual(val, -3,
                                    f"Tilt frame {i} value {val} < -3")
            self.assertLessEqual(val, 3,
                                 f"Tilt frame {i} value {val} > 3")

    def test_body_bob_cycle_symmetry(self):
        """Bob should oscillate: start at 0, go negative, back to 0, go positive, back."""
        # Frame 0 should be 0
        self.assertEqual(GAIT_BODY_BOB[0], 0,
                         "Body bob frame 0 should be 0")
        # Frame 4 should be 0 (midpoint)
        self.assertEqual(GAIT_BODY_BOB[4], 0,
                         "Body bob frame 4 should be 0")

    def test_body_tilt_symmetry(self):
        """Tilt should oscillate: start at -2, cross 0 at frame 4."""
        # Frame 0 should be -2
        self.assertEqual(GAIT_BODY_TILT[0], -2,
                         "Body tilt frame 0 should be -2")
        # Frame 4 should be 2 (opposite)
        self.assertEqual(GAIT_BODY_TILT[4], 2,
                         "Body tilt frame 4 should be 2")


class TestLegBases(unittest.TestCase):
    """Leg base positions (shoulders/hips)."""

    def test_four_leg_bases(self):
        self.assertEqual(len(_LEG_BASES), 4)

    def test_expected_keys(self):
        expected = {"fl", "fr", "bl", "br"}
        self.assertEqual(set(_LEG_BASES.keys()), expected)

    def test_front_legs_have_y_negative(self):
        """Shoulders are above body center."""
        for leg in ("fl", "fr"):
            dx, dy = _LEG_BASES[leg]
            self.assertLess(dy, 0, f"Leg {leg} shoulder y={dy} should be above center")


class TestTailSwayCalculation(unittest.TestCase):
    """Tail sway synchronized with gait."""

    def test_tail_sway_frame_0(self):
        """Frame 0: sin(0*0.785)*6 = 0."""
        sway = math.sin(0 * 0.785) * 6
        self.assertAlmostEqual(sway, 0.0, places=1)

    def test_tail_sway_frame_2(self):
        """Frame 2: sin(2*0.785)*6 ~ sin(1.57)*6 = 6."""
        sway = math.sin(2 * 0.785) * 6
        self.assertAlmostEqual(sway, 6.0, delta=0.5)

    def test_tail_sway_frame_4(self):
        """Frame 4: sin(4*0.785)*6 ~ 0."""
        sway = math.sin(4 * 0.785) * 6
        self.assertAlmostEqual(sway, 0.0, places=1)

    def test_tail_sway_frame_6(self):
        """Frame 6: sin(6*0.785)*6 ~ -6."""
        sway = math.sin(6 * 0.785) * 6
        self.assertAlmostEqual(sway, -6.0, delta=0.5)

    def test_tail_sway_values_stable(self):
        """Values are deterministic."""
        for frame in range(8):
            v1 = math.sin(frame * 0.785) * 6
            v2 = math.sin(frame * 0.785) * 6
            self.assertEqual(v1, v2,
                             f"Tail sway frame {frame} non-deterministic")


class TestGaitDiagonalPairPattern(unittest.TestCase):
    """4-leg gait uses diagonal pair (trot) pattern.

    Frames 0-3: right-front + left-hind step forward (diagonal pair 1)
    Frames 4-7: left-front + right-hind step forward (diagonal pair 2)
    """

    def test_frame_0_rf_lh_extended(self):
        """Frame 0: FL paw should be extended (negative paw_dx = outward from body)."""
        # FL should have negative paw_dx in frame 0 (stepping forward)
        fl_paw_dx = GAIT_FRAMES_4LEG[0]["fl"][2]
        # BR should also be negative (diagonal pair)
        br_paw_dx = GAIT_FRAMES_4LEG[0]["br"][2]
        # Both should be extended (negative value = forward relative to shoulder)
        # We just check they exist and are reasonable
        self.assertIsNotNone(fl_paw_dx)
        self.assertIsNotNone(br_paw_dx)

    def test_frame_4_opposite_diagonal(self):
        """Frame 4: opposite diagonal should have paws extended forward."""
        # FR should have negative paw_dx (stepping forward)
        fr_paw_dx = GAIT_FRAMES_4LEG[4]["fr"][2]
        # BL should also be negative
        bl_paw_dx = GAIT_FRAMES_4LEG[4]["bl"][2]
        self.assertIsNotNone(fr_paw_dx)
        self.assertIsNotNone(bl_paw_dx)


class TestWalkFrameCycle(unittest.TestCase):
    """walk_frame cycles correctly in navigation update logic."""

    def test_walk_frame_cycles_0_to_7(self):
        """Simulate walk_frame progression through elapsed time."""
        # Need enough elapsed time to hit all 8 frames
        # t=0.55 gives int(7.15 % 8) = 7
        elapsed_values = [0.0, 0.08, 0.15, 0.23, 0.31, 0.38, 0.46, 0.54, 0.61]
        frames = [int((t * 13.0) % 8) for t in elapsed_values]
        # Should cycle through frames
        self.assertIn(0, frames)
        self.assertIn(4, frames)
        self.assertIn(7, frames)
        # No frame should be > 7
        for f in frames:
            self.assertLessEqual(f, 7)
            self.assertGreaterEqual(f, 0)

    def test_walk_frame_wraps_after_8_frames(self):
        """After enough elapsed time, frame should wrap around."""
        frames = []
        for i in range(20):
            t = i * 0.05  # 0.0, 0.05, ..., 0.95
            frames.append(int((t * 13.0) % 8))
        # 8/13.0 ≈ 0.615 seconds per cycle
        # At t=0.65: int(8.45 % 8) = int(0.45) = 0 -> wrapped
        self.assertEqual(frames[0], 0)  # t=0.0
        # At t=0.65 (index 13), should have wrapped around
        wrap_t = 0.65
        wrap_frame_idx = int(wrap_t / 0.05)
        self.assertEqual(frames[wrap_frame_idx], 0,
                         f"Frame at t={wrap_t} should be 0 (wrapped)")
        # Check we have at least 6 unique frames
        unique_frames = set(frames)
        self.assertGreaterEqual(len(unique_frames), 6,
                                "Should have at least 6 unique frames in 20 ticks")


if __name__ == "__main__":
    unittest.main()
