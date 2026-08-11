# Tablet Clank Soak Readiness

Audit date: 2026-08-11. The bounded soak runner is implemented, but no 12-cycle soak or scheduler is running.

## Frozen roster

The frozen soak roster contains 6 enabled experimental sources across four OEMs. `apple_in_sitemap` remains inspectable historical source metadata but is disabled and excluded from runtime selection.

| Source | OEM / region | Collector | Baseline | Latest state | Readiness |
|---|---|---|---|---|---|
| `apple_us_ipad_pro_store` | Apple / US | `AppleStoreIPadProCollector` | Complete | Run 14: 48 accepted/resighted | `READY` |
| `apple_in_ipad_pro_store` | Apple / IN | `AppleStoreIPadProCollector` | Complete | Run 15: 48 accepted/resighted | `READY` |
| `samsung_us_sitemap` | Samsung / US | `XmlSitemapCollector` | Complete | Run 4: 3 accepted/resighted | `READY` |
| `honor_cn_tablets_catalogue` | Honor / CN | `HonorCNTabletsCollector` | Complete | Run 18: 32 accepted/resighted | `READY` |
| `honor_cn_tablets_comparison` | Honor / CN | `HonorCNTabletsCollector` | Complete | Run 19: 24 accepted/resighted | `READY` |
| `tcl_global_tablets` | TCL / GLOBAL | `TCLGlobalTabletsCollector` | Complete | Run 21: 24 accepted/resighted | `READY` |

The Apple sitemap is retired from runtime with state `DISABLED`. Its source record, products, observations, rejected candidates, runs and events remain historical evidence. The registry’s single runtime rule selects only sources with state `EXPERIMENTAL`, making accidental soak inclusion impossible.

## Current protections

- HTTP status/content-type and retrieval errors: `PASS` through the shared collector fetch path.
- Zero-result protection: `PASS`; zero accepted candidates fail the run and do not advance health.
- Major-collapse protection: `PARTIAL`; Honor and TCL have source-specific minimum/anchor guards, while Apple Store and Samsung rely on zero-result and filtering protections. This is safe enough for bounded experimental soak because disappearance detection is not implemented and failed/empty runs do not advance health or emit disappearance events.
- Baseline false-success protection: `PASS` for new baselines; a baseline is completed only after accepted candidates. Historical Apple sitemap state remains explicitly untrusted.
- No-silent-drop protection: `PASS`; missing candidates do not create disappearance state or events.
- Source failure isolation: `PASS`; each collector result is recorded independently and a failed source does not abort processing of other sources.
- Duplicate identity protection: `PASS`; normalized identity keys are unique and the current database has zero duplicates.

## Event and identity safety

The database contains 48 historical Apple `identity_correction` events and no Honor/TCL events. Correction events are not editorial `new_product` events and must remain excluded from future alert delivery. Honor’s two sources resolve shared regional slugs to one canonical product identity while preserving separate observations/evidence paths.

## Conceptual execution model

Use one deterministic process per cycle, with fixed source order and no concurrency. `python -m tablet_clank.cli soak` runs a finite number of cycles and then stops. Each cycle continues after an individual source failure and finishes as `SUCCESS` or `PARTIAL_FAILURE`; integrity and duplicate failures abort the soak.

Recommended order: Apple Store US, Apple Store IN, Samsung US, Honor catalogue, Honor comparison, TCL.

Recommended cadence is one cycle every two hours. This is slow enough to observe longitudinal drift without aggressive polling and is appropriate for experimental first-party catalogue monitoring.

## Cycle record

Reuse `collector_runs`, `source_state`, observations and change events. A small future summary should record cycle number, start/end time, source ID, retrieval result, raw/validated/rejected/accepted counts, new/updated/resighted counts, events, health status, error and database-integrity result. Do not duplicate observation or event schema.

## Failure semantics

One failed source must produce a recorded source failure while allowing other sources to complete. It must not advance baseline/healthy state, absence state or editorial events. The cycle is `PARTIAL_FAILURE` if at least one source succeeds and another fails. A cycle-level failure is reserved for infrastructure/database failure.

## Run locking and portability

The implemented runner uses the smallest cross-platform lock around a cycle: an exclusive lock file created atomically beside the database, containing PID/start metadata, removed on normal exit, and treated as stale only when local liveness proves the owner is dead. Manual collection and soak execution use the same lock policy. Paths are configurable and portable, defaulting to `var/tablet_clank.db` and `var/logs/soak.jsonl`.

## Success criteria

Require 12 consecutive two-hour cycles for the six-source healthy soak roster. Every cycle must preserve database integrity, have no duplicate identities, no false `new_product` events, no silent-drop regression, no unhandled source crash, isolated failures, and stable baseline/resight behaviour. Successful soak completion must produce a review report; it must not modify the production allowlist or enable alerts.

## Promotion policy

Promotion is a separate human-reviewed phase. Soak completion never automatically promotes a source. Production allowlist remains empty and alerts remain disabled.

## Smoke validation

One live cycle was run on 2026-08-11 with `--cycles 1 --interval-seconds 0`. All six sources succeeded serially, existing identities were resighted, Samsung accepted 3 of 4 candidates with 1 expected rejection, all other sources accepted their full candidate sets, and the cycle produced 0 events, 0 duplicates and database integrity `ok`.

## Readiness verdict

`READY_TO_IMPLEMENT_SOAK`. The six enabled sources are healthy enough for bounded experimental soak; the retired Apple sitemap is excluded by the registry selection rule.
