from __future__ import annotations

from typing import Any

RELATIONSHIP_TYPES = {
    "supports", "contradicts", "elaborates", "derives_from",
    "variant_of", "translated_from", "supersedes", "related_to",
    "appears_in", "remembers", "told", "about", "describes",
    "protects", "predecessor_of", "supported_by",
}


def validate_relationship(relationship: dict[str, Any]) -> None:
    required = {"id", "type", "source", "target"}
    missing = required - relationship.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(relationship["id"], str) or not relationship["id"].startswith("moh:rel:"):
        raise ValueError("relationship id must start with moh:rel:")
    if relationship["type"] not in RELATIONSHIP_TYPES:
        raise ValueError("unsupported relationship type")
    for field in ("source", "target"):
        value = relationship[field]
        if not isinstance(value, str) or not value.startswith("moh:"):
            raise ValueError(f"{field} must be a moh: identifier")


def create_relationship(relationship_id: str, source: str, target: str, relationship_type: str) -> dict[str, Any]:
    relationship = {
        "id": relationship_id,
        "type": relationship_type,
        "source": source,
        "target": target,
    }
    validate_relationship(relationship)
    return relationship
