from __future__ import annotations

from typing import Any

from .federated_explorer import explore_federated_history
from .query import validate_query
from .search import search_records


def federated_query(
    envelopes: list[dict[str, Any]],
    query: dict[str, Any],
    *,
    allowed_visibilities: set[str] | None = None,
) -> dict[str, Any]:
    validate_query(query)
    if not envelopes:
        raise ValueError("at least one federation envelope is required")

    query_type = query["query_type"]
    if query_type == "place_memory":
        if not query.get("place_id"):
            raise ValueError("place_memory query requires place_id")
        result = explore_federated_history(
            envelopes,
            exploration_id=f"moh:historical-exploration:{query['query_id'].split(':')[-1]}",
            place_id=query["place_id"],
            time=query.get("time"),
            record_types=set(query.get("record_types") or []),
            relationship_types=set(query.get("relationship_types") or []),
            limit=query.get("limit", 100),
            allowed_visibilities=allowed_visibilities,
        )
        result["query_id"] = query["query_id"]
        return result

    if query_type == "text":
        from .federated_explorer import _allowed, _merge_by_id
        from .federation import validate_envelope
        pairs = []
        for envelope in envelopes:
            validate_envelope(envelope)
            for record in envelope.get("records", []):
                if _allowed(record, allowed_visibilities or {"public"}):
                    pairs.append((record, envelope["instance_id"]))
        records, conflicts = _merge_by_id(pairs)
        search = search_records(
            records,
            text=query.get("text"),
            record_types=set(query.get("record_types") or []),
            limit=query.get("limit", 100),
        )
        return {
            "query_id": query["query_id"],
            "results": search["results"],
            "federation": {
                "instances": sorted({e["instance_id"] for e in envelopes}),
                "record_conflicts": conflicts,
            },
        }

    raise ValueError("federated query currently supports text and place_memory")
