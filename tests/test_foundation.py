from tablet_clank.collectors.html_catalogue import HtmlCatalogueCollector
from tablet_clank.collectors.xml_sitemap import XmlSitemapCollector
from tablet_clank.collectors.apple_store import AppleStoreIPadProCollector
from tablet_clank.sources.registry import SOURCES
from tablet_clank.validation import validate
from tablet_clank.normalization import parse_ram,parse_storage,canonical_url
from tablet_clank.models import Candidate
from tablet_clank.storage.db import Database
from tablet_clank.pipeline import process

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
