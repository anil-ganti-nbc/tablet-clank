# Source inventory

| Source ID | Manufacturer | Region | Collector | Implementation | Validation | Production |
|---|---|---|---|---|---|---|
| `apple_in_sitemap` | Apple | IN | `HtmlCatalogueCollector` | experimental | live probe: 372 raw / 23 accepted; repeat cycle required | disabled |
| `samsung_us_sitemap` | Samsung | US | `HtmlCatalogueCollector` | experimental | fixture validated; configured live URL returned HTTP 404 | disabled |

The authoritative production allowlist is `tablet_clank.sources.registry.PRODUCTION_ALLOWLIST`, currently an empty tuple. Implemented does not mean production-safe.
