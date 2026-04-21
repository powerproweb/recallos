"""
desktop/tray.py — System tray icon for RecallOS Desktop.

Uses pystray (optional dependency).  If pystray is not installed, the
tray is silently skipped — the app works fine without it.

The tray provides:
  - Status indicator (running / indexing)
  - Quick actions: Show Window, Run Doctor, Backup Now, Quit
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger("tray")

_tray_icon = None


def _has_pystray() -> bool:
    try:
        import pystray  # noqa: F401

        return True
    except Exception:
        # ImportError if not installed; Xlib.error.DisplayNameError on headless Linux
        return False


def start_tray(on_show_window=None, on_quit=None) -> None:
    """Start the system tray icon in a background thread.

    Callbacks:
      on_show_window — called when user clicks "Show Window"
      on_quit        — called when user clicks "Quit"
    """
    if not _has_pystray():
        logger.debug("pystray not installed — skipping system tray")
        return

    import pystray
    from PIL import Image

    # Create a minimal icon (16x16 teal square)
    icon_image = Image.new("RGB", (16, 16), (88, 166, 255))

    def _show(icon, item):
        if on_show_window:
            on_show_window()

    def _quit(icon, item):
        icon.stop()
        if on_quit:
            on_quit()

    def _doctor(icon, item):
        from desktop.services.backup_service import backup

        try:
            backup()
            logger.info("Tray: backup created")
        except Exception as e:
            logger.error("Tray: backup failed: %s", e)

    menu = pystray.Menu(
        pystray.MenuItem("Show Window", _show, default=True),
        pystray.MenuItem("Backup Now", _doctor),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit RecallOS", _quit),
    )

    global _tray_icon
    _tray_icon = pystray.Icon("RecallOS", icon_image, "RecallOS", menu)

    thread = threading.Thread(target=_tray_icon.run, daemon=True)
    thread.start()
    logger.info("System tray started")


def stop_tray() -> None:
    """Stop the system tray icon."""
    global _tray_icon
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass
        _tray_icon = None
