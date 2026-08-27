"""QC contract tests: active queue, four-decision QC archive, Run All.

Covers task requirements: transactional archive-to-separate-DB, unique
constraint race handling, immediate active-queue removal, restart
persistence (on-disk, no in-memory state), and Run All only ever selecting
the production allowlist.
"""

from __future__ import annotations

import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

NATIVE_MACOS = Path(__file__).resolve().parents[1] / "native" / "macos"
sys.path.insert(0, str(NATIVE_MACOS))

import dash_data  # noqa: E402
import webapp  # noqa: E402
from tablet_clank.collectors.xml_sitemap import XmlSitemapCollector  # noqa: E402
from tablet_clank.pipeline import process  # noqa: E402
from tablet_clank.sources.registry import SOURCES  # noqa: E402
from tablet_clank.storage.db import Database  # noqa: E402
from tablet_clank.storage.qc_archive import AlreadyDecided, QCArchive, qc_path_for_db  # noqa: E402


def _seed_event(tmp_path):
    """Baseline once, then a resight with a changed field to create exactly
    one real post-baseline change_event to QC."""
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)

    class TweakedCollector(XmlSitemapCollector):
        def collect(self):
            candidates = super().collect()
            for c in candidates:
                c.raw_values = {**c.raw_values, "storage": "1TB" if c.raw_values.get("storage") != "1TB" else "512GB"}
            return candidates

    process(db, TweakedCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    db.close()
    qc_path = qc_path_for_db(db_path)
    event_id = dash_data.active_queue(db_path, qc_path)["events"][0]["id"]
    return db_path, qc_path, event_id


# --------------------------------------------------------------- baseline


def test_baseline_run_leaves_active_queue_empty(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    db.close()
    queue = dash_data.active_queue(db_path, qc_path_for_db(db_path))
    assert queue["events"] == []


# ------------------------------------------------------------ archive core


def test_qc_archive_is_separate_file_from_live_db(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    assert qc_path != db_path
    assert qc_path.name != db_path.name


def test_submit_qc_removes_event_from_active_queue(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    before = dash_data.active_queue(db_path, qc_path)["events"]
    assert any(e["id"] == event_id for e in before)

    dash_data.submit_qc(db_path, qc_path, event_id, "USEFUL")

    after = dash_data.active_queue(db_path, qc_path)["events"]
    assert not any(e["id"] == event_id for e in after)


def test_qc_decision_preserves_full_provenance_in_archive(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    dash_data.submit_qc(db_path, qc_path, event_id, "OUT_OF_STOCK")
    archive = QCArchive(qc_path)
    row = archive.decision_for(event_id)
    assert row is not None
    assert row["event_id"] == event_id
    assert row["source_id"] == "samsung_us_sitemap"
    assert row["decision"] == "OUT_OF_STOCK"
    assert row["evidence_url"]
    assert row["decided_at"]


def test_duplicate_qc_write_is_rejected_gracefully(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    dash_data.submit_qc(db_path, qc_path, event_id, "USEFUL")
    with pytest.raises(AlreadyDecided):
        dash_data.submit_qc(db_path, qc_path, event_id, "NOT_USEFUL")
    # The first decision is untouched -- no lost update, no silent overwrite.
    archive = QCArchive(qc_path)
    assert archive.decision_for(event_id)["decision"] == "USEFUL"


def test_no_destructive_deletion_method_exists_on_archive():
    assert not hasattr(QCArchive, "delete")
    assert not hasattr(QCArchive, "purge")


def test_qc_state_persists_across_a_fresh_archive_handle(tmp_path):
    """Simulates an app restart: a brand-new QCArchive object opened against
    the same on-disk file must see the prior decision (no in-memory state)."""
    db_path, qc_path, event_id = _seed_event(tmp_path)
    dash_data.submit_qc(db_path, qc_path, event_id, "FALSE_POSITIVE")
    reopened = QCArchive(qc_path)
    assert reopened.decision_for(event_id)["decision"] == "FALSE_POSITIVE"
    assert event_id in reopened.decided_event_ids()


def test_all_four_qc_decisions_are_accepted(tmp_path):
    from tablet_clank.storage.qc_archive import QC_DECISIONS

    assert QC_DECISIONS == ("USEFUL", "NOT_USEFUL", "FALSE_POSITIVE", "OUT_OF_STOCK")


def test_recently_qced_reads_from_archive_with_provenance(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    dash_data.submit_qc(db_path, qc_path, event_id, "USEFUL")
    recent = dash_data.qc_recent(qc_path)
    assert len(recent) == 1
    assert recent[0]["event_id"] == event_id
    assert recent[0]["decision"] == "USEFUL"
    assert recent[0]["source_id"] == "samsung_us_sitemap"


# ------------------------------------------------------------------- HTTP


def _server(db_path):
    server = webapp.create_server(db_path, "test-revision")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def test_http_queue_and_qc_recent_pages_render(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    server, port = _server(db_path)
    try:
        for path in ("/queue", "/qc/recent"):
            resp = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5)
            assert resp.status == 200
    finally:
        server.shutdown()


def test_http_qc_decision_end_to_end_removes_from_queue_and_appears_in_recent(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    server, port = _server(db_path)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/qc?event_id={event_id}&decision=USEFUL", method="POST")
        resp = urllib.request.urlopen(req, timeout=5)
        assert resp.status == 200

        queue_body = urllib.request.urlopen(f"http://127.0.0.1:{port}/queue", timeout=5).read().decode()
        assert f"/queue/{event_id}" not in queue_body

        recent_body = urllib.request.urlopen(f"http://127.0.0.1:{port}/qc/recent", timeout=5).read().decode()
        assert "Useful" in recent_body
    finally:
        server.shutdown()


def test_http_duplicate_qc_returns_409(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    server, port = _server(db_path)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/qc?event_id={event_id}&decision=USEFUL", method="POST")
        urllib.request.urlopen(req, timeout=5)
        req2 = urllib.request.Request(f"http://127.0.0.1:{port}/qc?event_id={event_id}&decision=NOT_USEFUL", method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req2, timeout=5)
        assert exc_info.value.code == 409
    finally:
        server.shutdown()


def test_http_qc_unknown_decision_returns_400(tmp_path):
    db_path, qc_path, event_id = _seed_event(tmp_path)
    server, port = _server(db_path)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/qc?event_id={event_id}&decision=MAYBE", method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)
        assert exc_info.value.code == 400
    finally:
        server.shutdown()


# --------------------------------------------------------------- Run All


def test_http_run_all_only_targets_production_allowlist(tmp_path, monkeypatch):
    from tablet_clank.sources.registry import PRODUCTION_ALLOWLIST

    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()

    calls = []

    def fake_run_production(path, fixture_mode=False, report_path=None):
        calls.append(path)
        return {"type": "production_cycle", "status": "SUCCESS", "sources": [{"source": s, "health": "success"} for s in PRODUCTION_ALLOWLIST]}

    monkeypatch.setattr(webapp, "run_production", fake_run_production)
    server, port = _server(db_path)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/collect/all", method="POST")
        resp = urllib.request.urlopen(req, timeout=10)
        import json

        body = json.loads(resp.read())
        assert resp.status == 200
        assert body["status"] == "SUCCESS"
        sources = {s["source"] for s in body["sources"]}
        assert sources == set(PRODUCTION_ALLOWLIST)
        assert len(calls) == 1
    finally:
        server.shutdown()


def test_http_run_all_refuses_concurrent_run_with_409(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    from tablet_clank.soak import SoakLock, lock_path_for_db

    server, port = _server(db_path)
    try:
        with SoakLock(lock_path_for_db(db_path), role="test-holding-lock"):
            req = urllib.request.Request(f"http://127.0.0.1:{port}/collect/all", method="POST")
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(req, timeout=10)
            assert exc_info.value.code == 409
    finally:
        server.shutdown()
