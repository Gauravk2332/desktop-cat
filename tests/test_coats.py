"""tests/test_coats.py — Unit tests for coat color system.

Tests cover:
- config.get_coat() returns correct coat by index
- Fallback behavior for out-of-range index
- COAT_NAME_INDEX covers all coat names
- Each coat's critical color values and properties
- Coat stripe styles, forehead M, chin chest
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from PyQt6.QtGui import QColor


class TestCoatIndexing(unittest.TestCase):
    """Coat indexing and fallback."""

    def test_coat_0_is_gray_tabby(self):
        coat = config.get_coat(0)
        self.assertEqual(coat.name, "Gray Tabby")

    def test_coat_1_is_orange_tabby(self):
        coat = config.get_coat(1)
        self.assertEqual(coat.name, "Orange Tabby")

    def test_out_of_range_falls_back_to_0(self):
        coat = config.get_coat(999)
        self.assertEqual(coat.name, "Gray Tabby")

    def test_negative_index_falls_back(self):
        coat = config.get_coat(-1)
        self.assertEqual(coat.name, "Gray Tabby")

    def test_list_coat_returns_first_item(self):
        count = len(config.COAT_COLORS_STRUCTURED)
        coat = config.get_coat(count)
        self.assertEqual(coat.name, "Gray Tabby")


class TestCoatNameIndex(unittest.TestCase):
    """COAT_NAME_INDEX maps coat names correctly."""

    def test_russian_blue_name_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("russian_blue"), 0)

    def test_orange_tabby_name_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("orange_tabby"), 1)

    def test_ginger_alias_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("ginger"), 1)

    def test_tuxedo_name_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("tuxedo"), 2)

    def test_calico_name_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("calico"), 3)

    def test_siamese_name_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("siamese"), 4)

    def test_black_name_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("black"), 5)

    def test_white_alias_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("white"), 5)

    def test_tortoiseshell_name_index(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("tortoiseshell"), 6)

    def test_empty_name_falls_back(self):
        self.assertEqual(config.COAT_NAME_INDEX.get("nonexistent_coat", 0), 0)


class TestCoatProperties(unittest.TestCase):
    """Critical coat properties — colors, stripe styles, markings."""

    def test_gray_tabby_colors(self):
        coat = config.get_coat(0)
        self.assertEqual(coat.body, QColor("#7C8E9E"))
        self.assertEqual(coat.belly, QColor("#D4D9DE"))
        self.assertEqual(coat.nose, QColor("#FF9494"))

    def test_gray_tabby_stripes(self):
        coat = config.get_coat(0)
        self.assertEqual(coat.stripe_style, "mackerel")
        self.assertTrue(coat.has_forehead_m)
        self.assertIsNotNone(coat.stripe)

    def test_gray_tabby_no_chin_chest(self):
        coat = config.get_coat(0)
        self.assertIsNone(coat.chin_chest)

    def test_gray_tabby_stripe_color(self):
        coat = config.get_coat(0)
        self.assertEqual(coat.stripe, QColor("#5A6B7A"))

    def test_orange_tabby_colors(self):
        coat = config.get_coat(1)
        self.assertEqual(coat.body, QColor("#E89B5D"))
        self.assertEqual(coat.belly, QColor("#FCE6C9"))
        self.assertEqual(coat.nose, QColor("#F08080"))

    def test_orange_tabby_stripes(self):
        coat = config.get_coat(1)
        self.assertEqual(coat.stripe_style, "mackerel")
        self.assertTrue(coat.has_forehead_m)
        self.assertIsNotNone(coat.stripe)

    def test_orange_tabby_stripe_color(self):
        coat = config.get_coat(1)
        self.assertEqual(coat.stripe, QColor("#C47A3C"))

    def test_orange_tabby_eye_color(self):
        coat = config.get_coat(1)
        self.assertEqual(coat.eye, QColor("#4CAF50"))

    def test_orange_tabby_chin_chest(self):
        coat = config.get_coat(1)
        self.assertEqual(coat.chin_chest, QColor("#FEFEFE"))

    def test_tuxedo_style(self):
        coat = config.get_coat(2)
        self.assertEqual(coat.stripe_style, "tuxedo")

    def test_tuxedo_body_color(self):
        coat = config.get_coat(2)
        self.assertEqual(coat.body, QColor("#2F2F2F"))

    def test_tuxedo_belly_color(self):
        coat = config.get_coat(2)
        self.assertEqual(coat.belly, QColor("#FEFEFE"))

    def test_tuxedo_chin_chest(self):
        coat = config.get_coat(2)
        self.assertEqual(coat.chin_chest, QColor("#FEFEFE"))

    def test_tuxedo_no_forehead_m(self):
        coat = config.get_coat(2)
        self.assertFalse(coat.has_forehead_m)

    def test_siamese_body_cream(self):
        coat = config.get_coat(4)
        self.assertEqual(coat.body, QColor("#F5E6CC"))

    def test_siamese_point_style(self):
        coat = config.get_coat(4)
        self.assertEqual(coat.stripe_style, "point")

    def test_calico_body_cream(self):
        coat = config.get_coat(3)
        self.assertEqual(coat.body, QColor("#FEFAF0"))

    def test_calico_patch_style(self):
        coat = config.get_coat(3)
        self.assertEqual(coat.stripe_style, "patch")

    def test_solid_black_no_style(self):
        coat = config.get_coat(5)
        self.assertEqual(coat.stripe_style, "none")

    def test_solid_black_body(self):
        coat = config.get_coat(5)
        self.assertEqual(coat.body, QColor("#1A1A1A"))

    def test_tortoiseshell_body(self):
        coat = config.get_coat(6)
        self.assertEqual(coat.body, QColor("#2F2F2F"))

    def test_tortoiseshell_patch_style(self):
        coat = config.get_coat(6)
        self.assertEqual(coat.stripe_style, "patch")


class TestCoatColorStability(unittest.TestCase):
    """Coat colors are stable across repeated calls."""

    def test_get_coat_twice_same_object(self):
        c1 = config.get_coat(0)
        c2 = config.get_coat(0)
        self.assertEqual(c1.body, c2.body)
        self.assertEqual(c1.belly, c2.belly)
        self.assertEqual(c1.ear_inner, c2.ear_inner)

    def test_all_coats_have_pupil_color(self):
        for i in range(len(config.COAT_COLORS_STRUCTURED)):
            coat = config.get_coat(i)
            self.assertIsNotNone(coat.pupil,
                                  f"Coat index {i} ({coat.name}) missing pupil color")

    def test_all_coats_have_paw_pads(self):
        for i in range(len(config.COAT_COLORS_STRUCTURED)):
            coat = config.get_coat(i)
            self.assertIsNotNone(coat.paw_pads,
                                  f"Coat index {i} ({coat.name}) missing paw_pads color")


if __name__ == "__main__":
    unittest.main()
