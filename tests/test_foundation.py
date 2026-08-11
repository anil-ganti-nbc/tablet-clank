from tablet_clank.collectors.html_catalogue import HtmlCatalogueCollector
from tablet_clank.collectors.xml_sitemap import XmlSitemapCollector
from tablet_clank.collectors.apple_store import AppleStoreIPadProCollector
from tablet_clank.sources.registry import SOURCES
from tablet_clank.validation import validate
from tablet_clank.normalization import parse_ram,parse_storage,canonical_url
from tablet_clank.models import Candidate
from tablet_clank.storage.db import Database
from tablet_clank.pipeline import process
from tablet_clank.collectors.lenovo_psref import parse_psref_fixture

LENOVO_FIXTURE = "tests/fixtures/lenovo_psref_reduced.json"
LENOVO_CROSSCHECK_FIXTURE = "tests/fixtures/lenovo_psref_crosscheck.json"

def test_fixture_parsing_and_validation():
    cs=HtmlCatalogueCollector(SOURCES["apple_in_sitemap"],True); candidates=cs.collect()
    assert len(candidates)==4
    assert sum(validate(c)[0] for c in candidates)==2

def test_normalization_helpers():
    assert parse_ram("8 GB")==8; assert parse_storage("1TB")==1024; assert canonical_url("HTTPS://EXAMPLE.COM/a/?x=1")=="https://example.com/a"

def test_xml_sitemap_parsing():
    candidates=XmlSitemapCollector(SOURCES["samsung_us_sitemap"],True).collect()
    assert len(candidates)==3
    assert candidates[0].source_identifier=="SM-X930"
    assert sum(validate(c)[0] for c in candidates)==2

def test_apple_navigation_without_identifier_is_rejected():
    candidate=Candidate("apple_in_sitemap","Apple","IN","https://www.apple.com/in/ipad-pro","iPad Pro")
    assert validate(candidate)==(False,"no_stable_product_identifier")

def test_apple_store_us_fixture_parsing():
    candidates=AppleStoreIPadProCollector(SOURCES["apple_us_ipad_pro_store"],True).collect()
    assert len(candidates)==3
    assert candidates[0].source_identifier=="MDWK4LL/A"
    assert candidates[0].raw_values["display"]=="11-inch"
    assert candidates[0].raw_values["storage"]=="256 GB"
    assert candidates[0].raw_values["connectivity"]=="Wi-Fi"
    assert candidates[1].raw_values["connectivity"]=="Wi-Fi + Cellular"
    assert all(validate(candidate)[0] for candidate in candidates)

def test_apple_store_deduplicates_carrier_representations():
    candidates=AppleStoreIPadProCollector(SOURCES["apple_us_ipad_pro_store"],True).collect()
    assert len(candidates)==3
    assert candidates[1].raw_values["connectivity"]=="Wi-Fi + Cellular"

def test_apple_store_india_fixture_has_regional_part_numbers():
    candidates=AppleStoreIPadProCollector(SOURCES["apple_in_ipad_pro_store"],True).collect()
    assert len(candidates)==3
    assert all(candidate.source_identifier.endswith("HN/A") for candidate in candidates)
    assert len({candidate.source_identifier for candidate in candidates})==3

def test_apple_store_rejects_non_family_links():
    source=SOURCES["apple_us_ipad_pro_store"]
    class BadStoreCollector(AppleStoreIPadProCollector):
        def fetch(self):
            return '<script type="application/json">{"products":[{"partNumber":"X/A","basePartNumber":"X","dimensionCapacity":"256gb","dimensionScreensize":"11inch","dimensionConnection":"wifi","dimensionColor":"spaceblack"}]}</script><a href="/us/shop/buy-ipad/ipad-pro/11-inch-display-256gb-space-black-wifi-standard-glass-unlocked">iPad Pro</a><a href="/us/shop/buy-ipad/apple-pencil">Apple Pencil</a>'
    assert len(BadStoreCollector(source,False).collect())==1

def test_baseline_then_resight(tmp_path):
    db=Database(tmp_path/"x.db"); s=SOURCES["samsung_us_sitemap"]; c=XmlSitemapCollector(s,True)
    first=process(db,c); second=process(db,c)
    assert first.status=="success" and first.new_count==2
    assert second.status=="success" and second.new_count==0 and second.resighted_count==2
    assert db.conn.execute("SELECT COUNT(*) FROM change_events").fetchone()[0]==0
    assert db.integrity()=="ok"

