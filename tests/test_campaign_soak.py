"""Campaign-scoped isolated soak runner (2026-08-28).

Covers manifest authoring/validation, fail-closed preflight refusals,
campaign lock scoping, roster isolation from the frozen soak roster,
baseline/resight behavior on the isolated database, canonical write
isolation, resume behavior, and refusal/abort/interruption evidence
records. No test touches the repository's real var/ tree: all manifest,
canonical, campaign, and report paths are per-test tmp_path absolutes.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
import os

import pytest

from tablet_clank.storage.db import Database


def _write_manifest(directory: Path, **overrides) -> Path:
    from tablet_clank.campaign import build_manifest
    manifest = build_manifest(
        overrides.pop("campaign", "honor-uk-test"),
        overrides.pop("sources", ["honor_uk_tablets"]),
        cycles=overrides.pop("cycles", 3),
        interval_seconds=overrides.pop("interval_seconds", 7200.0),
        canonical_db=overrides.pop("canonical_db", str(directory / "canonical.db")),
        campaign_db=str(directory / "campaign" / "tablet_clank.db"),
        report_path=str(directory / "soak.jsonl"),
    )
    manifest.update(overrides)
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _make_canonical(directory: Path) -> Path:
    db = Database(directory / "canonical.db")
    db.close()
    return directory / "canonical.db"


def _report_records(directory: Path) -> list[dict]:
    return [json.loads(line) for line in (directory / "soak.jsonl").read_text(encoding="utf-8").splitlines()]


@pytest.fixture()
def _campaign_approved_honor_uk(monkeypatch):
    """No source is campaign-approved since the honor_uk promotion (Wave 3);
    tests that exercise the post-approval preflight/runner path simulate an
    approved source. Refusal-path tests stay unpatched on purpose."""
    import tablet_clank.campaign as campaign_module
    monkeypatch.setattr(
        campaign_module, "campaign_approved_source_ids", lambda: ("honor_uk_tablets",)
    )


def test_build_manifest_pins_roster_hash_and_environment():
    from tablet_clank.campaign import build_manifest, campaign_roster_hash, current_environment
    manifest = build_manifest("honor-uk-test", ["honor_uk_tablets"], cycles=12, interval_seconds=7200)
    assert manifest["sources"] == ["honor_uk_tablets"]
    assert manifest["roster_hash"] == campaign_roster_hash(["honor_uk_tablets"])
    assert manifest["environment"] == current_environment()
    assert manifest["immediate_resight"] is True


def test_manifest_validation_refuses_bad_names_sources_and_keys(tmp_path):
    from tablet_clank.campaign import CampaignError, build_manifest
    with pytest.raises(CampaignError, match="campaign name"):
        build_manifest("Not_A_Valid_Name", ["honor_uk_tablets"], cycles=1)
    with pytest.raises(CampaignError, match="unknown source"):
        build_manifest("honor-uk-test", ["not_a_registered_source"], cycles=1)
    with pytest.raises(CampaignError, match="duplicates"):
        build_manifest("honor-uk-test", ["honor_uk_tablets", "honor_uk_tablets"], cycles=1)
    with pytest.raises(CampaignError, match="cycles"):
        build_manifest("honor-uk-test", ["honor_uk_tablets"], cycles=0)
    with pytest.raises(CampaignError, match="interval_seconds"):
        build_manifest("honor-uk-test", ["honor_uk_tablets"], cycles=1, interval_seconds=-1)
    from tablet_clank.campaign import _validate_manifest_data
    partial = build_manifest("honor-uk-test", ["honor_uk_tablets"], cycles=1)
    del partial["sources"]
    with pytest.raises(CampaignError, match="missing required keys"):
        _validate_manifest_data(partial)
    with pytest.raises(CampaignError, match="unknown keys"):
        _validate_manifest_data({**build_manifest("honor-uk-test", ["honor_uk_tablets"], cycles=1), "sorce": "typo"})


def test_manifest_rejects_campaign_db_colliding_with_canonical(tmp_path):
    from tablet_clank.campaign import CampaignError, build_manifest
    canonical = _make_canonical(tmp_path)
    manifest = build_manifest("honor-uk-test", ["honor_uk_tablets"], cycles=1, canonical_db=str(canonical))
    manifest["campaign_db"] = str(canonical)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    from tablet_clank.campaign import load_manifest
    with pytest.raises(CampaignError, match="isolated from the canonical"):
        load_manifest(path)


def test_preflight_refuses_unapproved_sources(tmp_path):
    from tablet_clank.campaign import CampaignError, load_manifest, preflight_campaign
    canonical = _make_canonical(tmp_path)
    # Production-allowlisted sources are never campaign-approved…
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical), sources=["tcl_global_tablets"])
    with pytest.raises(CampaignError, match="not approved for campaign soak"):
        preflight_campaign(load_manifest(manifest_path))
    # …and neither are experimental sources that simply lack campaign review.
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical), sources=["apple_us_ipad_pro_store"])
    with pytest.raises(CampaignError, match="not approved for campaign soak"):
        preflight_campaign(load_manifest(manifest_path))


def test_preflight_refuses_roster_hash_drift(tmp_path, monkeypatch, _campaign_approved_honor_uk):
    from dataclasses import replace
    import tablet_clank.campaign as campaign_module
    from tablet_clank.campaign import CampaignError, load_manifest, preflight_campaign
    from tablet_clank.sources.registry import SOURCES
    canonical = _make_canonical(tmp_path)
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical), roster_hash="deadbeef")
    with pytest.raises(CampaignError, match="roster hash mismatch"):
        preflight_campaign(load_manifest(manifest_path))
    # Real drift: a post-authoring registry state flip must refuse the run.
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical))
    drifted = {**SOURCES, "honor_uk_tablets": replace(SOURCES["honor_uk_tablets"], state="DISABLED")}
    monkeypatch.setattr(campaign_module, "SOURCES", drifted)
    with pytest.raises(CampaignError, match="roster hash mismatch"):
        preflight_campaign(load_manifest(manifest_path))


def test_preflight_refuses_environment_mismatch(tmp_path, _campaign_approved_honor_uk):
    from tablet_clank.campaign import CampaignError, load_manifest, preflight_campaign
    canonical = _make_canonical(tmp_path)
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical),
                                    environment={"python_version": "3.0.0", "platform": "win32"})
    with pytest.raises(CampaignError, match="environment mismatch"):
        preflight_campaign(load_manifest(manifest_path))


def test_preflight_refuses_missing_canonical_database(tmp_path, _campaign_approved_honor_uk):
    from tablet_clank.campaign import CampaignError, load_manifest, preflight_campaign
    manifest_path = _write_manifest(tmp_path, canonical_db=str(tmp_path / "does_not_exist.db"))
    with pytest.raises(CampaignError, match="canonical database unavailable"):
        preflight_campaign(load_manifest(manifest_path))


def test_preflight_refuses_active_or_unreadable_canonical_lock_but_tolerates_stale(tmp_path, monkeypatch, _campaign_approved_honor_uk):
    from tablet_clank.campaign import CampaignError, load_manifest, preflight_campaign, _canonical_lock_state
    from tablet_clank.soak import lock_path_for_db
    import tablet_clank.soak as soak_module
    canonical = _make_canonical(tmp_path)
    lock_file = lock_path_for_db(canonical)
    lock_file.write_text(json.dumps({"pid": os.getpid(), "role": "production"}), encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical))
    with pytest.raises(CampaignError, match="canonical lock domain is not clear: active"):
        preflight_campaign(load_manifest(manifest_path))
    lock_file.write_text("not json at all", encoding="utf-8")
    with pytest.raises(CampaignError, match="canonical lock domain is not clear: unreadable"):
        preflight_campaign(load_manifest(manifest_path))
    # A stale lock (dead owner) is inactive; the campaign may proceed but
    # must never remove a canonical lock file it did not create.
    lock_file.write_text(json.dumps({"pid": 123456, "role": "stale"}), encoding="utf-8")
    monkeypatch.setattr(soak_module, "_pid_alive", lambda pid: False)
    preflight = preflight_campaign(load_manifest(manifest_path))
    assert preflight["canonical"]["lock_state"] == "stale"
    assert lock_file.exists()


def test_campaign_baseline_resight_is_immediate_and_canonical_stays_untouched(tmp_path, _campaign_approved_honor_uk):
    from tablet_clank.campaign import run_campaign
    canonical = _make_canonical(tmp_path)
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical), cycles=3)
    sleeps: list[float] = []
    reports = run_campaign(manifest_path, fixture_mode=True, sleep=sleeps.append)
    assert len(reports) == 3
    assert all(report["status"] == "SUCCESS" for report in reports)
    # Campaign shape: baseline (cycle 1) is followed IMMEDIATELY by the
    # resight (cycle 2); the interval only applies between later cycles.
    assert sleeps == [7200]
    baseline = reports[0]["sources"][0]
    resight = reports[1]["sources"][0]
    assert baseline["source"] == "honor_uk_tablets"
    assert baseline["new"] > 0 and baseline["events"] == []
    assert resight["new"] == 0 and resight["resighted"] == baseline["new"]
    assert resight["events"] == []
    records = _report_records(tmp_path)
    assert records[0]["type"] == "campaign_start"
    assert records[0]["preflight"]["campaign_db"]["state"] == "fresh"
    assert [record["cycle"] for record in records[1:-1]] == [1, 2, 3]
    assert records[-1]["type"] == "campaign_end"
    assert records[-1]["completed_cycles"] == 3
    # Canonical write isolation: the campaign must leave zero rows behind.
    check = Database(canonical)
    try:
        assert check.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
        assert check.conn.execute("SELECT COUNT(*) FROM collector_runs").fetchone()[0] == 0
    finally:
        check.close()


def test_campaign_resume_reuses_baseline_and_refuses_when_missing(tmp_path, _campaign_approved_honor_uk):
    from tablet_clank.campaign import CampaignError, run_campaign
    canonical = _make_canonical(tmp_path)
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical))
    run_campaign(manifest_path, fixture_mode=True, sleep=lambda seconds: None)
    reports = run_campaign(manifest_path, fixture_mode=True, sleep=lambda seconds: None)
    assert len(reports) == 3
    assert reports[0]["sources"][0]["new"] == 0 and reports[0]["sources"][0]["resighted"] > 0
    campaign_db = tmp_path / "campaign" / "tablet_clank.db"
    db = Database(campaign_db)
    try:
        db.conn.execute("DELETE FROM source_state")
        db.conn.commit()
    finally:
        db.close()
    with pytest.raises(CampaignError, match="campaign baseline incomplete"):
        run_campaign(manifest_path, fixture_mode=True, sleep=lambda seconds: None)


def test_campaign_aborts_on_first_unhealthy_cycle(tmp_path, monkeypatch, _campaign_approved_honor_uk):
    import tablet_clank.campaign as campaign_module
    canonical = _make_canonical(tmp_path)
    for status in ("PARTIAL_FAILURE", "SOAK_ABORTED_DB_INTEGRITY"):
        directory = tmp_path / status
        directory.mkdir()
        manifest_path = _write_manifest(directory, canonical_db=str(canonical), cycles=5)

        def unhealthy(db, number, fixture_mode=False, *, sources=None, _status=status):
            return {"cycle": number, "status": _status, "sources": []}
        monkeypatch.setattr(campaign_module, "run_cycle", unhealthy)
        reports = campaign_module.run_campaign(manifest_path, fixture_mode=True, sleep=lambda seconds: None)
        assert len(reports) == 1
        records = _report_records(directory)
        aborted = [record for record in records if record.get("type") == "campaign_aborted"]
        assert len(aborted) == 1
        assert aborted[0]["reason"] == status
        assert aborted[0]["completed_cycles"] == 1
        assert records[-1].get("type") == "campaign_end"
        assert records[-1]["completed_cycles"] == 1


def test_campaign_refusal_writes_refused_evidence_record(tmp_path, _campaign_approved_honor_uk):
    from tablet_clank.campaign import CampaignError, run_campaign
    canonical = _make_canonical(tmp_path)
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical), roster_hash="deadbeef")
    with pytest.raises(CampaignError, match="roster hash mismatch"):
        run_campaign(manifest_path, fixture_mode=True, sleep=lambda seconds: None)
    records = _report_records(tmp_path)
    assert records[-1]["type"] == "campaign_refused"
    assert "roster hash mismatch" in records[-1]["reason"]


def test_campaign_lock_conflict_refuses(tmp_path):
    from tablet_clank.campaign import run_campaign
    from tablet_clank.soak import SoakLockError, lock_path_for_db
    canonical = _make_canonical(tmp_path)
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical))
    campaign_db = tmp_path / "campaign" / "tablet_clank.db"
    campaign_db.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path_for_db(campaign_db)
    lock_file.write_text(json.dumps({"pid": os.getpid(), "role": "campaign:honor-uk-test"}), encoding="utf-8")
    with pytest.raises(SoakLockError, match="active soak lock"):
        run_campaign(manifest_path, fixture_mode=True, sleep=lambda seconds: None)


def test_keyboard_interrupt_records_interruption(tmp_path, _campaign_approved_honor_uk):
    from tablet_clank.campaign import run_campaign
    canonical = _make_canonical(tmp_path)
    manifest_path = _write_manifest(tmp_path, canonical_db=str(canonical), cycles=3)

    def interrupting_sleep(seconds):
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        run_campaign(manifest_path, fixture_mode=True, sleep=interrupting_sleep)
    records = _report_records(tmp_path)
    # Cycle 1 (baseline) flows straight into cycle 2 (resight); the first
    # interval sleep is where the interrupt lands.
    assert records[0]["type"] == "campaign_start"
    assert [record["cycle"] for record in records[1:-1]] == [1, 2]
    assert records[-1]["type"] == "campaign_interrupted"
    assert records[-1]["completed_cycles"] == 2


def test_registry_campaign_roster_empty_after_honor_uk_promotion():
    """Promotion Wave 3 (2026-08-29): honor_uk_tablets moved to
    PRODUCTION_ALLOWLIST and its campaign approval was retired. A promoted
    source must not remain campaign-eligible."""
    from tablet_clank.sources.registry import (
        CAMPAIGN_APPROVED_SOURCE_IDS,
        campaign_approved_source_ids,
        production_source_ids,
        runtime_source_ids,
    )
    assert set(CAMPAIGN_APPROVED_SOURCE_IDS) == set()
    assert campaign_approved_source_ids() == ()
    assert "honor_uk_tablets" in production_source_ids()
    assert set(campaign_approved_source_ids()).isdisjoint(production_source_ids())
    assert "honor_uk_tablets" in runtime_source_ids()


def test_run_cycle_sources_override_isolates_from_frozen_roster(tmp_path):
    from tablet_clank.soak import run_cycle
    from tablet_clank.sources.registry import SOURCES
    db = Database(tmp_path / "campaign.db")
    try:
        report = run_cycle(db, 1, fixture_mode=True, sources=[SOURCES["honor_uk_tablets"]])
        assert report["status"] == "SUCCESS"
        assert [item["source"] for item in report["sources"]] == ["honor_uk_tablets"]
    finally:
        db.close()


def test_cli_soak_campaign_init_check_run_and_refusal(tmp_path, capsys, _campaign_approved_honor_uk):
    from tablet_clank import cli
    canonical = _make_canonical(tmp_path)
    manifest_path = tmp_path / "cli-campaign.json"
    campaign_db = tmp_path / "campaign" / "tablet_clank.db"
    report_path = tmp_path / "soak.jsonl"
    rc = cli.main([
        "soak-campaign", "--manifest", str(manifest_path), "--init",
        "--campaign", "cli-campaign", "--sources", "honor_uk_tablets",
        "--cycles", "2", "--canonical-db", str(canonical),
        "--campaign-db", str(campaign_db), "--report-path", str(report_path),
    ])
    assert rc == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["campaign"] == "cli-campaign" and manifest["roster_hash"]
    capsys.readouterr()
    rc = cli.main(["soak-campaign", "--manifest", str(manifest_path), "--check"])
    assert rc == 0
    preflight = json.loads(capsys.readouterr().out)
    assert preflight["campaign"] == "cli-campaign"
    assert preflight["campaign_db"]["state"] == "fresh"
    capsys.readouterr()
    rc = cli.main(["soak-campaign", "--manifest", str(manifest_path)])
    assert rc == 0
    cycle_lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(cycle_lines) == 2
    assert all(json.loads(line)["status"] == "SUCCESS" for line in cycle_lines)
    # Tampered roster hash must refuse with the standard refusal contract.
    manifest["roster_hash"] = "deadbeef"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    rc = cli.main(["soak-campaign", "--manifest", str(manifest_path), "--check"])
    assert rc == 2
    assert "campaign refused" in capsys.readouterr().out
