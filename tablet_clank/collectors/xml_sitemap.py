import re
from html import unescape
from urllib.parse import urlparse
from xml.etree import ElementTree

from .base import Collector
from ..models import Candidate


class XmlSitemapCollector(Collector):
    """Collect first-party product URLs from a standard XML sitemap."""

    def __init__(self, source, fixture_mode=False):
        super().__init__(source)
        self.fixture_mode = fixture_mode

    def collect(self):
        document = self.fetch_fixture() if self.fixture_mode else self.fetch()
        root = ElementTree.fromstring(document)
        candidates = []
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "loc" or not element.text:
                continue
            url = unescape(element.text.strip())
            path = urlparse(url).path.lower()
            if "/us/mobile/tablets/" not in path:
                continue
            slug = path.rstrip("/").rsplit("/", 1)[-1]
            model_match = re.search(r"(sm-[a-z0-9]+)", slug, re.I)
            title = re.sub(r"[-_]+", " ", slug).strip().title()
            candidates.append(Candidate(
                self.source.id,
                self.source.manufacturer,
                self.source.region,
                url,
                title,
                model_match.group(1).upper() if model_match else None,
                {"model_number": model_match.group(1).upper() if model_match else None},
            ))
        return candidates
