"""Separate, numbered on-disk QC decision archive."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .db import SchemaCompatibility, SchemaCompatibilityError

QC_DECISIONS = ("USEFUL", "NOT_USEFUL", "FALSE_POSITIVE", "OUT_OF_STOCK")
QC_SCHEMA_VERSION = 1
_SCHEMA = """
CREATE TABLE qc_decisions (id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL UNIQUE, run_id INTEGER, product_id INTEGER, source_id TEXT NOT NULL, event_type TEXT NOT NULL, manufacturer TEXT, product_name TEXT, model_number TEXT, region TEXT, old_value TEXT, new_value TEXT, evidence_url TEXT, event_observed_at TEXT, decision TEXT NOT NULL, note TEXT, decided_at TEXT NOT NULL, decided_by TEXT);
CREATE INDEX qc_decisions_decided_at_idx ON qc_decisions(decided_at DESC);
CREATE INDEX qc_decisions_source_idx ON qc_decisions(source_id);
"""


def _iso(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()


class AlreadyDecided(Exception):
    pass


def inspect_compatibility(path: str | Path) -> SchemaCompatibility:
    """Read archive metadata without creating a file, table, or marker."""
    path = Path(path)
    if not path.exists(): return SchemaCompatibility("FRESH", QC_SCHEMA_VERSION, (), "QC archive does not exist")
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok": return SchemaCompatibility("CORRUPT", QC_SCHEMA_VERSION, (), f"QC archive integrity check failed: {integrity}")
            rows = conn.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            tables = {name for kind, name in rows if kind == "table"}; indexes = {name for kind, name in rows if kind == "index"}
            if not tables: return SchemaCompatibility("FRESH", QC_SCHEMA_VERSION, (), "QC archive is empty")
            if "qc_schema_migrations" not in tables: return SchemaCompatibility("UNKNOWN", QC_SCHEMA_VERSION, (), "non-empty QC archive has no version marker")
            marker_columns = {row[1] for row in conn.execute("PRAGMA table_info(qc_schema_migrations)")}
            if not {"version", "applied_at"}.issubset(marker_columns): return SchemaCompatibility("CORRUPT", QC_SCHEMA_VERSION, (), "QC archive marker shape is invalid")
            versions = tuple(row[0] for row in conn.execute("SELECT version FROM qc_schema_migrations ORDER BY version"))
            if any(not isinstance(v, int) or v <= 0 for v in versions): return SchemaCompatibility("CORRUPT", QC_SCHEMA_VERSION, (), "QC archive marker contains an invalid version")
            if any(v > QC_SCHEMA_VERSION for v in versions): return SchemaCompatibility("INCOMPATIBLE_NEWER", QC_SCHEMA_VERSION, versions, "QC archive is newer than this Tablet binary")
            if versions == (1,) and {"qc_decisions", "qc_schema_migrations"}.issubset(tables) and {"qc_decisions_decided_at_idx", "qc_decisions_source_idx"}.issubset(indexes): return SchemaCompatibility("COMPATIBLE", QC_SCHEMA_VERSION, versions, "exact QC archive contract is present")
            return SchemaCompatibility("PARTIAL", QC_SCHEMA_VERSION, versions, "QC archive marker and structure disagree")
        finally:
            conn.close()
    except sqlite3.Error as error:
        return SchemaCompatibility("CORRUPT", QC_SCHEMA_VERSION, (), f"QC archive inspection failed: {error}")


def _structure(conn: sqlite3.Connection) -> dict:
    """Normalised structural fingerprint of everything except the marker table.

    Compared against the canonical contract below to decide whether an
    unmarked archive is *provably* v1 rather than merely plausible.
    """
    rows = conn.execute("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    tables = {name for kind, name, _ in rows if kind == "table" and name != "qc_schema_migrations"}
    indexes = {name: " ".join((sql or "").split()) for kind, name, sql in rows if kind == "index"}
    columns = {
        table: [(r[1], (r[2] or "").upper(), r[3], r[5]) for r in conn.execute(f'PRAGMA table_info("{table}")')]
        for table in sorted(tables)
    }
    return {"tables": tables, "indexes": indexes, "columns": columns}


def _canonical_v1_structure() -> dict:
    """Derive the v1 contract from _SCHEMA itself, so this proof can never
    drift from the schema it is supposed to be proving against."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(_SCHEMA)
        return _structure(conn)
    finally:
        conn.close()


