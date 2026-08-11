# Source research

Research was performed against official first-party surfaces on 2026-08-10 through 2026-08-11. No browser automation, third-party sources, access-control bypasses or collector implementation were used in this reconnaissance pass.

## Apple reconnaissance

| Official surface | Region | HTTP/structure probe | Identity and discovery assessment | Decision |
|---|---|---|---|---|
| `https://www.apple.com/in/sitemap/` | IN | HTTP 200 HTML; 372 links in the existing live probe | Navigation-oriented. Tablet-looking links were categories, services, accessories or marketing pages; no stable product identifiers in accepted-looking links. | UNSUITABLE as a product collector |
| `https://www.apple.com/in/ipad/` | IN | HTTP 200 HTML, approximately 840 KB; product tiles and `productId` references present | Current lineup landing page, but its product tiles are family/category presentation rather than individual SKU/model inventory. | MARGINAL for corroboration only |
| `https://www.apple.com/us/shop/buy-ipad` | US | HTTP 200 HTML, approximately 526 KB; embedded serialized data includes 35 regional `baseIdentifier` values, 16 `partNumber` values and links to four family selectors | Official Store catalogue entry point. It exposes current families and regional Store identifiers, but the landing page alone is not configuration-complete. | PROMISING entry point |
| `https://www.apple.com/in/shop/buy-ipad` | IN | HTTP 200 HTML, approximately 417 KB; embedded data includes 31 regional `baseIdentifier` values and 12 `partNumber` values | Same Store infrastructure with India-specific SKU suffixes and availability. | PROMISING regional counterpart |
| `https://www.apple.com/us/shop/buy-ipad/ipad-pro` | US | HTTP 200 HTML, approximately 2.16 MB; 96 SKU entries and 96 individual configuration links observed | Individual configuration paths expose screen size, capacity, colour, Wi-Fi/cellular and glass options. Embedded data includes stable Apple SKU/part numbers such as `MDWK4LL/A`; configuration names include current model generation such as iPad Pro M5. | **PROMISING best discovery candidate** |
| `https://www.apple.com/in/shop/buy-ipad/ipad-pro` | IN | HTTP 200 HTML, approximately 2.15 MB; 48 configuration links observed; regional SKUs such as `MDWK4HN/A` | Demonstrates regional configuration and identity differences on the same Store family surface. | PROMISING regional validation candidate |
| `https://support.apple.com/en-in/108043` | IN | HTTP 200 HTML, approximately 1.24 MB; 142 distinct `A####` model identifiers observed | Strong canonical identity/reference surface: model names, year, capacities, Wi-Fi/Wi-Fi + Cellular distinctions and technical-specification references. It describes the known model universe, but is not an early product-publication feed. | PROMISING complement, not primary discovery |
| `https://support.apple.com/ipad` | Global/US support | HTTP 200 HTML | Generic support landing page; useful navigation to model identification, not an individual-product source. | MARGINAL |

### Best candidate decision: PROMISING

The Apple Store family selector pages are the best candidate. They are official, machine-readable enough for a narrow parser, expose individual configuration links, preserve regional Store identity through SKU/part number values, and distinguish meaningful variants such as capacity, colour and Wi-Fi/cellular. The current probes did not expose Apple hardware `A####` model numbers on Store pages; the Support model-identification page can provide a complementary A-model mapping later.

Expected coverage is current purchasable/marketed Store configurations rather than the complete historical Apple catalogue. The main limitations are large embedded HTML/serialized state, possible Store markup changes, no proven public JSON endpoint, and uncertainty about how reliably SKU-to-A-model mapping can be joined. The Store pages may also represent sellable configurations rather than separate hardware models.

The experimental implementation confirmed the key risk: the US page exposes repeated carrier/unlocked URLs for one part number. The corrected parser deduplicates by regional part number and prefers the non-carrier representation; it also maps Apple’s `wificell` value to Wi-Fi + Cellular. After correction, both US and IN produced 48 accepted configurations and then 48 resighted configurations. The first pre-correction runs and their 48 correction events remain retained as evidence.

### Failed approaches preserved

- The regional sitemap was tested first and proved too navigation-heavy; stable product identity could not be defended from its accepted-looking links.
- The generic iPad landing page exposes product-family presentation but not a complete individual configuration inventory.
- No standalone public Apple Store JSON/catalogue endpoint was confirmed during lightweight probing. Do not invent an endpoint from embedded page state.
- Apple Support model identification is valuable for identity enrichment, but its purpose and structure suggest reference/backfill rather than timely discovery.

## Samsung US research

Samsung research remains documented for continuity. The old `/us/sitemap/` returned 404. The official `https://www.samsung.com/us/top_sitemap.xml` replacement is already implemented and experimentally validated; it is outside this Apple-only reconnaissance scope and was not modified.

## Other research

Lenovo, Xiaomi, OnePlus, Google, Huawei, Honor, RedMagic, Asus, Acer and TCL remain RESEARCH only. Search results alone are not treated as evidence or a source registry.

## Lenovo first-party reconnaissance

Research was performed on 2026-08-11 against official Lenovo-controlled domains only. No Lenovo collector, registry entry, browser automation, access-control bypass, or runtime/database change was made.

### Surfaces investigated

