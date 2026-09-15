from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
#: States that mean "this source is not run at all". Everything else is an
#: active source. Kept as the exclusion list rather than an allow-list of
#: maturities so an EXPERIMENTAL source remains runnable without becoming
#: production-selected. The 2026-09-15 policy alignment restores that
#: distinction for Apple US/IN and Samsung US while preserving their state.
INACTIVE_STATES: frozenset[str] = frozenset({"DISABLED", "RETIRED"})


def is_active(source: "Source") -> bool:
    """True when a source may run at all. Maturity (PRODUCTION vs a future
    EXPERIMENTAL) is a separate axis from active/retired, and from health."""
    return source.state not in INACTIVE_STATES


@dataclass(frozen=True)
class Source:
    id: str; manufacturer: str; region: str; kind: str; url: str; state: str; fixture: str | None = None

SOURCES = {
 "apple_in_sitemap": Source("apple_in_sitemap", "Apple", "IN", "regional HTML sitemap", "https://www.apple.com/in/sitemap/", "DISABLED", str(ROOT / "tests/fixtures/apple_sitemap.html")),
 "apple_us_ipad_pro_store": Source("apple_us_ipad_pro_store", "Apple", "US", "Apple Store iPad Pro configuration page", "https://www.apple.com/us/shop/buy-ipad/ipad-pro", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_store_us_ipad_pro.html")),
 "apple_in_ipad_pro_store": Source("apple_in_ipad_pro_store", "Apple", "IN", "Apple Store iPad Pro configuration page", "https://www.apple.com/in/shop/buy-ipad/ipad-pro", "EXPERIMENTAL", str(ROOT / "tests/fixtures/apple_store_in_ipad_pro.html")),
 "samsung_us_sitemap": Source("samsung_us_sitemap", "Samsung", "US", "regional XML product sitemap", "https://www.samsung.com/us/top_sitemap.xml", "EXPERIMENTAL", str(ROOT / "tests/fixtures/samsung_sitemap.xml")),
 "honor_cn_tablets_catalogue": Source("honor_cn_tablets_catalogue", "Honor", "CN", "Honor China tablet catalogue", "https://www.honor.com/cn/tablets/", "PRODUCTION", str(ROOT / "tests/fixtures/honor_cn_tablets_catalogue.json")),
 "honor_cn_tablets_comparison": Source("honor_cn_tablets_comparison", "Honor", "CN", "Honor China tablet comparison", "https://www.honor.com/cn/tablets/comparison/", "PRODUCTION", str(ROOT / "tests/fixtures/honor_cn_tablets_comparison.json")),
 "tcl_global_tablets": Source("tcl_global_tablets", "TCL", "GLOBAL", "TCL global tablet catalogue", "https://www.tcl.com/global/en/tablets", "PRODUCTION", str(ROOT / "tests/fixtures/tcl_global_tablets.html")),
 "honor_uk_tablets": Source("honor_uk_tablets", "Honor", "UK", "Honor UK tablet storefront catalogue", "https://www.honor.com/uk/tablets/", "PRODUCTION", str(ROOT / "tests/fixtures/honor_uk_tablets.html")),
}
PRODUCTION_ALLOWLIST: tuple[str, ...] = (
    # Operator decision 2026-09-15: Tablet is intentionally dormant/manual,
    # and its production-selected policy roster is exactly Honor + TCL.
    # Apple US/IN and Samsung US retain their collectors, baselines, and
    # experimental maturity but are not production-selected.
    "honor_cn_tablets_catalogue",
    "honor_cn_tablets_comparison",
    "tcl_global_tablets",
    # Promotion Wave 3 (2026-08-29): honor-uk-iso-nas-001 completed 12/12 live
    # campaign cycles SUCCESS (0 events, 0 duplicates, canonical untouched).
    "honor_uk_tablets",
)

# Campaign-soak approval is a separate, narrower gate than the frozen soak
# roster: a source enters an isolated campaign only after an explicit
# frozen-roster review. Campaign approval never implies production
# eligibility — PRODUCTION_ALLOWLIST remains the only promotion path.
# Empty since 2026-08-29: honor_uk_tablets was promoted to production
# (Wave 3), retiring its campaign approval; no other source is
# campaign-approved.
CAMPAIGN_APPROVED_SOURCE_IDS: tuple[str, ...] = ()

ALERTS_ENABLED: bool = False

def runtime_source_ids() -> tuple[str, ...]:
    """Single authority for enabled runtime/soak membership (any active state)."""
    return tuple(sorted(source_id for source_id, source in SOURCES.items() if is_active(source)))

def production_source_ids() -> tuple[str, ...]:
    """Single authority for production-eligible membership: explicit allowlist AND active."""
    return tuple(sorted(source_id for source_id in PRODUCTION_ALLOWLIST if source_id in SOURCES and is_active(SOURCES[source_id])))

def campaign_approved_source_ids() -> tuple[str, ...]:
    """Single authority for campaign-soak eligible membership: explicitly campaign-approved, still experimental, and NOT production-allowlisted."""
    return tuple(sorted(
        source_id for source_id in CAMPAIGN_APPROVED_SOURCE_IDS
        if source_id in SOURCES and is_active(SOURCES[source_id]) and source_id not in PRODUCTION_ALLOWLIST
    ))

def get_source(source_id): return SOURCES[source_id]
