"""Finder entry point for the isolated Tablet Clank field test."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

APP_NAME = "Tablet Clank"


def state_root() -> Path:
    override = os.getenv("TABLET_CLANK_FIELD_TEST_HOME")
    return Path(override).expanduser().resolve() if override else Path.home() / "Library" / "Application Support" / APP_NAME


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
        TABLET_CLANK_INSTANCE="Tablet Clank FIELD TEST",
        TABLET_CLANK_STATE_ROOT=str(root),
        TABLET_CLANK_RELEASE_CHANNEL="field-test",
        TABLET_CLANK_BUILD_REVISION=build_revision(),
    )
    os.chdir(root)


def wait_ready(url: str, server, timeout: float = 30.0) -> None:
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
    sys.path.insert(0, str(Path(__file__).resolve().parent))

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
        wait_ready(url, server)
        marker.write_text(json.dumps({"pid": os.getpid(), "port": port, "url": url}), encoding="utf-8")
        if os.getenv("TABLET_CLANK_NO_BROWSER") != "1":
            subprocess.Popen(["open", url], close_fds=True)
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
