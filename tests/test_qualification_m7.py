from __future__ import annotations

from tablet_clank.qualification import (
    QualificationProvenance,
    gate,
    finish,
    material_identity,
    prepare,
    reset_rows,
    terminal_rows,
)
from tablet_clank.storage.db import Database


def _run(db, source, scope, material, provenance=QualificationProvenance.SCHEDULED):
    db.conn.execute(
        "INSERT OR IGNORE INTO sources(id,manufacturer,region,kind,url,state) VALUES (?,?,?,?,?,?)",
        (source, "M", "R", "K", "https://example.test/" + source, "EXPERIMENTAL"),
    )
    cur = db.conn.execute(
        "INSERT INTO collector_runs(source_id, started_at, status) VALUES (?,?,?)",
        (source, "2026-09-01T00:00:00+00:00", "running"),
    )
    db.conn.commit()
    context = prepare(
        db, run_id=cur.lastrowid, scope_key=scope,
        material=material_identity({"source": source, "material": material}),
        provenance=provenance,
    )
    return context


def test_first_changed_campaign_execution_resets_before_gate(tmp_path):
    db = Database(tmp_path / "qualification.db")
    try:
        first = _run(db, "source-a", "campaign:alpha:source-a", "A")
        finish(db, first, "success")
        assert gate(db, "campaign:alpha:source-a")["eligible"]

        changed = _run(db, "source-a", "campaign:alpha:source-a", "B")
        assert changed.epoch_id != first.epoch_id
        assert changed.gate_status == "NOT_QUALIFIED"
        assert not gate(db, "campaign:alpha:source-a")["eligible"]
        resets = reset_rows(db, "campaign:alpha:source-a")
        assert len(resets) == 1
        assert resets[0]["prior_material_identity"]
        assert resets[0]["new_material_identity"] != resets[0]["prior_material_identity"]

        finish(db, changed, "success")
        finish(db, changed, "success")
        assert len(terminal_rows(db, "campaign:alpha:source-a")) == 2
        assert gate(db, "campaign:alpha:source-a")["eligible"]
    finally:
        db.close()


def test_source_scope_isolation_and_unknown_provenance(tmp_path):
    db = Database(tmp_path / "qualification.db")
    try:
        a = _run(db, "source-a", "production:source-a", "A")
        finish(db, a, "success")
        b = _run(db, "source-b", "production:source-b", "B")
        finish(db, b, "success")
        assert gate(db, "production:source-a")["eligible"]
        assert gate(db, "production:source-b")["eligible"]

        _run(db, "source-a", "production:source-a", "A2")
        assert not gate(db, "production:source-a")["eligible"]
        assert gate(db, "production:source-b")["eligible"]

        unknown = _run(db, "source-c", "production:source-c", "C", QualificationProvenance.UNKNOWN)
        finish(db, unknown, "success")
        assert not gate(db, "production:source-c")["eligible"]
        assert terminal_rows(db, "production:source-c")[0]["provenance"] == "UNKNOWN"
    finally:
        db.close()


def test_migration_is_additive_and_existing_history_survives(tmp_path):
    path = tmp_path / "qualification.db"
    db = Database(path)
    db.conn.execute("INSERT INTO sources(id,manufacturer,region,kind,url,state) VALUES (?,?,?,?,?,?)", ("legacy", "M", "R", "K", "https://x", "EXPERIMENTAL"))
    cur = db.conn.execute("INSERT INTO collector_runs(source_id,started_at,status) VALUES (?,?,?)", ("legacy", "2026-09-01", "success"))
    db.conn.commit(); run_id = cur.lastrowid
    db.close()

    upgraded = Database(path)
    try:
        assert upgraded.conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 3
        row = upgraded.conn.execute("SELECT status, provenance FROM collector_runs WHERE id=?", (run_id,)).fetchone()
        assert row["status"] == "success" and row["provenance"] == "UNKNOWN"
        assert upgraded.integrity() == "ok"
    finally:
        upgraded.close()
