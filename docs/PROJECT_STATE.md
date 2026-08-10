PROJECT
Tablet Clank

PHASE
Stage 1 controlled live validation checkpoint

PRODUCTION
Allowlist empty; scheduling absent; alerts disabled

DATABASE
var/tablet_clank.db; integrity ok; 25 products, 76 observations, 7 runs, 1420 rejected candidates, 0 events; 0 duplicate identity keys

SCHEMA
1

TESTS
python -m pytest -q -rA; passed=6 failed=0 skipped=0 xfailed=0

SOURCES
apple_in_sitemap=EXPERIMENTAL, 2 mechanically stable but low-quality live resight runs, post-fix run failed closed 372/0/372/0; DB baseline flag historical but not trusted
samsung_us_sitemap=EXPERIMENTAL, official XML replacement live, run 3 4/4/0/4 then run 4 4/3/1/3 resight; baseline complete

KNOWN_GOOD
Fixture parsing, XML sitemap parsing, conservative validation, normalization helpers, SQLite bootstrap/integrity, Samsung resighting, failure recording, Apple fail-closed behavior

KNOWN_BROKEN
Apple regional HTML sitemap does not provide stable product identifiers and is not a trustworthy product source; historical false-positive observations remain retained

UNVERIFIED
Apple Store parser behavior, SKU-to-A-model mapping, production safety, cross-region identity behavior, repeated Samsung stability beyond one resight cycle

NEXT_ACTION
Implement a fixture-backed narrow probe/collector for Apple Store Buy iPad family pages, starting with US and IN iPad Pro configuration data; keep it experimental

STOP_CONDITIONS
Do not promote sources, enable production/alerts, expand OEM scope, scrape retailers, or refactor speculatively. Stop if identity is indefensible, source responses cannot be distinguished from error/challenge pages, or integrity/migrations fail.
