PROJECT
Tablet Clank

PHASE
Pre-soak roster frozen; bounded soak runner implemented, not started

PRODUCTION
Allowlist empty; scheduling absent; alerts disabled

DATABASE
var/tablet_clank.db; integrity ok; 225 products, 847 observations, 27 runs, 1421 rejected candidates, 48 events; 48 identity_correction, 0 duplicate identity keys

SCHEMA
1

TESTS
python -m pytest -q -rA; passed=32 failed=0 skipped=0 xfailed=0

SOURCES
apple_in_sitemap=DISABLED/RETIRED, post-fix run failed closed 372/0/372/0; historical baseline untrusted; excluded from runtime/soak
apple_us_ipad_pro_store=EXPERIMENTAL, run 14 48/48/0/48, 0 new, 48 resighted; 24 historical identity_correction events
apple_in_ipad_pro_store=EXPERIMENTAL, run 15 48/48/0/48, 0 new, 48 resighted; 24 historical identity_correction events
samsung_us_sitemap=EXPERIMENTAL, official XML replacement live, run 3 4/4/0/4 then run 4 4/3/1/3 resight; unchanged
honor_cn_tablets_catalogue=EXPERIMENTAL, runs 16/18 32/32/0/32 baseline/resight; 0 events
honor_cn_tablets_comparison=EXPERIMENTAL, runs 17/19 24/24/0/24 baseline/resight; 0 events
tcl_global_tablets=EXPERIMENTAL, runs 20/21 24/24/0/24 baseline/resight; 0 events

KNOWN_GOOD
Fixture parsing, offline Lenovo PSREF reduced-fixture parsing, exact PSREF identifier preservation, PSREF regional separation, WLAN/WWAN distinction, Apple Store structured configuration parsing, regional SKU extraction, carrier deduplication, corrected US/IN resighting, XML sitemap parsing, conservative validation, SQLite integrity, failure recording

KNOWN_BROKEN
Apple regional HTML sitemap is retired from runtime after failing closed; Store-SKU to A-number mapping is unresolved; early Apple Store identity repairs remain historical evidence; Lenovo PSREF live model-table retrieval is not reliable through safe non-browser requests

XIAOMI_RESEARCH
China Mi Mall tablet catalogue/detail pages remain a discovery lead, but the requested IDs 10050031 and 19509 currently resolve to unrelated products on direct official inspection. Offline mismatch fixtures fail closed; numeric product ID and variant identity are unproven. Xiaomi runtime source, products, observations, runs and baseline are absent.

HONOR_RESEARCH
Honor China/global tablet catalogues and comparison pages are promising discovery surfaces. The China catalogue and comparison pages passed a six-read live stability audit; product slugs and regulatory model identifiers appear stronger than Xiaomi numeric commerce IDs, but store/configuration identifier durability is only partially proven. Recommended strategy: MULTI_SOURCE_REQUIRED. Honor runtime source, products, observations, runs and baseline are absent.

HONOR_OFFLINE_PROBE
China catalogue/comparison fixtures for MagicPad3, MagicPad 2 and Pad V9 pass exact slug extraction, tablet-only filtering, duplicate-slug handling, snapshot stability and unseen-slug discovery tests. Slugs are stable enough for regional observation in fixtures and in the audited live pages; regulatory mapping remains unproven. Honor runtime source, products, observations, runs and baseline remain absent.

HONOR_LIVE_AUDIT
On 2026-08-11, three ordinary HTTP reads of each official China catalogue/comparison page returned stable HTTP 200 HTML, stable byte counts, stable exact target slugs and no parse errors. Catalogue broad tablet-like set: 29 unique slugs; comparison: 24, with comparison observed as a subset. Honor runs 16/18 accepted and resighted 32; runs 17/19 accepted and resighted 24. Result: LIVE_STABLE; both sources are experimental, baselined and resighted with 0 events.

TCL_EXPANSION
The official global HTML tablet catalogue passed fixture/parser validation and live baseline/resight. Runs 20/21 accepted and resighted 24 candidates with 0 events and 0 duplicate identities. TCL is experimental only.

UNVERIFIED
Long-term Apple Store markup stability, SKU-to-A-model mapping, production safety, global canonical unification, additional Samsung stability

NEXT_ACTION
Implement the bounded experimental soak runner for the frozen six-source roster.

STOP_CONDITIONS
Do not promote sources, enable production/alerts, expand OEM scope, scrape retailers, or refactor speculatively. Stop if identity is indefensible, source responses cannot be distinguished from error/challenge pages, or integrity/migrations fail.
