from __future__ import annotations

from typing import Any

QUERY_TYPES = {"text", "graph", "timeline", "place_memory"}


def validate_query(query: dict[str, Any]) -> None:
    required = {"query_id", "query_type"}
    missing = required - query.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not query["query_id"].startswith("moh:query:"):
        raise ValueError("query_id must start with moh:query:")
    if query["query_type"] not in QUERY_TYPES:
        raise ValueError("unsupported query_type")
    if query.get("limit") is not None and not 1 <= query["limit"] <= 1000:
        raise ValueError("limit must be between 1 and 1000")


def create_query(*, query_id: str, query_type: str,
                 text: str | None = None,
                 entity_id: str | None = None,
                 place_id: str | None = None,
                 limit: int = 100) -> dict[str, Any]:
    query = {
        "query_id": query_id,
        "query_type": query_type,
        "text": text,
        "entity_id": entity_id,
        "place_id": place_id,
        "time": None,
        "record_types": [],
        "relationship_types": [],
        "limit": limit,
    }
    validate_query(query)
    return query
