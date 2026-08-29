PROJECT
Tablet Clank

PHASE
Promotion Wave 3 complete: honor_uk_tablets production-approved after isolated NAS campaign soak 12/12; controlled production cycle verified with all four sources healthy

PRODUCTION
Allowlist = honor_cn_tablets_catalogue, honor_cn_tablets_comparison, tcl_global_tablets, honor_uk_tablets (Wave 3, 2026-08-29); execution is ON-DEMAND ONLY via `python -m tablet_clank.cli production` — the twice-daily `tablet-clank-production.timer` documented 2026-08-26 was NOT found on any host (NAS user+system units, WSL Ubuntu, Windows Task Scheduler checked 2026-08-29; `deploy/systemd/` ships .example templates only); alerts disabled

DATABASE
var/tablet_clank.db; integrity ok; 179 products, 646 observations, 23 runs, 2 rejected candidates, 0 change_events (48 historical events live in the QC archive, var/tablet_clank_qc.db); 0 duplicate identity keys; pre-promotion backup var/backups/tablet_clank-pre-honoruk-promotion.db (sha256 169fe9e2…)

SCHEMA
2

TESTS
python -m pytest -q; passed=117 failed=0 skipped=0

SOURCES
apple_in_sitemap=DISABLED/RETIRED, post-fix run failed closed 372/0/372/0; historical baseline untrusted; excluded from runtime/soak; not production eligible
apple_us_ipad_pro_store=EXPERIMENTAL, post-soak, NOT production-approved; 18 total runs, 12 in-soak, all healthy; 24 historical identity_correction events
apple_in_ipad_pro_store=EXPERIMENTAL, post-soak, NOT production-approved; 18 total runs, 12 in-soak, all healthy; 24 historical identity_correction events
samsung_us_sitemap=EXPERIMENTAL, post-soak, NOT production-approved; 17 total runs, 12 in-soak, all healthy
honor_cn_tablets_catalogue=EXPERIMENTAL, PRODUCTION-APPROVED (Wave 1); 12/12 soak cycles + 2 controlled production cycles, all healthy, 0 events
honor_cn_tablets_comparison=EXPERIMENTAL, PRODUCTION-APPROVED (Wave 1); 12/12 soak cycles + 2 controlled production cycles, all healthy, 0 events
tcl_global_tablets=EXPERIMENTAL, PRODUCTION-APPROVED (Wave 1); 12/12 soak cycles + 2 controlled production cycles, all healthy, 0 events
honor_uk_tablets=EXPERIMENTAL, PRODUCTION-APPROVED (Wave 3, 2026-08-29); isolated NAS campaign honor-uk-iso-nas-001 12/12 SUCCESS (0 events, 0 duplicates, canonical untouched) + 1 controlled production cycle healthy (32/24/25/23 accepted, all resights, 0 events); canonical baseline dates to 2026-08-27 Wave 2 validation; campaign approval retired on promotion

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
Unattended production scheduling is live (twice-daily systemd timer since 2026-08-26 10:49Z, commit d2ab5ba). Design and validate internal event review for the promoted Honor/TCL sources before enabling any external delivery.

STOP_CONDITIONS
Do not promote Apple or Samsung, enable alerts/external delivery, expand OEM scope, scrape retailers, or refactor speculatively. (Unattended production scheduling was validated and enabled 2026-08-26 via commit d2ab5ba.) Do not restart the old 6-source frozen soak. Stop if identity is indefensible, source responses cannot be distinguished from error/challenge pages, or integrity/migrations fail.

---

# Wave 2 status update (2026-08-27)

## SOURCE
Added `honor_uk_tablets` (Honor UK storefront, server-rendered HTML,
`HonorUKTabletsCollector`). EXPERIMENTAL; in experimental runtime roster and
frozen soak roster; NOT production-approved. Probe evidence: HTTP 200, 23
products parsed with 0 rejections, ~0.5 s latency, no JS dependency.
Baseline cycle accepted 23 creating **0 events** (FIRST_SEEN != NOVELTY);
immediate re-sight produced 0 duplicates and 0 events; integrity ok.

