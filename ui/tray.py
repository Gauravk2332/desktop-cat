"""ui/tray.py — System tray icon and context menu."""
import logging
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction

logger = logging.getLogger(__name__)


class CatTrayIcon:
    """System tray icon for desktop-cat."""

    def __init__(self, app: QApplication, state):
        self.app = app
        self.state = state
        self.tray = QSystemTrayIcon()

        # Load icon
        icon = QIcon.fromTheme("cat", QIcon("assets/icon.png"))
        if icon.isNull():
            icon = QIcon("assets/icon.png")
        self.tray.setIcon(icon)
        self.tray.setToolTip("Desktop Cat")

        # Build menu
        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)

        # Signal
        self.tray.activated.connect(self._on_activated)

    def _build_menu(self):
        self.act_show = QAction("Show Cat", checkable=True)
        self.act_show.setChecked(True)
        self.menu.addAction(self.act_show)
        self.menu.addSeparator()
        self.act_quit = QAction("Quit", self.menu)
        self.act_quit.triggered.connect(self.app.quit)
        self.menu.addAction(self.act_quit)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            pass  # Could toggle visibility

    def show(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        else:
            logger.warning("System tray not available on this system")

    def set_tooltip(self, text: str):
        self.tray.setToolTip(text)
