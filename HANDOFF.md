# Tablet Clank Handoff

## Mission

Tablet Clank is an independent, evidence-first system for discovering meaningful tablet product and catalogue changes from first-party manufacturer sources. Trustworthy provenance and failure isolation take priority over source count.

## Current Project State

Foundation/Stage 1 Apple source reconnaissance is complete. The repository is the authoritative project state. Lenovo first-party reconnaissance is documented as research only; no next feature phase has started. Current Git branch is `master`; this work started from Git HEAD `a66e52f`.

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

The canonical database currently has integrity `ok`, 6 enabled experimental sources plus 1 retired historical source, 225 products, 668 observations, 21 collector runs, 1420 rejected candidates, and 48 change events. All 48 are typed `identity_correction` (24 US, 24 IN); Honor and TCL baselines/resights emitted no events. `var/debug.db` is an ignored, non-canonical artifact from an earlier failed debugging run and must not be used as project state.

## Implemented Sources

- `apple_in_sitemap`: Apple, IN, regional HTML sitemap, retired/disabled. Two pre-audit runs mechanically resighted 23/23 identities; after the stable-identifier audit fix, run 7 failed closed with 372 raw, 0 accepted and 372 rejected. Historical source/products/observations/events remain retained.
- `apple_us_ipad_pro_store`: Apple, US, experimental Store configuration collector. Run 14 produced 48 raw/validated/accepted configurations, 0 new, 48 resighted.
- `apple_in_ipad_pro_store`: Apple, IN, experimental Store configuration collector. Run 15 produced 48 raw/validated/accepted configurations, 0 new, 48 resighted.
- `samsung_us_sitemap`: Samsung, US, official regional XML product sitemap at `https://www.samsung.com/us/top_sitemap.xml`, experimental. Run 3 accepted 4 URLs including one generic category; run 4 accepted/resighted 3 genuine model-code URLs and rejected the category.
- `honor_cn_tablets_catalogue`: Honor, CN, official HTML catalogue, experimental. Runs 16/18 accepted and resighted 32 candidates with zero events.
- `honor_cn_tablets_comparison`: Honor, CN, official HTML comparison surface, experimental. Runs 17/19 accepted and resighted 24 shared identities with zero events.
- `tcl_global_tablets`: TCL, GLOBAL, official HTML tablet catalogue, experimental. Runs 20/21 accepted and resighted 24 candidates with zero events.

Full source truth is in `docs/SOURCE_INVENTORY.md`. Broader reconnaissance is in `docs/SOURCE_RESEARCH.md`.

## Production State

Production allowlist is empty. Production scheduling is absent. Alerts are disabled; no Discord integration or destination is configured. Experimental sources must not be promoted automatically.

## Test State

Fresh checkpoint command: `python -m pytest -q -rA`. Current result: 26 passed, 0 failed, 0 skipped, 0 xfailed.

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

Pre-soak roster is frozen. Implement the bounded soak runner next; do not start execution or promotion in this phase.

## Next Recommended Step

Implement the bounded experimental soak runner for the frozen six-source roster.

Honor and TCL expansion gates completed. The current soak roster is 6 enabled sources across Apple, Samsung, Honor and TCL; `apple_in_sitemap` is retired/disabled with all historical evidence retained. Production remains empty and alerts remain disabled.

## Do Not Do Yet

Do not add manufacturers, expand regions, promote sources, enable production or alerts, scrape retailers, add AI, build a dashboard, or perform speculative architecture refactors. Do not delete historical false-positive evidence.

## Essential Commands

```text
python -m pytest -q -rA
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect samsung_us_sitemap
python -m tablet_clank.cli collect --all
python -m tablet_clank.cli status
python -m tablet_clank.cli health
python -m tablet_clank.cli db-integrity
```

## Continuation Protocol

Before stopping: run tests; check database integrity if database code/state changed; update source inventory, architecture and known issues when applicable; update `docs/PROJECT_STATE.md`; set exactly one clear next action; update this file; then record Git HEAD and status. Do not leave essential state only in conversation.
