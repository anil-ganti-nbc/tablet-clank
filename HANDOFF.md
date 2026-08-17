# Tablet Clank Handoff

## Mission

Tablet Clank is an independent, evidence-first system for discovering meaningful tablet product and catalogue changes from first-party manufacturer sources. Trustworthy provenance and failure isolation take priority over source count.

## Current Project State

The bounded 12-cycle experimental soak completed successfully and Promotion Wave 1 (Honor + TCL) is now live. The repository is the authoritative project state. Lenovo first-party reconnaissance is documented as research only. Current Git branch is `main`; this handoff reflects Git HEAD `f38f36e` plus the Promotion Wave 1 commit on top of it.

## Repository / Environment

- Repository: the directory containing this file; the current machine path is `C:\Users\anil\Desktop\tablet clank`.
- Python verified: 3.14.6. No project virtual environment exists; this is recorded as UNKNOWN for other machines.
- Runtime database: `var/tablet_clank.db`, ignored by Git and created on demand.
- Schema/migration version: 1.
- Runtime dependencies: Python standard library; tests require pytest.

## Architecture

`source -> HtmlCatalogueCollector -> Candidate -> validator -> normaliser -> identity resolution -> SQLite products/observations/evidence -> baseline-aware change events`

Implemented modules are documented in `docs/ARCHITECTURE.md`. There is no scheduler, external alert delivery, dashboard, disappearance detector, or AI classifier.

## Database

The canonical database currently has integrity `ok`, 6 enabled experimental sources plus 1 retired historical source, 225 products, 3254 observations, 108 collector runs, 1434 rejected candidates, and 48 change events. All 48 are typed `identity_correction` (24 US, 24 IN), and all predate the soak (2026-08-10); the 12-cycle soak and the first controlled production cycle produced zero soak/production-generated events and zero duplicate identity keys. `var/debug.db` is an ignored, non-canonical artifact from an earlier failed debugging run and must not be used as project state.

## Completed 12-Cycle Soak (historical fact)

Ran 2026-08-12T08:54:59Z through 2026-08-13T06:59:48Z (22h04m49s wall-clock) against the frozen six-source roster. Result: 12/12 cycles `SUCCESS`, 0 `PARTIAL_FAILURE`, 0 correctness failures, 0 soak-generated events, 0 duplicate identities, database integrity `ok` on every cycle. Full evidence in `var/logs/soak.jsonl` and the `tablet-clank-soak.service` systemd journal. The soak service is disabled/inactive; it was not restarted for this promotion.

## Promotion Wave 1 (2026-08-17)

`honor_cn_tablets_catalogue`, `honor_cn_tablets_comparison` and `tcl_global_tablets` are now production-approved via an explicit `PRODUCTION_ALLOWLIST` in `tablet_clank/sources/registry.py`. `apple_us_ipad_pro_store`, `apple_in_ipad_pro_store` and `samsung_us_sitemap` remain experimental, post-soak, not production-approved, pending a later hardening/review phase. `apple_in_sitemap` remains disabled/retired. Source `state` (`EXPERIMENTAL`/`DISABLED`) is unchanged by promotion — production eligibility is a separate, explicit, auditable allowlist layered on top of state, not a new state value. See `docs/OPERATIONS.md` for the `production`/`production --check` commands.

A new `tablet_clank/production.py` module runs a single bounded, serial, locked collection cycle for exactly the production-allowlisted sources, reusing the soak module's lock, identity/baseline semantics and collector selection. It shares the soak/manual-collect lock domain (`var/tablet_clank.soak.lock`) so a production run cannot overlap a soak or manual collection. One controlled production cycle was run on 2026-08-17: all three sources succeeded, all resighted their existing baseline with 0 new products and 0 events. No alerts or external delivery exist in this codebase; `ALERTS_ENABLED = False` is an explicit, tested invariant. No scheduling was added — the completed soak service and the new production path both remain inactive/on-demand only.

