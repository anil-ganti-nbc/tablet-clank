# Source inventory

| Manufacturer | Source ID | Region | Source type | Collector | Validation state | Baseline state | Production state | Live validation | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| Apple | `apple_in_sitemap` | IN | Regional HTML sitemap | `HtmlCatalogueCollector` | EXPERIMENTAL; candidate-quality audit failed closed | DB flag historical but not trusted; accepted set was navigation/category/service material | Disabled; not allowlisted | Runs 5–6 mechanically resighted 23/23; post-fix run 7 rejected all 372 and failed safely | Not a product source; retained for evidence/history only |
| Apple | `apple_store_buy_ipad` | US/IN research | Apple Store family/configuration pages | **Not implemented** | RESEARCH — PROMISING | None | Disabled; not registered or allowlisted | Lightweight probes only: US iPad Pro exposed 96 SKU/configuration entries; IN exposed 48 links | Embedded HTML state, no confirmed public JSON endpoint, SKU/A-model join unresolved |
| Apple | `apple_support_model_identification` | IN/global regional variants research | Apple Support model-reference page | **Not implemented** | RESEARCH — PROMISING complement | None | Disabled; not registered or allowlisted | Lightweight probe: 142 distinct `A####` identifiers on `en-in/108043` | Reference/backfill surface, not timely discovery; regional content varies |
| Samsung | `samsung_us_sitemap` | US | Regional XML product sitemap | `XmlSitemapCollector` | EXPERIMENTAL; live parser/validation plausible | Complete after run 3; run 4 resighted 3 valid products | Disabled; not allowlisted | Run 3: 4/4/0/4; run 4: 4/3/1/3 | Existing validated source; unchanged in this reconnaissance |

Metric order is `raw / validated / rejected / accepted`.

The authoritative production membership is `PRODUCTION_ALLOWLIST` in `tablet_clank/sources/registry.py`, currently empty. Research candidates are not runtime sources and must not be promoted automatically.
