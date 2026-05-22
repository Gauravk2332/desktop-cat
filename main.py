"""
main.py — Entry point.

Creates the window, state, engine, and starts everything.
Single import tree root — wires the module graph together.
Hardened with file logging and top-level crash resilience.
"""

import sys
import os
import logging
import traceback
from datetime import datetime

# ── File logging ──
_log_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
_log_dir = os.path.join(_log_dir, "DesktopCat")
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "desktop-cat.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(_log_path, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)

logger = logging.getLogger("desktop-cat")


def main():
    from PyQt6.QtWidgets import QApplication

    import config
    from core.state import CatState
    from core.window import CatWindow
    from core.engine import Engine
    from core.api import start_api

    logger.info("=== Desktop Cat STARTING ===")
    logger.info("Python: %s", sys.version)
    logger.info("Platform: %s", sys.platform)

    app = QApplication(sys.argv)
    app.setApplicationName("DesktopCat")

    # 1. Create shared state
    state = CatState()
    logger.info("State created: %d cat(s)", len(state.cats))

    # 2. Create window
    try:
        window = CatWindow(state)
        window.show()
        window._remove_dwm_border()
        logger.info("Window shown: %dx%d", state.screen_width, state.screen_height)
    except Exception as e:
        logger.critical("Window creation failed: %s", exc_info=True)
        sys.exit(1)

    # 3. Create engine
    try:
        engine = Engine(state, window)
        window.controls.engine = engine
        engine.load_state()
        logger.info("Engine created, state loaded")
    except Exception as e:
        logger.critical("Engine creation failed: %s", exc_info=True)
        sys.exit(1)

    # 4. Pass state reference to API
    from core.api import set_state_ref
    set_state_ref(state)

    # 5. Start HTTP API daemon
    try:
        start_api()
        logger.info("API started on port %d", config.API_PORT)
    except Exception as e:
        logger.warning("API failed to start: %s", e)

    # 6. System tray
    try:
        from ui.tray import CatTrayIcon
        tray = CatTrayIcon(app, state, window)
        tray.engine = engine
        tray.show()
        logger.info("System tray ready")
    except Exception as e:
        logger.warning("Tray failed to load (non-fatal): %s", e)

    # 7. Enter event loop
    try:
        exit_code = app.exec()
        logger.info("Event loop exited with code %d", exit_code)
    except Exception as e:
        logger.critical("Event loop crashed: %s", exc_info=True)
        exit_code = 1

    # 8. Save state on clean exit
    try:
        engine.save_state()
        logger.info("State saved on exit")
    except Exception as e:
        logger.warning("State save on exit failed: %s", e)

    logger.info("=== Desktop Cat STOPPED ===")
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Absolute last resort — log to file since logging may not be configured
        try:
            with open(os.path.join(_log_dir, "desktop-cat-fatal.log"), "a") as f:
                f.write(f"{datetime.now()} FATAL: {traceback.format_exc()}\n")
        except Exception:
            pass
        raise
