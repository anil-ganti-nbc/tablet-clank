# Tablet Clank Soak Readiness

Audit date: 2026-08-11. This document is a design review only; no soak runner or scheduled execution exists.

## Frozen roster

The frozen experimental roster contains 7 runtime sources across four OEMs:

| Source | OEM / region | Collector | Baseline | Latest state | Readiness |
|---|---|---|---|---|---|
| `apple_in_sitemap` | Apple / IN | `HtmlCatalogueCollector` | Historical flag exists but is untrusted | Latest run 7 failed closed: 0 accepted | `SOAK_BLOCKED` |
| `apple_us_ipad_pro_store` | Apple / US | `AppleStoreIPadProCollector` | Complete | Run 14: 48 accepted/resighted | `READY` |
| `apple_in_ipad_pro_store` | Apple / IN | `AppleStoreIPadProCollector` | Complete | Run 15: 48 accepted/resighted | `READY` |
| `samsung_us_sitemap` | Samsung / US | `XmlSitemapCollector` | Complete | Run 4: 3 accepted/resighted | `READY` |
| `honor_cn_tablets_catalogue` | Honor / CN | `HonorCNTabletsCollector` | Complete | Run 18: 32 accepted/resighted | `READY` |
| `honor_cn_tablets_comparison` | Honor / CN | `HonorCNTabletsCollector` | Complete | Run 19: 24 accepted/resighted | `READY` |
| `tcl_global_tablets` | TCL / GLOBAL | `TCLGlobalTabletsCollector` | Complete | Run 21: 24 accepted/resighted | `READY` |

The Apple sitemap is not silently included in soak scope: its latest run correctly failed closed because the source is navigation/category material after the stable-identifier correction. It must be explicitly removed from soak scope or replaced before a runner is implemented.

## Current protections

- HTTP status/content-type and retrieval errors: `PASS` through the shared collector fetch path.
- Zero-result protection: `PASS`; zero accepted candidates fail the run and do not advance health.
- Major-collapse protection: `PARTIAL`; Honor and TCL have source-specific minimum/anchor guards, while Apple Store and Samsung rely on zero-result and filtering protections. No current gap permits mass disappearance events because disappearance detection is not implemented.
- Baseline false-success protection: `PASS` for new baselines; a baseline is completed only after accepted candidates. Historical Apple sitemap state remains explicitly untrusted.
- No-silent-drop protection: `PASS`; missing candidates do not create disappearance state or events.
- Source failure isolation: `PASS`; each collector result is recorded independently and a failed source does not abort processing of other sources.
- Duplicate identity protection: `PASS`; normalized identity keys are unique and the current database has zero duplicates.

## Event and identity safety

The database contains 48 historical Apple `identity_correction` events and no Honor/TCL events. Correction events are not editorial `new_product` events and must remain excluded from future alert delivery. Honor’s two sources resolve shared regional slugs to one canonical product identity while preserving separate observations/evidence paths.

## Conceptual execution model

Use one deterministic process per cycle, with fixed source order and no concurrency. The future manual command should run one cycle explicitly; the bounded soak command should run a finite number of cycles and then stop. Each cycle should continue after an individual source failure and finish as `SUCCESS`, `PARTIAL_FAILURE`, or `FAILED` according to source outcomes.

Recommended order: Apple Store US, Apple Store IN, Samsung US, Honor catalogue, Honor comparison, TCL. Do not include `apple_in_sitemap` until its soak status is resolved.

Recommended cadence is one cycle every two hours. This is slow enough to observe longitudinal drift without aggressive polling and is appropriate for experimental first-party catalogue monitoring.

## Cycle record

Reuse `collector_runs`, `source_state`, observations and change events. A small future summary should record cycle number, start/end time, source ID, retrieval result, raw/validated/rejected/accepted counts, new/updated/resighted counts, events, health status, error and database-integrity result. Do not duplicate observation or event schema.

## Failure semantics

One failed source must produce a recorded source failure while allowing other sources to complete. It must not advance baseline/healthy state, absence state or editorial events. The cycle is `PARTIAL_FAILURE` if at least one source succeeds and another fails. A cycle-level failure is reserved for infrastructure/database failure.

## Run locking and portability

Implement the smallest cross-platform lock around a cycle: an exclusive lock file created atomically beside the database, containing PID/start metadata, removed on normal exit, and treated as stale only after an explicit age/process check. Manual collection and soak execution should use the same lock policy. Avoid PowerShell-only commands, Windows paths, shell-specific quoting and absolute desktop paths; resolve paths relative to the repository or configured environment variables. The database path should remain configurable, defaulting to `var/tablet_clank.db`, with logs/reports under ignored `var/logs/` or an explicitly configured output directory.

## Success criteria

Require 12 consecutive two-hour cycles for the healthy soak roster after the Apple sitemap decision is resolved. Every cycle must preserve database integrity, have no duplicate identities, no false `new_product` events, no silent-drop regression, no unhandled source crash, isolated failures, and stable baseline/resight behaviour. Successful soak completion must produce a review report; it must not modify the production allowlist or enable alerts.

## Promotion policy

Promotion is a separate human-reviewed phase. Soak completion never automatically promotes a source. Production allowlist remains empty and alerts remain disabled.

## Readiness verdict

`SOAK_BLOCKED_SOURCE_HEALTH` because `apple_in_sitemap` is currently registered but its latest run failed closed and its historical baseline is untrusted. No soak execution should begin until that source is explicitly resolved.
