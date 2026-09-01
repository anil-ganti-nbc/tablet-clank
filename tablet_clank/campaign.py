"""Campaign-scoped, isolated soak execution.

soak.run_bounded is bound to the full frozen roster and correctly refuses
while any frozen source is production-allowlisted, so the historical soak
path can no longer run at all. Campaign soaks are a separate runner with
narrower scope:

- The source set comes from the campaign manifest, never from the frozen
  roster (FROZEN_SOAK_SOURCE_IDS stays untouched).
- Execution happens against an isolated SQLite database. The canonical
  production database is opened READ-ONLY (SQLite ``mode=ro`` URI) for
  preflight checks only — a campaign structurally cannot write to it.
- The campaign lock lives beside the campaign database. Preflight still
  refuses while the canonical production/soak lock domain is active, and
  never removes a canonical lock it did not create.
- Reports go to a campaign-specific JSONL. Refusals, aborts, and
  interruptions are recorded there so evidence survives a failed campaign.
- Any cycle that does not end SUCCESS aborts the campaign (stricter than
  run_bounded): the promotion gate requires all cycles healthy, so
  continuing past an unhealthy cycle would only poison the evidence.
- By default cycle 1 (baseline) is followed immediately by cycle 2
  (resight) with no interval sleep, per the reviewed campaign shape;
  set ``immediate_resight: false`` in the manifest to disable.

Manifest paths are resolved against the current working directory when
relative, matching every other CLI ``--db`` default in this repository.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .soak import (
    _DUPLICATE_IDENTITY_SQL,
    SoakLock,
    SoakLockError,
    append_report,
    duplicate_identity_count,
    lock_path_for_db,
    run_cycle,
    utcnow,
)
from .sources.registry import SOURCES, campaign_approved_source_ids
from .storage.db import Database

CAMPAIGN_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

REQUIRED_MANIFEST_KEYS = ("campaign", "sources", "cycles", "interval_seconds")
KNOWN_MANIFEST_KEYS = frozenset({
    *REQUIRED_MANIFEST_KEYS,
    "canonical_db", "campaign_db", "report_path", "roster_hash",
    "environment", "immediate_resight", "created_at",
})
ENVIRONMENT_KEYS = ("python_version", "platform")


class CampaignError(RuntimeError):
    pass


@dataclass(frozen=True)
class CampaignManifest:
    name: str
    sources: tuple[str, ...]
    cycles: int
    interval_seconds: float
    canonical_db: Path
    campaign_db: Path
    report_path: Path
    roster_hash: str | None
    environment: dict | None
    immediate_resight: bool
    path: Path
    sha256: str


def current_environment() -> dict:
    return {"python_version": platform.python_version(), "platform": sys.platform}


def campaign_roster_hash(source_ids) -> str:
    """Pin the selected sources' registry identity (id, state, url) so a
    state flip or URL change after manifest authoring refuses the campaign."""
    entries = [
        {"id": source_id, "state": SOURCES[source_id].state, "url": SOURCES[source_id].url}
        for source_id in sorted(source_ids)
    ]
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode("utf-8")).hexdigest()


def build_manifest(name, sources, cycles, interval_seconds=7200.0, canonical_db="var/tablet_clank.db",
                   campaign_db=None, report_path=None, immediate_resight=True) -> dict:
    """Author a campaign manifest dict with roster hash and environment pinned."""
    manifest = {
        "campaign": name,
        "sources": list(sources),
        "cycles": cycles,
        "interval_seconds": interval_seconds,
        "canonical_db": str(canonical_db),
        "environment": current_environment(),
        "immediate_resight": immediate_resight,
        "created_at": utcnow(),
    }
    if campaign_db:
        manifest["campaign_db"] = str(campaign_db)
    if report_path:
        manifest["report_path"] = str(report_path)
    # Validate before hashing so an unknown source raises CampaignError
    # instead of a KeyError from the roster hash lookup.
    _validate_manifest_data(manifest)
    manifest["roster_hash"] = campaign_roster_hash(sources)
    return manifest


def _validate_manifest_data(data) -> None:
    if not isinstance(data, dict):
        raise CampaignError("manifest is not a JSON object")
    unknown = sorted(set(data) - KNOWN_MANIFEST_KEYS)
    if unknown:
        raise CampaignError(f"manifest has unknown keys: {', '.join(unknown)}")
    missing = [key for key in REQUIRED_MANIFEST_KEYS if key not in data]
    if missing:
        raise CampaignError(f"manifest missing required keys: {', '.join(missing)}")
    name = data["campaign"]
    if not isinstance(name, str) or not CAMPAIGN_NAME_RE.fullmatch(name):
        raise CampaignError("campaign name must match [a-z0-9][a-z0-9-]{0,63}")
    sources = data["sources"]
    if not isinstance(sources, list) or not sources or not all(isinstance(s, str) for s in sources):
        raise CampaignError("manifest sources must be a non-empty list of source ids")
    if len(set(sources)) != len(sources):
        raise CampaignError("manifest sources contain duplicates")
    unknown_sources = [sid for sid in sources if sid not in SOURCES]
    if unknown_sources:
        raise CampaignError(f"manifest references unknown source(s): {', '.join(unknown_sources)}")
    cycles = data["cycles"]
    if isinstance(cycles, bool) or not isinstance(cycles, int) or cycles < 1:
        raise CampaignError("manifest cycles must be an integer >= 1")
    interval = data["interval_seconds"]
    if isinstance(interval, bool) or not isinstance(interval, (int, float)) or interval < 0:
        raise CampaignError("manifest interval_seconds must be a number >= 0")
    environment = data.get("environment")
    if environment is not None:
        if not isinstance(environment, dict):
            raise CampaignError("manifest environment must be an object")
        unsupported = sorted(set(environment) - set(ENVIRONMENT_KEYS))
        if unsupported:
            raise CampaignError(f"manifest environment has unsupported keys: {', '.join(unsupported)}")


def _resolve_path(value, base: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def load_manifest(manifest_path) -> CampaignManifest:
    path = Path(manifest_path)
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except FileNotFoundError as exc:
        raise CampaignError(f"manifest not found: {path}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CampaignError(f"manifest is not valid JSON: {path}: {exc}") from exc
    _validate_manifest_data(data)
    base = Path.cwd()
    canonical_db = _resolve_path(data["canonical_db"], base) if data.get("canonical_db") else base / "var" / "tablet_clank.db"
    campaign_db = _resolve_path(data["campaign_db"], base) if data.get("campaign_db") else base / "var" / "campaigns" / data["campaign"] / "tablet_clank.db"
    report_path = _resolve_path(data["report_path"], base) if data.get("report_path") else base / "var" / "logs" / f"soak-{data['campaign']}.jsonl"
    if os.path.normcase(canonical_db.resolve()) == os.path.normcase(campaign_db.resolve()):
        raise CampaignError("campaign database must be isolated from the canonical database")
    return CampaignManifest(
        name=data["campaign"],
        sources=tuple(data["sources"]),
        cycles=data["cycles"],
        interval_seconds=float(data["interval_seconds"]),
        canonical_db=canonical_db,
        campaign_db=campaign_db,
        report_path=report_path,
        roster_hash=data.get("roster_hash"),
        environment=dict(data["environment"]) if data.get("environment") is not None else None,
        immediate_resight=bool(data.get("immediate_resight", True)),
        path=path,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _canonical_lock_state(canonical_db: Path) -> str:
    """Inspect the canonical lock using the same kernel authority as writers.

    A readable marker with no held descriptor is retained as ``stale`` for
    campaign-report compatibility. PID metadata is never consulted.
    """
    return SoakLock.inspect(lock_path_for_db(canonical_db))


def _open_canonical_readonly(canonical_db: Path):
    # mode=ro refuses every write, including WAL recovery, so a canonical
    # database mid-maintenance fails the preflight instead of being touched.
    uri = canonical_db.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _baseline_complete(db: Database, source_id: str) -> bool:
    row = db.conn.execute("SELECT baseline_complete FROM source_state WHERE source_id=?", (source_id,)).fetchone()
    return bool(row and row[0])


def preflight_campaign(manifest: CampaignManifest) -> dict:
    """Fail-closed preflight. Raises CampaignError on any refusal; returns a
    summary for the campaign_start record. Never mutates the canonical
    database or its lock domain, and never creates the campaign database
    (a fresh start is created later, by run_campaign)."""
    approved = set(campaign_approved_source_ids())
    unapproved = [sid for sid in manifest.sources if sid not in approved]
    if unapproved:
        raise CampaignError(f"source(s) not approved for campaign soak: {', '.join(unapproved)}")
    effective_roster_hash = campaign_roster_hash(manifest.sources)
    if manifest.roster_hash and manifest.roster_hash != effective_roster_hash:
        raise CampaignError(f"roster hash mismatch: manifest={manifest.roster_hash} current={effective_roster_hash}")
    if manifest.environment:
        current = current_environment()
        for key in sorted(manifest.environment):
            if manifest.environment[key] != current.get(key):
                raise CampaignError(f"environment mismatch for {key}: manifest={manifest.environment[key]!r} current={current.get(key)!r}")
    lock_state = _canonical_lock_state(manifest.canonical_db)
    if lock_state != "clear" and lock_state != "stale":
        raise CampaignError(f"canonical lock domain is not clear: {lock_state}")
    if not manifest.canonical_db.exists():
        raise CampaignError(f"canonical database unavailable: {manifest.canonical_db}")
    try:
        ro = _open_canonical_readonly(manifest.canonical_db)
    except sqlite3.Error as exc:
        raise CampaignError(f"canonical database unavailable: {exc}") from exc
    try:
        try:
            canonical_integrity = ro.execute("PRAGMA integrity_check").fetchone()[0]
        except sqlite3.Error as exc:
            raise CampaignError(f"canonical database unavailable (read-only): {exc}") from exc
        if canonical_integrity != "ok":
            raise CampaignError(f"canonical database integrity is {canonical_integrity}")
        canonical_duplicates = ro.execute(_DUPLICATE_IDENTITY_SQL).fetchone()[0]
    finally:
        ro.close()
    if canonical_duplicates:
        raise CampaignError(f"canonical database has {canonical_duplicates} duplicate identities")

    campaign_info: dict = {"path": str(manifest.campaign_db)}
    if manifest.campaign_db.exists():
        db = Database(manifest.campaign_db)
        try:
            integrity = db.integrity()
            if integrity != "ok":
                raise CampaignError(f"campaign database integrity is {integrity}")
            duplicates = duplicate_identity_count(db)
            if duplicates:
                raise CampaignError(f"campaign database has {duplicates} duplicate identities")
            missing = [sid for sid in manifest.sources if not _baseline_complete(db, sid)]
            if missing:
                raise CampaignError(f"campaign baseline incomplete for: {', '.join(missing)}")
            campaign_info.update(state="resume", integrity=integrity, duplicates=duplicates)
        finally:
            db.close()
    else:
        campaign_info.update(state="fresh")
    return {
        "campaign": manifest.name,
        "sources": list(manifest.sources),
        "cycles": manifest.cycles,
        "interval_seconds": manifest.interval_seconds,
        "immediate_resight": manifest.immediate_resight,
        "roster_hash": effective_roster_hash,
        "manifest_sha256": manifest.sha256,
        "environment": current_environment(),
        "canonical": {
            "db": str(manifest.canonical_db), "lock_state": lock_state,
            "integrity": canonical_integrity, "duplicates": canonical_duplicates,
        },
        "campaign_db": campaign_info,
    }


def run_campaign(manifest_path, fixture_mode: bool = False, sleep=time.sleep) -> list[dict]:
    manifest = load_manifest(manifest_path)
    sources = [SOURCES[sid] for sid in manifest.sources]
    lock = SoakLock(lock_path_for_db(manifest.campaign_db), role=f"campaign:{manifest.name}")
    reports: list[dict] = []
    with lock:
        try:
            preflight = preflight_campaign(manifest)
        except CampaignError as exc:
            append_report(manifest.report_path, {
                "type": "campaign_refused", "campaign": manifest.name,
                "reason": str(exc), "ended_at": utcnow(),
            })
            raise
        append_report(manifest.report_path, {
            "type": "campaign_start", "campaign": manifest.name,
            "started_at": utcnow(), "manifest_path": str(manifest.path),
            "preflight": preflight, "fixture_mode": fixture_mode,
        })
        try:
            db = Database(manifest.campaign_db)
            try:
                for number in range(1, manifest.cycles + 1):
                    report = run_cycle(db, number, fixture_mode=fixture_mode, sources=sources)
                    reports.append(report)
                    append_report(manifest.report_path, report)
                    if report["status"] != "SUCCESS":
                        append_report(manifest.report_path, {
                            "type": "campaign_aborted", "campaign": manifest.name,
                            "reason": report["status"], "completed_cycles": len(reports),
                            "ended_at": utcnow(),
                        })
                        break
                    if number < manifest.cycles and (number > 1 or not manifest.immediate_resight):
                        sleep(manifest.interval_seconds)
            finally:
                db.close()
            append_report(manifest.report_path, {
                "type": "campaign_end", "campaign": manifest.name, "ended_at": utcnow(),
                "completed_cycles": len(reports),
                "status": reports[-1]["status"] if reports else "NO_CYCLES",
            })
        except KeyboardInterrupt:
            append_report(manifest.report_path, {
                "type": "campaign_interrupted", "campaign": manifest.name,
                "ended_at": utcnow(), "status": "INTERRUPTED",
                "completed_cycles": len(reports),
            })
            raise
    return reports
