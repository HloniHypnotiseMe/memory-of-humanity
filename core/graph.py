from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from .records import validate_record
from .relationships import validate_relationship


def build_graph(
    records: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    adjacency: dict[str, list[dict[str, Any]]] = {}

    for record in records:
        validate_record(record)
        node_id = record["id"]
        nodes[node_id] = record
        adjacency.setdefault(node_id, [])

    for relationship in relationships:
        validate_relationship(relationship)
        source = relationship["source"]
        target = relationship["target"]
        if source not in nodes or target not in nodes:
            raise ValueError("relationship endpoints must exist in records")
        adjacency.setdefault(source, []).append(relationship)
        reverse = dict(relationship)
        reverse["_direction"] = "reverse"
        adjacency.setdefault(target, []).append(reverse)

    return {"nodes": nodes, "adjacency": adjacency}


def traverse(
    records: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
    start_id: str,
    max_depth: int = 1,
    relationship_types: set[str] | None = None,
    direction: str = "both",
) -> dict[str, Any]:
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    if direction not in {"outgoing", "incoming", "both"}:
        raise ValueError("direction must be outgoing, incoming, or both")

    graph = build_graph(records, relationships)
    if start_id not in graph["nodes"]:
        raise ValueError("start_id must exist in records")

    nodes = {start_id}
    edges: dict[str, dict[str, Any]] = {}
    paths: list[dict[str, Any]] = []
    queue = deque([(start_id, 0, [start_id], [])])

    while queue:
        current, depth, path_nodes, path_edges = queue.popleft()
        if depth >= max_depth:
            continue

        for edge in graph["adjacency"].get(current, []):
            reverse = edge.get("_direction") == "reverse"
            if direction == "outgoing" and reverse:
                continue
            if direction == "incoming" and not reverse:
                continue
            if relationship_types and edge["type"] not in relationship_types:
                continue

            edge_id = edge["id"]
            next_id = edge["source"] if reverse else edge["target"]
            clean_edge = {k: v for k, v in edge.items() if k != "_direction"}
            edges[edge_id] = clean_edge

            if next_id not in nodes:
                nodes.add(next_id)
                queue.append((next_id, depth + 1, path_nodes + [next_id], path_edges + [edge_id]))
            elif next_id not in path_nodes:
                queue.append((next_id, depth + 1, path_nodes + [next_id], path_edges + [edge_id]))

            paths.append({
                "start": start_id,
                "end": next_id,
                "nodes": path_nodes + [next_id],
                "edges": path_edges + [edge_id],
            })

    return {
        "nodes": [{"id": node_id, "record": graph["nodes"][node_id]} for node_id in sorted(nodes)],
        "edges": [edges[key] for key in sorted(edges)],
        "paths": paths,
    }


def explain_connection(
    records: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
    start_id: str,
    target_id: str,
    max_depth: int = 3,
    relationship_types: set[str] | None = None,
    direction: str = "both",
) -> dict[str, Any] | None:
    result = traverse(
        records, relationships, start_id, max_depth,
        relationship_types, direction,
    )
    for path in result["paths"]:
        if path["end"] == target_id:
            return path
    return None
