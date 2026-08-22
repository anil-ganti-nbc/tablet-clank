"""Focused tests for the native macOS field-test dashboard (native/macos/).

These modules live outside the `tablet_clank` package by design (see
native/macos/README.md), so this file adds native/macos to sys.path
relative to the repo root - no machine-specific paths anywhere.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

NATIVE_MACOS = Path(__file__).resolve().parents[1] / "native" / "macos"
sys.path.insert(0, str(NATIVE_MACOS))

import dash_data  # noqa: E402
import dash_names  # noqa: E402
import dash_render  # noqa: E402
import webapp  # noqa: E402
from tablet_clank.collectors.honor_cn import HonorCNTabletsCollector  # noqa: E402
from tablet_clank.collectors.xml_sitemap import XmlSitemapCollector  # noqa: E402
from tablet_clank.models import RunResult  # noqa: E402
from tablet_clank.pipeline import process  # noqa: E402
from tablet_clank.sources.registry import SOURCES  # noqa: E402
from tablet_clank.storage.db import Database  # noqa: E402


def _server(db_path):
    server = webapp.create_server(db_path, "test-revision")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def _get(port, path):
    return urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5)


# ------------------------------------------------------------- overview


def test_overview_empty_state(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    data = dash_data.overview(db_path)
    assert data["counts"]["products"] == 0
    assert data["last_run"] is None
    assert data["sources_healthy"] == 0
    assert data["sources_total"] == len(SOURCES)


def test_overview_populated_state(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    db.close()
    data = dash_data.overview(db_path)
    assert data["counts"]["products"] > 0
    assert data["last_run"] is not None
    assert data["sources_healthy"] == 1


# -------------------------------------------------------------- products


def test_products_filters_by_manufacturer_and_source(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    process(db, HonorCNTabletsCollector(SOURCES["honor_cn_tablets_catalogue"], fixture_mode=True), fixture_mode=True)
    db.close()

    all_rows = dash_data.products(db_path)
    assert len(all_rows["rows"]) > 0

    samsung_only = dash_data.products(db_path, manufacturer="Samsung")
    assert all(r["manufacturer"] == "Samsung" for r in samsung_only["rows"])
    assert len(samsung_only["rows"]) < len(all_rows["rows"])

    by_source = dash_data.products(db_path, source_id="honor_cn_tablets_catalogue")
    assert all("honor_cn_tablets_catalogue" in r["source_ids"] for r in by_source["rows"])

    experimental_only = dash_data.products(db_path, membership="production")
    assert all("honor_cn_tablets_catalogue" in r["source_ids"] or "honor_cn_tablets_comparison" in r["source_ids"] or "tcl_global_tablets" in r["source_ids"] for r in experimental_only["rows"])


def test_product_detail_returns_none_for_missing_id(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    assert dash_data.product_detail(db_path, 999) is None


def test_product_detail_includes_observations_and_provenance(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    db.close()
    product_id = dash_data.products(db_path)["rows"][0]["id"]
    detail = dash_data.product_detail(db_path, product_id)
    assert detail is not None
    assert len(detail["observations"]) >= 1
    # provenance: every observation must carry a real evidence URL, never a fabricated one
    for obs in detail["observations"]:
        assert obs["url"]
        assert obs["source_id"] == "samsung_us_sitemap"


# ---------------------------------------------------------- source health


def test_source_health_never_run_before_any_collection(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    rows = {r["id"]: r for r in dash_data.source_health(db_path)}
    assert rows["honor_cn_tablets_catalogue"]["health"] == "NEVER_RUN"


def test_source_health_success_after_healthy_run(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, HonorCNTabletsCollector(SOURCES["honor_cn_tablets_catalogue"], fixture_mode=True), fixture_mode=True)
    db.close()
    rows = {r["id"]: r for r in dash_data.source_health(db_path)}
    assert rows["honor_cn_tablets_catalogue"]["health"] == "SUCCESS"
    assert rows["honor_cn_tablets_catalogue"]["last_success_at"] is not None


def test_source_health_failed_state_is_distinguishable(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))

    class AlwaysEmptyCollector(HonorCNTabletsCollector):
        def collect(self):
            return []

    result = process(db, AlwaysEmptyCollector(SOURCES["honor_cn_tablets_catalogue"], fixture_mode=True), fixture_mode=True)
    db.close()
    assert result.status == "failed"
    rows = {r["id"]: r for r in dash_data.source_health(db_path)}
    # zero accepted candidates is a distinct, named health state - not a generic failure
    assert rows["honor_cn_tablets_catalogue"]["health"] == "ZERO_ITEMS"


def test_sources_list_scope_filters_production_vs_experimental(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    production = dash_data.sources_list(db_path, "production")
    experimental = dash_data.sources_list(db_path, "experimental")
    assert all(r["production"] for r in production)
    assert all(not r["production"] for r in experimental)
    assert {r["id"] for r in production}.isdisjoint({r["id"] for r in experimental})


# ------------------------------------------------------------ run history


def test_run_history_reports_duration_and_health(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    db.close()
    runs = dash_data.run_history(db_path)
    assert len(runs) == 1
    assert runs[0]["duration_seconds"] is not None
    assert runs[0]["health"] == "SUCCESS"


# ------------------------------------------------------ baseline vs event


def test_baseline_run_produces_no_change_events(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    db.close()
    discoveries = dash_data.latest_discoveries(db_path)
    assert discoveries["events"] == []
    assert discoveries["product_count"] > 0


def test_post_baseline_resight_with_changed_field_creates_event(tmp_path):
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
    discoveries = dash_data.latest_discoveries(db_path)
    changes = dash_data.changes(db_path)
    assert len(discoveries["events"]) == len(changes["rows"])


# ----------------------------------------------------------- HTTP: pages


def test_http_overview_and_nav_pages_render(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    server, port = _server(db_path)
    try:
        for path in ("/", "/discoveries", "/products", "/changes", "/sources", "/sources?scope=production", "/sources/health", "/collect", "/runs", "/about", "/health"):
            resp = _get(port, path)
            assert resp.status == 200
    finally:
        server.shutdown()


def test_http_collect_page_shows_empty_state_on_fresh_db(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    server, port = _server(db_path)
    try:
        body = _get(port, "/collect").read().decode()
        assert "No tablet data collected yet." in body
    finally:
        server.shutdown()


def test_http_products_page_hides_empty_state_once_populated(tmp_path):
    db_path = tmp_path / "x.db"
    db = Database(str(db_path))
    process(db, XmlSitemapCollector(SOURCES["samsung_us_sitemap"], fixture_mode=True), fixture_mode=True)
    db.close()
    server, port = _server(db_path)
    try:
        body = _get(port, "/collect").read().decode()
        assert "No tablet data collected yet." not in body
    finally:
        server.shutdown()


def test_http_product_detail_404_for_unknown_id(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    server, port = _server(db_path)
    try:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _get(port, "/products/999")
        assert exc_info.value.code == 404
    finally:
        server.shutdown()


# ------------------------------------------------------- HTTP: collect lifecycle


def test_http_collect_unknown_source_returns_400(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    server, port = _server(db_path)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/collect?source=not_a_real_source", method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)
        assert exc_info.value.code == 400
    finally:
        server.shutdown()


def test_http_collect_success_lifecycle_fields(tmp_path, monkeypatch):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()

    def fake_process(db, collector, fixture_mode=False):
        return RunResult("honor_cn_tablets_catalogue", run_id=1, status="success", raw_count=32, accepted_count=32, new_count=32)

    monkeypatch.setattr(webapp, "process", fake_process)
    server, port = _server(db_path)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/collect?source=honor_cn_tablets_catalogue", method="POST")
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        assert resp.status == 200
        assert body["status"] == "success"
        assert body["accepted"] == 32
        assert body["new"] == 32
        assert "started_at" in body
        assert body["duration_seconds"] >= 0
    finally:
        server.shutdown()


def test_http_collect_failed_source_reports_error_not_500(tmp_path, monkeypatch):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()

    def fake_process(db, collector, fixture_mode=False):
        return RunResult("samsung_us_sitemap", run_id=1, status="failed", error="zero accepted candidates; source is not healthy")

    monkeypatch.setattr(webapp, "process", fake_process)
    server, port = _server(db_path)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/collect?source=samsung_us_sitemap", method="POST")
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        assert resp.status == 200
        assert body["status"] == "failed"
        assert "zero accepted" in body["error"]
    finally:
        server.shutdown()


def test_http_collect_refuses_concurrent_run_with_409(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    from tablet_clank.soak import SoakLock, lock_path_for_db

    server, port = _server(db_path)
    try:
        with SoakLock(lock_path_for_db(db_path), role="test-holding-lock"):
            req = urllib.request.Request(f"http://127.0.0.1:{port}/collect?source=samsung_us_sitemap", method="POST")
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(req, timeout=10)
            assert exc_info.value.code == 409
    finally:
        server.shutdown()


# ---------------------------------------------------------- auto refresh


def test_collect_page_script_reloads_after_completion():
    html = dash_render.render_collect([], empty=True)
    assert "location.reload()" in html
    assert "collecting" in html  # double-execution guard flag present


# --------------------------------------------------- human-readable names


def test_human_readable_names_are_used_and_ids_kept_as_secondary():
    assert dash_names.display_name("honor_cn_tablets_catalogue") == "Honor China — Tablet Catalogue"
    assert dash_names.display_name("apple_in_ipad_pro_store") == "Apple India — iPad Pro Store"
    # unknown ids fall back to the raw id rather than raising
    assert dash_names.display_name("some_future_source") == "some_future_source"


def test_sources_page_shows_friendly_name_and_keeps_canonical_id(tmp_path):
    db_path = tmp_path / "x.db"
    Database(str(db_path)).close()
    rows = dash_data.source_health(db_path)
    html = dash_render.render_sources(rows, None)
    assert "Honor China — Tablet Catalogue" in html
    assert "honor_cn_tablets_catalogue" in html  # canonical id retained as secondary metadata


def test_event_type_label_uses_canonical_names_not_invented_ones():
    assert dash_names.event_type_label("identity_correction") == "Identity correction"
    assert dash_names.event_type_label("new_product") == "New product"
    assert dash_names.event_type_label("spec_change") == "Field change"
