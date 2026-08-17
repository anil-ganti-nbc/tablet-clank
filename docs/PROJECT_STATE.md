PROJECT
Tablet Clank

PHASE
Promotion Wave 1 complete: 12-cycle soak passed 12/12; Honor + TCL production-approved and controlled-production-verified

PRODUCTION
Allowlist = honor_cn_tablets_catalogue, honor_cn_tablets_comparison, tcl_global_tablets; scheduling absent (on-demand only); alerts disabled

DATABASE
var/tablet_clank.db; integrity ok; 225 products, 3254 observations, 108 runs, 1434 rejected candidates, 48 events; 48 identity_correction (all pre-soak), 0 duplicate identity keys

SCHEMA
1

TESTS
python -m pytest -q -rA; passed=43 failed=0 skipped=0 xfailed=0

SOURCES
apple_in_sitemap=DISABLED/RETIRED, post-fix run failed closed 372/0/372/0; historical baseline untrusted; excluded from runtime/soak; not production eligible
apple_us_ipad_pro_store=EXPERIMENTAL, post-soak, NOT production-approved; 18 total runs, 12 in-soak, all healthy; 24 historical identity_correction events
apple_in_ipad_pro_store=EXPERIMENTAL, post-soak, NOT production-approved; 18 total runs, 12 in-soak, all healthy; 24 historical identity_correction events
samsung_us_sitemap=EXPERIMENTAL, post-soak, NOT production-approved; 17 total runs, 12 in-soak, all healthy
honor_cn_tablets_catalogue=EXPERIMENTAL, PRODUCTION-APPROVED (Wave 1); 12/12 soak cycles + 1 controlled production cycle, all healthy, 0 events
honor_cn_tablets_comparison=EXPERIMENTAL, PRODUCTION-APPROVED (Wave 1); 12/12 soak cycles + 1 controlled production cycle, all healthy, 0 events
tcl_global_tablets=EXPERIMENTAL, PRODUCTION-APPROVED (Wave 1); 12/12 soak cycles + 1 controlled production cycle, all healthy, 0 events

SOAK_HISTORY
2026-08-12T08:54:59Z to 2026-08-13T06:59:48Z (22h04m49s); 12/12 SUCCESS; 0 PARTIAL_FAILURE; 0 correctness failures; 0 soak-generated events; 0 duplicates; integrity ok throughout. Full evidence: var/logs/soak.jsonl. Soak service now permanently retired for the old 6-source roster (refuses to run: 3 of its sources are production-allowlisted).

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
Design and validate unattended production scheduling and internal event review for the promoted Honor/TCL sources before enabling any external delivery.

STOP_CONDITIONS
Do not promote Apple or Samsung, enable alerts/external delivery, expand OEM scope, scrape retailers, add unattended scheduling, or refactor speculatively. Do not restart the old 6-source frozen soak. Stop if identity is indefensible, source responses cannot be distinguished from error/challenge pages, or integrity/migrations fail.
