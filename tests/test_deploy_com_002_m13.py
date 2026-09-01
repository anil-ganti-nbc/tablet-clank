"""M13 regressions for Tablet's numbered SQLite compatibility barriers."""

import sqlite3
from pathlib import Path

import pytest

from tablet_clank.campaign import CampaignError, build_manifest, load_manifest, preflight_campaign
from tablet_clank.storage.db import Database, MIGRATIONS, SCHEMA_VERSION, SchemaCompatibilityError, inspect_compatibility
from tablet_clank.storage.qc_archive import QCArchive


def _prefix(path: Path, through: int):
    con = sqlite3.connect(path)
    try:
        con.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        for version, sql in MIGRATIONS[:through]:
            con.executescript(sql)
            con.execute("INSERT INTO schema_migrations VALUES (?, 'now')", (version,))
        con.commit()
    finally:
        con.close()


def test_fresh_current_and_old_prefix_contract(tmp_path):
    fresh = tmp_path / "fresh.db"
    assert inspect_compatibility(fresh).state == "FRESH" and not fresh.exists()
    db = Database(fresh)
    try:
        assert db.inspect_compatibility().ready and SCHEMA_VERSION == 3
    finally:
        db.close()
    old = tmp_path / "old.db"; _prefix(old, 2)
    assert inspect_compatibility(old).state == "MIGRATION_REQUIRED"
    # Construction is Tablet's documented canonical migration boundary.
    db = Database(old)
    db.close()
    assert inspect_compatibility(old).state == "COMPATIBLE"


def test_unknown_newer_partial_and_failed_migration_fail_closed(tmp_path, monkeypatch):
    unknown = tmp_path / "unknown.db"
    with sqlite3.connect(unknown) as con: con.execute("CREATE TABLE existing_state (id INTEGER)")
    assert inspect_compatibility(unknown).state == "UNKNOWN"
    with pytest.raises(SchemaCompatibilityError, match="UNKNOWN"): Database(unknown)
    newer = Database(tmp_path / "newer.db"); newer.close()
    with sqlite3.connect(newer.path) as con: con.execute("INSERT INTO schema_migrations VALUES (4, 'future')")
    assert inspect_compatibility(newer.path).state == "INCOMPATIBLE_NEWER"
    with pytest.raises(SchemaCompatibilityError, match="INCOMPATIBLE_NEWER"): Database(newer.path)
    partial = Database(tmp_path / "partial.db"); partial.close()
    with sqlite3.connect(partial.path) as con: con.execute("DROP TABLE qualification_terminals")
    assert inspect_compatibility(partial.path).state == "PARTIAL"
    with pytest.raises(SchemaCompatibilityError, match="PARTIAL"): Database(partial.path)


def test_qc_and_campaign_preflight_cannot_bypass_compatibility(tmp_path, monkeypatch):
    archive = QCArchive(tmp_path / "archive.db")
    assert archive.inspect_compatibility().ready
    unknown_qc = tmp_path / "unknown-qc.db"
    with sqlite3.connect(unknown_qc) as con: con.execute("CREATE TABLE qc_decisions (id INTEGER)")
    with pytest.raises(SchemaCompatibilityError, match="UNKNOWN"): QCArchive(unknown_qc)
    canonical = Database(tmp_path / "canonical.db"); canonical.close()
    with sqlite3.connect(canonical.path) as con: con.execute("INSERT INTO schema_migrations VALUES (4, 'future')")
    monkeypatch.setattr("tablet_clank.campaign.campaign_approved_source_ids", lambda: ("honor_uk_tablets",))
    manifest = build_manifest("m13", ["honor_uk_tablets"], 1, canonical_db=str(canonical.path), campaign_db=str(tmp_path / "campaign.db"))
    manifest_path = tmp_path / "manifest.json"; manifest_path.write_text(__import__("json").dumps(manifest), encoding="utf-8")
    with pytest.raises(CampaignError, match="compatibility is INCOMPATIBLE_NEWER"):
        preflight_campaign(load_manifest(manifest_path))
