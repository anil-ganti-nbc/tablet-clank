"""Read-only query layer for the Tablet Clank field-test dashboard.

Every function opens its own short-lived `Database` connection and returns
plain dicts/lists so the render layer never touches sqlite directly. Nothing
here writes to the database or invents values that aren't already in it -
health/duration are derived labels computed from real columns, not new data.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tablet_clank.sources.registry import ALERTS_ENABLED, PRODUCTION_ALLOWLIST, SOURCES, production_source_ids, runtime_source_ids
from tablet_clank.storage.db import Database


def _open(db_path) -> Database:
    return Database(str(db_path))


def _duration_seconds(started_at, finished_at):
    if not started_at or not finished_at:
        return None
    try:
        started = datetime.fromisoformat(started_at)
        finished = datetime.fromisoformat(finished_at)
        return round((finished - started).total_seconds(), 2)
    except ValueError:
        return None


def classify_health(run_row) -> str:
    """SOURCE HEALTH != SOURCE MATURITY. This only looks at the most recent run."""
    if run_row is None:
        return "NEVER_RUN"
    if run_row["status"] == "success":
        accepted = run_row["accepted_count"] or 0
        rejected = run_row["rejected_count"] or 0
        # A source that legitimately filters out a minority of candidates (e.g. a
        # generic category link) is healthy - rejections becoming the dominant
        # outcome is the actual degradation signal.
        return "DEGRADED" if rejected > 0 and rejected >= accepted else "SUCCESS"
    error = (run_row["error"] or "").lower()
    if "zero accepted" in error:
        return "ZERO_ITEMS"
    if "blocked" in error or "forbidden" in error or "403" in error:
        return "BLOCKED"
    return "FAILED"


def counts(db_path) -> dict:
    db = _open(db_path)
    try:
        return {
            "products": db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "observations": db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0],
            "change_events": db.conn.execute("SELECT COUNT(*) FROM change_events").fetchone()[0],
            "collector_runs": db.conn.execute("SELECT COUNT(*) FROM collector_runs").fetchone()[0],
        }
    finally:
        db.close()


def source_health(db_path) -> list[dict]:
    db = _open(db_path)
    try:
        rows = []
        for source_id, source in SOURCES.items():
            last = db.conn.execute(
                "SELECT status, error, accepted_count, rejected_count, new_count, resighted_count, started_at, finished_at "
                "FROM collector_runs WHERE source_id=? ORDER BY id DESC LIMIT 1",
                (source_id,),
            ).fetchone()
            last_success = db.conn.execute(
                "SELECT finished_at FROM collector_runs WHERE source_id=? AND status='success' ORDER BY id DESC LIMIT 1",
                (source_id,),
            ).fetchone()
            rows.append(
                {
                    "id": source_id,
                    "manufacturer": source.manufacturer,
                    "region": source.region,
                    "kind": source.kind,
                    "state": source.state,
                    "production": source_id in PRODUCTION_ALLOWLIST,
                    "health": classify_health(last),
                    "last_status": last["status"] if last else None,
                    "last_finished_at": last["finished_at"] if last else None,
                    "last_success_at": last_success["finished_at"] if last_success else None,
                    "last_item_count": last["accepted_count"] if last else None,
                    "last_error": last["error"] if last else None,
                }
            )
        return rows
    finally:
        db.close()


def overview(db_path) -> dict:
    health_rows = source_health(db_path)
    healthy = sum(1 for r in health_rows if r["health"] == "SUCCESS")
    db = _open(db_path)
    try:
        last_run = db.conn.execute(
            "SELECT source_id, status, finished_at FROM collector_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        integrity = db.integrity()
    finally:
        db.close()
    return {
        "counts": counts(db_path),
        "sources_healthy": healthy,
        "sources_total": len(health_rows),
        "last_run": dict(last_run) if last_run else None,
        "integrity": integrity,
        "alerts_enabled": ALERTS_ENABLED,
    }


def latest_discoveries(db_path, limit: int = 20) -> dict:
    db = _open(db_path)
    try:
        rows = db.conn.execute(
            "SELECT ce.*, p.manufacturer, p.name, p.region AS product_region, p.model_number "
            "FROM change_events ce JOIN products p ON p.id = ce.product_id "
            "ORDER BY ce.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        product_count = db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        return {
            "events": [dict(r) for r in rows],
            "product_count": product_count,
            "source_count": len(runtime_source_ids()),
        }
    finally:
        db.close()


def products(db_path, manufacturer=None, source_id=None, region=None, membership=None) -> dict:
    db = _open(db_path)
    try:
        manufacturers = [r[0] for r in db.conn.execute("SELECT DISTINCT manufacturer FROM products ORDER BY manufacturer").fetchall()]
        regions = [r[0] for r in db.conn.execute("SELECT DISTINCT region FROM products ORDER BY region").fetchall()]
        source_ids_present = [r[0] for r in db.conn.execute("SELECT DISTINCT source_id FROM observations ORDER BY source_id").fetchall()]

        clauses, params = [], []
        if manufacturer:
            clauses.append("p.manufacturer = ?")
            params.append(manufacturer)
        if region:
            clauses.append("p.region = ?")
            params.append(region)
        if source_id:
            clauses.append("EXISTS (SELECT 1 FROM observations o WHERE o.product_id = p.id AND o.source_id = ?)")
            params.append(source_id)
        if membership in ("production", "experimental"):
            wanted = list(production_source_ids()) if membership == "production" else [s for s in runtime_source_ids() if s not in PRODUCTION_ALLOWLIST]
            if wanted:
                placeholders = ",".join("?" for _ in wanted)
                clauses.append(f"EXISTS (SELECT 1 FROM observations o WHERE o.product_id = p.id AND o.source_id IN ({placeholders}))")
                params.extend(wanted)
            else:
                clauses.append("0=1")

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = db.conn.execute(f"SELECT p.* FROM products p {where} ORDER BY p.last_seen DESC", params).fetchall()

        result_rows = []
        for row in rows:
            srcs = db.conn.execute("SELECT DISTINCT source_id FROM observations WHERE product_id=?", (row["id"],)).fetchall()
            result_rows.append({**dict(row), "source_ids": [s[0] for s in srcs]})

        return {
            "rows": result_rows,
            "filter_options": {"manufacturers": manufacturers, "regions": regions, "source_ids": source_ids_present},
            "applied": {"manufacturer": manufacturer, "region": region, "source": source_id, "membership": membership},
        }
    finally:
        db.close()


def product_detail(db_path, product_id: int):
    db = _open(db_path)
    try:
        row = db.conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if row is None:
            return None
        observations = db.conn.execute(
            "SELECT * FROM observations WHERE product_id=? ORDER BY observed_at DESC", (product_id,)
        ).fetchall()
        events = db.conn.execute(
            "SELECT * FROM change_events WHERE product_id=? ORDER BY observed_at DESC", (product_id,)
        ).fetchall()
        return {
            "product": dict(row),
            "observations": [dict(o) for o in observations],
            "events": [dict(e) for e in events],
        }
    finally:
        db.close()


def changes(db_path, event_type=None, limit: int = 200) -> dict:
    db = _open(db_path)
    try:
        clauses, params = [], []
        if event_type:
            clauses.append("ce.event_type = ?")
            params.append(event_type)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = db.conn.execute(
            f"SELECT ce.*, p.manufacturer, p.name FROM change_events ce JOIN products p ON p.id = ce.product_id {where} ORDER BY ce.id DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        types = [r[0] for r in db.conn.execute("SELECT DISTINCT event_type FROM change_events ORDER BY event_type").fetchall()]
        product_count = db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        return {"rows": [dict(r) for r in rows], "types": types, "applied_type": event_type, "product_count": product_count}
    finally:
        db.close()


def sources_list(db_path, scope=None) -> list[dict]:
    rows = source_health(db_path)
    if scope == "production":
        return [r for r in rows if r["production"]]
    if scope == "experimental":
        return [r for r in rows if r["state"] == "EXPERIMENTAL" and not r["production"]]
    return rows


def run_history(db_path, limit: int = 200) -> list[dict]:
    db = _open(db_path)
    try:
        rows = db.conn.execute("SELECT * FROM collector_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            entry = dict(r)
            entry["duration_seconds"] = _duration_seconds(entry.get("started_at"), entry.get("finished_at"))
            entry["health"] = classify_health(r)
            out.append(entry)
        return out
    finally:
        db.close()


def _event_snapshot(row) -> dict:
    """Build the full snapshot dict qc_archive.decide() expects, preserving
    original identifiers (event id, run id, source id) -- never inventing
    new ones."""
    return {
        "event_id": row["id"],
        "run_id": row["run_id"] if "run_id" in row.keys() else None,
        "product_id": row["product_id"],
        "source_id": row["source_id"],
        "event_type": row["event_type"],
        "manufacturer": row["manufacturer"],
        "product_name": row["name"],
        "model_number": row["model_number"] if "model_number" in row.keys() else None,
        "region": row["product_region"],
        "old_value": row["old_value"],
        "new_value": row["new_value"],
        "evidence_url": row["evidence_url"],
        "event_observed_at": row["observed_at"],
    }


def active_queue(db_path, qc_path) -> dict:
    """Active lead/event queue: change_events not yet QC'd, most recent
    first. A QC decision removes an event from this view immediately because
    this is a read-side filter against the QC archive's ledger, computed
    fresh on every call -- never a separate cleanup step."""
    from tablet_clank.storage.qc_archive import QCArchive

    archive = QCArchive(qc_path)
    decided_ids = archive.decided_event_ids()
    db = _open(db_path)
    try:
        rows = db.conn.execute(
            "SELECT ce.*, p.manufacturer, p.name, p.model_number, p.sku, p.region AS product_region, "
            "p.variant, p.connectivity, p.ram_gb, p.storage_gb, p.colour, p.processor, p.display_size_in, p.os "
            "FROM change_events ce JOIN products p ON p.id = ce.product_id "
            "ORDER BY ce.id DESC"
        ).fetchall()
        events = [dict(r) for r in rows if r["id"] not in decided_ids]
        return {"events": events, "total_events": len(rows), "decided_count": len(decided_ids)}
    finally:
        db.close()


def queue_item(db_path, qc_path, event_id: int):
    db = _open(db_path)
    try:
        row = db.conn.execute(
            "SELECT ce.*, p.manufacturer, p.name, p.model_number, p.sku, p.region AS product_region, "
            "p.variant, p.connectivity, p.ram_gb, p.storage_gb, p.colour, p.processor, p.display_size_in, "
            "p.os, p.identity_key, p.first_seen, p.last_seen "
            "FROM change_events ce JOIN products p ON p.id = ce.product_id WHERE ce.id=?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        observations = db.conn.execute(
            "SELECT * FROM observations WHERE product_id=? ORDER BY observed_at DESC", (row["product_id"],)
        ).fetchall()
        return {"event": dict(row), "observations": [dict(o) for o in observations]}
    finally:
        db.close()


def submit_qc(db_path, qc_path, event_id: int, decision: str, note: str | None = None):
    from tablet_clank.storage.qc_archive import QCArchive

    db = _open(db_path)
    try:
        row = db.conn.execute(
            "SELECT ce.*, p.manufacturer, p.name, p.model_number, p.region AS product_region "
            "FROM change_events ce JOIN products p ON p.id = ce.product_id WHERE ce.id=?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        snapshot = _event_snapshot(row)
    finally:
        db.close()
    archive = QCArchive(qc_path)
    archive.decide(snapshot, decision)
    return snapshot


def qc_recent(qc_path, limit: int = 50) -> list[dict]:
    from tablet_clank.storage.qc_archive import QCArchive

    archive = QCArchive(qc_path)
    return [dict(r) for r in archive.recent(limit)]


def about(db_path, build_revision: str) -> dict:
    db = _open(db_path)
    try:
        integrity = db.integrity()
    finally:
        db.close()
    return {
        "build_revision": build_revision,
        "integrity": integrity,
        "alerts_enabled": ALERTS_ENABLED,
        "production_allowlist": list(PRODUCTION_ALLOWLIST),
        "runtime_sources": list(runtime_source_ids()),
    }
