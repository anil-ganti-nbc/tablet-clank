# Source inventory

| Manufacturer | Source ID | Region | Source type | Collector | Validation state | Baseline state | Production state | Live validation | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| Apple | `apple_in_sitemap` | IN | Regional HTML sitemap | `HtmlCatalogueCollector` | EXPERIMENTAL; candidate-quality audit failed closed | DB flag historical but not trusted; accepted set was navigation/category/service material | Disabled; not allowlisted | Runs 5–6 mechanically resighted 23/23; post-fix run 7 rejected all 372 and failed safely | Not a product source; retained for evidence/history only |
| Apple | `apple_us_ipad_pro_store` | US | Apple Store iPad Pro configuration page | `AppleStoreIPadProCollector` | EXPERIMENTAL; corrected parser live-validated | DB flag complete; early correction evidence retained | Disabled; not allowlisted | Run 14: 48/48/0/48, 0 new, 48 resighted; 24 retained `identity_correction` events | Same part number can have carrier/unlocked URLs; historical evidence retained |
| Apple | `apple_in_ipad_pro_store` | IN | Apple Store iPad Pro configuration page | `AppleStoreIPadProCollector` | EXPERIMENTAL; corrected parser live-validated | DB flag complete; early correction evidence retained | Disabled; not allowlisted | Run 15: 48/48/0/48, 0 new, 48 resighted; 24 retained `identity_correction` events | Regional part numbers differ from US; global A-model mapping unresolved |
| Apple | `apple_support_model_identification` | IN/global regional variants research | Apple Support model-reference page | **Not implemented** | RESEARCH — PROMISING complement | None | Disabled; not registered or allowlisted | Lightweight probe only: 142 distinct `A####` identifiers | Reference/backfill surface, not timely discovery |
| Samsung | `samsung_us_sitemap` | US | Regional XML product sitemap | `XmlSitemapCollector` | EXPERIMENTAL; live parser/validation plausible | Complete after run 3; run 4 resighted 3 valid products | Disabled; not allowlisted | Run 3: 4/4/0/4; run 4: 4/3/1/3 | Existing validated source; unchanged in this probe |

Lenovo remains research-only. No Lenovo source is registered or implemented. The 2026-08-11 reconnaissance recommends PSREF as the primary future probe target because its official model tables expose Lenovo identifiers, regional fields, deep specifications, historical/withdrawn references and an Excel export path. Lenovo storefront/PDP, support lookup and HTML site-map surfaces remain corroboration or unsuitable discovery surfaces; direct undocumented PSREF API access was not pursued after token-gated 403/405 responses.

The independent Legion Tab cross-check passed offline (`tests/fixtures/lenovo_psref_crosscheck.json`, 8 rows), but the live-probe gate is blocked as `LIVE_SOURCE_NOT_RELIABLE`: the public model page is a JavaScript shell and safe direct model/spec/export probes returned empty responses. Lenovo remains unregistered, with no live runs, baseline, products, observations, or events.

Metric order is `raw / validated / rejected / accepted`.

The authoritative production membership is `PRODUCTION_ALLOWLIST` in `tablet_clank/sources/registry.py`, currently empty. Research and experimental sources must not be promoted automatically.

Xiaomi remains research-only and is not registered. The 2026-08-11 reconnaissance found a promising China Mi Mall catalogue/detail surface and useful global/regional product/spec complements, but no documented stable public SKU/variant feed was proven. The recommended future strategy is `MULTI_SOURCE_REQUIRED`, with the China catalogue as the first narrow probe target. No Xiaomi database rows, baseline, or runtime source exist.

Honor is experimentally registered only on the two audited China HTML surfaces. Regional store SKU-like values and official regulatory model identifiers remain useful but unresolved complements.

Expansion-wave runtime additions:

| Honor | `honor_cn_tablets_catalogue` | CN | China HTML tablet catalogue | `HonorCNTabletsCollector` | EXPERIMENTAL | Complete; baseline/resight 32/32/0/32 | Disabled; not allowlisted | Runs 16 and 18 healthy; 0 events | Regional slugs; model mapping unresolved |
| Honor | `honor_cn_tablets_comparison` | CN | China HTML tablet comparison | `HonorCNTabletsCollector` | EXPERIMENTAL | Complete; baseline/resight 24/24/0/24 | Disabled; not allowlisted | Runs 17 and 19 healthy; 0 events | Complementary surface |
| TCL | `tcl_global_tablets` | GLOBAL | Global HTML tablet catalogue | `TCLGlobalTabletsCollector` | EXPERIMENTAL | Complete; baseline/resight 24/24/0/24 | Disabled; not allowlisted | Runs 20 and 21 healthy; 0 events | Configuration/global equivalence unresolved |

Honor is now landed experimentally only on the two audited China HTML surfaces. TCL is now landed experimentally on the global HTML tablet catalogue. Huawei, OnePlus, OPPO, RedMagic/Nubia, Asus, Acer and Vivo/iQOO remain parked after bounded reconnaissance; reopen only if stable public product-index/model-code infrastructure appears.
