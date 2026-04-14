"""
desktop/app.py — RecallOS desktop application entry point.

Starts the FastAPI/Uvicorn backend on a random localhost port,
then opens a pywebview native window pointing at that server.
Closing the window shuts down the server gracefully.
"""

import socket
import sys
import threading

import uvicorn

from desktop.auth import generate_session_token


def _find_free_port() -> int:
    """Bind to port 0 and let the OS assign an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    """Entry point for ``recallos-desktop``."""
    port = _find_free_port()
    host = "127.0.0.1"

    # --- Generate per-session auth token ------------------------------------
    token = generate_session_token()

    # --- Start Uvicorn in a daemon thread -----------------------------------
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

    # webview.start() blocks until the window is closed
    webview.start()

    # --- Graceful shutdown ---------------------------------------------------
    server.should_exit = True
    thread.join(timeout=3)


if __name__ == "__main__":
    main()
