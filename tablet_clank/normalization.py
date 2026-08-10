import re
from urllib.parse import urlsplit, urlunsplit

def clean(value: str | None) -> str | None:
    if value is None: return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None

def manufacturer_name(value: str) -> str:
    return {"apple inc.": "Apple", "samsung electronics": "Samsung"}.get(value.lower().strip(), value.strip().title())

def canonical_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))

def parse_ram(value: str | None) -> float | None:
    if not value: return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(GB|MB)", value, re.I)
    if not m: return None
    n = float(m.group(1)); return n if m.group(2).upper() == "GB" else round(n / 1024, 3)

def parse_storage(value: str | None) -> int | None:
    if not value: return None
    m = re.search(r"(\d+)\s*(TB|GB)", value, re.I)
    if not m: return None
    n = int(m.group(1)); return n * 1024 if m.group(2).upper() == "TB" else n

def parse_display(value: str | None) -> float | None:
    if not value: return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:in|inch|\")", value, re.I)
    return float(m.group(1)) if m else None

def normalize_candidate(c):
    from .models import NormalizedProduct
    raw = c.raw_values
    title = clean(c.title) or "Unknown tablet"
    model = clean(raw.get("model_number") or c.source_identifier)
    return NormalizedProduct(
        manufacturer=manufacturer_name(c.manufacturer), family=clean(raw.get("family")), name=title,
        model_number=model, sku=clean(raw.get("sku")), region=c.region.upper(), variant=clean(raw.get("variant")),
        connectivity=clean(raw.get("connectivity")), ram_gb=parse_ram(raw.get("ram")), storage_gb=parse_storage(raw.get("storage")),
        colour=clean(raw.get("colour")), processor=clean(raw.get("processor")), display_size_in=parse_display(raw.get("display")),
        os=clean(raw.get("os")), url=canonical_url(c.url), raw_values=raw, source_id=c.source_id, observed_at=c.observed_at)
