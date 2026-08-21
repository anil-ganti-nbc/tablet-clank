# Tablet Clank

> **Phase 0: UNVERIFIED_PRODUCTION — promotion frozen.** Repository state is
> not proof of the deployed SHA, scheduler, database, notification authority,
> backup, or rollback target; those facts remain `UNKNOWN` in the fleet ledger.

Tablet Clank is an independent, evidence-first product-intelligence system for discovering meaningful tablet catalogue changes from first-party manufacturer sources.

Stage 1 is intentionally small: Apple’s historical India sitemap remains an experimental/untrusted source, Apple US/India iPad Pro Store configuration pages are experimental collectors, and Samsung US has an experimental XML sitemap collector. Production membership is empty and alerts are disabled.

## Quick start

```text
python -m pytest
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect --all
python -m tablet_clank.cli status
python -m tablet_clank.cli db-integrity
```

The default database is `var/tablet_clank.db`. Use `--live` with `collect` for a controlled network probe. No credentials are required.
