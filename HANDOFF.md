# Tablet Clank Handoff

## Mission

Tablet Clank is an independent, evidence-first system for discovering meaningful tablet product and catalogue changes from first-party manufacturer sources. Trustworthy provenance and failure isolation take priority over source count.

## Current Project State

Foundation/Stage 1 live validation is in progress. The repository is the authoritative project state. No next feature phase has started. Current Git branch is `master`; validation started from Git HEAD `31a637c`.

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

The canonical database currently has integrity `ok`, 2 sources, 25 products, 76 observations, 7 collector runs, 1420 rejected candidates, and 0 change events. SQLite baseline flags are set for both sources, but the Apple flag is historical and untrusted because its accepted set was false-positive navigation material. `var/debug.db` is an ignored, non-canonical artifact from an earlier failed debugging run and must not be used as project state.

## Implemented Sources

- `apple_in_sitemap`: Apple, IN, regional HTML sitemap, experimental. Two pre-audit runs mechanically resighted 23/23 identities; after the stable-identifier audit fix, run 7 failed closed with 372 raw, 0 accepted and 372 rejected.
- `samsung_us_sitemap`: Samsung, US, official regional XML product sitemap at `https://www.samsung.com/us/top_sitemap.xml`, experimental. Run 3 accepted 4 URLs including one generic category; run 4 accepted/resighted 3 genuine model-code URLs and rejected the category.

Full source truth is in `docs/SOURCE_INVENTORY.md`. Broader reconnaissance is in `docs/SOURCE_RESEARCH.md`.

## Production State

Production allowlist is empty. Production scheduling is absent. Alerts are disabled; no Discord integration or destination is configured. Experimental sources must not be promoted automatically.

## Test State

Fresh checkpoint command: `python -m pytest -q -rA`. Current result: 4 passed, 0 failed, 0 skipped, 0 xfailed.

## Known Issues

- Apple’s navigation sitemap contains substantial non-tablet material. After a narrow stable-identifier rule, live runs fail closed with zero accepted candidates; the historical Apple baseline is not trusted.
- Samsung’s old HTML sitemap URL was replaced by the official XML `https://www.samsung.com/us/top_sitemap.xml`; one mixed generic category was rejected after the first replacement run.
- The canonical identity key is conservative and has not been audited against real cross-region variant examples.
- There is no real virtual environment captured in the repository; create one locally when needed.

## Important Invariants

- Preserve raw source values and evidence URL for accepted observations.
- A failed or zero-accepted run must not establish or advance a baseline.
- One source failure must not abort other sources.
- Do not infer product disappearance from a missed run.
- Implemented and experimental are not production approval.
- Unknown values remain unknown; do not fabricate specifications or identity.

## Current Work

Controlled Stage 1 live validation only. No broader feature-development work is authorized by this handoff.

## Next Recommended Step

Do not promote either source. The next action is to review the documented live-validation evidence and decide whether to research a better Apple product-discovery surface; keep both sources experimental.

## Do Not Do Yet

Do not add manufacturers, expand regions, promote sources, enable production or alerts, scrape retailers, add AI, build a dashboard, or perform speculative architecture refactors. Do not delete historical false-positive evidence.

## Essential Commands

```text
python -m pytest -q -rA
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect apple_in_sitemap
python -m tablet_clank.cli collect samsung_us_sitemap
python -m tablet_clank.cli collect --all
python -m tablet_clank.cli collect apple_in_sitemap --live
python -m tablet_clank.cli status
python -m tablet_clank.cli health
python -m tablet_clank.cli db-integrity
```

## Continuation Protocol

Before stopping: run tests; check database integrity if database code/state changed; update source inventory, architecture and known issues when applicable; update `docs/PROJECT_STATE.md`; set exactly one clear next action; update this file; then record Git HEAD and status. Do not leave essential state only in conversation.
