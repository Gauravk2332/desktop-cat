#!/usr/bin/env python3
"""
Day 1, Hour 1: PyQt6 Transparent Overlay Smoke Test.

Run this on gk-pc (Windows 11) to verify that WA_TranslucentBackground works
before any Phase 0 development proceeds.

Expected behavior:
  - A small transparent window appears with NO visible content
  - No white box, no flickering, no compositing artifacts
  - Window stays on top, frameless

If this test FAILS (white box, flicker, crash):
  - Document the GPU driver model (dxdiag)
  - Test with different Qt backends (ANGLE, Desktop GL, Software)
  - Investigate Direct2D or Skia as fallback rendering approaches
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt, QTimer


class TransparentTestWindow(QMainWindow):
    """Minimal transparent overlay window for testing."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Overlay Smoke Test")

        # Critical flags for transparent overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Make a small window in top-right corner
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        win_w, win_h = 200, 200
        x = screen_geo.width() - win_w - 20
        y = 20
        self.setGeometry(x, y, win_w, win_h)

        self.setStyleSheet("background: transparent")

        # Auto-close after 5 seconds
        QTimer.singleShot(5000, self.close)

    def paintEvent(self, event):
        """Override paint — draw nothing to verify transparency."""
        # A white box here would mean WA_TranslucentBackground is broken
        pass  # No drawing = fully transparent


def main():
    app = QApplication(sys.argv)

    print("=== PyQt6 Transparent Overlay Smoke Test ===")
    print(f"Qt backend: {QApplication.platformName()}")
    print("Creating transparent window...")

    win = TransparentTestWindow()
    win.show()

    print("Window created. It should be invisible (transparent).")
    print("Check for: white box, black box, flicker, or any artifact.")
    print("Window will auto-close in 5 seconds.")
    print()

    app.exec()

    print("=== Test Complete ===")
    print("PASS if: no visible window, no flicker, no crash")
    print("FAIL if: white/black box appeared, window flickered, or crash")


if __name__ == "__main__":
    main()