Note: the old frozen six-source soak roster (`FROZEN_SOAK_SOURCE_IDS` in `tablet_clank/soak.py`) now intentionally refuses to run, because 3 of its 6 sources are production-allowlisted (`resolve_soak_sources` raises `"soak roster contains a production-allowlisted source"`). Do not restart the old 12-cycle soak; it is retired by design now that Wave 1 is promoted.

## Implemented Sources

- `apple_in_sitemap`: Apple, IN, regional HTML sitemap, retired/disabled. Two pre-audit runs mechanically resighted 23/23 identities; after the stable-identifier audit fix, run 7 failed closed with 372 raw, 0 accepted and 372 rejected. Historical source/products/observations/events remain retained.
- `apple_us_ipad_pro_store`: Apple, US, experimental Store configuration collector. Run 14 produced 48 raw/validated/accepted configurations, 0 new, 48 resighted.
- `apple_in_ipad_pro_store`: Apple, IN, experimental Store configuration collector. Run 15 produced 48 raw/validated/accepted configurations, 0 new, 48 resighted.
- `samsung_us_sitemap`: Samsung, US, official regional XML product sitemap at `https://www.samsung.com/us/top_sitemap.xml`, experimental. Run 3 accepted 4 URLs including one generic category; run 4 accepted/resighted 3 genuine model-code URLs and rejected the category.
- `honor_cn_tablets_catalogue`: Honor, CN, official HTML catalogue, experimental, **production-approved (Wave 1)**. 12/12 soak cycles healthy plus one controlled production cycle, all resighting 32 candidates with zero events.
- `honor_cn_tablets_comparison`: Honor, CN, official HTML comparison surface, experimental, **production-approved (Wave 1)**. 12/12 soak cycles healthy plus one controlled production cycle, all resighting 24 shared identities with zero events.
- `tcl_global_tablets`: TCL, GLOBAL, official HTML tablet catalogue, experimental, **production-approved (Wave 1)**. 12/12 soak cycles healthy plus one controlled production cycle, all resighting 24 candidates with zero events.

Full source truth is in `docs/SOURCE_INVENTORY.md`. Broader reconnaissance is in `docs/SOURCE_RESEARCH.md`.

## Production State

Production allowlist contains exactly `honor_cn_tablets_catalogue`, `honor_cn_tablets_comparison`, `tcl_global_tablets` (Promotion Wave 1, 2026-08-17). Production scheduling is absent — the production path runs on demand only (`python -m tablet_clank.cli production`), the same as manual collection; nothing is unattended. Alerts are disabled (`ALERTS_ENABLED = False`); no Discord integration or destination is configured. Remaining experimental sources (Apple US/IN, Samsung) must not be promoted automatically; any future promotion remains a separate human-reviewed decision, same as this one.

## Test State

Fresh checkpoint command: `python -m pytest -q -rA`. Current result: 43 passed, 0 failed, 0 skipped, 0 xfailed.

## Known Issues

