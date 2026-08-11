"""Offline-only parser contract for a reduced Lenovo PSREF row fixture.

This module deliberately has no source registration or network access. It converts
faithful fixture rows into existing Candidate objects for parser/identity tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import Candidate

FIXTURE_SOURCE_ID = "lenovo_psref_offline_fixture"
FIXTURE_URL = "https://psref.lenovo.com/"


def _identity_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    """Return fields that define an exact repeated source row for this snapshot."""
    return tuple(row.get(key) for key in (
        "family", "product_name", "psref_product_code", "machine_type",
        "model_code", "country_region", "region", "region_code",
        "ean_upc_jan", "processor", "ram", "storage", "display",
        "connectivity", "colour", "os", "announce_date", "last_modify_time",
        "withdrawn",
    ))


def parse_psref_fixture(path: str | Path) -> list[Candidate]:
    """Parse reduced PSREF rows, preserving raw values and exact model codes.

    Exact duplicate rows are collapsed within this fixture snapshot only. Rows
    differing by region, model code, connectivity, or any other retained source
    field remain separate. Missing identifiers remain missing; they are never
    synthesized from product names or machine types.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("PSREF fixture must contain a rows list")

    fixture_metadata = {
        "source_document": payload.get("source"),
        "fixture_capture_date": payload.get("capture_date"),
        "fixture_family": payload.get("family"),
    }
    candidates: list[Candidate] = []
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("PSREF fixture rows must be objects")
        if row.get("manufacturer", "Lenovo") != "Lenovo":
            raise ValueError("PSREF fixture manufacturer must be Lenovo")
        key = _identity_tuple(row)
        if key in seen:
            continue
        seen.add(key)
        model_code = row.get("model_code")
        title = row.get("product_name") or row.get("family") or "Lenovo tablet"
        region = row.get("region_code") or row.get("region") or "UNKNOWN"
        candidates.append(Candidate(
            source_id=FIXTURE_SOURCE_ID,
            manufacturer="Lenovo",
            region=str(region).upper(),
            url=row.get("source_url") or FIXTURE_URL,
            title=str(title),
            source_identifier=model_code,
            raw_values={**fixture_metadata, **row, "source_fixture": str(path)},
        ))
    return candidates
