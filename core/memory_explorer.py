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
    sources: Iterable[dict[str, Any]] | None = None,
    source_links: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    record_list = list(records)
    relationship_list = list(relationships)
    source_list = list(sources or [])
    source_link_list = list(source_links or [])
    for link in source_link_list:
        validate_source_link(link)
    source_ids = {source.get("id") for source in source_list if isinstance(source, dict)}
    selected_record_ids = {record["id"] for record in record_list}
    relevant_source_links = [
        link for link in source_link_list
        if link["record_id"] in selected_record_ids and link["source_id"] in source_ids
    ]
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
        "sources": [source for source in source_list if source.get("id") in {link["source_id"] for link in relevant_source_links}],
        "source_links": relevant_source_links,
    }
