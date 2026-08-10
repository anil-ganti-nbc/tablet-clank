import json
import re
from html import unescape
from urllib.parse import urljoin

from .base import Collector
from ..models import Candidate


class AppleStoreIPadProCollector(Collector):
    """Experimental parser for Apple Store iPad Pro family selectors only."""

    def __init__(self, source, fixture_mode=False):
        super().__init__(source)
        self.fixture_mode = fixture_mode

    @staticmethod
    def _json_arrays(document):
        arrays = []
        for match in re.finditer(r'"products"\s*:\s*\[', document):
            start = match.end() - 1
            depth = 0
            in_string = False
            escaped = False
            for index in range(start, len(document)):
                char = document[index]
                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                    continue
                if char == '"':
                    in_string = True
                elif char == '[':
                    depth += 1
                elif char == ']':
                    depth -= 1
                    if depth == 0:
                        try:
                            arrays.append(json.loads(document[start:index + 1]))
                        except json.JSONDecodeError:
                            pass
                        break
        return arrays

    @staticmethod
    def _links(document, source_url):
        links = []
        pattern = r'<a\b[^>]*href=["\']([^"\']*/shop/buy-ipad/ipad-pro/[^"\']+)["\'][^>]*>'
        for match in re.finditer(pattern, document, re.I):
            href = unescape(match.group(1))
            links.append(urljoin(source_url, href))
        return links

    @staticmethod
    def _display(value):
        match = re.search(r"(\d+(?:\.\d+)?)", value or "")
        return f"{match.group(1)}-inch" if match else None

    @staticmethod
    def _storage(value):
        value = (value or "").lower().replace(" ", "")
        match = re.search(r"(\d+)(tb|gb)", value)
        return f"{match.group(1)} {match.group(2).upper()}" if match else None

    @staticmethod
    def _connectivity(value):
        value = (value or "").lower().replace(" ", "")
        if "cellular" in value or "wificell" in value:
            return "Wi-Fi + Cellular"
        if "wifi" in value:
            return "Wi-Fi"
        return None

    @staticmethod
    def _colour(value):
        return value.replace("-", " ").title() if value else None

    def collect(self):
        document = self.fetch_fixture() if self.fixture_mode else self.fetch()
        arrays = self._json_arrays(document)
        configurations = next((items for items in arrays if items and "dimensionCapacity" in items[0]), None)
        if not configurations:
            raise RuntimeError("Apple Store iPad Pro configuration data not found")
        links = self._links(document, self.source.url)
        if len(links) != len(configurations):
            raise RuntimeError(f"configuration/link count mismatch: {len(configurations)} vs {len(links)}")

        unique = {}
        for config, url in zip(configurations, links):
            part_number = config.get("partNumber")
            if not part_number:
                continue
            existing = unique.get(part_number)
            if existing is None or (existing[0].get("isCarrierDevice", False) and not config.get("isCarrierDevice", False)):
                unique[part_number] = (config, url)

        candidates = []
        for config, url in unique.values():
            part_number = config.get("partNumber")
            candidates.append(Candidate(
                self.source.id,
                "Apple",
                self.source.region,
                url,
                "iPad Pro",
                part_number,
                {
                    "family": "iPad Pro",
                    "sku": config.get("basePartNumber"),
                    "part_number": part_number,
                    "display": self._display(config.get("dimensionScreensize")),
                    "storage": self._storage(config.get("dimensionCapacity")),
                    "colour": self._colour(config.get("dimensionColor")),
                    "connectivity": self._connectivity(config.get("dimensionConnection")),
                    "store_family_type": config.get("familyType"),
                    "raw_store_config": config,
                },
            ))
        return candidates
