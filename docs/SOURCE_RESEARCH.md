# Source research

Research was performed against official first-party surfaces on 2026-08-10 and 2026-08-11. No browser automation or third-party sources were used.

## Samsung US re-research

| URL | HTTP behaviour | Structure/usefulness | Decision |
|---|---|---|---|
| `https://www.samsung.com/us/sitemap/` | HTTP 404 in the original configured run | Not usable as configured | Rejected; old source URL retained only in historical run 2 |
| `https://www.samsung.com/us/common/sitemap/` | HTTP 200, HTML | Official navigation directory; contains Galaxy Tab links but is broad and noisy | Rejected as primary collector because the XML sitemap is more machine-readable |
| `https://www.samsung.com/us/common/sitemap.html` | HTTP 200, redirects/canonicalizes to `/us/common/sitemap/` | Same HTML directory | Rejected in favor of XML |
| `https://www.samsung.com/us/sitemap.xml` | HTTP 200, XML sitemap index | Lists official child indexes including `top_sitemap.xml` | Useful index, but not direct tablet product collection |
| `https://www.samsung.com/us/top_sitemap.xml` | HTTP 200, XML URL set; current probe exposed four `/us/mobile/tablets/` URLs | Machine-readable official product URLs with model-code-bearing slugs such as `SM-T837VZKAVZW` and `SM-T830NZKLXAR`; one generic `/all-tablets/` URL is mixed in | **Chosen** as `samsung_us_sitemap` replacement |
| `https://www.samsung.com/us/tablets/` | HTTP 200, HTML catalogue landing page | Strong tablet context and current family navigation, but product details are partly page/JS-oriented | Useful corroborating surface; not selected for the Stage 1 collector |

The chosen XML sitemap is defensible for discovery because it is first-party, stable enough to retrieve, machine-readable, and exposes model identifiers in product URL slugs. The collector filters to `/us/mobile/tablets/`, then the generic validator rejects `/all-tablets/` category URLs. The first replacement run showed 4 raw URLs; after the narrow category fix, 3 were accepted and 1 rejected.

## Other research

Initial targets were Apple, Lenovo, Xiaomi, OnePlus, Google, Huawei, Honor, RedMagic, Asus, Acer and TCL. Apple’s regional HTML sitemap is easy to retrieve but is navigation-oriented. The live audit showed its tablet-looking links were categories, services, support or navigation pages without stable product identifiers; it is not currently a trustworthy product collector. Other manufacturers remain RESEARCH only.

Search results alone are not treated as evidence or a source registry. No credentials, cookies, retailer scraping or external alerting were introduced.
