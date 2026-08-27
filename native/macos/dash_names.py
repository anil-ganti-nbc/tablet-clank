"""Editorial display names for canonical Tablet Clank source ids.

Canonical ids (`SOURCES` keys in `tablet_clank.sources.registry`) stay the
source of truth everywhere in the data model and in diagnostics; this module
only supplies a friendlier label for the GUI. Unknown ids fall back to the
raw id itself, so this mapping can lag behind new sources without breaking.
"""

from __future__ import annotations

SOURCE_DISPLAY_NAMES = {
    "apple_us_ipad_pro_store": "Apple US — iPad Pro Store",
    "apple_in_ipad_pro_store": "Apple India — iPad Pro Store",
    "apple_in_sitemap": "Apple India — Sitemap (retired)",
    "samsung_us_sitemap": "Samsung US — Product Sitemap",
    "honor_cn_tablets_catalogue": "Honor China — Tablet Catalogue",
    "honor_cn_tablets_comparison": "Honor China — Tablet Comparison",
    "tcl_global_tablets": "TCL Global — Tablet Catalogue",
}


def display_name(source_id: str) -> str:
    return SOURCE_DISPLAY_NAMES.get(source_id, source_id)


EVENT_TYPE_LABELS = {
    "new_product": "New product",
    "identity_correction": "Identity correction",
    "spec_change": "Field change",
}


def event_type_label(event_type: str) -> str:
    return EVENT_TYPE_LABELS.get(event_type, event_type)


QC_DECISION_LABELS = {
    "USEFUL": "Useful",
    "NOT_USEFUL": "Not useful",
    "FALSE_POSITIVE": "False positive",
    "OUT_OF_STOCK": "Out of stock",
}


def qc_decision_label(decision: str) -> str:
    return QC_DECISION_LABELS.get(decision, decision)
