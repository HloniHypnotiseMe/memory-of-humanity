from __future__ import annotations

from typing import Any

LINK_TYPES = {
    "supports", "mentions", "quotes", "depicts", "documents",
    "published_in", "derived_from", "contextualizes", "contradicts",
}


def validate_source_link(link: dict[str, Any]) -> None:
    required = {"id", "record_id", "source_id", "link_type", "provenance"}
    missing = required - link.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(link["id"], str) or not link["id"].startswith("moh:sourcelink:"):
        raise ValueError("id must start with moh:sourcelink:")
    if not isinstance(link["record_id"], str) or not link["record_id"].startswith("moh:"):
        raise ValueError("record_id must start with moh:")
    if not isinstance(link["source_id"], str) or not link["source_id"].startswith("moh:source:"):
        raise ValueError("source_id must start with moh:source:")
    if link["link_type"] not in LINK_TYPES:
        raise ValueError("unsupported link_type")
    if not isinstance(link["provenance"], dict) or not link["provenance"].get("created_by"):
        raise ValueError("provenance.created_by is required")


def create_source_link(
    link_id: str,
    record_id: str,
    source_id: str,
    link_type: str,
    created_by: str,
    **metadata: Any,
) -> dict[str, Any]:
    link = {
        "id": link_id,
        "record_id": record_id,
        "source_id": source_id,
        "link_type": link_type,
        "provenance": {"created_by": created_by},
        **metadata,
    }
    validate_source_link(link)
    return link
