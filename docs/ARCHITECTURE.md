# Architecture

## Actual implemented data path

`first-party HTML/XML source -> collector -> Candidate -> validator -> normalizer -> identity_key -> SQLite products + observations/evidence -> baseline-aware change_events`

### Source and collection

- `tablet_clank/sources/registry.py` defines the four registered experimental sources and the empty production allowlist.
- `tablet_clank/collectors/base.py` retrieves HTML/XML with timeout, user agent, status and content-type checks.
- `tablet_clank/collectors/html_catalogue.py` parses HTML anchor links and metadata for Apple.
- `tablet_clank/collectors/xml_sitemap.py` parses standard XML `<loc>` entries, filters Samsung tablet paths and extracts `SM-*` identifiers from URL slugs.
- `tablet_clank/collectors/apple_store.py` parses the embedded Apple Store `products` configuration array plus matching iPad Pro configuration links, then deduplicates repeated carrier/unlocked URLs by regional part number while preferring the non-carrier representation.
- Fixture mode supports offline tests.

### Validation and normalization

- `tablet_clank/validation.py` rejects obvious non-tablets, support/accessory surfaces, generic category pages and Apple navigation candidates without a stable model/SKU signal.
- `tablet_clank/normalization.py` canonicalizes URLs, manufacturer names, RAM, storage and display values while preserving raw values.
- `tablet_clank/models.py` defines candidates, normalized products and run results.

### Identity, persistence and intelligence

- `tablet_clank/pipeline/__init__.py` performs validation, normalization, identity lookup, observation/evidence persistence, metrics, baseline handling and conservative specification change events.
- `tablet_clank/storage/db.py` bootstraps schema version 1, enables SQLite foreign keys and WAL, and exposes integrity checking.
- Accepted observations retain source ID, URL, timestamp, raw JSON, normalized JSON and collector name.
- Rejected candidates retain run, URL, title, reason and raw values.

## Validation caveat

The historical Apple sitemap baseline contains false-positive navigation-like records from the first live run. They were not deleted because evidence is retained; current validation now rejects the same identifier-free candidates and fails closed at zero accepted candidates. Samsung’s first replacement run likewise retained one historical generic category observation; later runs reject that category. Apple Store runs 8–9 preceded the duplicate-part-number fix; their evidence and resulting correction events remain retained, while runs 12–13 prove the corrected parser resights cleanly.

## Explicitly not implemented

PLANNED: scheduler, repeated-healthy-run disappearance semantics, source-specific Apple product discovery, external alert delivery, editorial scoring, dashboard, AI classification, historical backfill and production deployment.
