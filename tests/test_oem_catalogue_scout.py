"""P0 OEM source scouts: fixture-only parsing and silent identity semantics.

No network, scheduled collection, production admission, or alerts are exercised.
"""

from pathlib import Path

import pytest

from tablet_clank.collectors.html_catalogue import HtmlCatalogueCollector
from tablet_clank.collectors.oem_catalogues import OEMTabletCatalogueCollector
from tablet_clank.models import Candidate
from tablet_clank.pipeline import process
from tablet_clank.soak import collector_for
from tablet_clank.sources.registry import (
    PRODUCTION_ALLOWLIST, SOURCES, is_active, runtime_source_ids,
)
from tablet_clank.storage.db import Database
from tablet_clank.validation import validate

P0 = (
    "alldocube_global_tablets",
    "teclast_global_tablets",
    "blackview_zeno_tablets",
)


@pytest.mark.parametrize("source_id,expected_count,anchor", [
    ("alldocube_global_tablets", 5, "iplay80miniturbo"),
    ("teclast_global_tablets", 10, "t/t70max"),
    ("blackview_zeno_tablets", 5, "zeno-6"),
])
def test_p0_offline_scoped_discovery(source_id, expected_count, anchor):
    source = SOURCES[source_id]
    collector = collector_for(source, fixture_mode=True)
    assert isinstance(collector, OEMTabletCatalogueCollector)
    assert not isinstance(collector, HtmlCatalogueCollector)
    candidates = collector.collect()
    assert len(candidates) == expected_count
    assert len({candidate.source_identifier for candidate in candidates}) == len(candidates)
    assert anchor in {candidate.source_identifier for candidate in candidates}
    assert all(candidate.source_identifier for candidate in candidates)
    assert all(candidate.raw_values["identifier_kind"] == "catalogue_slug" for candidate in candidates)
    assert all(validate(candidate)[0] for candidate in candidates)
    assert all(candidate.url.startswith("https://") for candidate in candidates)
    assert not any("impersonator" in candidate.url or "other.example" in candidate.url for candidate in candidates)


def test_blackview_category_does_not_fabricate_missing_zeno2():
    # The public ZENO 2 PDP exists but was absent from the observed 5-item
    # series index. A separate sitemap/product-URL lane is required.
    candidates = collector_for(SOURCES["blackview_zeno_tablets"], fixture_mode=True).collect()
    assert "zeno2" not in {candidate.source_identifier for candidate in candidates}
    assert "zeno-2" not in {candidate.source_identifier for candidate in candidates}


@pytest.mark.parametrize("source_id", P0)
def test_contamination_and_truncated_catalogues_fail_closed(source_id):
    collector = OEMTabletCatalogueCollector(SOURCES[source_id], fixture_mode=True)
    with pytest.raises(RuntimeError, match="completeness guard"):
        collector.parse_live("<html><title>Access Denied</title></html>")
    with pytest.raises(RuntimeError, match="missing known product anchors"):
        # Enough different syntactically valid products, but the known
        # catalogue anchors are absent. A login/redirect shell is not healthy.
        collector.parse_live(_fixture_text(source_id).replace(
            {"alldocube_global_tablets": "iplay80miniturbo",
             "teclast_global_tablets": "T70Max",
             "blackview_zeno_tablets": "zeno-6"}[source_id],
            {"alldocube_global_tablets": "iplay99new",
             "teclast_global_tablets": "T99New",
             "blackview_zeno_tablets": "zeno-99"}[source_id],
        ))


def _fixture_text(source_id):
    return Path(SOURCES[source_id].fixture).read_text(encoding="utf-8")


def test_registered_oem_scouts_do_not_change_runtime_or_delivery():
    from tablet_clank.sources.registry import ALERTS_ENABLED
    assert not ALERTS_ENABLED
    assert all(not is_active(SOURCES[s]) for s in P0)
    assert not (set(P0) & set(PRODUCTION_ALLOWLIST))
    assert not (set(P0) & set(runtime_source_ids()))


def test_silent_baseline_then_unseen_slug_event(tmp_path):
    source = SOURCES["alldocube_global_tablets"]
    collector = OEMTabletCatalogueCollector(source, fixture_mode=True)
    db = Database(tmp_path / "experimental.db")
    try:
        first = process(db, collector)
        second = process(db, collector)
        assert first.status == second.status == "success"
        assert first.new_count == 5
        assert second.new_count == 0 and second.resighted_count == 5
        assert db.conn.execute("SELECT count(*) FROM change_events").fetchone()[0] == 0

        class OneExtra(OEMTabletCatalogueCollector):
            def fetch_fixture(self):
                return _fixture_text(source.id).replace(
                    "</body>", '<a href="/en/products/iplay81mini/">iPlay 81 mini</a></body>'
                )

        delta = process(db, OneExtra(source, fixture_mode=True))
        assert delta.status == "success"
        assert delta.new_count == 1 and delta.resighted_count == 5
        events = db.conn.execute(
            "SELECT event_type,source_id FROM change_events ORDER BY id"
        ).fetchall()
        assert [(row[0], row[1]) for row in events] == [
            ("new_product", "alldocube_global_tablets")
        ]
        assert db.integrity() == "ok"
    finally:
        db.close()
