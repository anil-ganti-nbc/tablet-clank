# Bounded Experimental Soak Operations

The soak runner is bounded and experimental. It does not schedule itself, send alerts, promote sources, or modify the production allowlist.

## Campaign-scoped isolated soaks (current mechanism, 2026-08-29)

The historical frozen-roster runner below is RETAINED but can no longer start: its roster overlaps `PRODUCTION_ALLOWLIST`, and `resolve_soak_sources()` refuses that overlap by design. Campaign soaks are the active mechanism:

```text
python -m tablet_clank.cli soak-campaign --manifest <path> --init --campaign <id> --sources honor_uk_tablets --cycles 12 --interval-seconds 7200
python -m tablet_clank.cli soak-campaign --manifest <path> --check
python -m tablet_clank.cli soak-campaign --manifest <path> [--live]
```

Campaigns take explicit source IDs (gated by `CAMPAIGN_APPROVED_SOURCE_IDS` in the registry), pin a roster hash and interpreter environment in the manifest, run against an isolated SQLite database with a campaign-scoped lock, open the canonical DB read-only (`mode=ro`) for preflight only, and append evidence records (start / per-cycle / aborted / refused / interrupted / end) to a campaign-specific JSONL. Any non-SUCCESS cycle aborts the campaign. Never launch one as a fragile interactive background job — use a durable supervisor (on the NAS: a dedicated Docker container with `restart=no`).

honor_uk_tablets was promoted to `PRODUCTION_ALLOWLIST` on 2026-08-29 (Wave 3) and is no longer campaign-approved. Reference campaign: `honor-uk-iso-nas-001` on the NAS (`/volume2/clank/tablet-clank`, container `tablet-clank-honor-uk-iso-nas-001`), 12/12 SUCCESS 2026-08-28→29; evidence under `state/logs/` and `state/campaigns/`. The Windows campaign `honor-uk-iso-001` is CLOSED (`OPERATOR_ABORTED_FOR_HOST_RELOCATION`, 2 healthy cycles preserved as supporting evidence only, not counted toward promotion).

## Frozen roster and command (historical, retained)

The runner resolves exactly the registry sources whose state is `EXPERIMENTAL` and compares them with the frozen six-source set:

```text
apple_in_ipad_pro_store
apple_us_ipad_pro_store
honor_cn_tablets_catalogue
honor_cn_tablets_comparison
samsung_us_sitemap
tcl_global_tablets
```

Readiness check:

```text
python -m tablet_clank.cli soak --check
```

Bounded execution:

```text
python -m tablet_clank.cli soak
python -m tablet_clank.cli soak --cycles 12 --interval-seconds 7200
```

The default is 12 cycles with a two-hour post-cycle interval. Tests inject a zero/synthetic sleep; production behavior remains bounded and deterministic. An interrupted run restarts from cycle 1 on the next invocation; completed cycles are preserved in the JSONL report but are not fabricated as resumed state.

## Execution and locking

Sources run serially in sorted source-ID order. The default database is `var/tablet_clank.db`; `--db PATH` is supported. Reports are appended to `var/logs/soak.jsonl`, derived from the database directory. The lock is an atomically created `tablet_clank.soak.lock` beside the configured database and records PID, start time, role and path.

Manual `collect` commands use the same lock domain, so a manual collection cannot overlap a soak cycle. Active locks fail closed. A lock owned by a clearly dead local PID is recoverable; malformed locks or liveness that cannot be established remain blocking. Normal completion and `KeyboardInterrupt` release the lock.

## Cycle and failure semantics

Each cycle records source metrics, source errors, newly created event details, integrity, duplicate count and overall status. A source failure is isolated and later sources still run; the cycle becomes `PARTIAL_FAILURE`. Database-integrity failure or duplicate identities abort the soak immediately. Roster drift, missing baselines, production membership or lock conflict refuse startup.

Historical events are excluded from per-cycle event counts. The runner never calls alert delivery. Event evidence is recorded for human review only.

## Outcomes and promotion

Possible outcomes include `SUCCESS`, `PARTIAL_FAILURE`, `SOAK_ABORTED_DB_INTEGRITY`, `SOAK_ABORTED_DUPLICATE_IDENTITY` and `INTERRUPTED`. Twelve completed healthy cycles are required for a clean `PASSED` review; isolated source failures yield a reviewable completed-with-failures result. No outcome automatically promotes a source. Production remains empty and alerts remain disabled.
