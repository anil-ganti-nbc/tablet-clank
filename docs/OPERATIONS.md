# Operations

Create the local database and establish fixture baselines:

```text
python -m tablet_clank.cli collect --all
python -m tablet_clank.cli status
python -m tablet_clank.cli db-integrity
```

Run a controlled live probe:

```text
python -m tablet_clank.cli collect apple_in_sitemap --live
python -m tablet_clank.cli collect samsung_us_sitemap --live
```

The CLI prints source state and run results. Inspect SQLite directly for evidence, rejected candidates and events. A failed or zero-accepted run is unhealthy and cannot advance baseline state. Production scheduling is deliberately absent; the allowlist is empty and no Discord integration exists.

Live validation on 2026-08-10: Apple IN responded successfully but its navigation sitemap includes substantial non-tablet material, visible in rejection metrics. Samsung US's configured sitemap URL returned HTTP 404 and must be re-researched before promotion.
