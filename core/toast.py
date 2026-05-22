"""core/toast.py — Windows toast notifications for the cat."""

import sys
import logging

_notification_enabled = True


def notify(title: str, message: str) -> None:
    """Send a Windows toast notification. Safe no-op on non-Windows."""
    if not _notification_enabled:
        return
    if sys.platform != "win32":
        return
    try:
        from winrt.windows.ui.notifications import (
            ToastNotificationManager,
            ToastNotification,
        )
        from winrt.windows.data.xml.dom import XmlDocument

        # Build toast XML
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<toast>\n"
            "    <visual>\n"
            '        <binding template="ToastText02">\n'
            f'            <text id="1">{title}</text>\n'
            f'            <text id="2">{message}</text>\n'
            "        </binding>\n"
            "    </visual>\n"
            "</toast>"
        )

        doc = XmlDocument()
        doc.load_xml(xml)

        notifier = ToastNotificationManager.create_toast_notifier()
        notification = ToastNotification(doc)
        notifier.show(notification)
    except ImportError:
        logging.debug("winrt not available — skipping toast")
    except Exception as e:
        logging.debug("toast failed: %s", e)


def set_notifications_enabled(enabled: bool) -> None:
    """Enable or disable toast notifications globally."""
    global _notification_enabled
    _notification_enabled = enabled
