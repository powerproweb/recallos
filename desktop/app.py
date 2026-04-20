"""
desktop/app.py — RecallOS desktop application entry point.

Starts the FastAPI/Uvicorn backend on a random localhost port,
then opens a pywebview native window pointing at that server.
Closing the window shuts down the server gracefully.
"""

import logging
import multiprocessing
import socket
import sys
import threading

import uvicorn

from desktop.auth import generate_session_token
from desktop.crash import check_unclean_shutdown, clear_running, mark_running, write_crash_dump
from desktop.services.logging_service import init_logging
from desktop.tray import start_tray, stop_tray

logger = logging.getLogger("app")


def _find_free_port() -> int:
    """Bind to port 0 and let the OS assign an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    """Entry point for ``recallos-desktop``."""
    multiprocessing.freeze_support()  # required for Windows frozen exe

    # --- Structured logging -------------------------------------------------
    init_logging()

    # --- Unclean shutdown detection -----------------------------------------
    if check_unclean_shutdown():
        logger.warning("Previous session did not exit cleanly")
    mark_running()

    port = _find_free_port()
    host = "127.0.0.1"

    # --- Generate per-session auth token ------------------------------------
    token = generate_session_token()

    # --- Start Uvicorn in a daemon thread -----------------------------------
    # When running inside a PyInstaller bundle, string-based import
    # ("desktop.server:app") fails because PyInstaller's importer can't
    # resolve it.  Pass the WSGI/ASGI app object directly instead.
    if getattr(sys, "frozen", False):
        from desktop.server import app as _app

        server_config = uvicorn.Config(
            _app,
            host=host,
            port=port,
            log_level="warning",
        )
    else:
        server_config = uvicorn.Config(
            "desktop.server:app",
            host=host,
            port=port,
            log_level="warning",
        )
    server = uvicorn.Server(server_config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # --- Open the native desktop window -------------------------------------
    try:
        import webview  # pywebview
    except ImportError:
        print("pywebview is not installed.  Install it with:\n  pip install recallos[desktop]")
        sys.exit(1)

    url = f"http://{host}:{port}?token={token}"
    webview.create_window(
        "RecallOS",
        url=url,
        width=1280,
        height=820,
        min_size=(900, 600),
    )

    # --- System tray (optional) ----------------------------------------------
    start_tray()

    # webview.start() blocks until the window is closed
    try:
        webview.start()
    except Exception as exc:
        write_crash_dump(exc)
        raise
    finally:
        # --- Graceful shutdown -----------------------------------------------
        stop_tray()
        server.should_exit = True
        thread.join(timeout=3)
        clear_running()
        logger.info("RecallOS Desktop shut down cleanly")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        write_crash_dump(exc)
        raise
