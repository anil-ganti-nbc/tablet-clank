# Bounded Experimental Soak Operations

The soak runner is bounded and experimental. It does not schedule itself, send alerts, promote sources, or modify the production allowlist.

## Frozen roster and command

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
