"""Bounded, serial experimental soak orchestration."""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .collectors.apple_store import AppleStoreIPadProCollector
from .collectors.honor_cn import HonorCNTabletsCollector
from .collectors.html_catalogue import HtmlCatalogueCollector
from .collectors.tcl_global import TCLGlobalTabletsCollector
from .collectors.xml_sitemap import XmlSitemapCollector
from .models import RunResult
from .pipeline import process
from .sources.registry import PRODUCTION_ALLOWLIST, SOURCES, runtime_source_ids
from .storage.db import Database

FROZEN_SOAK_SOURCE_IDS = frozenset({
    "apple_in_ipad_pro_store", "apple_us_ipad_pro_store", "samsung_us_sitemap",
    "honor_cn_tablets_catalogue", "honor_cn_tablets_comparison", "tcl_global_tablets",
})


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def lock_path_for_db(db_path: str | Path) -> Path:
    path = Path(db_path)
    return path.parent / "tablet_clank.soak.lock"


class SoakLockError(RuntimeError):
    pass


class SoakLock:
    def __init__(self, path: str | Path, role: str = "soak"):
        self.path = Path(path)
        self.role = role
        self.acquired = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"pid": os.getpid(), "started_at": utcnow(), "role": self.role, "lock_path": str(self.path)}
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            try:
                existing = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as read_exc:
                raise SoakLockError(f"lock exists and cannot be inspected: {self.path}") from read_exc
            pid = existing.get("pid")
            if not isinstance(pid, int) or pid <= 0:
                raise SoakLockError(f"lock exists with unknown owner: {self.path}") from exc
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                try:
                    self.path.unlink()
                except OSError as unlink_exc:
                    raise SoakLockError(f"stale lock detected but cannot remove it: {self.path}") from unlink_exc
                return self.acquire()
            except PermissionError as alive_exc:
                raise SoakLockError(f"lock owner liveness cannot be established for PID {pid}") from alive_exc
            except OSError as alive_exc:
                # Windows commonly reports a definitely nonexistent PID as ERROR_INVALID_PARAMETER.
                if getattr(alive_exc, "winerror", None) == 87:
                    try:
                        self.path.unlink()
                    except OSError as unlink_exc:
                        raise SoakLockError(f"stale lock detected but cannot remove it: {self.path}") from unlink_exc
                    return self.acquire()
                raise SoakLockError(f"lock owner liveness cannot be established for PID {pid}") from alive_exc
            else:
                raise SoakLockError(f"active soak lock held by PID {pid}: {self.path}") from exc
        os.write(fd, json.dumps(metadata, sort_keys=True).encode("utf-8"))
        os.close(fd)
        self.acquired = True

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            self.path.unlink()
        finally:
            self.acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False


def duplicate_identity_count(db: Database) -> int:
    return db.conn.execute("SELECT count(*) FROM (SELECT identity_key FROM products GROUP BY identity_key HAVING count(*) > 1)").fetchone()[0]


def resolve_soak_sources(db: Database) -> list:
    ids = tuple(runtime_source_ids())
    if set(ids) != FROZEN_SOAK_SOURCE_IDS or len(ids) != len(FROZEN_SOAK_SOURCE_IDS):
        raise RuntimeError(f"soak roster drift: resolved={list(ids)} expected={sorted(FROZEN_SOAK_SOURCE_IDS)}")
    if any(source_id in PRODUCTION_ALLOWLIST for source_id in ids):
        raise RuntimeError("soak roster contains a production-allowlisted source")
    sources = [SOURCES[source_id] for source_id in ids]
    if any(source.state != "EXPERIMENTAL" for source in sources):
        raise RuntimeError("soak roster contains a non-experimental source")
    return sources


def readiness_check(db: Database) -> dict:
    sources = resolve_soak_sources(db)
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
    return {"sources": [source.id for source in sources], "integrity": integrity, "duplicates": duplicates, "production_allowlist": list(PRODUCTION_ALLOWLIST)}


