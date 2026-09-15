# Tablet Clank

> **Phase 0: UNVERIFIED_PRODUCTION — promotion frozen.** Repository state is
> not proof of the deployed SHA, scheduler, database, notification authority,
> backup, or rollback target; those facts remain `UNKNOWN` in the fleet ledger.

Tablet Clank is an independent, evidence-first product-intelligence system for discovering meaningful tablet catalogue changes from first-party manufacturer sources.

Stage 1 is intentionally small: Apple's historical India sitemap remains a
disabled/untrusted source, Apple US/India iPad Pro Store configuration pages
and Samsung US XML sitemap are experimental collectors, and Honor (CN
catalogue + comparison) and TCL (global catalogue) are experimental sources
promoted to the production allowlist after successful isolated soaks (Honor
UK joined in Wave 3). The intended profile is manually triggered and
intentionally dormant, and alerts are disabled (`ALERTS_ENABLED = False`). A
2026-09-15 read-only observation found a live Hetzner systemd timer; that
runtime drift is recorded separately and is not authorization to mutate it.

## Operations

```text
python -m tablet_clank.cli backup var/backups/<timestamp>.db   # SQLite-safe recovery point
python -m tablet_clank.cli production --check                  # production readiness
python -m tablet_clank.cli soak --check                        # experimental readiness
```

Deployment artefacts: `Dockerfile` + `docker-compose.staging.yml` (one-shot,
named volume) and `deploy/systemd/*.example` (single scheduler authority).
The container schedules nothing; an external timer drives it.

## Quick start

```text
python -m pytest
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect --all
python -m tablet_clank.cli status
python -m tablet_clank.cli db-integrity --db var/tablet_clank.db
```

The default database is `var/tablet_clank.db`. Use `--live` with `collect` for a controlled network probe. No credentials are required.
