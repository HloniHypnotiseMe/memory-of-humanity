from __future__ import annotations

from typing import Any

LINEAGE_TYPES = {
    "retelling", "variant", "translation", "adaptation",
    "quotation", "appearance", "derived_from",
}


def validate_lineage(lineage: dict[str, Any]) -> None:
    required = {"id", "source", "relationship"}
    missing = required - lineage.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not lineage["id"].startswith("moh:lineage:"):
        raise ValueError("id must start with moh:lineage:")
    if not lineage["source"].startswith("moh:"):
        raise ValueError("source must be a moh: identifier")
    if lineage["relationship"] not in LINEAGE_TYPES:
        raise ValueError("unsupported lineage relationship")


def create_lineage(*, lineage_id: str, source: str, relationship: str,
                   contributor_id: str, target: str | None = None) -> dict[str, Any]:
    lineage = {
        "id": lineage_id,
        "source": source,
        "target": target,
        "relationship": relationship,
        "date": None,
        "language": None,
        "contributor_id": contributor_id,
        "notes": None,
    }
    validate_lineage(lineage)
    return lineage
