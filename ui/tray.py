"""ui/tray.py — System tray icon and context menu."""
import logging
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction

logger = logging.getLogger(__name__)


class CatTrayIcon:
    """System tray icon for desktop-cat."""

    def __init__(self, app: QApplication, state, window=None):
        self.app = app
        self.state = state
        self.window = window
        self.engine = None  # set externally after engine init
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

        # Sync tray state with window visibility
        if self.window is not None:
            self.window.visibility_changed.connect(self._on_visibility_changed)

    def _build_menu(self):
        self.act_show = QAction("Show Cat", checkable=True)
        self.act_show.setChecked(True)
        self.act_show.toggled.connect(self._on_show_toggled)
        self.menu.addAction(self.act_show)
        self.menu.addSeparator()

        # ── Multi-cat management ──
        self.act_add_cat = QAction("Add Cat ➕", self.menu)
        self.act_add_cat.triggered.connect(self._add_cat)
        self.menu.addAction(self.act_add_cat)

        self.act_remove_cat = QAction("Remove Last Cat ➖", self.menu)
        self.act_remove_cat.triggered.connect(self._remove_last_cat)
        self.menu.addAction(self.act_remove_cat)
        self.menu.addSeparator()

        self.act_settings = QAction("Settings...", self.menu)
        self.act_settings.triggered.connect(self._open_settings)
        self.menu.addAction(self.act_settings)
        self.menu.addSeparator()

        self.act_quit = QAction("Quit", self.menu)
        self.act_quit.triggered.connect(self.app.quit)
        self.menu.addAction(self.act_quit)

    def _add_cat(self):
        """Add a new cat (max MAX_CATS)."""
        import config as _cfg
        max_cats = _cfg.MAX_CATS
        if len(self.state.cats) >= max_cats:
            self._show_notification("🐱 Max cats reached",
                                    f"Maximum {max_cats} cats allowed")
            return
        cat_id = self.state.add_cat()
        if cat_id >= 0:
            # Save state
            if self.engine is not None:
                self.engine.save_state()
            self._show_notification("🐱 Cat joined!",
                                    f"Cat #{cat_id + 1} has arrived")

    def _remove_last_cat(self):
        """Remove the most recently added cat (keep at least 1)."""
        if len(self.state.cats) <= 1:
            self._show_notification("🐱 Minimum 1 cat",
                                    "Must keep at least one cat")
            return
        removed = self.state.cats.pop()
        # Save state
        if self.engine is not None:
            self.engine.save_state()
        self._show_notification("🐱 Cat left",
                                f"Cat #{len(self.state.cats) + 1} has left")

    def _show_notification(self, title: str, message: str):
        """Show a tray notification."""
        try:
            self.tray.showMessage(title, message,
                                  QSystemTrayIcon.MessageIcon.Information,
                                  3000)
        except Exception:
            pass

    def _open_settings(self):
        """Open the settings dialog."""
        from ui.settings import SettingsDialog
        result = SettingsDialog.open()
        if result is not None and hasattr(self, '_on_settings_changed'):
            self._on_settings_changed()

    def _on_show_toggled(self, checked: bool):
        """Toggle window visibility from tray menu."""
        if self.window is not None:
            self.window.setVisible(checked)

    def _on_visibility_changed(self, visible: bool):
        """Sync tray check state when window visibility changes externally."""
        self.act_show.setChecked(visible)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.window is not None:
                self.window.setVisible(not self.window.isVisible())

    def show(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        else:
            logger.warning("System tray not available on this system")

    def set_tooltip(self, text: str):
        self.tray.setToolTip(text)
