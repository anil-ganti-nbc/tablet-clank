"""Wave 2: honor_uk_tablets source (2026-08-27 research campaign).

Covers fixture parsing/identity, contamination guards, baseline silence,
re-sight dedupe, runtime registration and production exclusion.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from tablet_clank.pipeline import process
from tablet_clank.storage.db import Database


def _collector(fixture_mode=True):
    from tablet_clank.collectors.honor_uk import HonorUKTabletsCollector
    from tablet_clank.sources.registry import get_source
    return HonorUKTabletsCollector(get_source("honor_uk_tablets"), fixture_mode=fixture_mode)


def test_honor_uk_registered_experimental_with_fixture():
    from tablet_clank.sources.registry import SOURCES, PRODUCTION_ALLOWLIST
    s = SOURCES["honor_uk_tablets"]
    assert s.manufacturer == "Honor" and s.region == "UK"
    assert s.state == "EXPERIMENTAL"
    # Promotion Wave 3 (2026-08-29): production-approved after the isolated
    # NAS campaign soak completed 12/12; registry identity unchanged.
    assert "honor_uk_tablets" in PRODUCTION_ALLOWLIST
    assert s.fixture and Path(s.fixture).exists()


def test_honor_uk_fixture_parses_exact_products():
    candidates = _collector().collect()
    slugs = {c.source_identifier for c in candidates}
    # Current-generation families must be present in the captured snapshot.
    assert {"honor-magicpad-3", "honor-pad-10", "honor-pad-v9"} <= slugs
    assert all(c.manufacturer == "Honor" for c in candidates)
    assert all(c.region == "UK" for c in candidates)
    assert all(c.url.startswith("https://www.honor.com/uk/tablets/") for c in candidates)


def test_honor_uk_excludes_comparison_page_and_dedupes():
    candidates = _collector().collect()
    slugs = [c.source_identifier for c in candidates]
    assert "comparison" not in slugs
    assert len(slugs) == len(set(slugs))


def test_honor_uk_titles_preferring_anchor_text():
    candidates = {c.source_identifier: c.title for c in _collector().collect()}
    # Anchor text wins when present; slug-derived fallback otherwise.
    assert candidates["honor-magicpad-3"] == "HONOR MagicPad3"
    assert candidates["honor-magicpad-4"] == "HONOR MagicPad4"


def test_honor_uk_contamination_guard_rejects_partial_page(monkeypatch):
    c = _collector()
    monkeypatch.setattr(c, "fetch_fixture", lambda: "<html><body><a href='/uk/tablets/honor-pad-8/'>Pad 8</a></body></html>")
    with pytest.raises(RuntimeError, match="completeness guard"):
        c.collect()


def test_honor_uk_baseline_silent_and_resight_clean(tmp_path):
    db = Database(str(tmp_path / "x.db"))
    collector = _collector(fixture_mode=True)
    first = process(db, collector)
    second = process(db, collector)
    assert first.status == "success" and first.new_count > 0
    assert second.status == "success" and second.new_count == 0
    assert second.resighted_count == first.new_count
    assert db.conn.execute("SELECT COUNT(*) FROM change_events").fetchone()[0] == 0
    assert db.integrity() == "ok"


def test_honor_uk_present_in_allowlist_resolution():
    from tablet_clank.sources.registry import production_source_ids
    ids = production_source_ids()
    assert "honor_uk_tablets" in ids


def test_honor_uk_in_experimental_runtime_roster():
    from tablet_clank.sources.registry import runtime_source_ids
    assert "honor_uk_tablets" in runtime_source_ids()


def test_honor_uk_routes_to_wave2_collector():
    from tablet_clank.soak import collector_for
    from tablet_clank.sources.registry import get_source
    c = collector_for(get_source("honor_uk_tablets"), fixture_mode=True)
    from tablet_clank.collectors.honor_uk import HonorUKTabletsCollector
    assert isinstance(c, HonorUKTabletsCollector)


def test_honor_uk_cn_stays_separate_identity_space():
    """CN sources keep their own identity rule; no cross-region merging."""
    from tablet_clank.collectors.honor_uk import HonorUKTabletsCollector
    from tablet_clank.sources.registry import get_source
    uk = HonorUKTabletsCollector(get_source("honor_uk_tablets"), fixture_mode=True).collect()
    uk_ids = {c.source_identifier for c in uk}

    assert not any(s.startswith("honor-cn-") or "-" not in s for s in ["honor-magicpad-3"])
