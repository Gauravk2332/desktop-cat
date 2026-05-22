"""
main.py — Entry point.

Creates the window, state, engine, and starts everything.
Single import tree root — wires the module graph together.
"""

import sys

from PyQt6.QtWidgets import QApplication

import config
from core.state import CatState
from core.window import CatWindow
from core.engine import Engine
from core.api import start_api


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopCat")

    # 1. Create shared state
    state = CatState()

    # 2. Create window (full-screen overlay, sets screen dimensions + cat pos)
    #    Engine not yet created — pass None, engine sets itself on window later
    window = CatWindow(state)

    # 3. Create engine (references state + window)
    engine = Engine(state, window)
    window.controls.engine = engine  # back-reference so controls can use engine
    engine.load_state()

    # 4. Pass state reference to API (for debug status)
    from core.api import set_state_ref
    set_state_ref(state)

    # 5. Start HTTP API daemon
    start_api()

    # 6. System tray
    from ui.tray import CatTrayIcon
    tray = CatTrayIcon(app, state, window)
    tray.engine = engine  # wire engine ref for save_state
    tray.show()

    # 7. Show window
    window.show()
    window._remove_dwm_border()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
