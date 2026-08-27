"""Separate, on-disk QC/decision archive database.

Modeled on korean-tech-wire's `storage/qc_archive.py` pattern: a physically
separate SQLite file (never a second table bolted onto the live collector
database), a full snapshot of the reviewed item + its provenance captured at
decision time, and a UNIQUE constraint on the reviewed identifier as the race
guard for duplicate QC writes.

Why a separate file rather than a table in tablet_clank.db:
  - The live DB is the collector/evidence store; a QC decision is a distinct
    editorial record layered on top of it. Keeping it in its own file means
    QC operation never needs a schema migration on the live DB, and the live
    DB's own backup/integrity story stays untouched by QC activity.
  - A decision is a durable audit record. Storing a full snapshot (product
    identity, event type/values, source, run id, evidence url, observed_at)
    means the archive stays self-contained and readable even if the
    underlying product/event row is later altered by a future collector run.
  - UNIQUE(event_id) is the race guard: two concurrent QC submissions for the
    same event can both attempt an INSERT, but only one commits. The caller
    sees AlreadyDecided and reports 409, so there is never a duplicate
    decision or a silently lost update.

"Active queue" filtering (removing a QC'd event from the default queue view)
is done by the caller consulting `decided_event_ids()` -- the live DB's
change_events table is never mutated by a QC decision. This is also what
makes a restart safe (SQLite-on-disk, no in-memory state): the active queue
is a read-side filter recomputed every time, not a flag that needs to be
persisted elsewhere.

No destructive deletion exists anywhere in this module -- decisions are
append-only, and there is no method that deletes a row.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Tablet Clank's own vocabulary for the four terminal QC decisions (task
# spec / GUI contract): Useful, Not useful, False positive, Out of stock.
# "Out of stock" is a real terminal disposition here (unlike a pure news
# lead) because a Tablet Clank event can represent a still-listed vs.
# withdrawn catalogue entry.
QC_DECISIONS = ("USEFUL", "NOT_USEFUL", "FALSE_POSITIVE", "OUT_OF_STOCK")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS qc_decisions (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL UNIQUE,
    run_id INTEGER,
    product_id INTEGER,
    source_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    manufacturer TEXT,
    product_name TEXT,
    model_number TEXT,
    region TEXT,
    old_value TEXT,
    new_value TEXT,
    evidence_url TEXT,
    event_observed_at TEXT,
    decision TEXT NOT NULL,
    note TEXT,
    decided_at TEXT NOT NULL,
    decided_by TEXT
);
CREATE INDEX IF NOT EXISTS qc_decisions_decided_at_idx ON qc_decisions(decided_at DESC);
CREATE INDEX IF NOT EXISTS qc_decisions_source_idx ON qc_decisions(source_id);
"""


def _iso(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()


class AlreadyDecided(Exception):
    """Raised when an event already has a QC decision (race or re-submit)."""


class QCArchive:
    """A separate, append-only ledger of editorial QC decisions."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def migrate(self) -> None:
        with self.connect() as con:
            con.executescript(_SCHEMA)

    def integrity(self) -> str:
        with self.connect() as con:
            return con.execute("PRAGMA integrity_check").fetchone()[0]

    def decided_event_ids(self) -> set[int]:
        with self.connect() as con:
            return {row[0] for row in con.execute("SELECT event_id FROM qc_decisions")}

    def decision_for(self, event_id: int) -> sqlite3.Row | None:
        with self.connect() as con:
            return con.execute("SELECT * FROM qc_decisions WHERE event_id=?", (event_id,)).fetchone()

    def decide(self, event: dict, decision: str, *, note: str | None = None, decided_by: str = "owner") -> None:
        """Transactionally archive one event's full snapshot + provenance and
        record the decision.

        Raises AlreadyDecided if this event_id already has a row (the
        UNIQUE(event_id) race guard) -- never a silent duplicate write, and
        never an unhandled sqlite3.IntegrityError bubbling out to a caller.
        """
        if decision not in QC_DECISIONS:
            raise ValueError(f"unknown QC decision: {decision!r}")
        try:
            with self.connect() as con:
                con.execute(
                    "INSERT INTO qc_decisions(event_id,run_id,product_id,source_id,event_type,manufacturer,"
                    "product_name,model_number,region,old_value,new_value,evidence_url,event_observed_at,"
                    "decision,note,decided_at,decided_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event["event_id"], event.get("run_id"), event.get("product_id"), event["source_id"],
                        event["event_type"], event.get("manufacturer"), event.get("product_name"),
                        event.get("model_number"), event.get("region"), event.get("old_value"),
                        event.get("new_value"), event.get("evidence_url"), event.get("event_observed_at"),
                        decision, note, _iso(), decided_by,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise AlreadyDecided(f"event {event['event_id']} already has a QC decision") from error

    def recent(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as con:
            return con.execute("SELECT * FROM qc_decisions ORDER BY decided_at DESC LIMIT ?", (limit,)).fetchall()

    def status(self) -> dict[str, int]:
        with self.connect() as con:
            total = con.execute("SELECT COUNT(*) FROM qc_decisions").fetchone()[0]
            by_decision = {row["decision"]: row["n"] for row in con.execute("SELECT decision, COUNT(*) AS n FROM qc_decisions GROUP BY decision")}
        return {"total": total, **by_decision}


def qc_path_for_db(db_path: str | Path) -> Path:
    """Sibling archive file next to the live DB: <name>_qc.db, never a table
    inside the same file (see module docstring)."""
    path = Path(db_path)
    return path.with_name(path.stem + "_qc" + path.suffix)
