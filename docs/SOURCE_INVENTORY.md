# Source inventory

| Manufacturer | Source ID | Region | Source type | Collector | Validation state | Baseline state | Production state | Live validation | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| Apple | `apple_in_sitemap` | IN | Regional HTML sitemap | `HtmlCatalogueCollector` | EXPERIMENTAL; candidate-quality audit failed closed | DB flag historical but not trusted; accepted set was navigation/category/service material | Disabled; not allowlisted | Runs 5–6 mechanically resighted 23/23; post-fix run 7 rejected all 372 and failed safely | Not a product source; retained for evidence/history only |
| Apple | `apple_us_ipad_pro_store` | US | Apple Store iPad Pro configuration page | `AppleStoreIPadProCollector` | EXPERIMENTAL; corrected parser live-validated | DB flag complete, but early run 8 preceded duplicate-part-number correction; runs 12 stable | Disabled; not allowlisted | Run 8: 96/96/0/96 with 48 new + 48 same-run resights; run 10 after fix: 48/48/0/48 with 24 corrections; run 12: 48/48/0/48, 0 new, 48 resighted | Same part number can have carrier/unlocked URLs; historical pre-fix evidence/events retained |
| Apple | `apple_in_ipad_pro_store` | IN | Apple Store iPad Pro configuration page | `AppleStoreIPadProCollector` | EXPERIMENTAL; corrected parser live-validated | DB flag complete, but early run 9 preceded duplicate-part-number correction; runs 13 stable | Disabled; not allowlisted | Run 9: 48/48/0/48, 48 new; run 11 after fix: 48/48/0/48 with 24 corrections; run 13: 48/48/0/48, 0 new, 48 resighted | Regional part numbers differ from US; global A-model mapping unresolved |
| Apple | `apple_support_model_identification` | IN/global regional variants research | Apple Support model-reference page | **Not implemented** | RESEARCH — PROMISING complement | None | Disabled; not registered or allowlisted | Lightweight probe only: 142 distinct `A####` identifiers | Reference/backfill surface, not timely discovery |
| Samsung | `samsung_us_sitemap` | US | Regional XML product sitemap | `XmlSitemapCollector` | EXPERIMENTAL; live parser/validation plausible | Complete after run 3; run 4 resighted 3 valid products | Disabled; not allowlisted | Run 3: 4/4/0/4; run 4: 4/3/1/3 | Existing validated source; unchanged in this probe |

Metric order is `raw / validated / rejected / accepted`.

The authoritative production membership is `PRODUCTION_ALLOWLIST` in `tablet_clank/sources/registry.py`, currently empty. Research and experimental sources must not be promoted automatically.
