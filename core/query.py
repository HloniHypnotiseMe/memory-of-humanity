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
    if query.get("record_types") is not None and not isinstance(query["record_types"], list):
        raise ValueError("record_types must be a list")
    if query.get("relationship_types") is not None and not isinstance(query["relationship_types"], list):
        raise ValueError("relationship_types must be a list")


def create_query(*, query_id: str, query_type: str,
                 text: str | None = None,
                 entity_id: str | None = None,
                 place_id: str | None = None,
                 time: dict[str, Any] | None = None,
                 record_types: list[str] | None = None,
                 relationship_types: list[str] | None = None,
                 limit: int = 100) -> dict[str, Any]:
    query = {
        "query_id": query_id,
        "query_type": query_type,
        "text": text,
        "entity_id": entity_id,
        "place_id": place_id,
        "time": time,
        "record_types": record_types or [],
        "relationship_types": relationship_types or [],
        "limit": limit,
    }
    validate_query(query)
    return query
