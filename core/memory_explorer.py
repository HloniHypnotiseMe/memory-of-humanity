from __future__ import annotations

from typing import Any, Iterable

from .graph import traverse
from .records import validate_record
from .search import search_records
from .source_links import validate_source_link


def explore(
    records: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
    text: str | None = None,
    start_id: str | None = None,
    max_depth: int = 1,
    record_types: set[str] | None = None,
    epistemic_statuses: set[str] | None = None,
    relationship_types: set[str] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    record_list = list(records)
    relationship_list = list(relationships)
    for record in record_list:
        validate_record(record)

    search = search_records(
        record_list,
        text=text,
        record_types=record_types,
        epistemic_statuses=epistemic_statuses,
        limit=limit,
    )

    graph = {"nodes": [], "edges": [], "paths": []}
    if start_id is not None:
        graph = traverse(
            record_list,
            relationship_list,
            start_id=start_id,
            max_depth=max_depth,
            relationship_types=relationship_types,
        )

    return {
        "query": {
            "text": text,
            "start_id": start_id,
            "max_depth": max_depth,
            "record_types": sorted(record_types) if record_types else [],
            "epistemic_statuses": sorted(epistemic_statuses) if epistemic_statuses else [],
            "relationship_types": sorted(relationship_types) if relationship_types else [],
            "limit": limit,
        },
        "records": search["results"],
        "graph": graph,
        "sources": [],
    }
