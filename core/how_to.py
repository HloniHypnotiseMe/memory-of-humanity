from __future__ import annotations

from typing import Any

KNOWLEDGE_TYPES = {
    "repair", "manufacturing", "craft", "agriculture", "construction",
    "engineering", "process", "recipe", "trade_practice",
    "technical_reference", "other",
}


def validate_how_to(record: dict[str, Any]) -> None:
    required = {"id", "title", "knowledge_type", "provenance"}
    missing = required - record.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(record["id"], str) or not record["id"].startswith("moh:howto:"):
        raise ValueError("id must start with moh:howto:")
    if not isinstance(record["title"], str) or not record["title"].strip():
        raise ValueError("title is required")
    if record["knowledge_type"] not in KNOWLEDGE_TYPES:
        raise ValueError("unsupported knowledge_type")
    if not isinstance(record["provenance"], dict) or not record["provenance"].get("contributor_id"):
        raise ValueError("provenance.contributor_id is required")


def create_how_to(*, record_id: str, title: str, knowledge_type: str,
                  contributor_id: str, description: str | None = None) -> dict[str, Any]:
    record = {
        "id": record_id,
        "title": title,
        "knowledge_type": knowledge_type,
        "description": description,
        "steps": [],
        "materials": [],
        "tools": [],
        "technology_period": None,
        "sources": [],
        "intellectual_property": None,
        "safety_notes": [],
        "provenance": {"contributor_id": contributor_id},
    }
    validate_how_to(record)
    return record
