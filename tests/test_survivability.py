"""Fleet-parity additions: datastore survivability + health honesty.

- SQLite-safe backup (online backup API, atomic rename, integrity+hash
  verification, overwrite refusal) with an isolated restore drill.
- consecutive_healthy_runs must reset to 0 on a failed run (Law 3:
  health honesty) — the counter previously only ever incremented.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from tablet_clank.models import Candidate
from tablet_clank.pipeline import process
from tablet_clank.storage.db import Database


class FakeCollector:
    """Scripted collector standing in for a real one (no network)."""

    def __init__(self, candidates):
        self.candidates = candidates
        from tablet_clank.sources.registry import SOURCES

        self.source = SOURCES["samsung_us_sitemap"]
        self.__class__.__name__ = "FakeCollector"

    def collect(self):
        return list(self.candidates)


def _candidate(name="Galaxy Tab S11", model="SM-X730"):
    raw = {
        "manufacturer": "Samsung",
        "name": name,
        "model_number": model,
        "region": "us",
    }
    return Candidate(
        source_id="samsung_us_sitemap",
        manufacturer="Samsung",
        region="us",
        url=f"https://www.samsung.com/us/tablets/{model.lower()}/",
        title=name,
        raw_values=raw,
    )


def test_backup_creates_verified_snapshot(tmp_path: Path):
    db = Database(tmp_path / "t.db")
    try:
        process(db, FakeCollector([_candidate()]))
        target = tmp_path / "backups" / "rp1.db"
        report = db.backup_to(target)
        assert report["integrity_check"] == "ok"
        assert report["size_bytes"] > 0 and len(report["sha256"]) == 64
        # Schema version 3 adds the target-local qualification projection;
        # migration 2 (change_events.run_id) remains intact.
        assert report["schema_version"] == 3
    finally:
        db.close()


def test_backup_refuses_overwrite_then_round_trips_in_isolation(tmp_path: Path):
    db = Database(tmp_path / "t.db")
    try:
        process(db, FakeCollector([_candidate()]))
        target = tmp_path / "rp1.db"
        db.backup_to(target)
        import pytest

        with pytest.raises(FileExistsError):
            db.backup_to(target)

        # Restore drill: open the snapshot standalone; verify integrity,
        # schema presence, and row survival.
        con = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
        try:
            assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            assert {"products", "observations", "collector_runs", "source_state"} <= tables
            assert con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1
        finally:
            con.close()
    finally:
        db.close()


def test_consecutive_healthy_runs_resets_on_failure(tmp_path: Path):
    db = Database(tmp_path / "t.db")
    try:
        good = FakeCollector([_candidate()])
        result = process(db, good)
        assert result.status == "success"
        state = db.conn.execute("SELECT consecutive_healthy_runs FROM source_state WHERE source_id=?", ("samsung_us_sitemap",)).fetchone()
        assert state[0] == 1

        # A second healthy run increments...
        process(db, FakeCollector([_candidate()]))
        state = db.conn.execute("SELECT consecutive_healthy_runs FROM source_state WHERE source_id=?", ("samsung_us_sitemap",)).fetchone()
        assert state[0] == 2

        # ...and a failing run (zero accepted candidates) MUST reset it.
        result = process(db, FakeCollector([]))
        assert result.status == "failed"
        state = db.conn.execute("SELECT consecutive_healthy_runs FROM source_state WHERE source_id=?", ("samsung_us_sitemap",)).fetchone()
        assert state[0] == 0
    finally:
        db.close()
