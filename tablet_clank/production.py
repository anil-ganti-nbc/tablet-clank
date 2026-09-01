"""Bounded, serial production-allowlisted collection orchestration.

Reuses the soak module's lock, collector selection and reporting helpers so
production execution shares the same locking domain, identity semantics and
baseline semantics as manual collection and the experimental soak.
"""

from __future__ import annotations

from pathlib import Path

from .models import RunResult
from .qualification import QualificationProvenance
from .pipeline import process
from .sources.registry import ALERTS_ENABLED, PRODUCTION_ALLOWLIST, SOURCES, production_source_ids
from .soak import (
    SoakLock,
    append_report,
    collector_for,
    duplicate_identity_count,
    lock_path_for_db,
    result_summary,
    utcnow,
)
from .storage.db import Database


def resolve_production_sources(db: Database) -> list:
    ids = production_source_ids()
    if not ids:
        raise RuntimeError("production allowlist is empty")
    sources = [SOURCES[source_id] for source_id in ids]
    if any(source.state != "EXPERIMENTAL" for source in sources):
        raise RuntimeError("production roster contains a non-experimental source")
    return sources


def readiness_check(db: Database) -> dict:
    if ALERTS_ENABLED:
        raise RuntimeError("alerts must remain disabled for production execution")
    sources = resolve_production_sources(db)
    integrity = db.integrity()
    duplicates = duplicate_identity_count(db)
    if integrity != "ok":
        raise RuntimeError(f"database integrity is {integrity}")
    if duplicates:
        raise RuntimeError(f"duplicate identity count is {duplicates}")
    missing = []
    for source in sources:
        state = db.conn.execute("SELECT baseline_complete FROM source_state WHERE source_id=?", (source.id,)).fetchone()
        if not state or not state[0]:
            missing.append(source.id)
    if missing:
        raise RuntimeError(f"baseline incomplete for: {', '.join(missing)}")
    return {
        "sources": [source.id for source in sources],
        "integrity": integrity,
        "duplicates": duplicates,
        "production_allowlist": list(PRODUCTION_ALLOWLIST),
        "alerts_enabled": ALERTS_ENABLED,
    }


def run_production_cycle(db: Database, fixture_mode: bool = False) -> dict:
    started = utcnow()
    source_summaries = []
    sources = resolve_production_sources(db)
    event_ids_before = {row[0] for row in db.conn.execute("SELECT id FROM change_events")}
    for source in sources:
        before = event_ids_before | {row[0] for row in db.conn.execute("SELECT id FROM change_events")}
        try:
            result = process(
                db, collector_for(source, fixture_mode), fixture_mode=fixture_mode,
                provenance=QualificationProvenance.SCHEDULED,
                scope_key=f"production:{source.id}",
                material_inputs={"production_allowlist": sorted(PRODUCTION_ALLOWLIST)},
            )
        except Exception as exc:  # defensive isolation around a source boundary
            result = RunResult(source.id, status="failed", error=str(exc))
        source_summaries.append(result_summary(result, db, before))
    integrity = db.integrity()
    duplicates = duplicate_identity_count(db)
    if integrity != "ok":
        status = "PRODUCTION_ABORTED_DB_INTEGRITY"
    elif duplicates:
        status = "PRODUCTION_ABORTED_DUPLICATE_IDENTITY"
    elif all(item["health"] == "success" for item in source_summaries):
        status = "SUCCESS"
    else:
        status = "PARTIAL_FAILURE"
    return {
        "type": "production_cycle",
        "started_at": started,
        "ended_at": utcnow(),
        "sources": source_summaries,
        "status": status,
        "db_integrity": integrity,
        "duplicates": duplicates,
    }


def run_production(db_path: str | Path = "var/tablet_clank.db", fixture_mode: bool = False, report_path: str | Path | None = None) -> dict:
    db_path = Path(db_path)
    report_path = Path(report_path) if report_path else db_path.parent / "logs" / "production.jsonl"
    lock = SoakLock(lock_path_for_db(db_path), role="production")
    with lock:
        db = Database(db_path)
        try:
            readiness = readiness_check(db)
            append_report(report_path, {"type": "production_start", "started_at": utcnow(), "readiness": readiness})
            report = run_production_cycle(db, fixture_mode=fixture_mode)
            append_report(report_path, report)
            return report
        finally:
            db.close()
