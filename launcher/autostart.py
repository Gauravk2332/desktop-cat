"""launcher/autostart.py — Register/unregister desktop-cat to start with Windows.

Uses HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run registry key.
No admin required — HKCU is user-scoped.
"""

import sys
import logging

logger = logging.getLogger(__name__)

APP_NAME = "DesktopCat"

# Module-level winreg reference for cross-platform testing and clean API.
# On non-Windows systems, winreg is None and all operations return False.
try:
    import winreg as _winreg_mod  # type: ignore[import-untyped]

    winreg = _winreg_mod
except ImportError:
    winreg = None  # type: ignore[assignment]

REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_reg_key():
    """Return (key_handle, key_path) for reading/writing autostart."""
    return winreg.HKEY_CURRENT_USER, REG_RUN_PATH


def is_registered() -> bool:
    """Check if desktop-cat is registered for autostart."""
    if winreg is None:
        return False
    try:
        key_path = _get_reg_key()[1]
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except (OSError, FileNotFoundError):
        return False


def register(exe_path: str | None = None) -> bool:
    """Register desktop-cat to run at Windows startup.

    Args:
        exe_path: Path to the executable. If None, uses sys.executable + -m launcher.autostart.

    Returns:
        True if registered successfully, False otherwise.
    """
    if winreg is None:
        logger.warning("winreg not available (not Windows)")
        return False
    try:
        if exe_path is None:
            exe_path = f'"{sys.executable}" -m launcher.autostart'
        key = _get_reg_key()
        with winreg.OpenKey(key[0], key[1], 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        logger.info("Autostart registered: %s", exe_path)
        return True
    except Exception as e:
        logger.error("Failed to register autostart: %s", e)
        return False


def unregister() -> bool:
    """Remove desktop-cat from Windows autostart."""
    if winreg is None:
        return False
    try:
        key = _get_reg_key()
        with winreg.OpenKey(key[0], key[1], 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.DeleteValue(reg_key, APP_NAME)
        logger.info("Autostart unregistered")
        return True
    except FileNotFoundError:
        return True  # already clean
    except Exception as e:
        logger.error("Failed to unregister autostart: %s", e)
        return False


def toggle() -> bool:
    """Toggle autostart on/off. Returns new state (True = registered)."""
    if is_registered():
        unregister()
        return False
    else:
        return register()
