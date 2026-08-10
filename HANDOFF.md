# Tablet Clank handoff

Current truth: independent Python/SQLite foundation implemented. Stage 1 collectors are experimental and fixture-backed. Apple India and Samsung US HTML sitemap sources are registered, but the production allowlist is empty and production alerts are disabled.

The offline suite passes 4 tests. A fixture collection establishes a safe baseline; the next identical run resights observations without creating new-product events. Failed or zero-accepted runs do not establish a baseline. Live probe: Apple IN succeeded with 372 raw links and 23 accepted candidates; Samsung US returned HTTP 404 and remains unvalidated.

Next recommended step: run controlled live probes for each source, inspect candidate quality and source terms, then add source-specific parsing only if the live sitemap pages expose stable product links and identifiers.
