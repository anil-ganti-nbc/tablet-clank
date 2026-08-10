from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Candidate:
    source_id: str
    manufacturer: str
    region: str
    url: str
    title: str
    source_identifier: str | None = None
    raw_values: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=utcnow)

@dataclass
class NormalizedProduct:
    manufacturer: str
    family: str | None
    name: str
    model_number: str | None
    sku: str | None
    region: str
    variant: str | None
    connectivity: str | None
    ram_gb: float | None
    storage_gb: int | None
    colour: str | None
    processor: str | None
    display_size_in: float | None
    os: str | None
    url: str
    raw_values: dict[str, Any]
    source_id: str
    observed_at: str

    @property
    def identity_key(self) -> str:
        base = self.model_number or self.sku or f"{self.manufacturer}|{self.family or self.name}"
        return "|".join((self.manufacturer, base, self.region, self.connectivity or "unknown", str(self.ram_gb or ""), str(self.storage_gb or "")))

@dataclass
class RunResult:
    source_id: str
    run_id: int | None = None
    status: str = "failed"
    raw_count: int = 0
    validated_count: int = 0
    rejected_count: int = 0
    accepted_count: int = 0
    new_count: int = 0
    updated_count: int = 0
    resighted_count: int = 0
    error: str | None = None
    drops: list[str] = field(default_factory=list)
