PROJECT
Tablet Clank

PHASE
Stage 1 controlled live validation checkpoint

PRODUCTION
Allowlist empty; scheduling absent; alerts disabled

DATABASE
var/tablet_clank.db; integrity ok; 169 products, 508 observations, 15 runs, 1420 rejected candidates, 48 events; 48 identity_correction, 0 duplicate identity keys

SCHEMA
1

TESTS
python -m pytest -q -rA; passed=12 failed=0 skipped=0 xfailed=0

SOURCES
apple_in_sitemap=EXPERIMENTAL, post-fix run failed closed 372/0/372/0; historical baseline untrusted
apple_us_ipad_pro_store=EXPERIMENTAL, run 14 48/48/0/48, 0 new, 48 resighted; 24 historical identity_correction events
apple_in_ipad_pro_store=EXPERIMENTAL, run 15 48/48/0/48, 0 new, 48 resighted; 24 historical identity_correction events
samsung_us_sitemap=EXPERIMENTAL, official XML replacement live, run 3 4/4/0/4 then run 4 4/3/1/3 resight; unchanged

KNOWN_GOOD
Fixture parsing, Apple Store structured configuration parsing, regional SKU extraction, carrier deduplication, corrected US/IN resighting, XML sitemap parsing, conservative validation, SQLite integrity, failure recording

KNOWN_BROKEN
Apple regional HTML sitemap remains untrustworthy; Store-SKU to A-number mapping is unresolved; early Apple Store identity repairs remain historical evidence

UNVERIFIED
Long-term Apple Store markup stability, SKU-to-A-model mapping, production safety, global canonical unification, additional Samsung stability

NEXT_ACTION
Continue a small number of repeated experimental Apple Store monitoring cycles without promotion, then reassess long-term markup and identity stability

STOP_CONDITIONS
Do not promote sources, enable production/alerts, expand OEM scope, scrape retailers, or refactor speculatively. Stop if identity is indefensible, source responses cannot be distinguished from error/challenge pages, or integrity/migrations fail.
