# Source research

Research was performed against public first-party surfaces on 2026-08-10. Initial targets were Apple, Samsung, Lenovo, Xiaomi, OnePlus, Google, Huawei, Honor, RedMagic, Asus, Acer and TCL.

| Manufacturer | Surface | Findings | Stage 1 decision |
|---|---|---|---|
| Apple | Regional HTML sitemap, e.g. `https://www.apple.com/in/sitemap/` | First-party regional sitemap page exposes iPad navigation and country-specific surface; HTML is easy to retrieve, but the sitemap is navigation-oriented rather than a complete product API. | Selected as experimental HTML sitemap collector. |
| Samsung | Regional sitemap/product directory, e.g. `https://www.samsung.com/us/sitemap/` | First-party regional directory exposes Galaxy Tab entries and product URLs; sitemap includes many non-tablet surfaces, so validation is required. | Selected as experimental HTML sitemap collector. |
| Lenovo | Regional tablet catalogue/product pages | Strong product catalogue candidate; likely useful for a later structured product-page adapter. | Research only. |
| Xiaomi | Regional product/catalogue pages | Region and market availability are valuable; page structures vary by market. | Research only. |
| OnePlus | Product and newsroom pages | Smaller catalogue; useful for announcement corroboration, not selected for first collector pair. | Research only. |
| Google | Pixel Tablet product/support surfaces | Small, stable product family but limited discovery breadth. | Research only. |
| Huawei/Honor | Regional storefronts and product pages | Region-specific naming and availability are valuable; regional complexity warrants later validation. | Research only. |
| RedMagic | Gaming tablet product pages | High editorial value but narrow catalogue and page-specific parsing needed. | Research only. |
| Asus/Acer/TCL | Regional catalogues and support/product pages | Potentially useful, with mixed catalogue quality and regional fragmentation. | Research only. |

Failed/limited approach: search results alone are not treated as evidence or a source registry. No browser automation, retailer scraping, credentials or external alerting were introduced.
