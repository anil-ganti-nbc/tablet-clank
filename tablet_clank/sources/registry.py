from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
@dataclass(frozen=True)
class Source:
    id: str; manufacturer: str; region: str; kind: str; url: str; state: str; fixture: str | None = None

SOURCES = {
 "apple_in_sitemap": Source("apple_in_sitemap", "Apple", "IN", "regional HTML sitemap", "https://www.apple.com/in/sitemap/", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_sitemap.html")),
 "samsung_us_sitemap": Source("samsung_us_sitemap", "Samsung", "US", "regional HTML sitemap", "https://www.samsung.com/us/sitemap/", "EXPERIMENTAL", str(ROOT / "tests/fixtures/samsung_sitemap.html")),
}
PRODUCTION_ALLOWLIST: tuple[str, ...] = ()

def get_source(source_id): return SOURCES[source_id]