def test_failure_is_recorded_and_does_not_raise(tmp_path):
    db=Database(tmp_path/"x.db")
    class Bad:
        source=SOURCES["apple_in_sitemap"]
        def collect(self): raise RuntimeError("blocked")
    result=process(db,Bad()); assert result.status=="failed" and "blocked" in result.error

def test_apple_identity_repair_is_not_new_product_event(tmp_path):
    db=Database(tmp_path/"x.db"); s=SOURCES["apple_us_ipad_pro_store"]
    class Sequence:
        source=s
        def __init__(self): self.calls=0
        def collect(self):
            self.calls += 1
            connectivity = "Wi-Fi" if self.calls == 1 else "Wi-Fi + Cellular"
            from tablet_clank.models import Candidate
            return [Candidate(s.id,"Apple","US","https://www.apple.com/us/shop/buy-ipad/ipad-pro/x","iPad Pro","TESTLL/A", {"family":"iPad Pro","sku":"TEST","storage":"256GB","display":"11-inch","colour":"Silver","connectivity":connectivity})]
    collector=Sequence(); first=process(db,collector); second=process(db,collector)
    assert first.status=="success" and second.status=="success"
    assert db.conn.execute("select event_type from change_events").fetchone()[0]=="identity_correction"

def test_apple_new_sku_remains_new_product_event(tmp_path):
    db=Database(tmp_path/"x.db"); s=SOURCES["apple_us_ipad_pro_store"]
    from tablet_clank.models import Candidate
    class One:
        source=s
        def __init__(self, sku): self.sku=sku
        def collect(self): return [Candidate(s.id,"Apple","US","https://www.apple.com/us/shop/buy-ipad/ipad-pro/x","iPad Pro",self.sku+"LL/A", {"family":"iPad Pro","sku":self.sku,"storage":"256GB","display":"11-inch","connectivity":"Wi-Fi"})]
    process(db,One("FIRST")); process(db,One("SECOND"))
    assert db.conn.execute("select count(*) from change_events where event_type='new_product'").fetchone()[0]==1

def test_lenovo_psref_preserves_identifiers_and_fields():
    candidates = parse_psref_fixture(LENOVO_FIXTURE)
    assert len(candidates) == 6  # seven source rows minus one exact duplicate
    p12 = next(c for c in candidates if c.source_identifier == "ZACH0239AU")
    assert p12.manufacturer == "Lenovo"
    assert p12.source_identifier == "ZACH0239AU"
    assert p12.region == "AU"
    assert p12.raw_values["machine_type"] == "ZACH"
    assert p12.raw_values["ram"] == "8GB Soldered LPDDR4x"
    assert p12.raw_values["storage"] == "128GB UFS 2.2 (uMCP)"
    assert p12.raw_values["announce_date"] == "2025-01-27"

def test_lenovo_psref_regional_codes_do_not_collapse():
    candidates = parse_psref_fixture(LENOVO_FIXTURE)
    p12 = [c for c in candidates if c.raw_values["family"] == "Tab P12"]
    assert {c.source_identifier for c in p12} == {"ZACH0239AU", "ZACL0045IN", "ZACL0046IN"}
    assert {c.region for c in p12} == {"AU", "IN"}

def test_lenovo_psref_wlan_wwan_remain_distinguishable():
    candidates = [c for c in parse_psref_fixture(LENOVO_FIXTURE) if c.raw_values["family"] == "Idea Tab"]
    assert {c.raw_values["connectivity"] for c in candidates} == {"WLAN", "WWAN"}
    assert len({c.identity_key for c in [__import__("tablet_clank.normalization", fromlist=["normalize_candidate"]).normalize_candidate(x) for x in candidates]}) == 2

def test_lenovo_psref_unknown_identifier_is_not_fabricated():
    candidates = parse_psref_fixture(LENOVO_FIXTURE)
    idea = next(c for c in candidates if c.raw_values["family"] == "Idea Tab")
    assert idea.source_identifier is None
    assert idea.raw_values["machine_type"] is None
    assert idea.raw_values["ean_upc_jan"] is None

