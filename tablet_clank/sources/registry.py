from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
@dataclass(frozen=True)
class Source:
    id: str; manufacturer: str; region: str; kind: str; url: str; state: str; fixture: str | None = None

SOURCES = {
 "apple_in_sitemap": Source("apple_in_sitemap", "Apple", "IN", "regional HTML sitemap", "https://www.apple.com/in/sitemap/", "DISABLED", str(ROOT / "tests/fixtures/apple_sitemap.html")),
 "apple_us_ipad_pro_store": Source("apple_us_ipad_pro_store", "Apple", "US", "Apple Store iPad Pro configuration page", "https://www.apple.com/us/shop/buy-ipad/ipad-pro", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_store_us_ipad_pro.html")),
 "apple_in_ipad_pro_store": Source("apple_in_ipad_pro_store", "Apple", "IN", "Apple Store iPad Pro configuration page", "https://www.apple.com/in/shop/buy-ipad/ipad-pro", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_store_in_ipad_pro.html")),
 "samsung_us_sitemap": Source("samsung_us_sitemap", "Samsung", "US", "regional XML product sitemap", "https://www.samsung.com/us/top_sitemap.xml", "EXPERIMENTAL", str(ROOT / "tests/fixtures/samsung_sitemap.xml")),
 "honor_cn_tablets_catalogue": Source("honor_cn_tablets_catalogue", "Honor", "CN", "Honor China tablet catalogue", "https://www.honor.com/cn/tablets/", "EXPERIMENTAL", str(ROOT / "tests/fixtures/honor_cn_tablets_catalogue.json")),
 "honor_cn_tablets_comparison": Source("honor_cn_tablets_comparison", "Honor", "CN", "Honor China tablet comparison", "https://www.honor.com/cn/tablets/comparison/", "EXPERIMENTAL", str(ROOT / "tests/fixtures/honor_cn_tablets_comparison.json")),
 "tcl_global_tablets": Source("tcl_global_tablets", "TCL", "GLOBAL", "TCL global tablet catalogue", "https://www.tcl.com/global/en/tablets", "EXPERIMENTAL", str(ROOT / "tests/fixtures/tcl_global_tablets.html")),
}
PRODUCTION_ALLOWLIST: tuple[str, ...] = ()

def runtime_source_ids() -> tuple[str, ...]:
    """Single authority for enabled experimental runtime/soak membership."""
    return tuple(sorted(source_id for source_id, source in SOURCES.items() if source.state == "EXPERIMENTAL"))

def get_source(source_id): return SOURCES[source_id]
