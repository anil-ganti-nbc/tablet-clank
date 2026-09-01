"""Tablet's canonical numbered-SQLite compatibility barrier."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path


SCHEMA_VERSION = 3

MIGRATIONS = [
    (1, """
    CREATE TABLE sources (id TEXT PRIMARY KEY, manufacturer TEXT NOT NULL, region TEXT NOT NULL, kind TEXT NOT NULL, url TEXT NOT NULL, state TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE products (id INTEGER PRIMARY KEY, manufacturer TEXT NOT NULL, family TEXT, name TEXT NOT NULL, model_number TEXT, sku TEXT, region TEXT NOT NULL, variant TEXT, connectivity TEXT, ram_gb REAL, storage_gb INTEGER, colour TEXT, processor TEXT, display_size_in REAL, os TEXT, identity_key TEXT NOT NULL UNIQUE, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL);
    CREATE TABLE observations (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id), source_id TEXT NOT NULL REFERENCES sources(id), url TEXT NOT NULL, observed_at TEXT NOT NULL, raw_values TEXT NOT NULL, normalized_values TEXT NOT NULL, collector TEXT NOT NULL, UNIQUE(product_id, source_id, observed_at));
    CREATE TABLE collector_runs (id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL, raw_count INTEGER NOT NULL DEFAULT 0, validated_count INTEGER NOT NULL DEFAULT 0, rejected_count INTEGER NOT NULL DEFAULT 0, accepted_count INTEGER NOT NULL DEFAULT 0, new_count INTEGER NOT NULL DEFAULT 0, updated_count INTEGER NOT NULL DEFAULT 0, resighted_count INTEGER NOT NULL DEFAULT 0, error TEXT);
    CREATE TABLE rejected_candidates (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES collector_runs(id), url TEXT NOT NULL, title TEXT NOT NULL, reason TEXT NOT NULL, raw_values TEXT NOT NULL);
    CREATE TABLE change_events (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id), source_id TEXT NOT NULL REFERENCES sources(id), event_type TEXT NOT NULL, old_value TEXT, new_value TEXT, evidence_url TEXT NOT NULL, observed_at TEXT NOT NULL, confidence REAL NOT NULL);
    CREATE TABLE source_state (source_id TEXT PRIMARY KEY REFERENCES sources(id), baseline_complete INTEGER NOT NULL DEFAULT 0, last_healthy_run_id INTEGER, consecutive_healthy_runs INTEGER NOT NULL DEFAULT 0);
    CREATE INDEX idx_products_manufacturer ON products(manufacturer);
    CREATE INDEX idx_observations_source ON observations(source_id);
    """),
    (2, "ALTER TABLE change_events ADD COLUMN run_id INTEGER REFERENCES collector_runs(id);"),
    (3, """
    ALTER TABLE collector_runs ADD COLUMN provenance TEXT NOT NULL DEFAULT 'UNKNOWN';
    ALTER TABLE collector_runs ADD COLUMN qualification_scope TEXT;
    ALTER TABLE collector_runs ADD COLUMN qualification_epoch_id INTEGER;
    ALTER TABLE collector_runs ADD COLUMN qualification_material_identity TEXT;
    ALTER TABLE collector_runs ADD COLUMN qualification_gate_status TEXT NOT NULL DEFAULT 'UNKNOWN';
    CREATE TABLE qualification_scopes (scope_key TEXT PRIMARY KEY, epoch_id INTEGER NOT NULL, material_identity TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE qualification_epochs (id INTEGER PRIMARY KEY, scope_key TEXT NOT NULL, epoch_number INTEGER NOT NULL, material_identity TEXT NOT NULL, prior_material_identity TEXT, reset_reason TEXT, created_at TEXT NOT NULL, UNIQUE(scope_key, epoch_number));
    CREATE INDEX idx_qualification_epochs_scope ON qualification_epochs(scope_key, epoch_number);
    CREATE TABLE qualification_resets (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES collector_runs(id), scope_key TEXT NOT NULL, epoch_id INTEGER NOT NULL REFERENCES qualification_epochs(id), prior_material_identity TEXT, new_material_identity TEXT NOT NULL, reason TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT 'UNKNOWN', created_at TEXT NOT NULL, UNIQUE(run_id));
    CREATE TABLE qualification_terminals (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES collector_runs(id), scope_key TEXT NOT NULL, epoch_id INTEGER NOT NULL REFERENCES qualification_epochs(id), material_identity TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT 'UNKNOWN', status TEXT NOT NULL, counts_for_qualification INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, UNIQUE(run_id));
    CREATE INDEX idx_qualification_terminals_scope ON qualification_terminals(scope_key, epoch_id);
    """),
]

_REQUIRED_BY_VERSION = {
    1: {"tables": {"sources", "products", "observations", "collector_runs", "rejected_candidates", "change_events", "source_state"}, "columns": {("collector_runs", "started_at"), ("change_events", "observed_at")}, "indexes": {"idx_products_manufacturer", "idx_observations_source"}},
    2: {"tables": set(), "columns": {("change_events", "run_id")}, "indexes": set()},
    3: {"tables": {"qualification_scopes", "qualification_epochs", "qualification_resets", "qualification_terminals"}, "columns": {("collector_runs", "provenance"), ("collector_runs", "qualification_scope"), ("collector_runs", "qualification_epoch_id"), ("collector_runs", "qualification_material_identity"), ("collector_runs", "qualification_gate_status")}, "indexes": {"idx_qualification_epochs_scope", "idx_qualification_terminals_scope"}},
}


class SchemaCompatibilityError(RuntimeError):
    """Raised when Tablet persistent state cannot safely admit normal work."""


@dataclass(frozen=True)
class SchemaCompatibility:
    state: str
    expected_version: int
    observed_versions: tuple[int, ...] = ()
    reason: str = ""

    @property
    def ready(self) -> bool:
        return self.state == "COMPATIBLE"


def _read_schema(path: Path):
    """Read existing SQLite metadata without creating a file, marker, or table."""
    if not path.exists():
        return set(), set(), {}, (), None
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                return set(), set(), {}, (), f"integrity check failed: {integrity}"
            rows = conn.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            tables = {name for kind, name in rows if kind == "table"}
            indexes = {name for kind, name in rows if kind == "index"}
            columns = {table: {row[1] for row in conn.execute(f"PRAGMA table_info({table})")} for table in tables}
            if "schema_migrations" not in tables:
                return tables, indexes, columns, (), None
            if not {"version", "applied_at"}.issubset(columns["schema_migrations"]):
                return tables, indexes, columns, (), "schema_migrations has an invalid marker shape"
            versions = []
            for (version,) in conn.execute("SELECT version FROM schema_migrations ORDER BY version"):
                if not isinstance(version, int):
                    return tables, indexes, columns, (), "schema_migrations contains a non-integer version"
                versions.append(version)
            return tables, indexes, columns, tuple(versions), None
        finally:
            conn.close()
    except sqlite3.Error as error:
        return set(), set(), {}, (), f"schema inspection failed: {error}"


def _has_required_structure(tables, indexes, columns, through: int) -> bool:
    for version in range(1, through + 1):
        required = _REQUIRED_BY_VERSION[version]
        if not required["tables"].issubset(tables) or not required["indexes"].issubset(indexes):
            return False
        if any(column not in columns.get(table, set()) for table, column in required["columns"]):
            return False
    return True


def _has_future_structure(tables, indexes, columns, after: int) -> bool:
    for version in range(after + 1, SCHEMA_VERSION + 1):
        required = _REQUIRED_BY_VERSION[version]
        if required["tables"] & tables or required["indexes"] & indexes:
            return True
        if any(column in columns.get(table, set()) for table, column in required["columns"]):
            return True
    return False


def inspect_compatibility(path: str | Path) -> SchemaCompatibility:
    """Return Tablet's auditable compatibility decision without mutation."""
    path = Path(path)
    tables, indexes, columns, versions, error = _read_schema(path)
    if error:
        return SchemaCompatibility("CORRUPT", SCHEMA_VERSION, versions, error)
    if not tables:
        return SchemaCompatibility("FRESH", SCHEMA_VERSION, (), "database does not exist or is empty")
    if "schema_migrations" not in tables:
        return SchemaCompatibility("UNKNOWN", SCHEMA_VERSION, (), "non-empty database has no schema_migrations marker")
    if not versions:
        return SchemaCompatibility("PARTIAL", SCHEMA_VERSION, (), "empty migration marker is not a fresh database")
    if any(version <= 0 for version in versions):
        return SchemaCompatibility("CORRUPT", SCHEMA_VERSION, versions, "schema_migrations contains an invalid version")
    if any(version > SCHEMA_VERSION for version in versions):
        return SchemaCompatibility("INCOMPATIBLE_NEWER", SCHEMA_VERSION, versions, "database schema is newer than this Tablet binary")
    expected_prefix = tuple(range(1, versions[-1] + 1))
    if versions != expected_prefix:
        return SchemaCompatibility("PARTIAL", SCHEMA_VERSION, versions, "schema_migrations is not a contiguous numbered prefix")
    applied = versions[-1]
    if not _has_required_structure(tables, indexes, columns, applied):
        return SchemaCompatibility("PARTIAL", SCHEMA_VERSION, versions, "marked migration structure is incomplete or contradictory")
    if _has_future_structure(tables, indexes, columns, applied):
        return SchemaCompatibility("PARTIAL", SCHEMA_VERSION, versions, "database contains unmarked future migration structure")
    if applied == SCHEMA_VERSION:
        return SchemaCompatibility("COMPATIBLE", SCHEMA_VERSION, versions, "exact numbered schema contract is present")
    return SchemaCompatibility("MIGRATION_REQUIRED", SCHEMA_VERSION, versions, "older valid numbered schema requires canonical migration")


class Database:
    def __init__(self, path="var/tablet_clank.db"):
        self.path = Path(path)
        self.conn: sqlite3.Connection | None = None
        # Construction is Tablet's canonical migration boundary. It permits
        # only a genuinely fresh store or a valid older numbered prefix.
        self.migrate()
        self.require_compatible()
        self.conn = self._connect_unchecked()

    def _connect_unchecked(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def inspect_compatibility(self) -> SchemaCompatibility:
        return inspect_compatibility(self.path)

    def require_compatible(self) -> SchemaCompatibility:
        status = self.inspect_compatibility()
        if not status.ready:
            raise SchemaCompatibilityError(f"Tablet database compatibility gate refused normal work: {status.state}: {status.reason}")
        return status

    def migrate(self) -> None:
        before = self.inspect_compatibility()
        if before.ready:
            return
        if before.state not in {"FRESH", "MIGRATION_REQUIRED"}:
            raise SchemaCompatibilityError(f"Tablet canonical migration refused {before.state} state: {before.reason}")
        conn = self._connect_unchecked()
        try:
            with conn:
                conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
                done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
                for version, sql in MIGRATIONS:
                    if version not in done:
                        conn.executescript(sql)
                        conn.execute("INSERT INTO schema_migrations VALUES (?, datetime('now'))", (version,))
        finally:
            conn.close()
        self.require_compatible()

    def integrity(self):
        self.require_compatible()
        return self.conn.execute("PRAGMA integrity_check").fetchone()[0]

    def backup_to(self, target, overwrite=False):
        """Create a verified SQLite recovery point from compatible state only."""
        self.require_compatible()
        target = Path(target)
        if target.exists() and not overwrite:
            raise FileExistsError(f"backup target already exists (refusing to overwrite a recovery point): {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".partial")
        if partial.exists(): partial.unlink()
        dest = sqlite3.connect(str(partial))
        try:
            with dest: self.conn.backup(dest)
        finally:
            dest.close()
        check = sqlite3.connect(str(partial))
        try:
            result = check.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            check.close()
        if result != "ok":
            partial.unlink(missing_ok=True)
            raise RuntimeError(f"backup failed integrity_check: {result}")
        os.replace(partial, target)
        data = target.read_bytes()
        return {"path": str(target), "integrity_check": result, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "schema_version": self.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]}

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None
