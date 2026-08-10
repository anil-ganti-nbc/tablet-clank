# Source inventory

| Manufacturer | Source ID | Region | Source type | Collector | Validation state | Baseline state | Production state | Last live result | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| Apple | `apple_in_sitemap` | IN | Regional HTML sitemap | `HtmlCatalogueCollector` | EXPERIMENTAL; fixture valid; one live run plausible | Complete in current DB | Disabled; not allowlisted | Success: 372 raw, 23 validated/accepted, 349 rejected | Navigation sitemap is noisy; repeated live cycles and stable identity audit needed |
| Samsung | `samsung_us_sitemap` | US | Regional HTML sitemap/product directory | `HtmlCatalogueCollector` | EXPERIMENTAL; fixture valid; live endpoint unvalidated | Not established | Disabled; not allowlisted | HTTP 404 from configured URL | URL must be re-researched; no live baseline |

Investigated but not implemented as collectors: Lenovo, Xiaomi, OnePlus, Google, Huawei, Honor, RedMagic, Asus, Acer and TCL. They remain RESEARCH only. See `docs/SOURCE_RESEARCH.md`.

Authoritative production membership is `PRODUCTION_ALLOWLIST` in `tablet_clank/sources/registry.py`, currently empty.