| Official surface | Region | HTTP/structure probe | Identity, discovery and regional assessment | Decision |
|---|---|---|---|---|
| [Lenovo PSREF](https://psref.lenovo.com/) product/family pages | Global reference surface | Public product pages returned HTTP 200. Representative `WDProduct` pages are server-delivered shells whose JavaScript calls Lenovo-owned product-info, model-list, comparison/spec and export functions. The visible model table is machine-readable after page execution; direct API calls without the page token returned HTTP 403/405 and were not pursued. | Strongest candidate. Family hierarchy is visible through product-line/series/product selection; model tables expose product names, regional codes, machine type, configuration rows, specifications, documentation and an Excel export action. The pages explicitly state that configurations vary by region and that PSREF models may not be sold in every country. | **PROMISING / recommended primary research target** |
| PSREF representative current/recent families | Global with regional columns | `Lenovo Tab`, `Idea Tab`, `Yoga Tab`, `Legion Tab`, `Tab P12`, and older `TAB3 7 Essential` pages were reachable. Search-indexed/rendered examples showed model-table counts from 2 (`TAB3 7 Essential`) to 187 (`Tab E7` historical family); current family pages expose multiple configuration columns. | Model/product identifiers include Lenovo product names and machine-type prefixes such as `ZA...`; regional MTM/SKU-like values appear as distinct model columns. Rich specs include processor, memory, storage, display, WWAN/WLAN, battery, colour, warranty and announcement date where populated. This is configuration/spec reference, not proof of current sale. | **PROMISING for identity/spec reference; freshness requires controlled baseline semantics** |
| PSREF HTML/Excel/PDF/documentation infrastructure | Global | Current pages visibly expose `Download in Excel`; product specification HTML/PDF documents are public, including dated last-modified/revision information and withdrawn-product books. | Excellent machine-readable or extractable specification depth and useful historical coverage. Excel/model tables are more useful than generic PDFs for enumeration; PDFs/HTML documents are better evidence/spec references than early discovery feeds. | **PROMISING complement** |
| [Lenovo US tablet storefront/category](https://www.lenovo.com/us/en/lenovotablets/) and product pages | US | HTTP 200, approximately 1 MB HTML in a lightweight probe. The category presents Yoga Tab, Idea Tab, Lenovo Tab and Legion Tab series; individual PDPs expose marketing copy and a limited Tech Specs section. | Good current commercial/marketing presence and individual PDP URLs, but pages mix products, accessories, bundles, campaigns and availability language. Storefront product identifiers are URL/part-number-like and may be regional; the surface is not a complete model/configuration inventory. | **MARGINAL as primary discovery; useful corroboration** |
| [Lenovo US product results](https://www.lenovo.com/us/en/tablets/results/) and [site map](https://www.lenovo.com/us/en/site-map/) | US | HTTP 200 for results/site-map HTML; no standalone `/sitemap.xml` or `/sitemap_index.xml` was found (both returned 404). | Navigation and merchandising indexes, not a clean tablet product feed. They can contain categories, accessories, editorial pages and product links, so they are noisy and not identity-safe without PSREF corroboration. | **UNSUITABLE as primary source** |
| [Lenovo Support](https://support.lenovo.com/us/en) product selection / detect-product surface | US/global variants | Generic support landing page is visible through official search, but direct `/products/tablets` and related lightweight requests returned HTTP 403 Access Denied. | Support is designed for lookup, drivers and troubleshooting after a product is known, not for timely discovery. Access behaviour and lookup-oriented semantics make it unsuitable as a first-party discovery feed in this reconnaissance. | **UNSUITABLE for discovery; possible later identity lookup only** |
| [PSREF withdrawn-products infrastructure](https://psref.lenovo.com/WithdrawnBook/) | Global historical | Official withdrawn-books page is reachable and explicitly says withdrawn information is no longer maintained or updated. | Valuable historical evidence and backfill context; not a current discovery stream. | **PROMISING historical complement only** |

### PSREF sample observations

- `Lenovo Tab`, `Idea Tab`, `Yoga Tab` and `Legion Tab` are distinct product/family surfaces rather than generic tablet navigation. Representative specification documents expose Android version, SoC, soldered RAM, storage, display, cellular/WLAN distinctions, battery, colour, accessories and regional caveats.
- Current/recent examples include `Idea Tab` with 4/8 GB and 128/256 GB options, `Yoga Tab` with region-dependent keyboard/pen availability, `Legion Tab (8.8", 5)` with 12/16 GB and 3K/165 Hz display data, and `Lenovo Tab` with 4/8 GB and 64/128 GB options. These are family-level configuration/spec examples, not a claim that every listed option is globally sold.
- PSREF’s model-table identifiers are materially stronger than marketing URLs: product/model labels, machine-type prefixes and regional model/configuration codes can support a conservative Lenovo identity key. A code such as `ZA...` should remain a source identifier until its exact MTM/SKU semantics are verified from the table/export; it must not be guessed into a global canonical model.
- PSREF regional semantics are explicit: a model can be present in the reference but unavailable in a country, and selected configurations are only available in selected regions. This is analogous to the current Apple finding that a regional commercial identifier should not automatically become a global hardware identity.
- PSREF has historical value through announcement dates, revision/last-modified metadata and withdrawn-product books. That history can distinguish a newly appearing PSREF model from a silently edited specification, but it does not prove a market launch or current sellability.

### Strategy decision

Recommended strategy: **PSREF_PRIMARY**.

PSREF is the only investigated Lenovo surface that combines a product/family hierarchy, individual model/configuration rows, Lenovo identifiers, regional semantics, deep specifications, historical documents and an official export path. Storefront/PDP pages should remain a future corroboration source for commercial presence, not the discovery authority. Support is lookup-oriented and access-controlled in lightweight probes; sitemaps are navigation/merchandising surfaces rather than product inventories.

### Freshness and baseline semantics to preserve in a future probe

The first PSREF observation must be a silent baseline. A later run should emit a candidate only for a previously unseen stable model/configuration identifier in the same source/region context, or for an explicitly documented regional appearance. A changed spec row, changed page revision or changed regional availability should be recorded as an observation/specification change and not treated as a new product. A retired/withdrawn PSREF entry should not be inferred as disappearance from a missed page. Cross-region rows must be joined only when Lenovo evidence shows the same machine type/model identity; regional codes remain observations/variants until proven otherwise.

### Failed approaches preserved

- Directly guessing or calling PSREF JSON endpoints without the page-provided token was not pursued after HTTP 403/405 responses. Do not bypass that control or turn an undocumented endpoint into an implementation assumption.
- Lenovo US `/sitemap.xml` and `/sitemap_index.xml` returned 404. The HTML site map and product-results pages are navigation/merchandising pages, not equivalent to a clean XML product sitemap.
- Lenovo Support tablet product paths returned HTTP 403 in lightweight requests and are lookup/support surfaces, not a defensible early-discovery feed.
- Search results and individual marketing/PDP pages were not treated as a complete model inventory. They are corroboration only until PSREF identity and model-table semantics are verified.

## Lenovo PSREF identity / fixture design review

This narrower review was performed on 2026-08-11 using official PSREF family/model pages and specification documents only. No collector, registry entry, identity code, schema, or database state was changed.

### Families reviewed

- `Lenovo Tab`: current specification document; 10.1-inch class, MediaTek Helio G85, 4/8 GB soldered memory, 64/128 GB storage, WLAN/WWAN alternatives.
- `Idea Tab`: current specification document; MediaTek Dimensity 6300, 4/8 GB soldered memory, 128/256 GB storage, WLAN/WWAN alternatives, country-dependent accessories.
- `Legion Tab (8.8", 5)`: current specification document; Snapdragon 8 Elite Gen 5 / Qualcomm 8850P, 12/16 GB soldered LPDDR5T, 3K 165 Hz display, colour and accessory alternatives.
- `Yoga Tab`: current specification document; Snapdragon 8 Gen 3 class platform, 8/12 GB soldered LPDDR5x, 256 GB storage, WLAN-only in the inspected document, country-dependent keyboard/pen availability.
- `Tab P12`: model-table page with the clearest row-level evidence; 268 loaded rows in the indexed view.

The specification documents confirm that PSREF rows can carry processor, RAM, storage, display, connectivity, colour, OS, accessories and revision information. For exact row identity, the Tab P12 table is the representative fixture source used below.

### Representative exact PSREF row evidence

The Tab P12 table identifies the product as `TB370FU` while exposing regional model codes including `ZACH0239AU` (Australia), `ZACL0045IN` and `ZACL0046IN` (India), `ZACL0047JP` (Japan), and many other country-suffixed values. The table separately reports `Region`, `Country/Region`, `Machine Type`, `EAN / UPC / JAN`, and `Announce Date`.

Examples:

| PSREF model code | Product | Region/country | Machine type | Example configuration evidence |
|---|---|---|---|---|
| `ZACH0239AU` | `TB370FU` | `ANZ` / Australia | `ZACH` | Dimensity 7050; 8 GB; 128 GB UFS 2.2; 12.7-inch 3K display; non-WWAN; 2025-01-27 |
| `ZACL0045IN` | `TB370FU` | `INDIA` / India | `ZACL` | Dimensity 7050; 8 GB; 128 GB UFS 2.2; 12.7-inch 3K display; non-WWAN; 2024-07-25 |
| `ZACL0046IN` | `TB370FU` | `INDIA` / India | `ZACL` | Dimensity 7050; 8 GB; 128 GB UFS 2.2; 12.7-inch 3K display; non-WWAN; 2024-07-25 |

The table also shows repeated machine types across many country-specific model codes, storage differences within the family, and colour differences such as `Storm Grey` and `Oat`. This proves that a family and machine type are not sufficient to identify a PSREF row. It does not prove that two regional codes are globally the same sellable configuration.

### Identifier hierarchy

- **Family/product line:** presentation and grouping only, such as `Tab P12`, `Idea Tab`, `Yoga Tab`, or `Legion Tab`. Not an identity.
- **Product name:** hardware/product designation such as `TB370FU`. Stronger than family, but still can have many regional/configuration rows.
- **Machine type:** a shorter platform/chassis/platform grouping such as `ZACH` or `ZACL`. Useful grouping evidence, not a sufficient global identity.
- **PSREF model/MTM-like code:** a code such as `ZACH0239AU` or `ZACL0045IN`. This is the strongest stable observation identifier in the inspected table because it is tied to a row and carries regional/configuration specificity.
- **Country/region and commercial identifiers:** `Region`, `Country/Region`, EAN/UPC/JAN and configuration fields describe market or sellable-row context. They must be retained as evidence and must not be collapsed into the model code.

The observation identity should therefore use the exact PSREF model code plus source family/context and region. A product canonical identity can conservatively use the PSREF product name only within a region and only as a grouping candidate; a global canonical hardware identity is **UNRESOLVED**.

### Within-family and cross-region findings

The Tab P12 rows show the following actual behaviour:

- The same product `TB370FU` appears under many distinct regional model codes.
- The machine type is repeated across those rows but changes between `ZACH` and `ZACL` for some regional rows.
- Country/region is a separate field, not merely encoded in the family name.
- Storage and RAM can vary by row; the inspected table includes 4/8 GB and 128/256 GB combinations in the family.
- Connectivity is represented by explicit `WWAN`/non-WWAN values; the inspected Tab P12 rows are non-WWAN, while Idea Tab documentation explicitly distinguishes WLAN and WWAN models.
- Colour and bundled accessories can vary without proving a different underlying hardware product.

Cross-region equivalence is only partially proven. `TB370FU` and common display/processor/connectivity values strongly suggest a shared product family across `ZACH0239AU`, `ZACL0045IN` and other rows, but the differing model codes, machine types, dates and possible commercial configurations mean Tablet Clank must not merge them globally. Exact equivalence of RAM/storage/colour and SKU-level sellability remains **UNRESOLVED** without a broader row/export comparison.

### Revision and freshness semantics

PSREF model rows expose `Announce Date`, which appears to be a product/model announcement field. It must not be treated as the time the row first appeared in the observed feed or as proof of retail launch. Specification documents expose `Last Modify Time` or dated document revisions; these appear to describe document/specification maintenance. They can detect that a reference changed, but cannot by themselves distinguish a new product from an editorial/specification edit. A future collector must retain both the observation timestamp and all source-provided dates.

### Withdrawn semantics

PSREF has a withdrawn-product infrastructure and states that withdrawn books are no longer maintained or updated and are provided as-is. Historical entries remain queryable through the withdrawn surface, with links and product identifiers preserved in the reference. This supports historical audit/backfill and a source-state flag, but not disappearance inference: an active row moving to withdrawn, a missing active row, and a stale/blocked page are different conditions. No safe disappearance rule is implemented or proposed here.

### Smallest faithful future fixture

Prefer a reduced, hand-verified fixture derived from a small PSREF Excel/model-table export rather than a full 268-row dump. It should retain:

- family/product name and source URL;
- exact model code, product name, machine type, region, country/region;
- EAN/UPC/JAN when present;
- representative processor, RAM, storage, display, WWAN/WLAN, colour and OS fields;
- `Announce Date`, source revision/last-modified value, active/withdrawn state;
- one duplicate/repeated-row case and one same-family differing-storage/connectivity case;
- raw row text or normalized cell representation sufficient to prove no identifier was fabricated.

The fixture should include at least the three Tab P12 rows above plus one Idea Tab WLAN/WWAN contrast and one Legion or Yoga row. PDFs should be retained as evidence/spec fixtures, not used as the primary enumeration fixture when an Excel/model-table subset is available.

### Proposed Tablet Clank mapping

```text
canonical family: Lenovo PSREF product/family name, e.g. Tab P12 or Idea Tab
source observation identity: exact PSREF model/MTM-like code + source family/page + observed region
regional/configuration identity: model code + Country/Region + Region + explicit RAM/storage/connectivity/colour fields
variant dimensions: connectivity, RAM, storage, colour, bundled accessories, country/region, EAN/UPC/JAN
global canonical identity: UNRESOLVED
```

The existing identity model can represent a conservative regional/configuration observation because it already retains model number, region, connectivity, RAM and storage, while colour remains non-splitting evidence. It cannot safely perform global Lenovo model merging from PSREF alone. Readiness is therefore **READY_FOR_NARROW_PROBE**, provided the first probe is fixture-only, uses the exact model code as the model-number/source identifier, preserves region, and emits no global merge or disappearance semantics.

## Lenovo reduced fixture and parser contract

Status: **OFFLINE_PROBE**. Fixture path: `tests/fixtures/lenovo_psref_reduced.json`. Parser module: `tablet_clank/collectors/lenovo_psref.py`. The fixture has seven source rows representing six distinct candidate rows after one deliberate exact duplicate is removed:

- three `Tab P12` rows, including exact `ZACH0239AU`, `ZACL0045IN`, and `ZACL0046IN` model codes;
- two `Idea Tab` rows showing WLAN versus WWAN, with model code, machine type, and EAN left null because the reviewed specification source did not provide exact row identifiers;
- one `Legion Tab` row using `ZACW0028IN`;
- one repeated `Tab P12` row to prove exact duplicate handling.

The JSON shape intentionally mirrors a reduced PSREF model-table row rather than pretending to be a complete export. It preserves raw source values, exact regional suffixes, dates, connectivity, specifications, and withdrawn state. The parser collapses only exact repeated rows within the supplied snapshot; it does not merge matching product names, machine types, specifications, or product codes. It has no network access and is not registered in `tablet_clank/sources/registry.py`.

## Lenovo PSREF independent cross-check and live-probe gate

The independent cross-check used the official [Legion Tab model table](https://psref.lenovo.com/WDProduct/Lenovo_Tablets/Legion_Tab?tab=model), captured 2026-08-11, with eight hand-verified rows: `ZACW0028IN`, `ZACW0029IN`, `ZACW0003GB`, `ZACW0008SE`, `ZACW0015ES`, `ZACW0027UA`, `ZACW0014KR`, and `ZACW0026GR`. The official table reports `TB320FC`, machine type `ZACW`, country/region values, EAN/UPC/JAN, Snapdragon 8+ Gen 1, 12 GB LPDDR5x, 256 GB UFS 3.1, 8.8-inch display, non-WWAN, Storm Grey, Android 13 or later, and row-specific announcement dates. The independent fixture is `tests/fixtures/lenovo_psref_crosscheck.json`.

Gate A: **PASS**. The existing offline parser preserved exact model codes and raw fields, kept the seven country/region values separate, retained machine type as metadata, and introduced no global merge. No mismatch was found; no parser bug or identity-model change was required.

Gate B: **BLOCKED — LIVE_SOURCE_NOT_RELIABLE**. Safe direct probes of the public Legion model page returned HTTP 200 but only a JavaScript application shell without model rows. The page-backed Lenovo calls identified in the official page scripts (`GetInfoByKey`, `SpecData`, and `ExportCompareModelExcel`) returned empty HTTP 200 responses when called without a browser-held application/session context. The older PSREF endpoints previously returned token-gated 403/405 responses. No browser automation, token/session extraction, access-control bypass, or undocumented brittle retrieval was attempted. The official family specification HTML/PDF remains useful reference evidence but does not provide a complete individual model-table feed.

Because the live model table cannot currently be retrieved reliably and safely from this environment, Lenovo was not registered, no live collection was run, no baseline was established, and no canonical database rows or events were created. The current recommendation is to obtain a documented/public export or supported machine-readable feed before revisiting live implementation.

## Xiaomi first-party reconnaissance

Research was performed on 2026-08-11 against Xiaomi-controlled surfaces only. No Xiaomi collector, registry entry, baseline, or database mutation was made. No browser automation, third-party source, authentication bypass, or anti-bot circumvention was used.

### Surfaces investigated

| Surface | Region | Findings | Decision |
|---|---|---|---|
| [Mi Mall category list](https://www.mi.com/shop/category/list) | China | Tablet category exposes Xiaomi Pad 8/8 Pro, Pad 7/7 Pro/7 Ultra/7S Pro, REDMI Pad 2/2 Pro/2 SE and REDMI K Pad among broader notebook/tablet merchandising. Presence is commercially useful but the page is mixed and name/price oriented. | PROMISING discovery lead; not identity-complete alone |
| [Mi Mall Xiaomi Pad 7 detail](https://www.mi.com/shop/buy/detail?product_id=10050031) and [Pad 8 detail](https://www.mi.com/shop/buy/detail?product_id=19509) | China | Public detail pages have stable numeric `product_id` values and separate overview/spec tabs. A documented public contract for variant/option IDs and complete SKU data was not proven. | PROMISING narrow probe target |
| [Global tablet product list](https://www.mi.com/global/product-list/tablets/tablet/) | Global | Enumerates Xiaomi, REDMI and POCO tablet product URLs, but adjacent list views include covers, keyboards and pens. | PROMISING corroborating catalogue; medium discovery value |
| [Global product/spec pages](https://www.mi.com/global/product/xiaomi-pad-7/) and [REDMI Pad 2 specs](https://www.mi.com/global/product/redmi-pad-2/specs/) | Global | Rich public product/spec content exposes processor, RAM/storage combinations, display, colours, connectivity and package notes. It is usually a marketing page with configuration ranges, not an individual SKU inventory. | PROMISING specification complement |
| [India tablet catalogue](https://www.mi.com/in/tablet) and [India sitemap](https://www.mi.com/in/sitemap/) | India | Lists Xiaomi/REDMI tablets and explicitly distinguishes Wi-Fi, 4G and 5G labels while placing accessories nearby. India Pad 7 specs expose 8GB+128GB and 12GB+256GB plus SoC/display details. | PROMISING regional corroboration |
| [Regional REDMI Pad Pro 5G specs](https://www.mi.com/uk/product/redmi-pad-pro-5g/specs/) | Europe/selected markets | Regional pages expose RAM/storage ranges, dual-SIM/5G and region-dependent configuration notes. | PROMISING complement, not primary |
| [Global sitemap](https://www.mi.com/global/sitemap/) | Global | Public, but mixed navigation/merchandising content with accessories and no proven model/SKU identity. | MARGINAL |
| [Support/model FAQ](https://www.mi.com/global/support/faq/details/KA-517361/) | Global | Confirms a REDMI Pad Pro model number is a unique identifier for versions/configurations and explains device lookup. It is lookup-oriented, not an early catalogue feed. | Identity complement only |
| [Official Discover/launch article](https://www.mi.com/global/discover/article?id=2966) | Global/international | Dated launch/article infrastructure provides announcement chronology and product specifications, but not a complete inventory. | Chronology complement only |

### China versus global

China and international Xiaomi infrastructure are materially different. China Mi Mall is commerce-led and exposes numeric store product IDs such as `10050031`; global/regional `mi.com` uses localized product-list and marketing/spec pages with readable family slugs. China exposes China-local families such as REDMI K Pad and Xiaomi Pad 7 Ultra/7S Pro that are not evidence of global availability. China catalogue discovery value is **HIGH for China-local commercial presence**, while identity quality is **MEDIUM** until product ID, variant/option ID and any official model field are proven together. Global/regional discovery value is **MEDIUM** for products entering international marketing and **LOW/UNKNOWN** for earliest launch detection.

Lightweight public inspection did not establish a documented Xiaomi JSON/XHR catalogue API carrying all tablet SKUs and variants. Some list surfaces require JavaScript; do not infer or use private/session-bound endpoints from page scripts. Product/spec pages are machine-readable enough for research, but configuration ranges are not equivalent to sellable SKU records.

### Representative products and configuration evidence

- **Xiaomi Pad 7 / Pad 8, China**: stable numeric store product IDs and separate product/spec tabs; suitable for the first contract probe.
- **Xiaomi Pad 7, India**: 8GB+128GB and 12GB+256GB, colours, Snapdragon 7+ Gen 3 and Wi-Fi details; useful regional configuration evidence.
- **REDMI Pad 2, global**: 4/6/8GB and 128/256GB ranges, colours, Helio G100-Ultra, display and Wi-Fi details; configuration-range evidence rather than SKU enumeration.
- **REDMI Pad Pro 5G, UK/Germany/Greece**: 6GB+128GB, 8GB+128GB and 8GB+256GB ranges with dual-SIM/5G; regional variation is explicit.
- **REDMI Pad SE/4G, India**: catalogue and sitemap distinguish tablet connectivity labels but place accessories nearby, requiring strict filtering.

Matching China/global marketing names do not prove hardware equivalence. Model numbers, regional configuration sets, connectivity, software and store IDs may differ; a China launch followed by a global listing must remain separate observations until official evidence proves equivalence. Global canonical identity is **UNRESOLVED**.

### Identity and freshness recommendation

For future research only: family identity should use normalized Xiaomi/REDMI family plus product-series context; China source observation identity should prefer official numeric `product_id` plus a documented variant/option ID; global/regional observation identity should prefer official SKU/model/configuration identifiers, falling back conservatively to URL plus configuration evidence; global canonical identity remains **UNRESOLVED**. RAM, storage, colour, Wi-Fi/cellular, processor and display are configuration evidence. A healthy baseline plus a previously unseen stable product/variant identity should underpin new-product/new-configuration events. A new regional page alone is not a launch; require dated official announcement or first-sale/pre-order evidence. Page mutation, price changes, translation and accessory additions are not editorial events. Historical/discontinued products may remain in catalogue pages or redirects, so absence is not disappearance.

### Strategy decision and first probe

Selected strategy: **MULTI_SOURCE_REQUIRED**. China catalogue/store infrastructure is needed for earliest China discovery; global/regional catalogue/spec pages are needed for international expansion and configuration differences; support and announcement pages are corroboration only. The first narrow implementation target, if research proceeds, is a fixture-backed **China Mi Mall tablet category/detail probe** limited to the tablet nodes in `https://www.mi.com/shop/category/list`, starting with Pad 7 (`product_id=10050031`) and Pad 8 (`product_id=19509`). It must prove product ID, tablet classification, variant identity, region, connectivity and RAM/storage before any runtime registration.

### Failed/limited approaches preserved

- Generic/global sitemaps mix navigation, accessories and marketing URLs and are not primary sources.
- Product/spec pages expose rich configuration ranges but not necessarily individual sellable SKUs.
- No documented public Xiaomi catalogue API or complete public JSON variant contract was confirmed by lightweight probing; do not use private/session-bound endpoints.
- Support/model lookup confirms identity after discovery but is not an early product feed.

### Xiaomi Mi Mall fixture-probe correction

The requested IDs were rechecked on 2026-08-11. The official public pages currently return unrelated products: `product_id=10050031` returned `米家智能欧式吸油烟机S2`, and `product_id=19509` returned `米家双核净水器1200G Pro`. Search-indexed Xiaomi results still associated those URLs with Pad 7/Pad 8, demonstrating stale or reassigned catalogue evidence; a separately indexed Pad 8 ID (`20824`) also returned an unrelated water flosser on direct inspection. The official [Mi Mall category](https://www.mi.com/shop/category/list) still lists tablet names, but its product links are not currently identity-safe.

The offline probe preserves both requested IDs and the observed mismatched titles in `tests/fixtures/xiaomi_mimall_pad7.json` and `tests/fixtures/xiaomi_mimall_pad8.json`. It produces zero Tablet Clank candidates for both mismatches. RAM, storage, colour, connectivity, display, processor and variant ID remain unknown; no composite variant identity is created. Product-level numeric ID stability is therefore **not proven**, variant identity is **UNRESOLVED**, and the source is **XIAOMI_SOURCE_NOT_RELIABLE** for live monitoring until Xiaomi exposes a non-reassigned, public product/variant contract.

## Honor first-party reconnaissance

Research was performed on 2026-08-11 against Honor-controlled surfaces only. No Honor collector, registry entry, fixture, baseline, or database mutation was made. No browser automation, third-party source, authentication bypass, or anti-bot circumvention was used.

### Surfaces investigated

| Surface | Region | Findings | Assessment |
|---|---|---|---|
| [Honor China tablet catalogue](https://www.honor.com/cn/tablets/) | China | Product/family catalogue lists MagicPad, GT, V, numeric Pad and X families, with product-specific links and prominent current/new labels. | Strong China discovery surface; high family discovery, medium configuration identity. |
| [Honor China comparison](https://www.honor.com/cn/tablets/comparison/) | China | Structured comparison surface enumerates many current/recent tablet families and exposes dimensions, display, processor, OS, memory, camera, battery, wireless and packaging categories. | Best China index candidate; rich specifications but comparison presentation is not yet proven as a stable JSON feed. |
| [Honor China product pages](https://www.honor.com/cn/tablets/honor-magicpad-3/) and [MagicPad 2](https://www.honor.com/cn/tablets/honor-magicpad-2/) | China | Product-specific slugs remain readable and expose display, processor, battery, colours, connectivity language and product/spec/support tabs. | Strong product/spec evidence; model number and sellable SKU are not consistently visible in indexed page text. |
| [Honor China sitemap](https://www.honor.com/cn/sitemap/) | China | Official sitemap exists and includes tablet entries. | Useful URL corroboration, but mixed navigation and not sufficient alone for identity. |
| [Honor global tablet catalogue](https://www.honor.com/global/tablets/) | Global | Enumerates MagicPad4/3/2, Pad V9, Pad 10/9/8 and Pad X families with product links and feature summaries. | Strong global product discovery; regional launch appearance is visible, but accessories and marketing labels require filtering. |
| [Honor UK tablet catalogue](https://www.honor.com/uk/tablets/) and [UK store](https://www.honor.com/uk/shop/buy/) | UK/global regional | Separates tablet product families and store product pages. Buy pages expose SKU-like `skucode` query values and an internal `under_product` value, but their cross-page durability is not proven. | High commercial configuration potential; commerce IDs require explicit durability testing. |
| [Honor regional product/spec pages](https://www.honor.com/uk/tablets/honor-pad-10/spec/) | UK | Specification pages expose colour, display, processor, storage and connectivity sections; some values are application-rendered/placeholders in indexed output. | Rich corroboration; medium machine-readability and uncertain direct structured payload contract. |
| [Honor global support/model pages](https://www.honor.com/global/support/tablets/honor-pad-10/) | Global | Product-specific support pages provide downloads/FAQs after a model is known. | Identity/support complement, not primary early discovery. |
| [Honor regulatory/product information](https://www.honor.com/content/dam/honor/common/energy/product-information-sheet/english/honor_magicpad4_data_sheet_en.pdf) | Global/EU | Official product information exposes model identifier `YLE-W09` for MagicPad4; other official conformity documents expose identifiers such as `HEY3-W00` for Pad 10 and `NDL2-W09` for Pad X8b. | Strong model-identity confirmation, but regulatory publication is not guaranteed to precede catalogue discovery. |
| [Honor China news](https://www.honor.com/cn/news/honor-magic-v3-series-launch/) | China | Official dated launch pages can establish announcement chronology and mention tablets such as MagicPad 2. | Chronology complement, not product inventory. |

### China findings

Honor China has a coherent tablet catalogue and comparison hierarchy rather than a generic commerce slot system. Product family and product-specific URL slugs are readable and appear tied to named devices such as MagicPad3, MagicPad 2, Pad V9, Pad 9 and GT models. The China catalogue/comparison surfaces provide **HIGH** discovery value for new families and model pages, with **MEDIUM** identity quality until exact model identifiers are consistently joined to each catalogue row. Machine readability is **MEDIUM**: structured headings and product links are public, but a supported public JSON/catalogue API was not confirmed. Access reliability is suitable for an offline fixture probe; live collection is not yet validated.

China product pages expose rich specifications such as display size/resolution/refresh rate, processor, battery, colours and wireless features. Configuration-level RAM/storage can be exposed in support compatibility material and comparison pages, but individual sellable variants and China store SKU semantics require a focused fixture review. China pages can provide earliest domestic evidence, but a page appearing in the catalogue is not by itself proof of launch date; use dated news, pre-order or store evidence for chronology.

### Global/regional findings

The global catalogue covers MagicPad4/3/2, Pad V9, Pad 10/9/8 and Pad X families. Regional catalogues such as the UK site expose product pages and store buy pages. A UK Pad 10 buy page includes a SKU-like `skucode` and an internal `under_product` value, while regional specification pages expose storage, processor, display and connectivity categories. These are promising configuration signals but have not been proven stable across regions or over time.

Global/regional discovery value is **MEDIUM/HIGH** for international listings and **UNKNOWN** for earliest launch. Global canonical identity remains **UNRESOLVED**. The presence of the same marketing family in China and the UK/global catalogue does not establish the same model or configuration.

### Representative products

- **HONOR MagicPad3, China** — product-specific slug; 13.3-inch/165Hz display, Snapdragon 8 Gen 3, 12,450mAh battery and colours are exposed in the official page.
- **HONOR MagicPad 2, China and UK/global** — shared family naming but regional page and specification presentation differ; China-first chronology remains plausible but not proven by these pages alone.
- **HONOR Pad V9, China/global** — official global page exposes 11.5-inch/2.8K/144Hz, Dimensity 8350 Elite, colours and 10,100mAh battery.
- **HONOR Pad 10, China/global/UK** — official global/UK pages expose 12.1-inch/2.5K, Snapdragon 7 Gen 3, 10,100mAh and storage/spec sections; UK buy page exposes a commerce SKU-like code.
- **HONOR Pad X8b/X9a, global/regional** — official regulatory documents expose model identifiers such as `NDL2-W09` and `ELN2-W29`, demonstrating that regulatory identity can be richer than marketing slugs.
- **HONOR MagicPad4, China/global/UK** — current product page exposes 12.3-inch OLED, Snapdragon 8 Gen 5, colours and 16GB+512GB/12GB+256GB commercial configurations; official EU product information exposes `YLE-W09`.

### Identifier hierarchy and durability

- Family identity: Honor product family and series, such as MagicPad, Pad V, Pad N, Pad X or GT.
- Source observation identity: product-specific regional URL slug, retained with region and source surface.
- Regional/configuration identity: official model identifier from regulatory/support documents where available; otherwise a verified regional SKU/configuration code from the store. RAM/storage/colour/connectivity remain configuration evidence until the code-to-variant relationship is proven.
- Global canonical identity: **UNRESOLVED** across China and international regions.

Honor’s product-specific slugs appear more product-oriented than Xiaomi’s reassigned numeric commerce IDs, and regulatory identifiers such as `YLE-W09` are device-model-like. However, durability is only **PARTIALLY PROVEN**: the same model identifier was not systematically cross-checked across China, global, support and store surfaces, and the UK `skucode`/`under_product` values were observed on one store page only. Treat store IDs as regional commerce observations until repeated cross-surface evidence proves otherwise.

### China ↔ global relationship

Honor exposes matching and near-matching marketing families across China and global catalogues, but current evidence does not prove same model number, same SKU, or identical configuration sets. Regional pages may differ in storage, colour, software, connectivity and sale availability. A future global merge should require matching official model identifier plus compatible specifications, or explicit first-party equivalence evidence. A China listing followed by a global listing should remain two regional observations until then.

### Source comparison and decision

| Strategy | Discovery | Identity | Configuration | Reliability/noise | Decision |
|---|---|---|---|---|---|
| China catalogue primary | High China | Medium | Medium | Medium; comparison/catalogue filtering required | Strong first probe, insufficient for global coverage |
| Global catalogue primary | Medium/high global | Medium | Medium | Medium; regional availability and marketing noise | Useful complement, misses China-first timing |
| Storefront primary | Medium/high commercial | Medium if SKU durable | High potential | Medium; price/bundle/stock noise | Corroboration until IDs are audited |
| Sitemap primary | Medium URL discovery | Low/medium | Low | Mixed navigation | Not primary |
| Support primary | Low discovery | High after model known | Medium | High lookup semantics | Identity complement |
| Regulatory/product sheets | Low early discovery | High model identity | Medium | High evidence quality, publication timing uncertain | Identity complement |
| Announcement/news | High chronology | Medium | Medium | Campaign-oriented | Chronology complement |

Selected strategy: **MULTI_SOURCE_REQUIRED**. China catalogue/comparison is the early domestic discovery role; global/regional catalogue is the international appearance role; product pages/specs provide configuration evidence; regulatory/support documents confirm model identifiers; news/store pages establish chronology and commercial availability. This separation is necessary because no single Honor surface currently combines early China discovery, durable model identity and complete regional SKU coverage.

### Historical behaviour and freshness

Honor catalogues and comparison pages mix current/new products with older retained products such as Pad 8, Pad 9 and MagicPad 2. Product pages and support pages may remain available after a product is no longer current. Future baseline semantics should require a healthy baseline and a previously unseen stable product/model identity; a new regional URL or “New” label is not alone a launch event. Use dated announcement, preorder/store evidence and model-identifier confirmation for editorial chronology. Do not infer disappearance from omission.

### Recommended first probe

Exactly one narrow target is recommended: a fixture-backed **Honor China tablet catalogue/comparison probe** limited to `HONOR MagicPad3`, `HONOR MagicPad 2`, and `HONOR Pad V9`, preserving product slugs, China region, displayed configuration fields, and any model identifier found in the linked official product/support/regulatory evidence. Do not include accessories or establish a live baseline.

### Failed/limited approaches preserved

- Honor global/China sitemaps were treated as URL corroboration, not identity-complete feeds.
- Store `skucode` and `under_product` values were not promoted to durable global identity after one-page observation.
- Regulatory PDFs provide strong model identifiers but are not assumed to be early-discovery feeds.
- Support pages are lookup-oriented and do not replace catalogue discovery.
- Xiaomi’s prior failure remains preserved: numeric Mi Mall IDs `10050031` and `19509` resolved to unrelated products and must not be used as durable identity.

### Honor China offline catalogue/comparison probe

The official [China catalogue](https://www.honor.com/cn/tablets/) and [comparison page](https://www.honor.com/cn/tablets/comparison/) were reconfirmed on 2026-08-11. Both expose the three probe products with the same product-specific slugs and URLs:

| Product | Slug | URL | Catalogue | Comparison |
|---|---|---|---|---|
| MagicPad3 | `honor-magicpad-3` | `https://www.honor.com/cn/tablets/honor-magicpad-3/` | Yes | Yes |
| MagicPad 2 | `honor-magicpad-2` | `https://www.honor.com/cn/tablets/honor-magicpad-2/` | Yes | Yes |
| Pad V9 | `honor-pad-v9` | `https://www.honor.com/cn/tablets/honor-pad-v9/` | Yes | Yes |

Reduced fixtures are `tests/fixtures/honor_cn_tablets_catalogue.json` and `tests/fixtures/honor_cn_tablets_comparison.json`. The offline parser is `tablet_clank/collectors/honor_cn.py`. It accepts only entries marked as tablet products, preserves exact regional slugs/URLs and explicit family grouping, rejects accessory/phone/category noise, and leaves model/SKU/RAM/storage/connectivity unknown when absent.

The catalogue fixture contains 3 accepted products and 3 rejected noise entries. The comparison fixture contains 4 accepted products, including Pad 9 as a comparison-only example, and 1 rejected accessory. The three target products overlap exactly. Exact repeated slugs collapse; similar names with different slugs remain distinct. Repeated identical snapshots produce identical ordered identities, and a clearly test-only unseen valid slug is detected as an unseen identity without creating a database event.

Slug classification: **STABLE_ENOUGH_FOR_OBSERVATION** for the China regional surface. This is fixture/probe evidence only, not proof of global hardware identity or long-term live stability. Catalogue slug ↔ regulatory model identifier remains **UNRESOLVED**.

## Honor China live retrieval stability audit (2026-08-11)

The official [China tablet catalogue](https://www.honor.com/cn/tablets/) and [China comparison surface](https://www.honor.com/cn/tablets/comparison/) were read three times each with ordinary HTTPS requests using `urllib.request`, a normal user agent and a 30-second timeout. No browser automation, JavaScript execution, cookies, session token or access-control workaround was used.

Every catalogue read returned HTTP 200, `text/html`, the same final URL and exactly 1,139,965 bytes. Every comparison read returned HTTP 200, `text/html`, the same final URL and exactly 1,325,999 bytes. There were no transport errors or parse errors.

The exact target audit set was identical on all six reads: `honor-magicpad-3`, `honor-magicpad-2`, `honor-pad-v9`, `honor-pad-9`, `honor-magicpad-3-pro`, `honor-magicpad-3-pro-12-3`, `honor-magicpad-3-12-5` and `honor-pad-9-pro`. For MagicPad3, MagicPad 2, Pad V9 and Pad 9, exact product slugs and product URLs were unchanged across both surfaces and all reads. Repeated anchors were collapsed by exact slug; no duplicate slug survived in the unique surface sets.

The broader in-memory HTML link audit found 29 unique tablet-like slugs on the catalogue and 24 on comparison. Comparison was a subset of the observed catalogue set; catalogue-only slugs were `honor-magicpad-13`, `honor-pad-8`, `honor-pad-x8`, `honor-pad7` and `honor-padx7`. The broader set includes genuine out-of-scope tablets, so it must not be reported as parser noise.

The reduced offline fixtures are intentionally not complete live catalogues: the live pages contain many additional tablet products and older models. This is `FIXTURE_STALENESS` / `EXPECTED_PRESENTATION_DIFFERENCE`, not evidence that the narrow offline parser is incorrect. The existing parser remains JSON-fixture-only; no live collector or runtime registration was added during this audit. A future live probe should use a full-page HTML completeness guard and fail closed if the broad unique tablet-like count drops sharply from a source-specific expectation.

Result: **LIVE_STABLE** for the audited China discovery surfaces. They are suitable for a controlled experimental live probe, but slugs remain regional observation identifiers and are not global hardware identity. Model-number/regulatory joins, variant completeness and long-term durability remain unresolved. No Honor baseline or database write was performed.

Honor passed the controlled implementation gate. The two audited China HTML surfaces were registered separately, use exact product slugs as regional observation identifiers, and share identity resolution without duplicate products. Catalogue runs 16 and 18 each accepted 32 candidates; comparison runs 17 and 19 each accepted 24 candidates. The first run for each source established a healthy baseline, the immediate repeat resighted all identities, and no `new_product`, `spec_change` or correction events were emitted. The completeness guard requires at least 20 unique slugs and the four known Honor anchors on live reads; fixture mode remains intentionally reduced.

TCL also passed the bounded workflow on `https://www.tcl.com/global/en/tablets`. Ordinary HTTP returned complete-enough HTML with stable product-specific paths such as `tcl-tab-a1-plus` and `tcl-nxtpaper-11-gen-2`. The narrow fixture preserves eight representative products, an exact duplicate, an accessory, a phone and a category link. Live baseline/resight accepted 24/24 candidates with zero events and zero identity duplicates. The completeness guard requires at least eight unique slugs and two known product anchors.

Queue outcomes:

- Huawei — **MARGINAL / PARKED**. The official China tablet page is rich in product content but its ordinary HTML exposed only a thin product-link set, so it is not yet a dependable complete discovery index. Reopen if a stable public catalogue/index or product sitemap becomes available.
- OnePlus — **MARGINAL / PARKED**. The global product index exposed one current tablet product in the inspected HTML; this is insufficient breadth for a catalogue source. Reopen when a multi-product public index or stable regional model feed is available.
- OPPO — **PARKED_IDENTITY_UNRELIABLE**. The official China catalogue is reachable and broad, but current buy links are numeric shop IDs and legacy product pages mix old product paths with accessory pages. A stable first-party product code/slug contract is required before registration.
- RedMagic/Nubia — **NO_USEFUL_SOURCE** in the bounded probe. The tested RedMagic tablet URL returned 404 and the Nubia China landing page did not expose a usable tablet catalogue. Reopen on a confirmed first-party gaming-tablet index.
- Asus — **NO_USEFUL_SOURCE**. The tested official URL redirected to a generic site surface without a meaningful tablet index. Reopen only with a current tablet catalogue or product sitemap.
- Acer — **NOT_RELIABLE**. The direct official tablet catalogue probe timed out. Reopen after a stable ordinary-HTTP catalogue is available.
- Vivo/iQOO — **NO_USEFUL_SOURCE**. Vivo’s tested product URL returned 404 and iQOO’s product page had no tablet signal. Reopen only after confirming a meaningful current tablet portfolio and public index.

No browser automation, private API, access-control bypass, retailer scraping, or speculative source registration was used.

## Apple regional sitemap retirement (2026-08-11)

`apple_in_sitemap` was the original Apple discovery experiment. Its pre-fix runs mechanically accepted 23 navigation/category/service-like identities and resighted them, but the stable-identifier correction demonstrated that the source did not expose a defensible individual-tablet identity signal: the post-fix live run returned 372 raw links, 0 accepted candidates and 372 rejected candidates. The historical products, observations, rejected candidates, runs and 48 Apple correction events remain preserved in the canonical database.

The source has no unique practical runtime capability that is unavailable from the working Apple US/IN Store iPad Pro configuration sources. It is therefore **RETIRED_FROM_RUNTIME**, represented by registry state `DISABLED`, and excluded from the runtime/soak selection rule (`state == EXPERIMENTAL`). This is a runtime retirement, not historical data deletion or reinterpretation.
