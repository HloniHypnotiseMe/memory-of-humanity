from __future__ import annotations
from typing import Any, Iterable

ACCESS_TYPES = {"open", "free_registration", "subscription", "onsite", "mixed", "unknown"}

def validate_collection(collection: dict[str, Any]) -> None:
    required = {"id", "name", "provider", "region", "source_types", "access"}
    missing = required - collection.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(collection["id"], str) or not collection["id"].startswith("moh:collection:"):
        raise ValueError("id must start with moh:collection:")
    if not isinstance(collection["name"], str) or not collection["name"].strip():
        raise ValueError("name is required")
    if not isinstance(collection["provider"], str) or not collection["provider"].strip():
        raise ValueError("provider is required")
    if not isinstance(collection["source_types"], list) or not collection["source_types"]:
        raise ValueError("source_types must be non-empty")
    if collection["access"] not in ACCESS_TYPES:
        raise ValueError("unsupported access type")

def discover_collections(collections: Iterable[dict[str, Any]], region: str | None = None, source_type: str | None = None, access: set[str] | None = None) -> list[dict[str, Any]]:
    result = []
    for collection in collections:
        validate_collection(collection)
        if region and collection["region"].casefold() != region.casefold():
            continue
        if source_type and source_type not in collection["source_types"]:
            continue
        if access and collection["access"] not in access:
            continue
        result.append(collection)
    return sorted(result, key=lambda item: item["id"])
