"""Narrow TCL global tablet catalogue collector."""

from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlsplit

from .base import Collector
from ..models import Candidate


class TCLGlobalTabletsCollector(Collector):
    MIN_HEALTHY_SLUGS = 8
    REQUIRED_ANCHORS = {"tcl-tab-a1-plus", "tcl-nxtpaper-11-gen-2"}

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
            path = urlsplit(url).path.rstrip("/")
            match_slug = re.fullmatch(r"/global/en/tablets/([^/]+)", path, re.I)
            if not match_slug:
                continue
            slug = match_slug.group(1).lower()
            if slug in seen:
                continue
            seen.add(slug)
            title = re.sub(r"<[^>]+>", " ", html.unescape(label))
            title = re.sub(r"\s+", " ", title).strip() or f"TCL {slug.replace('-', ' ')}"
            candidates.append(Candidate(self.source.id, self.source.manufacturer, self.source.region, url, title, slug, {"source_url": self.source.url, "slug": slug}))
        slugs = {c.source_identifier for c in candidates}
        if len(slugs) < self.MIN_HEALTHY_SLUGS:
            raise RuntimeError(f"TCL catalogue completeness guard: only {len(slugs)} unique tablet slugs")
        missing = self.REQUIRED_ANCHORS - slugs
        if missing:
            raise RuntimeError(f"TCL catalogue completeness guard: missing anchors {sorted(missing)}")
        return candidates