- Apple’s navigation sitemap contains substantial non-tablet material. After a narrow stable-identifier rule, live runs fail closed with zero accepted candidates; the historical Apple baseline is not trusted.
- Apple Store Buy iPad family pages are now implemented only as the experimental US/IN iPad Pro probe. Corrected cycles resight cleanly; early pre-fix evidence remains in the database and is explicitly typed `identity_correction`.
- Samsung’s old HTML sitemap URL was replaced by the official XML `https://www.samsung.com/us/top_sitemap.xml`; one mixed generic category was rejected after the first replacement run.
- Lenovo reconnaissance found PSREF to be the strongest future discovery target. It exposes model/configuration tables, Lenovo machine-type/regional identifiers, deep specifications, historical/withdrawn references and an Excel export action. No Lenovo source is registered or implemented. Storefront, support and HTML site-map surfaces are not identity-safe primary discovery sources; direct token-gated PSREF API access was not bypassed.
- Lenovo now has an `OFFLINE_PROBE` only: `tests/fixtures/lenovo_psref_reduced.json` and `tablet_clank/collectors/lenovo_psref.py`. It parses six distinct candidates from seven reduced rows, preserves exact model codes, separates WLAN/WWAN, and removes only one exact repeated row. It does not register Lenovo, touch the canonical database, establish a baseline, or solve global identity.
- An independent Legion Tab cross-check passed using `tests/fixtures/lenovo_psref_crosscheck.json` with eight exact regional model codes. The live gate is blocked as `LIVE_SOURCE_NOT_RELIABLE`: the public model page is a JavaScript shell and safe direct model/spec/export calls returned empty responses. No Lenovo source, run, baseline, product, observation, or event exists.
- The canonical identity key is conservative and has not been audited against real cross-region variant examples.
- There is no real virtual environment captured in the repository; create one locally when needed.
- Xiaomi reconnaissance is research-only. China Mi Mall category/detail pages are the strongest early-discovery lead, while global/regional product/spec pages provide configuration and chronology corroboration. No documented public Xiaomi SKU/variant feed has been proven; China/global equivalence is unresolved. Recommended strategy is `MULTI_SOURCE_REQUIRED`; no Xiaomi source, database rows, baseline or runtime registration exists.
- The Xiaomi Mi Mall Pad 7/Pad 8 offline probe found a current identity failure: requested IDs `10050031` and `19509` resolve to unrelated appliances on direct official inspection despite stale search labels. Fixtures `tests/fixtures/xiaomi_mimall_pad7.json` and `tests/fixtures/xiaomi_mimall_pad8.json` preserve the mismatch and emit no candidates. Variant identity is unresolved; Xiaomi is not ready for live probing.
- Honor is landed experimentally on two audited CN HTML surfaces. Six reconnaissance reads were stable; controlled runs 16/18 and 17/19 completed baseline/resight with zero events. Model-number mapping, configuration completeness and global equivalence remain unresolved.
- TCL is landed experimentally on one global HTML tablet catalogue. Runs 20/21 completed baseline/resight with zero events; configuration completeness and global canonical equivalence remain unresolved.
- Huawei, OnePlus, OPPO, RedMagic/Nubia, Asus, Acer and Vivo/iQOO are parked after bounded first-party reconnaissance; see `docs/SOURCE_RESEARCH.md`.

## Important Invariants

- Preserve raw source values and evidence URL for accepted observations.
- A failed or zero-accepted run must not establish or advance a baseline.
- One source failure must not abort other sources.
- Do not infer product disappearance from a missed run.
- Implemented and experimental are not production approval.
- Unknown values remain unknown; do not fabricate specifications or identity.

## Current Work

Promotion Wave 1 is complete: Honor (catalogue + comparison) and TCL are production-approved and have completed one controlled production cycle. Apple US/IN and Samsung remain experimental/soaked but not production-approved.

## Next Recommended Step

Design and validate unattended production scheduling and internal event review for the promoted Honor/TCL sources before enabling any external delivery.

## Do Not Do Yet

Do not add manufacturers, expand regions, promote Apple or Samsung, enable alerts/external delivery, scrape retailers, add AI, build a dashboard, add unattended/recurring scheduling, or perform speculative architecture refactors. Do not delete historical false-positive evidence. Do not restart the old 6-source frozen soak (it now refuses to run by design, since 3 of its sources are production-allowlisted).

## Essential Commands

```text
python -m pytest -q -rA
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect samsung_us_sitemap
python -m tablet_clank.cli collect --all
python -m tablet_clank.cli status
python -m tablet_clank.cli health
python -m tablet_clank.cli db-integrity
python -m tablet_clank.cli production --check
python -m tablet_clank.cli production
```

## Continuation Protocol

Before stopping: run tests; check database integrity if database code/state changed; update source inventory, architecture and known issues when applicable; update `docs/PROJECT_STATE.md`; set exactly one clear next action; update this file; then record Git HEAD and status. Do not leave essential state only in conversation.
