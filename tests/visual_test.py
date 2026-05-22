"""
tests/visual_test.py — Headless visual QA for desktop-cat.

Captures screenshots of the cat in various states via Xvfb.
Compares against baselines to detect rendering regressions.

Usage:
    python tests/visual_test.py capture-all     # Capture all states
    python tests/visual_test.py capture <state>  # Capture one state
    python tests/visual_test.py compare <state>  # Compare vs baseline
    python tests/visual_test.py compare-all      # Compare all states
"""

import os
import sys
import time
import json
import logging

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BASELINES_DIR = os.path.join(os.path.dirname(__file__), "baselines")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(BASELINES_DIR, exist_ok=True)

# Ensure project root on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def ensure_display():
    """Start Xvfb if no DISPLAY set."""
    if "DISPLAY" not in os.environ or not os.environ["DISPLAY"]:
        os.system("Xvfb :99 -screen 0 1920x1080x24 -ac &")
        os.environ["DISPLAY"] = ":99"
        time.sleep(0.5)


def _init_app():
    """Create QApplication once for all captures."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def capture(state_name: str):
    """Capture a screenshot of the cat in the given state."""
    from core.state import CatState
    from core.window import CatWindow

    ensure_display()
    app = _init_app()
    state = CatState()

    # Set up the specific state
    state.config.screen_width = 1920
    state.config.screen_height = 1080
    state.cat_x = float(960)
    state.cat_y = float(950)

    if state_name == "sit":
        state.state = config.STATE_SIT
    elif state_name == "sleep_hut":
        state.state = config.STATE_SLEEP
        state.at_home = True
    elif state_name == "wander":
        state.state = config.STATE_WANDER
        state.cat_x = 500
        state.cat_y = 600
    elif state_name == "field_sleep":
        state.state = config.STATE_SLEEP
        state.at_home = False
        state.cat_x = 300
        state.cat_y = 700
    elif state_name == "walk":
        state.state = config.STATE_WALK
        state.cat_x = 400
        state.cat_y = 800
    else:
        state.state = config.STATE_SIT

    window = CatWindow(state)
    window.show()
    app.processEvents()
    time.sleep(0.2)

    # Grab the full window
    pixmap = window.grab()
    path = os.path.join(SCREENSHOTS_DIR, f"{state_name}.png")
    pixmap.save(path)
    window.close()
    return path


def compare(state_name: str, threshold: float = 0.02) -> dict:
    """Compare screenshot against baseline."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("Pillow required for comparison")
        return {"pass": False, "error": "Pillow not installed"}

    screenshot = os.path.join(SCREENSHOTS_DIR, f"{state_name}.png")
    baseline = os.path.join(BASELINES_DIR, f"{state_name}.png")

    if not os.path.exists(baseline):
        return {"pass": False, "error": f"No baseline for {state_name}",
                "screenshot": screenshot}

    if not os.path.exists(screenshot):
        return {"pass": False, "error": f"No screenshot for {state_name}"}

    img1 = Image.open(screenshot)
    img2 = Image.open(baseline)

    if img1.size != img2.size:
        return {"pass": False,
                "error": f"Size mismatch: {img1.size} vs {img2.size}"}

    diff = ImageChops.difference(img1, img2)
    bbox = diff.getbbox()
    if bbox is None:
        return {"pass": True, "diff_pct": 0.0, "state": state_name}

    # Compute difference percentage
    pixels = img1.size[0] * img1.size[1]
    diff_pixels = sum(1 for x in range(img1.size[0]) for y in range(img1.size[1])
                      if diff.getpixel((x, y)) != (0, 0, 0, 0) if len(diff.getpixel((x, y))) == 4
                      else sum(diff.getpixel((x, y))[:3]) > 0)
    diff_pct = (diff_pixels / pixels) * 100

    # Save diff image
    diff_path = os.path.join(SCREENSHOTS_DIR, f"{state_name}_diff.png")
    diff.save(diff_path)

    result = {
        "pass": diff_pct <= threshold * 100,
        "diff_pct": round(diff_pct, 3),
        "state": state_name,
        "diff_image": diff_path if diff_pct > 0 else None,
    }
    return result


def capture_all():
    """Capture all defined state screenshots."""
    states = ["sit", "sleep_hut", "wander", "field_sleep", "walk", "walk2"]
    results = {}
    for s in states:
        try:
            path = capture(s)
            results[s] = {"path": path, "status": "ok"}
            print(f"  ✓ {s}: {path}")
        except Exception as e:
            results[s] = {"status": "error", "error": str(e)}
            print(f"  ✗ {s}: {e}")
    return results


def compare_all(threshold: float = 0.02):
    """Compare all screenshots against baselines."""
    states = ["sit", "sleep_hut", "wander", "field_sleep", "walk"]
    results = {}
    all_pass = True
    for s in states:
        result = compare(s, threshold)
        results[s] = result
        status = "PASS" if result.get("pass") else "FAIL"
        if not result.get("pass"):
            all_pass = False
        print(f"  {status} {s}: {result.get('diff_pct', 'N/A')}% diff")
    results["overall"] = "PASS" if all_pass else "FAIL"
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "capture-all":
        print("Capturing all states...")
        capture_all()
        print("Done.")

    elif cmd == "capture":
        if len(sys.argv) < 3:
            print("Usage: visual_test.py capture <state>")
            sys.exit(1)
        for state_name in sys.argv[2:]:
            print(f"Capturing {state_name}...")
            path = capture(state_name)
            print(f"  Saved: {path}")

    elif cmd == "compare-all":
        print("Comparing all screenshots...")
        compare_all()
        print("Done.")

    elif cmd == "compare":
        if len(sys.argv) < 3:
            print("Usage: visual_test.py compare <state>")
            sys.exit(1)
        for s in sys.argv[2:]:
            result = compare(s)
            status = "PASS" if result.get("pass") else "FAIL"
            print(f"  {status} {s}: {result.get('diff_pct', 'N/A')}% diff")

    elif cmd == "generate-baselines":
        """Capture all states and copy to baselines directory."""
        print("Generating baseline images...")
        capture_all()
        import shutil
        for f in os.listdir(SCREENSHOTS_DIR):
            if f.endswith(".png") and "_diff" not in f:
                src = os.path.join(SCREENSHOTS_DIR, f)
                dst = os.path.join(BASELINES_DIR, f)
                shutil.copy2(src, dst)
                print(f"  Baseline: {f}")
        print("Done.")
