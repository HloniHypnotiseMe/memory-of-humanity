from core.memory_explorer import explore
from core.records import create_memory
from core.relationships import create_relationship


def test_explorer_combines_search_and_graph():
    a = create_memory("moh:a", "Johannesburg childhood memory", "p1", "remembered")
    b = create_memory("moh:b", "Newspaper report", "p2", "documented")
    edge = create_relationship("moh:r1", "moh:a", "moh:b", "supported_by")

    result = explore([a, b], [edge], text="Johannesburg", start_id="moh:a", max_depth=1)
    assert result["records"][0]["id"] == "moh:a"
    assert result["graph"]["nodes"][1]["id"] == "moh:b"


def test_explorer_preserves_empty_graph_without_start():
    a = create_memory("moh:a", "Memory", "p1", "remembered")
    result = explore([a], [], text="Memory")
    assert result["graph"] == {"nodes": [], "edges": [], "paths": []}