def test_lenovo_psref_independent_legion_crosscheck():
    candidates = parse_psref_fixture(LENOVO_CROSSCHECK_FIXTURE)
    assert len(candidates) == 8
    assert {c.source_identifier for c in candidates} == {
        "ZACW0028IN", "ZACW0029IN", "ZACW0003GB", "ZACW0008SE",
        "ZACW0015ES", "ZACW0027UA", "ZACW0014KR", "ZACW0026GR",
    }
    assert {c.region for c in candidates} == {"IN", "GB", "SE", "ES", "UA", "KR", "GR"}
    assert all(c.raw_values["machine_type"] == "ZACW" for c in candidates)
    assert all(c.raw_values["processor"] == "Qualcomm Snapdragon 8+ Gen 1" for c in candidates)
    assert all(c.raw_values["connectivity"] == "Non-WWAN" for c in candidates)
    assert all(c.raw_values["source_document"].endswith("Legion_Tab?tab=model") for c in candidates)

def test_xiaomi_mimall_ids_are_preserved_but_mismatches_fail_closed():
    from tablet_clank.collectors.xiaomi_mimall import parse_mimall_fixture, probe_to_candidates
    pad7 = parse_mimall_fixture("tests/fixtures/xiaomi_mimall_pad7.json")
    pad8 = parse_mimall_fixture("tests/fixtures/xiaomi_mimall_pad8.json")
    assert pad7.product_id == "10050031"
    assert pad8.product_id == "19509"
    assert pad7.region == pad8.region == "CN"
    assert pad7.status == pad8.status == "identity_mismatch"
    assert pad7.raw_values["variant_id"] is None
    assert pad8.raw_values["ram"] is None
    assert probe_to_candidates(pad7) == []
    assert probe_to_candidates(pad8) == []

def test_xiaomi_mimall_verified_candidate_preserves_unknown_configuration_fields():
    from tablet_clank.collectors.xiaomi_mimall import MiMallProbe, probe_to_candidates
    probe = MiMallProbe(
        expected_product_name="Xiaomi Pad 7",
        requested_product_id="10050031",
        source_url="https://www.mi.com/shop/buy/detail?product_id=10050031",
        region="CN",
        observed_title="Xiaomi Pad 7",
        observed_category="tablet",
        status="matched_tablet",
        raw_values={"variant_id": "v1", "ram": "8GB", "storage": "128GB", "colour": None, "connectivity": None},
    )
    candidates = probe_to_candidates(probe)
    assert len(candidates) == 1
    assert candidates[0].manufacturer == "Xiaomi"
    assert candidates[0].source_identifier == "10050031"
    assert candidates[0].region == "CN"
    assert candidates[0].raw_values["colour"] is None

def test_honor_cn_catalogue_extracts_exact_products_and_filters_noise():
    from tablet_clank.collectors.honor_cn import parse_honor_cn_fixture
    candidates = parse_honor_cn_fixture("tests/fixtures/honor_cn_tablets_catalogue.json")
    assert [c.source_identifier for c in candidates] == ["honor-magicpad-3", "honor-magicpad-2", "honor-pad-v9"]
    assert all(c.manufacturer == "Honor" and c.region == "CN" for c in candidates)
    assert candidates[0].raw_values["family"] == "MagicPad"
    assert candidates[2].raw_values["family"] == "Pad V"
    assert all(c.raw_values.get("ram") is None for c in candidates)

def test_honor_cn_catalogue_and_comparison_overlap_and_exact_slug_deduplication():
    from tablet_clank.collectors.honor_cn import parse_honor_cn_fixture
    catalogue = parse_honor_cn_fixture("tests/fixtures/honor_cn_tablets_catalogue.json")
    comparison = parse_honor_cn_fixture("tests/fixtures/honor_cn_tablets_comparison.json")
    assert {c.source_identifier for c in catalogue} == {"honor-magicpad-3", "honor-magicpad-2", "honor-pad-v9"}
    assert {c.source_identifier for c in comparison} == {"honor-magicpad-3", "honor-magicpad-2", "honor-pad-v9", "honor-pad-9"}
    duplicate_fixture = "tests/fixtures/honor_cn_tablets_catalogue.json"
    assert len({c.source_identifier for c in parse_honor_cn_fixture(duplicate_fixture)}) == 3

