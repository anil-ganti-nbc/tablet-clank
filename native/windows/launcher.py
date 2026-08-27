"""Windows entry point for the local Tablet Clank dashboard.

Mirrors native/macos/launcher.py exactly in behavior (same webapp.py,
dash_data.py, dash_render.py -- shared, not duplicated) with two
platform-specific differences: the state root lives under
%LOCALAPPDATA%\\Tablet Clank instead of ~/Library/Application Support, and
the browser is opened with os.startfile instead of the macOS `open` command.

Launching this script starts the HTTP server ONLY. It never runs a
collector on its own -- collection only happens when a human clicks
"Collect Now" or "Run all finalized collectors" in the GUI (which POST to
/collect or /collect/all), or via the CLI. No Task Scheduler entry, cron, or
timer is created or required by this file.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
import urllib.request
from pathlib import Path

APP_NAME = "Tablet Clank"


def state_root() -> Path:
    override = os.getenv("TABLET_CLANK_FIELD_TEST_HOME")
    if override:
        return Path(override).expanduser().resolve()
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / APP_NAME


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


def build_revision() -> str:
    value = os.getenv("TABLET_CLANK_PACKAGED_REVISION", "").strip()
    return value or "local development build"


def configure_environment(root: Path) -> None:
    for relative in ("data", "logs", "runtime", "tmp"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    for name in tuple(os.environ):
        if "DISCORD" in name.upper() or "WEBHOOK" in name.upper():
            os.environ.pop(name, None)
    os.environ.update(
        TABLET_CLANK_FIELD_TEST="1",
        TABLET_CLANK_INSTANCE="Tablet Clank WINDOWS LOCAL",
        TABLET_CLANK_STATE_ROOT=str(root),
        TABLET_CLANK_RELEASE_CHANNEL="windows-local",
        TABLET_CLANK_BUILD_REVISION=build_revision(),
    )
    os.chdir(root)


def wait_ready(url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("dashboard did not become ready")


def main() -> int:
    sys.path.insert(0, str(resource_root()))
    # Shared GUI modules (webapp/dash_data/dash_render/dash_names/qc_archive
    # wiring) live in native/macos/ -- there is nothing macOS-specific in
    # those modules themselves (stdlib http.server only), so Windows reuses
    # them rather than forking a second copy of the dashboard.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))

    root = state_root()
    configure_environment(root)

    from tablet_clank.storage.db import Database

    db_path = root / "data" / "tablet_clank.db"
    Database(str(db_path)).close()

    import webapp

    server = webapp.create_server(db_path, build_revision())
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}"
    marker = root / "runtime" / "dashboard.json"

    thread = threading.Thread(target=server.serve_forever, name="tablet-clank-dashboard")
    thread.start()
    try:
        wait_ready(url)
        marker.write_text(json.dumps({"pid": os.getpid(), "port": port, "url": url}), encoding="utf-8")
        if os.getenv("TABLET_CLANK_NO_BROWSER") != "1":
            os.startfile(url)  # noqa: S606 - local loopback URL only
        stop = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        signal.signal(signal.SIGINT, lambda *_: stop.set())
        while not stop.wait(0.25) and thread.is_alive():
            pass
        return 0
    finally:
        server.shutdown()
        thread.join(timeout=15)
        marker.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
