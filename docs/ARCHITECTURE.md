# Architecture

## Actual implemented data path

`first-party HTML/XML source -> collector -> Candidate -> validator -> normalizer -> identity_key -> SQLite products + observations/evidence -> baseline-aware change_events`

### Source and collection

- `tablet_clank/sources/registry.py` defines the registered sources, the `EXPERIMENTAL`/`DISABLED` state per source, and `PRODUCTION_ALLOWLIST` — an explicit, auditable tuple of source IDs approved for production execution, separate from `state`. `production_source_ids()` is the single authority for production membership: it intersects `PRODUCTION_ALLOWLIST` with sources currently `EXPERIMENTAL`, so a source can never become production-eligible by allowlist membership alone, and demoting a source's `state` automatically removes it from production even if the allowlist tuple is stale. `ALERTS_ENABLED = False` is an explicit, tested invariant; no alert/delivery code exists anywhere in the codebase.
- `tablet_clank/collectors/base.py` retrieves HTML/XML with timeout, user agent, status and content-type checks.
- `tablet_clank/collectors/html_catalogue.py` parses HTML anchor links and metadata for Apple.
- `tablet_clank/collectors/xml_sitemap.py` parses standard XML `<loc>` entries, filters Samsung tablet paths and extracts `SM-*` identifiers from URL slugs.
- `tablet_clank/collectors/apple_store.py` parses the embedded Apple Store `products` configuration array plus matching iPad Pro configuration links, then deduplicates repeated carrier/unlocked URLs by regional part number while preferring the non-carrier representation.
- `tablet_clank/collectors/lenovo_psref.py` is an offline-only PSREF fixture parser contract. It is not registered, has no network access, and converts reduced JSON rows into existing `Candidate` objects while preserving exact model codes and collapsing only exact duplicate rows within the fixture snapshot.
- `tablet_clank/collectors/honor_cn.py` is the source-specific Honor China HTML catalogue/comparison collector. It preserves exact regional slugs, collapses duplicate anchors, and fails closed on a sharply reduced live set or missing known anchors.
- `tablet_clank/collectors/tcl_global.py` is the source-specific TCL global HTML catalogue collector. It preserves exact product-path slugs and fails closed on a sharply reduced live set or missing known anchors.
- Fixture mode supports offline tests.

### Validation and normalization

- `tablet_clank/validation.py` rejects obvious non-tablets, support/accessory surfaces, generic category pages and Apple navigation candidates without a stable model/SKU signal.
- `tablet_clank/normalization.py` canonicalizes URLs, manufacturer names, RAM, storage and display values while preserving raw values.
- `tablet_clank/models.py` defines candidates, normalized products and run results.

### Identity, persistence and intelligence

- `tablet_clank/pipeline/__init__.py` performs validation, normalization, identity lookup, observation/evidence persistence, metrics, baseline handling and conservative specification change events.
- Event semantics distinguish `new_product` from the narrow Apple Store `identity_correction` case: when a new identity has the same manufacturer, region and base SKU as an existing Apple Store product, it is treated as parser/identity repair rather than an editorial discovery. Ordinary resighting emits no event.
- `tablet_clank/storage/db.py` bootstraps schema version 1, enables SQLite foreign keys and WAL, and exposes integrity checking.
- Accepted observations retain source ID, URL, timestamp, raw JSON, normalized JSON and collector name.
- Rejected candidates retain run, URL, title, reason and raw values.

## Validation caveat

The historical Apple sitemap baseline contains false-positive navigation-like records from the first live run. They were not deleted because evidence is retained; current validation now rejects the same identifier-free candidates and fails closed at zero accepted candidates. Samsung’s first replacement run likewise retained one historical generic category observation; later runs reject that category. Apple Store runs 8–9 preceded the duplicate-part-number fix; their evidence remains retained. The 48 resulting events were reclassified from `new_product` to `identity_correction`; runs 14–15 prove the corrected parser resights cleanly.

## Explicitly not implemented

PLANNED: scheduler, repeated-healthy-run disappearance semantics, source-specific Apple product discovery, external alert delivery, editorial scoring, dashboard, AI classification, historical backfill and production deployment.

Pre-soak review is recorded in `docs/SOAK_READINESS.md`; operating instructions are in `docs/SOAK_OPERATIONS.md`. The bounded soak runner (`tablet_clank/soak.py`) executes the six enabled experimental sources serially under one cross-platform cycle lock, isolates source failures, and writes JSONL orchestration summaries while reusing collector-run/source-state/observation/event tables. The retired `apple_in_sitemap` source remains inspectable but is excluded by the registry's `state == "EXPERIMENTAL"` selection rule. The soak roster additionally refuses to run if any of its sources are production-allowlisted (`resolve_soak_sources` raises `RuntimeError`), which is why the soak is permanently retired for the old six-source roster now that Honor/TCL are promoted (Promotion Wave 1, 2026-08-17).

`tablet_clank/production.py` is a parallel, minimal bounded runner for exactly `production_source_ids()`. It imports and reuses `soak.py`'s `SoakLock`, `lock_path_for_db`, `duplicate_identity_count`, `collector_for` and `result_summary` rather than duplicating them, so production execution shares the same lock domain (`var/tablet_clank.soak.lock`), identity semantics and baseline semantics as soak and manual `collect`. It writes its own JSONL report to `var/logs/production.jsonl` (kept separate from soak evidence) and its own abort status names (`PRODUCTION_ABORTED_DB_INTEGRITY`/`PRODUCTION_ABORTED_DUPLICATE_IDENTITY`) to avoid conflating soak and production audit trails. `readiness_check` refuses to run if `ALERTS_ENABLED` is ever set. There is no scheduler for production execution, same as soak — both are on-demand/CLI-invoked only.

Lenovo PSREF is currently `OFFLINE_PROBE` only. The reduced fixture and parser contract do not establish a source, baseline, live ingestion path, database rows, or Lenovo event semantics.

The independent Legion cross-check passed, but no live Lenovo collector was added because the public PSREF model-table retrieval was not reliable through safe non-browser requests. The architecture therefore remains unchanged and Lenovo remains outside the runtime registry.

`tablet_clank/collectors/xiaomi_mimall.py` is an offline-only identity probe. It preserves requested China Mi Mall product IDs and rejects captured page-identity mismatches; it is not registered and emits no candidates for the current fixtures.
