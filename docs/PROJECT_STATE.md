PROJECT
Tablet Clank

PHASE
Stage 1 controlled live validation checkpoint

PRODUCTION
Allowlist empty; scheduling absent; alerts disabled

DATABASE
var/tablet_clank.db; integrity ok; 169 products, 412 observations, 13 runs, 1420 rejected candidates, 48 events; 0 duplicate identity keys

SCHEMA
1

TESTS
python -m pytest -q -rA; passed=10 failed=0 skipped=0 xfailed=0

SOURCES
apple_in_sitemap=EXPERIMENTAL, post-fix run failed closed 372/0/372/0; historical baseline untrusted
apple_us_ipad_pro_store=EXPERIMENTAL, corrected run 12 48/48/0/48, 0 new, 48 resighted; early duplicate-part-number evidence retained
apple_in_ipad_pro_store=EXPERIMENTAL, corrected run 13 48/48/0/48, 0 new, 48 resighted; early correction evidence retained
samsung_us_sitemap=EXPERIMENTAL, official XML replacement live, run 3 4/4/0/4 then run 4 4/3/1/3 resight; unchanged

KNOWN_GOOD
Fixture parsing, Apple Store structured configuration parsing, regional SKU extraction, carrier deduplication, corrected US/IN resighting, XML sitemap parsing, conservative validation, SQLite integrity, failure recording

KNOWN_BROKEN
Apple Store early runs created retained correction events before the duplicate-part-number fix; Apple regional HTML sitemap remains untrustworthy; Store-SKU to A-number mapping is unresolved

UNVERIFIED
Long-term Apple Store markup stability, SKU-to-A-model mapping, production safety, global canonical unification, additional Samsung stability

NEXT_ACTION
Review the Apple Store correction evidence and decide whether to keep the two experimental Store sources for longer repeated live monitoring; do not promote them

STOP_CONDITIONS
Do not promote sources, enable production/alerts, expand OEM scope, scrape retailers, or refactor speculatively. Stop if identity is indefensible, source responses cannot be distinguished from error/challenge pages, or integrity/migrations fail.
