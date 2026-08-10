import html
import re
from urllib.parse import urljoin
from .base import Collector
from ..models import Candidate

class HtmlCatalogueCollector(Collector):
    def __init__(self, source, fixture_mode=False): super().__init__(source); self.fixture_mode = fixture_mode

    def collect(self):
        document = self.fetch_fixture() if self.fixture_mode else self.fetch()
        candidates = []
        for match in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', document, re.I | re.S):
            href, label = match.groups()
            title = re.sub(r"<[^>]+>", " ", html.unescape(label)); title = re.sub(r"\s+", " ", title).strip()
            if not title: continue
            url = urljoin(self.source.url, href)
            context = match.group(0)
            def field(name):
                m = re.search(rf"data-{name}=[\"']([^\"']+)", context, re.I)
                return m.group(1) if m else None
            candidates.append(Candidate(self.source.id, self.source.manufacturer, self.source.region, url, title, field("model"), {
                "model_number": field("model"), "sku": field("sku"), "family": field("family"), "connectivity": field("connectivity"),
                "ram": field("ram"), "storage": field("storage"), "processor": field("processor"), "display": field("display"),
                "colour": field("colour"), "os": field("os") }))
        return candidates
