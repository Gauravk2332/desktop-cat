"""
tests/test_reactions.py — Unit tests for behavior/reactions.py

Tests reaction delay ranges for bold vs shy cats, pre-reaction cues,
and interaction type modifiers.
"""

import os
import sys
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from behavior.personality import Personality
from behavior.reactions import ReactionSystem, DELAY_BOLD, DELAY_SHY, PRE_REACTIONS


class TestReactionDelay(unittest.TestCase):
    """Test reaction delay ranges for different personalities."""

    def setUp(self):
        self.bold_personality = Personality(load_from_file=False)
        self.bold_personality.modify("boldness", 10)  # max bold: 10/10
        self.shy_personality = Personality(load_from_file=False)
        self.shy_personality.modify("boldness", -5)  # min shy: 0/10
        self.normal_personality = Personality(load_from_file=False)

    def test_bold_reaction_delay_range(self):
        """Bold cat should have delays in the bold range."""
        rs = ReactionSystem(self.bold_personality)
        for _ in range(50):
            delay = rs.get_reaction_delay("click")
            self.assertLessEqual(delay, DELAY_BOLD[1],
                                 f"Bold click delay {delay} > max {DELAY_BOLD[1]}")
            self.assertGreaterEqual(delay, 0.0)

    def test_shy_reaction_delay_range(self):
        """Shy cat should have delays in the shy range."""
        rs = ReactionSystem(self.shy_personality)
        for _ in range(50):
            delay = rs.get_reaction_delay("click")
            self.assertLessEqual(delay, DELAY_SHY[1],
                                 f"Shy click delay {delay} > max {DELAY_SHY[1]}")
            self.assertGreaterEqual(delay, 0.0)

    def test_bold_faster_than_shy_click(self):
        """Bold cats should consistently react faster than shy cats to clicks."""
        bold_rs = ReactionSystem(self.bold_personality)
        shy_rs = ReactionSystem(self.shy_personality)

        bold_delays = [bold_rs.get_reaction_delay("click") for _ in range(100)]
        shy_delays = [shy_rs.get_reaction_delay("click") for _ in range(100)]

        avg_bold = sum(bold_delays) / len(bold_delays)
        avg_shy = sum(shy_delays) / len(shy_delays)

        self.assertLess(avg_bold, avg_shy,
                        f"Bold avg {avg_bold:.3f}s should be < shy avg {avg_shy:.3f}s")

    def test_delay_deterministic_per_type_shift(self):
        """Interaction type should shift delay within the range."""
        rs = ReactionSystem(self.normal_personality)
        proximity_delays = [rs.get_reaction_delay("proximity") for _ in range(50)]
        hover_delays = [rs.get_reaction_delay("hover") for _ in range(50)]

        avg_prox = sum(proximity_delays) / len(proximity_delays)
        avg_hover = sum(hover_delays) / len(hover_delays)

        # Proximity is faster than hover
        self.assertLess(avg_prox, avg_hover,
                        f"Proximity avg {avg_prox:.3f}s should be < hover avg {avg_hover:.3f}s")

    def test_proximity_is_fastest(self):
        """Proximity should generally be the fastest interaction type."""
        rs = ReactionSystem(self.normal_personality)
        d1 = rs.get_reaction_delay("proximity")
        d2 = rs.get_reaction_delay("keypress")
        # Both should be within bounds; the type_offset for proximity is 0.0
        # so it should always be <= keypress
        self.assertLessEqual(d1, d2,
                             f"Proximity {d1} should be <= keypress {d2}")

    def test_unknown_interaction_type_defaults(self):
        """Unknown interaction type should use the default offset."""
        rs = ReactionSystem(self.normal_personality)
        delay = rs.get_reaction_delay("unknown_type_xyz")
        self.assertGreaterEqual(delay, 0.0)
        self.assertLessEqual(delay, 2.5)

    def test_delay_all_types_return_float(self):
        """All supported types should return a float."""
        rs = ReactionSystem(self.normal_personality)
        for typ in ("click", "hover", "proximity", "drag", "keypress", "speech", "pet"):
            delay = rs.get_reaction_delay(typ)
            self.assertIsInstance(delay, float)
            self.assertGreaterEqual(delay, 0.0)


class TestPreReaction(unittest.TestCase):
    """Test pre-reaction cues."""

    def setUp(self):
        self.rs = ReactionSystem(Personality(load_from_file=False))

    def test_pre_reaction_returns_tuple(self):
        result = self.rs.get_pre_reaction()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_pre_reaction_first_element_valid(self):
        for _ in range(200):
            cue, duration = self.rs.get_pre_reaction()
            # Cue must be None or a valid pre-reaction
            if cue is not None:
                valid_cues = [c for c in PRE_REACTIONS if c is not None]
                self.assertIn(cue, valid_cues, f"Unknown cue: {cue}")

    def test_pre_reaction_duration_range(self):
        for _ in range(200):
            cue, duration = self.rs.get_pre_reaction()
            if cue is not None:
                self.assertGreaterEqual(duration, 0.15)
                self.assertLessEqual(duration, 0.4)
            else:
                self.assertEqual(duration, 0.0)

    def test_pre_reaction_sometimes_none(self):
        """Pre-reaction should sometimes be None (direct reaction)."""
        results = [self.rs.get_pre_reaction()[0] for _ in range(100)]
        none_count = results.count(None)
        self.assertGreater(none_count, 0, "Pre-reaction should sometimes be None")
        self.assertLess(none_count, 100, "Pre-reaction should sometimes be non-None")


class TestReactionSystemRepr(unittest.TestCase):
    """Test __repr__ output."""

    def test_repr_includes_boldness(self):
        p = Personality(load_from_file=False)
        p.modify("boldness", 8)
        rs = ReactionSystem(p)
        r = repr(rs)
        self.assertIn("ReactionSystem", r)
        self.assertIn("boldness", r)


if __name__ == "__main__":
    unittest.main()
