"""Conservative first-party tablet catalogue scouts (no commerce-site scraping).

These adapters enumerate only product URLs on explicitly tablet-specific OEM
catalogues. Source identifiers are page slugs, not asserted regulatory models or
SKUs. Their registry entries remain disabled until access/robots and live
completeness preflights are approved.
"""

from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from .base import Collector
from ..models import Candidate

_ANCHOR = re.compile(
    r'<a\b[^>]*\bhref\s*=\s*(["\'])(.*?)\1[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_GENERIC_LABEL = re.compile(r"^(view detail|learn more|buy now|shop now|more)$", re.I)
_RULES = {
    "alldocube_global_tablets": {
        "host": "www.alldocube.com",
        "path": re.compile(r"/en/products/(iplay[a-z0-9-]+)", re.I),
        "minimum": 4,
        "anchors": {"iplay80miniturbo", "iplay80se"},
    },
    "teclast_global_tablets": {
        "host": "en.teclast.com",
        "path": re.compile(r"/([tmp])/([a-z0-9-]+)", re.I),
        "minimum": 8,
        "anchors": {"t/t70max", "m/m60"},
    },
    "blackview_zeno_tablets": {
        "host": "www.blackview.hk",
        "path": re.compile(r"/products/item/(zeno[-a-z0-9]+)", re.I),
        "minimum": 3,
        "anchors": {"zeno-6", "zeno-6-pro"},
    },
}


def _clean_label(markup: str) -> str:
    value = re.sub(r"<[^>]*>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


class OEMTabletCatalogueCollector(Collector):
    """Read a narrowly defined OEM catalogue, without following its links."""

    def __init__(self, source, fixture_mode: bool = False):
        super().__init__(source)
        self.fixture_mode = fixture_mode
        if source.id not in _RULES:
            raise ValueError(f"no OEM tablet catalogue rule for {source.id}")

    def collect(self) -> list[Candidate]:
        document = self.fetch_fixture() if self.fixture_mode else self.fetch()
        return self.parse_live(document)

    def parse_live(self, document: str) -> list[Candidate]:
        rule = _RULES[self.source.id]
        found: dict[str, tuple[str, str]] = {}
        for anchor in _ANCHOR.finditer(document):
            href, markup = anchor.group(2), anchor.group(3)
            url = urljoin(self.source.url, html.unescape(href))
            parts = urlsplit(url)
            if parts.scheme != "https" or parts.netloc.lower() != rule["host"]:
                continue
            path = parts.path.rstrip("/")
            match = rule["path"].fullmatch(path)
            if match is None:
                continue
            identifier = "/".join(group.lower() for group in match.groups())
            # Preserve the official path casing, but remove tracking and fragments.
            canonical = urlunsplit(("https", parts.netloc.lower(), path, "", ""))
            label = _clean_label(markup)
            if not label or _GENERIC_LABEL.fullmatch(label) or len(label) > 100:
                label = match.group(match.lastindex).replace("-", " ")
            prior = found.get(identifier)
            # Prefer an informative model label over an image-only first anchor.
            if prior is None or len(label) > len(prior[1]):
                found[identifier] = (canonical, label)
        identifiers = set(found)
        if len(identifiers) < rule["minimum"]:
            raise RuntimeError(
                f"{self.source.id} catalogue completeness guard: "
                f"{len(identifiers)} products, expected at least {rule['minimum']}"
            )
        missing = rule["anchors"] - identifiers
        if missing:
            raise RuntimeError(
                f"{self.source.id} catalogue completeness guard: "
                f"missing known product anchors {sorted(missing)}"
            )
        candidates = []
        for identifier in sorted(identifiers):
            url, label = found[identifier]
            # Tablet form factor is established by the narrow catalogue scope.
            title = f"{self.source.manufacturer} {label} tablet"
            candidates.append(Candidate(
                source_id=self.source.id,
                manufacturer=self.source.manufacturer,
                region=self.source.region,
                url=url,
                title=title,
                source_identifier=identifier,
                raw_values={
                    "identifier_kind": "catalogue_slug",
                    "source_url": self.source.url,
                    "slug": identifier,
                    "surface": "official_tablet_catalogue",
                },
            ))
        return candidates