def test_honor_cn_snapshot_stability_and_unseen_slug_contract():
    from tablet_clank.collectors.honor_cn import parse_honor_cn_fixture, unseen_slugs
    baseline = parse_honor_cn_fixture("tests/fixtures/honor_cn_tablets_catalogue.json")
    same = parse_honor_cn_fixture("tests/fixtures/honor_cn_tablets_catalogue.json")
    assert [c.source_identifier for c in baseline] == [c.source_identifier for c in same]
    assert unseen_slugs(baseline, same) == []
    synthetic = baseline + [same[0].__class__(
        source_id=same[0].source_id, manufacturer="Honor", region="CN",
        url="https://www.honor.com/cn/tablets/honor-pad-test-fixture/",
        title="TEST-ONLY synthetic Honor tablet", source_identifier="honor-pad-test-fixture",
        raw_values={"synthetic_test_only": True, "family": "Pad"})]
    assert unseen_slugs(baseline, synthetic) == ["honor-pad-test-fixture"]

def test_honor_cn_duplicate_slug_does_not_merge_similar_names():
    from tablet_clank.collectors.honor_cn import parse_honor_cn_fixture
    import json, tempfile
    payload = {"source_url": "https://www.honor.com/cn/tablets/", "capture_date": "2026-08-11", "surface": "test", "entries": [
        {"entry_type": "product", "category": "tablet", "name": "Honor Pad Alias A", "slug": "honor-pad-same", "url": "https://www.honor.com/cn/tablets/honor-pad-same/"},
        {"entry_type": "product", "category": "tablet", "name": "Honor Pad Alias B", "slug": "honor-pad-same", "url": "https://www.honor.com/cn/tablets/honor-pad-same/"},
        {"entry_type": "product", "category": "tablet", "name": "Honor Pad Different", "slug": "honor-pad-different", "url": "https://www.honor.com/cn/tablets/honor-pad-different/"}
    ]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as f:
        json.dump(payload, f, ensure_ascii=False); path = f.name
    try:
        candidates = parse_honor_cn_fixture(path)
        assert [c.source_identifier for c in candidates] == ["honor-pad-same", "honor-pad-different"]
    finally:
        __import__("pathlib").Path(path).unlink()

def test_tcl_global_catalogue_preserves_slugs_and_rejects_contamination():
    from tablet_clank.collectors.tcl_global import TCLGlobalTabletsCollector
    from tablet_clank.sources.registry import get_source
    candidates = TCLGlobalTabletsCollector(get_source("tcl_global_tablets"), fixture_mode=True).collect()
    assert [c.source_identifier for c in candidates] == [
        "tcl-tab-a1-plus", "tcl-tab-a1-plus-nxtpaper", "tcl-note-a1-nxtpaper",
        "tcl-tab-10-gen-4", "tcl-nxtpaper-11-gen-2", "tcl-nxtpaper-10s",
        "tcl-tab-10l", "tcl-tab8"
    ]
    assert len({c.source_identifier for c in candidates}) == 8
    assert all(c.manufacturer == "TCL" and c.region == "GLOBAL" for c in candidates)

def test_disabled_source_remains_inspectable_but_is_not_runtime_selectable():
    from tablet_clank.sources.registry import get_source, runtime_source_ids
    retired = get_source("apple_in_sitemap")
    assert retired.state == "DISABLED"
    assert retired.url == "https://www.apple.com/in/sitemap/"
    assert "apple_in_sitemap" not in runtime_source_ids()

def test_healthy_experimental_sources_remain_runtime_selectable():
    from tablet_clank.sources.registry import runtime_source_ids
    selected = set(runtime_source_ids())
    assert selected == {
        "apple_us_ipad_pro_store", "apple_in_ipad_pro_store", "samsung_us_sitemap",
        "honor_cn_tablets_catalogue", "honor_cn_tablets_comparison", "tcl_global_tablets",
    }

def test_soak_roster_resolves_exactly_and_rejects_drift(monkeypatch):
    import tablet_clank.soak as soak
    from tablet_clank.storage.db import Database
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        db = Database(f"{directory}/soak.db")
        assert [s.id for s in soak.resolve_soak_sources(db)] == sorted(soak.FROZEN_SOAK_SOURCE_IDS)
        monkeypatch.setattr(soak, "runtime_source_ids", lambda: tuple(sorted(soak.FROZEN_SOAK_SOURCE_IDS | {"unexpected_source"})))
        try:
            soak.resolve_soak_sources(db)
            assert False, "roster drift must refuse soak"
        except RuntimeError as exc:
            assert "roster drift" in str(exc)
        db.close()

def test_soak_lock_conflict_stale_recovery_and_cleanup():
    from tablet_clank.soak import SoakLock, SoakLockError
    import json, tempfile
    with tempfile.TemporaryDirectory() as directory:
        path = f"{directory}/tablet_clank.soak.lock"
        first = SoakLock(path); first.acquire()
        try:
            try:
                SoakLock(path).acquire()
                assert False, "active lock must refuse"
            except SoakLockError as exc:
                assert "active soak lock" in str(exc)
        finally:
            first.release()
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"pid": 999999, "role": "stale"}, handle)
        recovered = SoakLock(path); recovered.acquire(); assert recovered.acquired; recovered.release()
        assert not __import__("pathlib").Path(path).exists()

