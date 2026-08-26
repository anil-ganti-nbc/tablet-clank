"""Narrow Honor UK tablet storefront catalogue collector (Wave 2, 2026-08-27).

Honor's regional storefront is server-rendered with one stable slug per
catalogue member: /uk/tablets/<slug>/. This mirrors the proven infrastructure
behind the production-approved honor_cn collectors while closing the
regional-launch discovery gap (global/EU storefronts list new MagicPad/Pad
products around or before CN comparison-page inclusion).

Identity rule: canonical product slug. Stronger identifiers (SKU/model code)
are not exposed on the listing; per policy no identity is fabricated and
CN-lineage products remain separate sources.
"""

from __future__ import annotations

import html
import re
from urllib.parse import urljoin

from .base import Collector
from ..models import Candidate

_SLUG_RE = re.compile(r'href="(/uk/tablets/([a-z0-9\-]{3,60})/)"', re.I)
_NON_PRODUCT = {"comparison"}


class HonorUKTabletsCollector(Collector):
    MIN_HEALTHY_SLUGS = 8
    # Contamination tripwire: a capture missing the current-generation
    # flagship family indicates a broken/partial page rather than a real
    # catalogue change. Failing honestly preserves previous healthy state.
    REQUIRED_ANCHORS = {"honor-magicpad"}

    def __init__(self, source, fixture_mode=False):
        super().__init__(source)
        self.fixture_mode = fixture_mode

    def collect(self):
        document = self.fetch_fixture() if self.fixture_mode else self.fetch()
        candidates = []
        seen = set()
        for match in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', document, re.I | re.S):
            href, label = match.groups()
            url = urljoin(self.source.url, href)
            m = re.fullmatch(r"/uk/tablets/([a-z0-9\-]{3,60})", urlsplit_path(url), re.I)
            if not m:
                continue
            slug = m.group(1).lower()
            if slug in _NON_PRODUCT or slug in seen:
                continue
            seen.add(slug)
            title = re.sub(r"<[^>]+>", " ", html.unescape(label))
            title = re.sub(r"\s+", " ", title).strip()
            if title.lower().startswith("new "):
                title = title[4:]
            title = title or f"HONOR {slug.replace('-', ' ')}"
            candidates.append(Candidate(
                self.source.id, self.source.manufacturer, self.source.region,
                url, title, slug,
                {"source_url": self.source.url, "slug": slug}))
        slugs = {c.source_identifier for c in candidates}
        if len(slugs) < self.MIN_HEALTHY_SLUGS:
            raise RuntimeError(
                f"Honor UK catalogue completeness guard: only {len(slugs)} unique tablet slugs")
        joined = " ".join(slugs)
        for anchor in self.REQUIRED_ANCHORS:
            if not any(s.startswith(anchor) for s in slugs):
                raise RuntimeError(
                    f"Honor UK catalogue completeness guard: missing anchor family {anchor!r}")
        return candidates


def urlsplit_path(url: str) -> str:
    from urllib.parse import urlsplit
    return urlsplit(url).path.rstrip("/")