Tier A re-verification after fresh live probing: Lenovo PSREF confirmed
JS-only with no discoverable stable data API and the official Lenovo sitemap
contains zero tablet product pages; Xiaomi Mi Mall remains a JS shell with no
stable public SKU feed (spec DB not a change surface); Huawei consumer/vmall
surfaces are client-rendered. All recorded in SOURCE_RESEARCH.md Wave 2.

## DATABASE / SCHEMA
No schema change (schema v1). Authoritative datastore unchanged. No baseline
resets; new source baselines only on first soak cycle against the live DB.

## TESTS
python -m pytest -q: passed=82 failed=0 skipped=0 (72 prior + 10 new).

## NEXT_ACTION
Deployment/soak handoff for `honor_uk_tablets` per the campaign report;
24 h soak watch; reassess Xiaomi via its China store JSON surfaces if any are
later proven publicly documented; reopen Huawei if vmall/consumer exposes a
stable public catalogue API.

---

# Campaign soak status update (2026-08-29)

## CAMPAIGN RUNNER
Implemented `tablet_clank/campaign.py`: manifest-driven, campaign-scoped, isolated soaks.
Explicit source approval (`CAMPAIGN_APPROVED_SOURCE_IDS` in the registry), manifest-pinned
roster hash and interpreter environment, canonical DB opened read-only (`mode=ro`) for
preflight only, campaign-scoped lock, refusal/abort/interruption evidence records in a
campaign JSONL, stricter abort semantics (any non-SUCCESS cycle aborts), baseline cycle
followed by an immediate resight. `soak.run_cycle` gained a backward-compatible `sources`
override (frozen-roster default unchanged); the duplicate-identity SQL is shared with the
campaign preflight. CLI: `soak-campaign --init|--check|--live`. Tests: 117 passed,
0 failed (100 prior + 17 campaign tests), verified on Windows (Python 3.14.0) and on the
NAS inside the deployed image (Python 3.12.14).

## WINDOWS CAMPAIGN honor-uk-iso-001 (CLOSED)
`OPERATOR_ABORTED_FOR_HOST_RELOCATION` after 2 healthy live cycles (baseline 23 new /
0 events; immediate resight 0 new / 0 events; 0 duplicates; integrity ok). No cycle failed;
canonical DB proven byte-identical pre/post; evidence preserved under
`var/campaigns/honor-uk-iso-001/` including `operator_abort.json`. Its 2 cycles are NOT
counted toward the NAS promotion soak; retained as independent supporting evidence only.

## NAS CAMPAIGN honor-uk-iso-nas-001 (COMPLETE — 12/12 SUCCESS)
Relocated to the NAS (Anil_NAS, `/volume2/clank/tablet-clank`) and executed under Docker
(container `tablet-clank-honor-uk-iso-nas-001`, image `tablet-clank:honor-uk-iso-nas-001`,
`restart=no`), Python 3.12.14/linux. Manifest pins: sources `[honor_uk_tablets]`, cycles 12,
interval 7200 s, immediate resight, roster hash `c008b65b…`, manifest sha256 `4c21c2be…`;
live mode confirmed in the campaign_start record. Results at 7200 s cadence 2026-08-28
18:51Z → 2026-08-29 14:51Z: cycle 1 baseline 23 raw / 23 accepted / 23 new / **0 events**;
cycles 2–12 resight 23 / 0 new / **0 events**; **0 duplicate identities**; campaign DB
integrity `ok` in every cycle (final: 23 products, 276 observations = 23×12, 12 collector
runs, 0 change_events). Canonical NAS DB **byte-identical pre/post soak**
(sha256 `169fe9e2…`, mtime unchanged from before launch; logical snapshots identical;
contains 0 change_events). Zero notifications — the runner has no delivery surface.
Evidence: `state/logs/soak-honor-uk-iso-nas-001.jsonl`,
`canonical_pre_cycle12_snapshot.json`, `canonical_postsoak_snapshot.json`.

## NEXT_ACTION
Promotion review for `honor_uk_tablets` per the promotion gate — a separate explicit
`PRODUCTION_ALLOWLIST` decision; regional identity policy unchanged. Do not merge Windows
campaign cycles into NAS evidence; do not resume `honor-uk-iso-001`.
