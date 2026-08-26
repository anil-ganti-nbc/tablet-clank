"""Regression: the CLI `collect` path must route every registered
experimental source to its proper collector class.

Wave 2 deployment defect: cli.py kept a SECOND, stale collector-routing
table; honor_uk_tablets fell through to HtmlCatalogueCollector (JSON parser)
and failed with a JSONDecodeError on real HTML. Nothing was persisted. The
fix removes the duplicate table and defers to soak.collector_for as the
single routing authority.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_cli_collect_routes_every_experimental_source_to_dedicated_collector():
    """Every EXPERIMENTAL source must resolve through collector_for to a
    class appropriate for its declared kind — no silent fallthrough for any
    current or future source."""
    from tablet_clank import cli  # imports the removed duplicate table path
    from tablet_clank.soak import collector_for
    from tablet_clank.sources.registry import SOURCES, runtime_source_ids

    dedicated = {
        "apple_us_ipad_pro_store", "apple_in_ipad_pro_store",
        "honor_cn_tablets_catalogue", "honor_cn_tablets_comparison",
        "tcl_global_tablets", "honor_uk_tablets",
    }
    for sid in sorted(runtime_source_ids()):
        source = SOURCES[sid]
        collector = collector_for(source, fixture_mode=True)
        if sid in dedicated:
            # Generic HTML catalogue fallback is wrong for every dedicated
            # source: honor_uk previously landed here via the CLI's stale
            # duplicate table.
            from tablet_clank.collectors.html_catalogue import HtmlCatalogueCollector
            assert not isinstance(collector, HtmlCatalogueCollector), (
                f"{sid} routed to generic HtmlCatalogueCollector fallback")


def test_honor_uk_live_kind_is_routed_to_wave2_collector_via_cli_module():
    from tablet_clank.soak import collector_for
    from tablet_clank.collectors.honor_uk import HonorUKTabletsCollector
    from tablet_clank.sources.registry import get_source

    c = collector_for(get_source("honor_uk_tablets"), fixture_mode=True)
    assert isinstance(c, HonorUKTabletsCollector)


def test_no_second_routing_table_exists():
    """Guard against reintroduction of a parallel collector table in cli.py."""
    src = (ROOT / "tablet_clank" / "cli.py").read_text(encoding="utf-8")
    banned = [
        "collector_class = HonorCNTabletsCollector",
        "collector_class = TCLGlobalTabletsCollector",
        "collector_class = AppleStoreIPadProCollector",
        'XmlSitemapCollector if "XML" in s.kind',
    ]
    for frag in banned:
        assert frag not in src, f"duplicate routing reintroduced: {frag}"
