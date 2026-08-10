PROJECT
Tablet Clank

PHASE
Stage 1 foundation / continuity checkpoint

PRODUCTION
Allowlist empty; scheduling absent; alerts disabled

DATABASE
var/tablet_clank.db; integrity ok; 21 products, 23 observations, 2 runs, 349 rejected candidates, 0 events

SCHEMA
1

TESTS
python -m pytest -q -rA; passed=4 failed=0 skipped=0 xfailed=0

SOURCES
apple_in_sitemap=EXPERIMENTAL, one plausible live run, baseline complete
samsung_us_sitemap=EXPERIMENTAL, fixture valid, live HTTP 404, no baseline

KNOWN_GOOD
Fixture parsing, conservative validation, normalization helpers, SQLite bootstrap/integrity, baseline/resighting semantics, failure recording

KNOWN_BROKEN
Samsung configured live endpoint returns HTTP 404

UNVERIFIED
Repeated live stability, production safety, cross-region identity behavior, source-specific parsing quality

NEXT_ACTION
Re-research Samsung’s regional source URL and then repeat controlled live validation for both experimental sources

STOP_CONDITIONS
Do not promote sources, enable production/alerts, expand OEM scope, scrape retailers, or refactor speculatively. Stop if identity is indefensible, source responses cannot be distinguished from error/challenge pages, or integrity/migrations fail.
