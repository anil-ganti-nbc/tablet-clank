# Tablet Clank

Tablet Clank is an independent, evidence-first product-intelligence system for discovering meaningful tablet catalogue changes from first-party manufacturer sources.

Stage 1 is intentionally small: Apple India and Samsung US regional sitemap surfaces are implemented as experimental collectors. Production membership is empty and alerts are disabled.

## Quick start

```text
python -m pytest
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect --all
python -m tablet_clank.cli status
python -m tablet_clank.cli db-integrity
```

The default database is `var/tablet_clank.db`. Use `--live` with `collect` for a controlled network probe. No credentials are required.
