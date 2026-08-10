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
