"""Tablet-specific qualification projection over collector/campaign SQLite."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class QualificationProvenance(str, Enum):
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_provenance(value: QualificationProvenance | str | None) -> str:
    if isinstance(value, QualificationProvenance):
        return value.value
    try:
        return QualificationProvenance(str(value or "UNKNOWN").upper()).value
    except ValueError:
        return QualificationProvenance.UNKNOWN.value


def material_identity(inputs: dict[str, Any]) -> str:
    encoded = json.dumps({str(k): inputs[k] for k in sorted(inputs)}, sort_keys=True,
                         separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class QualificationContext:
    run_id: int
    scope_key: str
    epoch_id: int
    material_identity: str
    provenance: str
    gate_status: str


def _gate(conn, scope_key: str, epoch_id: int, material: str, provenance: str) -> dict[str, Any]:
    if provenance == QualificationProvenance.UNKNOWN.value:
        return {"eligible": False, "status": "UNKNOWN", "reason": "missing or untrusted provenance"}
    row = conn.execute(
        "SELECT 1 FROM qualification_terminals WHERE scope_key=? AND epoch_id=? "
        "AND material_identity=? AND status='success' AND counts_for_qualification=1 LIMIT 1",
        (scope_key, epoch_id, material),
    ).fetchone()
    if row is None:
        return {"eligible": False, "status": "NOT_QUALIFIED", "reason": "no qualifying terminal evidence in current epoch"}
    return {"eligible": True, "status": "QUALIFIED", "reason": "current epoch has qualifying terminal evidence"}


def prepare(db, *, run_id: int, scope_key: str, material: str,
            provenance: QualificationProvenance | str | None,
            reset_reason: str = "material identity changed") -> QualificationContext:
    if not scope_key:
        raise ValueError("qualification scope_key is required")
    provenance_value = normalize_provenance(provenance)
    conn = db.conn
    current = conn.execute(
        "SELECT epoch_id, material_identity FROM qualification_scopes WHERE scope_key=?",
        (scope_key,),
    ).fetchone()
    prior = current["material_identity"] if current else None
    if current is None or prior != material:
        next_number = (conn.execute(
            "SELECT COALESCE(MAX(epoch_number), 0) FROM qualification_epochs WHERE scope_key=?",
            (scope_key,),
        ).fetchone()[0] + 1)
        cur = conn.execute(
            "INSERT INTO qualification_epochs(scope_key, epoch_number, material_identity, prior_material_identity, reset_reason, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (scope_key, next_number, material, prior, None if current is None else reset_reason, utcnow()),
        )
        epoch_id = cur.lastrowid
        conn.execute(
            "INSERT INTO qualification_scopes(scope_key, epoch_id, material_identity, updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(scope_key) DO UPDATE SET epoch_id=excluded.epoch_id, material_identity=excluded.material_identity, updated_at=excluded.updated_at",
            (scope_key, epoch_id, material, utcnow()),
        )
        if current is not None:
            conn.execute(
                "INSERT OR IGNORE INTO qualification_resets(run_id, scope_key, epoch_id, prior_material_identity, new_material_identity, reason, provenance, created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (run_id, scope_key, epoch_id, prior, material, reset_reason, provenance_value, utcnow()),
            )
    else:
        epoch_id = current["epoch_id"]
    gate = _gate(conn, scope_key, epoch_id, material, provenance_value)
    conn.execute(
        "UPDATE collector_runs SET provenance=?, qualification_scope=?, qualification_epoch_id=?, qualification_material_identity=?, qualification_gate_status=? WHERE id=?",
        (provenance_value, scope_key, epoch_id, material, gate["status"], run_id),
    )
    conn.commit()
    return QualificationContext(run_id, scope_key, epoch_id, material, provenance_value, gate["status"])


def finish(db, context: QualificationContext, status: str) -> None:
    counts = int(status == "success" and context.provenance == QualificationProvenance.SCHEDULED.value)
    db.conn.execute(
        "INSERT OR IGNORE INTO qualification_terminals(run_id, scope_key, epoch_id, material_identity, provenance, status, counts_for_qualification, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (context.run_id, context.scope_key, context.epoch_id, context.material_identity, context.provenance, status, counts, utcnow()),
    )
    db.conn.commit()


def gate(db, scope_key: str, *, material: str | None = None) -> dict[str, Any]:
    row = db.conn.execute("SELECT epoch_id, material_identity FROM qualification_scopes WHERE scope_key=?", (scope_key,)).fetchone()
    if row is None:
        return {"eligible": False, "status": "UNKNOWN", "reason": "scope has no qualification epoch"}
    if material is not None and row["material_identity"] != material:
        return {"eligible": False, "status": "STALE", "reason": "material identity diverges from current epoch"}
    found = db.conn.execute(
        "SELECT 1 FROM qualification_terminals WHERE scope_key=? AND epoch_id=? AND status='success' AND counts_for_qualification=1 LIMIT 1",
        (scope_key, row["epoch_id"]),
    ).fetchone()
    return ({"eligible": True, "status": "QUALIFIED", "reason": "current epoch has qualifying terminal evidence"}
            if found else {"eligible": False, "status": "NOT_QUALIFIED", "reason": "no qualifying terminal evidence in current epoch"})


def reset_rows(db, scope_key: str) -> list:
    return db.conn.execute("SELECT * FROM qualification_resets WHERE scope_key=? ORDER BY id", (scope_key,)).fetchall()


def terminal_rows(db, scope_key: str) -> list:
    return db.conn.execute("SELECT * FROM qualification_terminals WHERE scope_key=? ORDER BY id", (scope_key,)).fetchall()
