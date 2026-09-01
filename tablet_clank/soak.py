"""Bounded, serial experimental soak orchestration."""

from __future__ import annotations

import json
import os
import sys
import time
import inspect
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

from .collectors.apple_store import AppleStoreIPadProCollector
from .collectors.honor_cn import HonorCNTabletsCollector
from .collectors.honor_uk import HonorUKTabletsCollector
from .collectors.html_catalogue import HtmlCatalogueCollector
from .collectors.tcl_global import TCLGlobalTabletsCollector
from .collectors.xml_sitemap import XmlSitemapCollector
from .models import RunResult
from .pipeline import process
from .qualification import QualificationProvenance
from .sources.registry import PRODUCTION_ALLOWLIST, SOURCES, runtime_source_ids
from .storage.db import Database

FROZEN_SOAK_SOURCE_IDS = frozenset({
    "apple_in_ipad_pro_store", "apple_us_ipad_pro_store", "samsung_us_sitemap",
    "honor_cn_tablets_catalogue", "honor_cn_tablets_comparison", "tcl_global_tablets",
    # Wave 2 (2026-08-27): regional-launch discovery source, deliberately
    # added to the freeze as part of the reviewed expansion campaign.
    "honor_uk_tablets",
})

_WINDOWS_LOCK_OFFSET = 1 << 20


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def lock_path_for_db(db_path: str | Path) -> Path:
    path = Path(db_path)
    return path.parent / "tablet_clank.soak.lock"


class SoakLockError(RuntimeError):
    pass


def _os_lock(fd: int) -> None:
    if sys.platform == "win32":
        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _os_unlock(fd: int) -> None:
    if sys.platform == "win32":
        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


def _read_lock_metadata(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


class SoakLock:
    """A target-local lock whose authority is the held OS descriptor.

    PID, role, and timestamps in the lock file remain useful diagnostics, but
    are never consulted to grant, deny, or reclaim the lock.
    """

    def __init__(self, path: str | Path, role: str = "soak"):
        self.path = Path(path)
        self.role = role
        self.acquired = False
        self._fd: int | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            _os_lock(fd)
        except OSError as exc:
            metadata = _read_lock_metadata(self.path)
            os.close(fd)
            rendered = json.dumps(metadata, sort_keys=True) if metadata is not None else "unreadable"
            raise SoakLockError(
                f"active soak lock is held by the kernel (metadata={rendered}): {self.path}"
            ) from exc

        metadata = {
            "pid": os.getpid(),
            "started_at": utcnow(),
            "role": self.role,
            "lock_path": str(self.path),
            "lock_authority": "os_advisory_lock",
        }
        try:
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, json.dumps(metadata, sort_keys=True).encode("utf-8"))
        except OSError:
            # The grant is already real; diagnostic metadata must not weaken it.
            pass
        self._fd = fd
        self.acquired = True

    def release(self) -> None:
        if not self.acquired or self._fd is None:
            return
        try:
            _os_unlock(self._fd)
        finally:
            os.close(self._fd)
            self._fd = None
            self.acquired = False

    @classmethod
    def inspect(cls, path: str | Path) -> str:
        """Inspect kernel authority without deleting or rewriting the marker.

        A held kernel grant is active. A readable marker with no held grant is
        reported as stale for compatibility with campaign reporting; its PID
        is never used in that decision.
        """
        path = Path(path)
        if not path.exists():
            return "clear"
        try:
            fd = os.open(str(path), os.O_RDWR)
        except FileNotFoundError:
            return "clear"
        except OSError:
            return "unreadable"
        try:
            try:
                _os_lock(fd)
            except OSError:
                return "active"
            else:
                _os_unlock(fd)
        finally:
            os.close(fd)
        return "stale" if _read_lock_metadata(path) is not None else "unreadable"

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False


# Shared with the campaign runner so preflight duplicate checks can never
# drift from the soak-path definition of a duplicate identity.
_DUPLICATE_IDENTITY_SQL = "SELECT count(*) FROM (SELECT identity_key FROM products GROUP BY identity_key HAVING count(*) > 1)"


def duplicate_identity_count(db: Database) -> int:
    return db.conn.execute(_DUPLICATE_IDENTITY_SQL).fetchone()[0]


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
    if "UK tablet storefront" in source.kind: cls = HonorUKTabletsCollector
    elif source.manufacturer == "Honor": cls = HonorCNTabletsCollector
    elif source.manufacturer == "TCL": cls = TCLGlobalTabletsCollector
    elif "Apple Store" in source.kind: cls = AppleStoreIPadProCollector
    elif "XML" in source.kind: cls = XmlSitemapCollector
    else: cls = HtmlCatalogueCollector
    return cls(source, fixture_mode=fixture_mode)


def result_summary(result: RunResult, db: Database, event_ids_before: set[int]) -> dict:
    new_events = [dict(row) for row in db.conn.execute("SELECT id,source_id,event_type,product_id,new_value,evidence_url FROM change_events WHERE id > 0") if row["id"] not in event_ids_before]
    return {"source": result.source_id, "health": result.status, "raw": result.raw_count, "validated": result.validated_count, "rejected": result.rejected_count, "accepted": result.accepted_count, "new": result.new_count, "updated": result.updated_count, "resighted": result.resighted_count, "events": new_events, "error": result.error}


def run_cycle(db: Database, cycle_number: int, fixture_mode: bool = False, *, sources: list | None = None,
              scope_prefix: str = "soak", provenance: QualificationProvenance | str = QualificationProvenance.SCHEDULED,
              material_inputs: dict | None = None) -> dict:
    started = utcnow(); start_time = time.monotonic(); source_summaries = []
    # sources=None keeps the frozen-roster contract; campaign-scoped callers
    # pass their explicitly approved source list instead.
    if sources is None:
        sources = resolve_soak_sources(db)
    event_ids_before = {row[0] for row in db.conn.execute("SELECT id FROM change_events")}
    for source in sources:
        before = event_ids_before | {row[0] for row in db.conn.execute("SELECT id FROM change_events")}
        try:
            collector = collector_for(source, fixture_mode)
            if "provenance" in inspect.signature(process).parameters:
                result = process(
                    db, collector, fixture_mode=fixture_mode,
                    provenance=provenance, scope_key=f"{scope_prefix}:{source.id}",
                    material_inputs=material_inputs,
                )
            else:  # compatibility with tests/third-party wrappers around process
                result = process(db, collector, fixture_mode=fixture_mode)
        except Exception as exc:  # defensive isolation around a source boundary
            result = RunResult(source.id, status="failed", error=str(exc))
        source_summaries.append(result_summary(result, db, before))
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