def adopt_unmarked_v1(path: str | Path) -> SchemaCompatibility:
    """Operator-invoked adoption of a pre-marker QC archive.

    Early Tablet builds created the v1 ``qc_decisions`` schema before the
    ``qc_schema_migrations`` marker existed, so those archives inspect as
    UNKNOWN and every QC surface fails closed against them. This stamps the
    marker, but *only* after proving the on-disk structure is byte-for-byte
    the canonical v1 contract -- table set, exact ordered column contract
    (name/type/notnull/pk) and both index definitions. A structure that does
    not match exactly is refused, never guessed at, and no row is read,
    written, or migrated: adoption is purely the marker.

    Deliberately not called from any dashboard/GET path. An UNKNOWN archive
    must never be silently auto-adopted by merely opening a page.
    """
    path = Path(path)
    status = inspect_compatibility(path)
    if status.state == "COMPATIBLE":
        return status  # idempotent: already adopted
    if status.state != "UNKNOWN":
        raise SchemaCompatibilityError(f"Tablet QC archive adoption refused {status.state} state: {status.reason}")

    conn = sqlite3.connect(path)
    try:
        actual, expected = _structure(conn), _canonical_v1_structure()
        if actual != expected:
            raise SchemaCompatibilityError(
                "Tablet QC archive adoption refused: structure is not the exact v1 contract "
                f"(tables {sorted(actual['tables'])} vs {sorted(expected['tables'])}; "
                f"indexes {sorted(actual['indexes'])} vs {sorted(expected['indexes'])}; "
                f"columns differ: {actual['columns'] != expected['columns']})"
            )
        with conn:
            conn.execute("CREATE TABLE qc_schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
            conn.execute("INSERT INTO qc_schema_migrations VALUES (?, ?)", (QC_SCHEMA_VERSION, _iso()))
    finally:
        conn.close()

    adopted = inspect_compatibility(path)
    if not adopted.ready:
        raise SchemaCompatibilityError(f"Tablet QC archive adoption did not reach a compatible state: {adopted.state}: {adopted.reason}")
    return adopted


class QCArchive:
    def __init__(self, path: str | Path):
        self.path = Path(path); self.migrate(); self.require_compatible()
    def _connect_unchecked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True); conn = sqlite3.connect(self.path); conn.row_factory = sqlite3.Row; conn.execute("PRAGMA journal_mode=WAL"); return conn
    def inspect_compatibility(self): return inspect_compatibility(self.path)
    def require_compatible(self):
        status = self.inspect_compatibility()
        if not status.ready: raise SchemaCompatibilityError(f"Tablet QC archive compatibility gate refused normal work: {status.state}: {status.reason}")
        return status
    def connect(self): self.require_compatible(); return self._connect_unchecked()
    def migrate(self):
        before = self.inspect_compatibility()
        if before.ready: return
        if before.state != "FRESH": raise SchemaCompatibilityError(f"Tablet QC archive migration refused {before.state} state: {before.reason}")
        con = self._connect_unchecked()
        try:
            with con:
                con.execute("CREATE TABLE qc_schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"); con.executescript(_SCHEMA); con.execute("INSERT INTO qc_schema_migrations VALUES (?, ?)", (1, _iso()))
        finally:
            con.close()
        self.require_compatible()
    def integrity(self):
        with self.connect() as con: return con.execute("PRAGMA integrity_check").fetchone()[0]
    def decided_event_ids(self):
        with self.connect() as con: return {row[0] for row in con.execute("SELECT event_id FROM qc_decisions")}
    def decision_for(self, event_id):
        with self.connect() as con: return con.execute("SELECT * FROM qc_decisions WHERE event_id=?", (event_id,)).fetchone()
    def decide(self, event, decision, *, note=None, decided_by="owner"):
        if decision not in QC_DECISIONS: raise ValueError(f"unknown QC decision: {decision!r}")
        try:
            with self.connect() as con:
                con.execute("INSERT INTO qc_decisions(event_id,run_id,product_id,source_id,event_type,manufacturer,product_name,model_number,region,old_value,new_value,evidence_url,event_observed_at,decision,note,decided_at,decided_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (event["event_id"], event.get("run_id"), event.get("product_id"), event["source_id"], event["event_type"], event.get("manufacturer"), event.get("product_name"), event.get("model_number"), event.get("region"), event.get("old_value"), event.get("new_value"), event.get("evidence_url"), event.get("event_observed_at"), decision, note, _iso(), decided_by))
        except sqlite3.IntegrityError as error: raise AlreadyDecided(f"event {event['event_id']} already has a QC decision") from error
    def recent(self, limit=50):
        with self.connect() as con: return con.execute("SELECT * FROM qc_decisions ORDER BY decided_at DESC LIMIT ?", (limit,)).fetchall()
    def status(self):
        with self.connect() as con:
            total = con.execute("SELECT COUNT(*) FROM qc_decisions").fetchone()[0]; by_decision = {row["decision"]: row["n"] for row in con.execute("SELECT decision, COUNT(*) AS n FROM qc_decisions GROUP BY decision")}
        return {"total": total, **by_decision}


def qc_path_for_db(db_path: str | Path) -> Path:
    path = Path(db_path); return path.with_name(path.stem + "_qc" + path.suffix)
