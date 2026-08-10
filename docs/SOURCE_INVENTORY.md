# Source inventory

| Manufacturer | Source ID | Region | Source type | Collector | Validation state | Baseline state | Production state | Live validation | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| Apple | `apple_in_sitemap` | IN | Regional HTML sitemap | `HtmlCatalogueCollector` | EXPERIMENTAL; retrieval works, candidate-quality audit failed closed after a narrow identifier rule | DB flag remains complete from historical run 1, but it is **not trusted** because the accepted set was navigation/category/service material | Disabled; not allowlisted | Runs 5–6: 372/23/349/23, 0 new, 23 resighted each. Run 7 after audit fix: 372/0/372/0, failed safely | Sitemap does not expose stable Apple product identifiers in the accepted-looking links |
| Samsung | `samsung_us_sitemap` | US | Regional XML product sitemap | `XmlSitemapCollector` | EXPERIMENTAL; replacement source live and parser/validation plausible | Complete after run 3; run 4 resighted 3 valid products | Disabled; not allowlisted | Run 3: 4/4/0/4, 4 new. Run 4: 4/3/1/3, 0 new, 3 resighted | Current sitemap mixed one generic `/all-tablets/` page; retained historical false-positive observation, later runs reject it |

Metric order in this document is `raw / validated / rejected / accepted`.

Investigated but not implemented as collectors: Lenovo, Xiaomi, OnePlus, Google, Huawei, Honor, RedMagic, Asus, Acer and TCL. They remain RESEARCH only. The authoritative production membership is `PRODUCTION_ALLOWLIST` in `tablet_clank/sources/registry.py`, currently empty.
