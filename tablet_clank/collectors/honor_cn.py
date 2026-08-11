"""Offline-only Honor China catalogue/comparison probe."""

from __future__ import annotations

import json
import html
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from ..models import Candidate
from .base import Collector

FIXTURE_SOURCE_ID = "honor_cn_tablets_offline_fixture"


def parse_honor_cn_fixture(path: str | Path, source_id: str = FIXTURE_SOURCE_ID) -> list[Candidate]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("entries")
    if not isinstance(rows, list):
        raise ValueError("Honor fixture must contain an entries list")
    source_url = payload.get("source_url")
    capture_date = payload.get("capture_date")
    surface = payload.get("surface")
    if not source_url or not capture_date or not surface:
        raise ValueError("Honor fixture requires source_url, capture_date and surface")

    candidates: list[Candidate] = []
    seen_slugs: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Honor fixture entries must be objects")
        if row.get("entry_type") != "product" or row.get("category") != "tablet":
            continue
        slug = row.get("slug")
        url = row.get("url")
        name = row.get("name")
        if not isinstance(slug, str) or not slug or not isinstance(url, str) or not isinstance(name, str):
            continue
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        raw_values: dict[str, Any] = {
            "source_document": source_url,
            "fixture_capture_date": capture_date,
            "surface": surface,
            "source_fixture": str(path),
            **row,
        }
        candidates.append(Candidate(
            source_id=source_id,
            manufacturer="Honor",
            region="CN",
            url=url,
            title=name,
            source_identifier=slug,
            raw_values=raw_values,
        ))
    return candidates


class HonorCNTabletsCollector(Collector):
    """Narrow public Honor China tablet catalogue/comparison collector."""

    MIN_HEALTHY_SLUGS = 20
    REQUIRED_ANCHORS = {"honor-magicpad-3", "honor-magicpad-2", "honor-pad-v9", "honor-pad-9"}

    def __init__(self, source, fixture_mode=False):
        super().__init__(source)
        self.fixture_mode = fixture_mode

    def collect(self):
        if self.fixture_mode:
            return parse_honor_cn_fixture(self.source.fixture, self.source.id)
        return self.parse_live(self.fetch())

    def parse_live(self, document: str) -> list[Candidate]:
        candidates: list[Candidate] = []
        seen: set[str] = set()
        pattern = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
        for match in pattern.finditer(document):
            href, label = match.groups()
            url = urljoin(self.source.url, href)
            path = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
            slug_match = re.search(r"/cn/tablets/([^/]+)$", path, re.I)
            if not slug_match:
                continue
            slug = slug_match.group(1).lower()
            if slug in {"more", "comparison", "index"} or slug == "learning-machine":
                continue
            if slug in seen:
                continue
            seen.add(slug)
            title = re.sub(r"<[^>]+>", " ", html.unescape(label))
            title = re.sub(r"\s+", " ", title).strip() or f"Honor {slug.replace('-', ' ')}"
            candidates.append(Candidate(
                source_id=self.source.id,
                manufacturer=self.source.manufacturer,
                region=self.source.region,
                url=url,
                title=title,
                source_identifier=slug,
                raw_values={"surface": self.source.id, "source_url": self.source.url, "slug": slug},
            ))
        slugs = {candidate.source_identifier for candidate in candidates}
        if len(slugs) < self.MIN_HEALTHY_SLUGS:
            raise RuntimeError(f"Honor catalogue completeness guard: only {len(slugs)} unique tablet slugs")
        missing = self.REQUIRED_ANCHORS - slugs
        if missing:
            raise RuntimeError(f"Honor catalogue completeness guard: missing anchors {sorted(missing)}")
        return candidates


def unseen_slugs(baseline: list[Candidate], current: list[Candidate]) -> list[str]:
    """Return deterministic exact-slug discoveries without creating events."""
    old = {candidate.source_identifier for candidate in baseline if candidate.source_identifier}
    return sorted({candidate.source_identifier for candidate in current if candidate.source_identifier} - old)
