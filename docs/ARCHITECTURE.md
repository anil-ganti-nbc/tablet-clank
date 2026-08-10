# Architecture

## Actual implemented data path

`first-party HTML sitemap -> HtmlCatalogueCollector -> Candidate -> validate() -> normalize_candidate() -> identity_key -> SQLite products + observations -> baseline-aware change_events`

### Source and collection

- `tablet_clank/sources/registry.py` defines the two registered sources and the empty production allowlist.
- `tablet_clank/collectors/base.py` retrieves HTML/XML with a timeout, user agent, status check and content-type check.
- `tablet_clank/collectors/html_catalogue.py` parses anchor links and nearby `data-*` metadata into `Candidate` objects. Fixture mode supports offline tests.

### Validation and normalization

- `tablet_clank/validation.py` conservatively accepts tablet signals and rejects phones, watches, laptops, accessories and support surfaces.
- `tablet_clank/normalization.py` canonicalizes URLs, manufacturer names, RAM, storage and display values while preserving raw values.
- `tablet_clank/models.py` defines candidates, normalized products and run results.

### Identity, persistence and intelligence

- `tablet_clank/pipeline/__init__.py` performs validation, normalization, identity lookup, observation/evidence persistence, metrics, baseline handling and conservative specification change events.
- `tablet_clank/storage/db.py` bootstraps schema version 1, enables SQLite foreign keys and WAL, and exposes integrity checking.
- Accepted observations retain source ID, URL, timestamp, raw JSON, normalized JSON and collector name.
- Rejected candidates retain run, URL, title, reason and raw values.

## Explicitly not implemented

PLANNED: scheduler, repeated-healthy-run disappearance semantics, source-specific parsers beyond HTML anchor catalogues, external alert delivery, editorial scoring, dashboard, AI classification, historical backfill and production deployment.
