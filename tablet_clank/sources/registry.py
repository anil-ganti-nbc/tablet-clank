from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
@dataclass(frozen=True)
class Source:
    id: str; manufacturer: str; region: str; kind: str; url: str; state: str; fixture: str | None = None

SOURCES = {
 "apple_in_sitemap": Source("apple_in_sitemap", "Apple", "IN", "regional HTML sitemap", "https://www.apple.com/in/sitemap/", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_sitemap.html")),
 "apple_us_ipad_pro_store": Source("apple_us_ipad_pro_store", "Apple", "US", "Apple Store iPad Pro configuration page", "https://www.apple.com/us/shop/buy-ipad/ipad-pro", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_store_us_ipad_pro.html")),
 "apple_in_ipad_pro_store": Source("apple_in_ipad_pro_store", "Apple", "IN", "Apple Store iPad Pro configuration page", "https://www.apple.com/in/shop/buy-ipad/ipad-pro", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_store_in_ipad_pro.html")),
 "samsung_us_sitemap": Source("samsung_us_sitemap", "Samsung", "US", "regional XML product sitemap", "https://www.samsung.com/us/top_sitemap.xml", "EXPERIMENTAL", str(ROOT / "tests/fixtures/samsung_sitemap.xml")),
}
PRODUCTION_ALLOWLIST: tuple[str, ...] = ()

def get_source(source_id): return SOURCES[source_id]
