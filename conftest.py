"""conftest.py — Force offscreen Qt platform for headless test environments."""
import os

# Must be set before any PyQt imports
if "DISPLAY" not in os.environ and "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
