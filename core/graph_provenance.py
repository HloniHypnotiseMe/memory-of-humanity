from __future__ import annotations

from typing import Any, Iterable

from .graph import explain_connection
from .records import validate_record
from .relationships import validate_relationship


def _provenance_refs(
    records: dict[str, dict[str, Any]],
    relationships: dict[str, dict[str, Any]],
    node_ids: list[str],
    edge_ids: list[str],
) -> list[str]:
    refs: list[str] = []
    for node_id in node_ids:
        provenance = records[node_id].get("provenance", {})
        contributor = provenance.get("contributor_id")
        if contributor:
            refs.append(f"contributor:{contributor}")
        source = provenance.get("source")
        if isinstance(source, str) and source:
            refs.append(f"source:{source}")
    for edge_id in edge_ids:
        provenance = relationships[edge_id].get("provenance", {})
        contributor = provenance.get("contributor_id")
        if contributor:
            refs.append(f"contributor:{contributor}")
        source = provenance.get("source")
        if isinstance(source, str) and source:
            refs.append(f"source:{source}")
    return list(dict.fromkeys(refs))


def explain_connection_with_provenance(
    records: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
    start_id: str,
    target_id: str,
    max_depth: int = 3,
    relationship_types: set[str] | None = None,
    direction: str = "both",
) -> dict[str, Any]:
    record_list = list(records)
    relationship_list = list(relationships)
    for record in record_list:
        validate_record(record)
    for relationship in relationship_list:
        validate_relationship(relationship)

    record_map = {record["id"]: record for record in record_list}
    relationship_map = {edge["id"]: edge for edge in relationship_list}

    path = explain_connection(
        record_list,
        relationship_list,
        start_id,
        target_id,
        max_depth,
        relationship_types,
        direction,
    )
    if path is None:
        return {
            "start": start_id,
            "target": target_id,
            "found": False,
            "paths": [],
            "notes": ["No connection was found within the requested traversal constraints."],
        }

    return {
        "start": start_id,
        "target": target_id,
        "found": True,
        "paths": [{
            "nodes": path["nodes"],
            "edges": path["edges"],
            "provenance": _provenance_refs(
                record_map, relationship_map, path["nodes"], path["edges"]
            ),
        }],
    }