def collector_for(source, fixture_mode: bool):
    if source.manufacturer == "Honor": cls = HonorCNTabletsCollector
    elif source.manufacturer == "TCL": cls = TCLGlobalTabletsCollector
    elif "Apple Store" in source.kind: cls = AppleStoreIPadProCollector
    elif "XML" in source.kind: cls = XmlSitemapCollector
    else: cls = HtmlCatalogueCollector
    return cls(source, fixture_mode=fixture_mode)


def _result_summary(result: RunResult, db: Database, event_ids_before: set[int]) -> dict:
    new_events = [dict(row) for row in db.conn.execute("SELECT id,source_id,event_type,product_id,new_value,evidence_url FROM change_events WHERE id > 0") if row["id"] not in event_ids_before]
    return {"source": result.source_id, "health": result.status, "raw": result.raw_count, "validated": result.validated_count, "rejected": result.rejected_count, "accepted": result.accepted_count, "new": result.new_count, "updated": result.updated_count, "resighted": result.resighted_count, "events": new_events, "error": result.error}


def run_cycle(db: Database, cycle_number: int, fixture_mode: bool = False) -> dict:
    started = utcnow(); start_time = time.monotonic(); source_summaries = []
    sources = resolve_soak_sources(db)
    event_ids_before = {row[0] for row in db.conn.execute("SELECT id FROM change_events")}
    for source in sources:
        before = event_ids_before | {row[0] for row in db.conn.execute("SELECT id FROM change_events")}
        try:
            result = process(db, collector_for(source, fixture_mode), fixture_mode=fixture_mode)
        except Exception as exc:  # defensive isolation around a source boundary
            result = RunResult(source.id, status="failed", error=str(exc))
        source_summaries.append(_result_summary(result, db, before))
    integrity = db.integrity()
    duplicates = duplicate_identity_count(db)
    if integrity != "ok": status = "SOAK_ABORTED_DB_INTEGRITY"
    elif duplicates: status = "SOAK_ABORTED_DUPLICATE_IDENTITY"
    elif all(item["health"] == "success" for item in source_summaries): status = "SUCCESS"
    else: status = "PARTIAL_FAILURE"
    return {"cycle": cycle_number, "started_at": started, "ended_at": utcnow(), "duration_seconds": round(time.monotonic() - start_time, 3), "sources": source_summaries, "status": status, "db_integrity": integrity, "duplicates": duplicates}


def append_report(report_path: str | Path, record: dict) -> None:
    path = Path(report_path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def run_bounded(db_path: str | Path = "var/tablet_clank.db", cycles: int = 12, interval_seconds: float = 7200, fixture_mode: bool = False, report_path: str | Path | None = None, sleep: Callable[[float], None] = time.sleep) -> list[dict]:
    if cycles < 1 or interval_seconds < 0: raise ValueError("cycles must be >= 1 and interval_seconds must be >= 0")
    db_path = Path(db_path); report_path = Path(report_path) if report_path else db_path.parent / "logs" / "soak.jsonl"
    lock = SoakLock(lock_path_for_db(db_path))
    reports = []
    with lock:
        db = Database(db_path)
        try:
            readiness = readiness_check(db)
            append_report(report_path, {"type": "soak_start", "started_at": utcnow(), "readiness": readiness, "cycles": cycles, "interval_seconds": interval_seconds})
            for number in range(1, cycles + 1):
                report = run_cycle(db, number, fixture_mode=fixture_mode); reports.append(report); append_report(report_path, report)
                if report["status"].startswith("SOAK_ABORTED_"): break
                if number < cycles: sleep(interval_seconds)
        except KeyboardInterrupt:
            record = {"type": "soak_interrupted", "ended_at": utcnow(), "status": "INTERRUPTED", "completed_cycles": len(reports)}
            append_report(report_path, record); raise
        finally:
            db.close()
    return reports