def test_soak_cycle_isolates_source_failure_and_reports_partial_failure(monkeypatch):
    import tablet_clank.soak as soak
    from tablet_clank.models import RunResult
    from tablet_clank.storage.db import Database
    import tempfile
    calls = []
    def fake_process(db, collector, fixture_mode=False):
        calls.append(collector.source.id)
        return RunResult(collector.source.id, status="failed" if len(calls) == 1 else "success", accepted_count=0 if len(calls) == 1 else 1)
    monkeypatch.setattr(soak, "process", fake_process)
    with tempfile.TemporaryDirectory() as directory:
        db = Database(f"{directory}/soak.db")
        report = soak.run_cycle(db, 1, fixture_mode=True)
        assert calls == sorted(soak.FROZEN_SOAK_SOURCE_IDS)
        assert report["status"] == "PARTIAL_FAILURE"
        assert len(report["sources"]) == 6
        db.close()

def test_soak_cycle_aborts_on_integrity_or_duplicate_failure(monkeypatch):
    import tablet_clank.soak as soak
    from tablet_clank.storage.db import Database
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        db = Database(f"{directory}/soak.db")
        monkeypatch.setattr(soak, "duplicate_identity_count", lambda db: 0)
        monkeypatch.setattr(db, "integrity", lambda: "broken")
        assert soak.run_cycle(db, 1, fixture_mode=True)["status"] == "SOAK_ABORTED_DB_INTEGRITY"
        monkeypatch.setattr(db, "integrity", lambda: "ok")
        monkeypatch.setattr(soak, "duplicate_identity_count", lambda db: 1)
        assert soak.run_cycle(db, 2, fixture_mode=True)["status"] == "SOAK_ABORTED_DUPLICATE_IDENTITY"
        db.close()

def test_soak_readiness_requires_all_baselines():
    import tablet_clank.soak as soak
    from tablet_clank.storage.db import Database
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        db = Database(f"{directory}/soak.db")
        try:
            soak.readiness_check(db)
            assert False, "missing baselines must refuse soak"
        except RuntimeError as exc:
            assert "baseline incomplete" in str(exc)
        db.close()

def test_bounded_soak_runs_without_real_sleep_and_writes_jsonl_report():
    import tablet_clank.soak as soak
    from tablet_clank.storage.db import Database
    import tempfile, json
    with tempfile.TemporaryDirectory() as directory:
        db_path = f"{directory}/soak.db"
        db = Database(db_path)
        soak.run_cycle(db, 0, fixture_mode=True)
        db.close()
        sleeps = []
        report_path = f"{directory}/logs/soak.jsonl"
        reports = soak.run_bounded(db_path, cycles=2, interval_seconds=7200, fixture_mode=True, report_path=report_path, sleep=sleeps.append)
        assert len(reports) == 2
        assert all(report["status"] == "SUCCESS" for report in reports)
        assert sleeps == [7200]
        records = [json.loads(line) for line in open(report_path, encoding="utf-8")]
        assert records[0]["type"] == "soak_start"
        assert [record["cycle"] for record in records[1:]] == [1, 2]
