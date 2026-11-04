# P0 lesser-known OEM tablet scouts (2026-11-04)

Status: **code/fixtures staged; sources DISABLED; live acceptance NOT RUN**.

Scope: expand the existing Tablet Clank source registry and its proven
collector/SQLite baseline machinery. This is not a new engine, a D1 profile
revision, a source promotion, or permission to restart a dormant scheduler.
No NAS, Dell or former Hetzner runtime has been changed.

## Source surfaces and operational state

| Source ID | Official entry | Discovery type | Limits |
|---|---|---|---|
| alldocube_global_tablets | https://www.alldocube.com/en/product-category/android/ | Android tablet catalogue, /en/products/iplay... links | Product slugs only; first page, not Japan teasers |
| teclast_global_tablets | https://en.teclast.com/tablet/ | T/M/P tablet series product links | No ArtPad/regional commerce yet |
| blackview_zeno_tablets | https://www.blackview.hk/products/81 | ZENO-series catalogue links | Incomplete for hidden/unlinked PDPs; ZENO 2 was absent |

The adapter extracts first-party product hyperlinks only; it does not follow
links, scrape marketplaces, infer regulatory model IDs or automate a browser.
It de-duplicates exact slugs, excludes off-origin/off-series links, and
fails closed on truncated/blocked pages using minimum count plus observed
anchor models. Missing anchors require reviewed changes. The title identifies
a catalogued tablet, not a confirmed announcement or editorial novelty.

## Live access and manual preflight (required before enablement)

1. Check current robots.txt and site terms from the intended host. Only
   Blackview robots text was retrievable in reconnaissance. It declares
   https://www.blackview.hk/sitemap.xml and does not generally exclude
   /products/, but this does not approve every path or request volume.
2. Make one bounded ordinary public HTML GET for each intended category,
   counting redirects and all network requests. Respect 403/429 and
   Retry-After; no challenge bypass, proxy rotation, credential guessing,
   or browser-to-HTTP laundering.
3. Parse the live response with OEMTabletCatalogueCollector.parse_live;
   inspect URL origin, exact product slugs, completeness anchors and count.
   Zero/partial responses fail closed.
4. Only after review, change one source at a time from DISABLED to
   EXPERIMENTAL. Keep PRODUCTION_ALLOWLIST and ALERTS_ENABLED unchanged.
   Use the existing isolated campaign database and locking controls.
5. Baseline quietly, then resight with zero duplicates/events. Later unseen
   slugs are discovery candidates only. FIRST_SEEN is not NEW_PRODUCT.

Offline verification:

    python -m pytest tests/test_oem_catalogue_scout.py -q

**Do not use `collector.collect()` as a live preflight.** Its ordinary
fetch follows redirects implicitly and does not account for each network
request, check robots, or enforce a response-size limit. A read-only parser
is not the same thing as a controlled network request. The manual preflight below is available for controlled evaluation, but it has
not yet been qualified against a live OEM source.

An authorized operator must first review the current terms and robots rules
from the intended host and explicitly approve the access. The future manual
preflight must count every request and redirect, enforce time and size limits,
stop on 403/429 (including Retry-After), and fail closed when permissions or
completeness are uncertain. It must not send credentials, cookies or alerts,
write a database, or alter source state. Save a private, reproducible snapshot
only after reviewing it for server-issued tokens or other sensitive data; do
not commit raw responses or sensitive headers. Treat hashes and extracted
candidate lists as useful evidence, not substitutes for a replayable snapshot.

For a future **authorized, manual** run on the intended host, review the
current terms and robots policy for that exact user agent and catalogue path,
confirm a suitably private output directory, and run exactly one source:

    python -m tablet_clank.oem_preflight alldocube_global_tablets --terms-reviewed --output /private/path/alldocube-preflight.json

The attestation is required; it does not replace human review. Substitute one
of the other two source IDs only after its own review. The probe makes at most
two attempts (robots, then category), never follows redirects or retries, and
stops on any non-200, unavailable/unparseable robots, disallow, unexpected
content type, oversize body, decode failure, or parser completeness failure.
It uses 15-second socket timeouts and a 2 MB per-response bound. It creates a
new mode-0600 report and refuses to overwrite an existing path. The report
contains status, count, hashes and slugs, not response bodies or headers other
than Retry-After; it is not a replayable raw snapshot. No opt-in raw capture
is implemented, so a separately reviewed privacy-safe capture procedure is
still required for reproducibility. Robots parsing is an additional guard,
not a substitute for manually reviewing all applicable rules and terms.
The script cannot establish legal permission or complete catalogue coverage.
A redirect or 403/429 is a stop for review, not permission to work around it.
Do not run the dormant scheduler or use the production database for a sample.

Hermetic probe tests:

    python -m pytest tests/test_oem_preflight.py -q

## Separate announcement/discovery lane

- Alldocube official blog: https://www.alldocube.com/en/blog/ .
  Its 2026-11-02 iPlay 80 mini teaser illustrates the value of early
  announcements before a global catalogue entry.
- Blackview sitemap is declared in robots.txt. Actual XML traversal,
  nested sitemap coverage, and newly unlinked product inventory are
  not yet validated. Do not claim comprehensive ZENO coverage.
- Japan/China listings, X posts and third-party news are research or
  the separate D1 proposal inbox, not automatic catalogue admission.
  The pinned D1 executable/profile and consumer evidence must not change
  incidentally during this work.

## Invariants and next steps

Canonical SQLite/QC history, identity keys, qualification clocks, existing
Honor/TCL membership and the D1 integration remain unchanged. All three
new entries are DISABLED. No source has been production-selected,
campaign-approved, scheduled or notification-enabled by these additions.
Fixtures are synthetic shape evidence, not live qualification results.
Never restart the frozen soak. Hetzner is retired; host readiness for
NAS/Dell must be checked independently, with backup before any deployment.

Next: verify live access/source controls, capture bounded real snapshots,
run isolated baseline/resight and a finite campaign, then evaluate editorial
lead time and signal quality before considering production promotion.
