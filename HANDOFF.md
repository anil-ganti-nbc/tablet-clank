# Tablet Clank Handoff

## Mission

Tablet Clank is an independent, evidence-first system for discovering meaningful tablet product and catalogue changes from first-party manufacturer sources. Trustworthy provenance and failure isolation take priority over source count.

## Current Project State

Foundation/Stage 1 is implemented. The repository is the authoritative project state. No next feature phase has started. Current Git branch is `master`; current checkpoint is `de921b4`.

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

The canonical database currently has integrity `ok`, 2 sources, 21 products, 23 observations, 2 collector runs, 349 rejected candidates, and 0 change events. Apple has a completed baseline; Samsung has no baseline. `var/debug.db` is an ignored, non-canonical artifact from an earlier failed debugging run and must not be used as project state.

## Implemented Sources

- `apple_in_sitemap`: Apple, IN, regional HTML sitemap, experimental. Live probe succeeded with 372 raw links and 23 accepted candidates; one live cycle only, so not trusted for production.
- `samsung_us_sitemap`: Samsung, US, regional HTML sitemap, experimental. Fixture parsing works; configured live URL returned HTTP 404. No baseline.

Full source truth is in `docs/SOURCE_INVENTORY.md`. Broader reconnaissance is in `docs/SOURCE_RESEARCH.md`.

## Production State

Production allowlist is empty. Production scheduling is absent. Alerts are disabled; no Discord integration or destination is configured. Experimental sources must not be promoted automatically.

## Test State

Fresh checkpoint command: `python -m pytest -q -rA`. Current result: 4 passed, 0 failed, 0 skipped, 0 xfailed.

## Known Issues

- Samsung’s configured live sitemap endpoint returns HTTP 404 and needs re-research before another live attempt.
- Apple’s navigation sitemap contains substantial non-tablet material; rejection metrics make this visible, but source-specific filtering and repeated live validation are still needed.
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

Continuity checkpoint only. No feature-development work is authorized by this handoff.

## Next Recommended Step

Re-research the Samsung regional source URL, then perform controlled repeated live validation for both existing experimental sources. Update source state only after evidence supports it.

## Do Not Do Yet

Do not add manufacturers, expand regions, promote sources, enable production or alerts, scrape retailers, add AI, build a dashboard, or perform speculative architecture refactors.

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
