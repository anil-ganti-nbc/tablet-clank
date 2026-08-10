from tablet_clank.collectors.html_catalogue import HtmlCatalogueCollector
from tablet_clank.sources.registry import SOURCES
from tablet_clank.validation import validate
from tablet_clank.normalization import parse_ram,parse_storage,canonical_url
from tablet_clank.storage.db import Database
from tablet_clank.pipeline import process

def test_fixture_parsing_and_validation():
    cs=HtmlCatalogueCollector(SOURCES["apple_in_sitemap"],True); candidates=cs.collect()
    assert len(candidates)==4
    assert sum(validate(c)[0] for c in candidates)==2

def test_normalization_helpers():
    assert parse_ram("8 GB")==8; assert parse_storage("1TB")==1024; assert canonical_url("HTTPS://EXAMPLE.COM/a/?x=1")=="https://example.com/a"

def test_baseline_then_resight(tmp_path):
    db=Database(tmp_path/"x.db"); s=SOURCES["samsung_us_sitemap"]; c=HtmlCatalogueCollector(s,True)
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
