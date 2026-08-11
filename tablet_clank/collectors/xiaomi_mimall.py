"""Offline-only Xiaomi Mi Mall identity probe.

This deliberately does not retrieve the network or register a runtime source.
It preserves the requested product ID and the observed public-page identity so
reassigned or stale Mi Mall IDs cannot become tablet candidates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import Candidate

FIXTURE_SOURCE_ID = "xiaomi_mimall_offline_fixture"


@dataclass(frozen=True)
class MiMallProbe:
    expected_product_name: str
    requested_product_id: str
    source_url: str
    region: str
    observed_title: str | None
    observed_category: str | None
    status: str
    raw_values: dict[str, Any]

    @property
    def product_id(self) -> str:
        return self.requested_product_id


def parse_mimall_fixture(path: str | Path) -> MiMallProbe:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    required = ("expected_product_name", "requested_product_id", "source_url", "region", "status")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Mi Mall fixture missing fields: {', '.join(missing)}")
    if payload["region"] != "CN":
        raise ValueError("Mi Mall fixture region must be CN")
    raw_values = dict(payload.get("raw_values") or {})
    raw_values.update({
        "expected_product_name": payload["expected_product_name"],
        "requested_product_id": str(payload["requested_product_id"]),
        "source_url": payload["source_url"],
        "region": "CN",
        "observed_title": payload.get("observed_title"),
        "observed_category": payload.get("observed_category"),
        "status": payload["status"],
        "source_fixture": str(path),
    })
    return MiMallProbe(
        expected_product_name=str(payload["expected_product_name"]),
        requested_product_id=str(payload["requested_product_id"]),
        source_url=str(payload["source_url"]),
        region="CN",
        observed_title=payload.get("observed_title"),
        observed_category=payload.get("observed_category"),
        status=str(payload["status"]),
        raw_values=raw_values,
    )


def probe_to_candidates(probe: MiMallProbe) -> list[Candidate]:
    """Convert only a verified tablet match into an existing Candidate.

    The current captured fixtures are identity mismatches and therefore return
    no candidates. Missing configuration dimensions are never synthesized.
    """
    if probe.status != "matched_tablet":
        return []
    if probe.observed_title != probe.expected_product_name:
        return []
    return [Candidate(
        source_id=FIXTURE_SOURCE_ID,
        manufacturer="Xiaomi",
        region="CN",
        url=probe.source_url,
        title=probe.expected_product_name,
        source_identifier=probe.product_id,
        raw_values=dict(probe.raw_values),
    )]
