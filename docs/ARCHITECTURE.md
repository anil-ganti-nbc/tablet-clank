# Architecture

The implemented flow is:

`first-party HTML sitemap -> collector -> Candidate -> conservative validator -> deterministic normaliser -> identity key -> products + observations/evidence -> baseline-aware change events`

Collectors only retrieve and parse. Validation rejects obvious non-tablets and support surfaces. Normalisation preserves raw values while deriving stable values. Persistence records every accepted observation and rejected candidate, plus per-run metrics. Change events are emitted only after a source baseline is complete; ordinary resighting is silent.

SQLite uses foreign keys, WAL mode, a migration marker and integrity checks. Each source run is isolated in `process`; errors are recorded on that run and are not raised into a multi-source scheduler.
