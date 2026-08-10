from abc import ABC, abstractmethod
from pathlib import Path
from urllib.request import Request, urlopen

class Collector(ABC):
    def __init__(self, source): self.source = source
    @abstractmethod
    def collect(self): ...

    def fetch(self) -> str:
        request = Request(self.source.url, headers={"User-Agent": "TabletClank/0.1 (+research; contact unavailable)"})
        with urlopen(request, timeout=30) as response:
            if response.status != 200: raise RuntimeError(f"unexpected HTTP status {response.status}")
            content_type = response.headers.get_content_type()
            if content_type not in ("text/html", "application/xhtml+xml", "application/xml", "text/xml"):
                raise RuntimeError(f"unexpected content type {content_type}")
            return response.read().decode("utf-8", errors="replace")

    def fetch_fixture(self) -> str:
        return Path(self.source.fixture).read_text(encoding="utf-8")
