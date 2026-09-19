from core.graph import build_graph, explain_connection, traverse
from core.records import create_memory
from core.relationships import create_relationship


def records():
    a = create_memory("moh:a", "A", "p1", "remembered")
    b = create_memory("moh:b", "B", "p1", "reported")
    c = create_memory("moh:c", "C", "p1", "documented")
    d = create_memory("moh:d", "D", "p1", "evidenced")
    return [a, b, c, d]


def relationships():
    return [
        create_relationship("moh:r1", "moh:a", "moh:b", "about"),
        create_relationship("moh:r2", "moh:b", "moh:c", "supports"),
        create_relationship("moh:r3", "moh:c", "moh:d", "contradicts"),
    ]


def test_build_graph_indexes_nodes_and_edges():
    graph = build_graph(records(), relationships())
    assert set(graph["nodes"]) == {"moh:a", "moh:b", "moh:c", "moh:d"}
    assert len(graph["adjacency"]["moh:a"]) == 1


def test_traverse_multi_hop():
    result = traverse(records(), relationships(), "moh:a", max_depth=3)
    assert {node["id"] for node in result["nodes"]} == {"moh:a", "moh:b", "moh:c", "moh:d"}


def test_relationship_filter():
    result = traverse(records(), relationships(), "moh:a", max_depth=3, relationship_types={"supports"})
    assert {node["id"] for node in result["nodes"]} == {"moh:a"}


def test_max_depth():
    result = traverse(records(), relationships(), "moh:a", max_depth=1)
    assert {node["id"] for node in result["nodes"]} == {"moh:a", "moh:b"}


def test_contradiction_path_is_preserved():
    path = explain_connection(records(), relationships(), "moh:a", "moh:d", max_depth=3)
    assert path is not None
    assert path["edges"] == ["moh:r1", "moh:r2", "moh:r3"]


def test_no_invented_edges():
    result = traverse(records(), relationships(), "moh:a", max_depth=3)
    assert "moh:fake" not in {edge["target"] for edge in result["edges"]}
