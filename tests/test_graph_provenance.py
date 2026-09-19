from core.graph_provenance import explain_connection_with_provenance
from core.records import create_memory
from core.relationships import create_relationship


def test_connection_exposes_provenance():
    a = create_memory("moh:a", "A", "person:1", "remembered")
    b = create_memory("moh:b", "B", "person:2", "reported")
    relationship = create_relationship("moh:r1", "moh:a", "moh:b", "about")

    result = explain_connection_with_provenance([a, b], [relationship], "moh:a", "moh:b")
    assert result["found"] is True
    assert "contributor:person:1" in result["paths"][0]["provenance"]
    assert "contributor:person:2" in result["paths"][0]["provenance"]


def test_missing_connection_is_explicit():
    a = create_memory("moh:a", "A", "person:1", "remembered")
    b = create_memory("moh:b", "B", "person:2", "reported")

    result = explain_connection_with_provenance([a, b], [], "moh:a", "moh:b")
    assert result["found"] is False
    assert result["paths"] == []


def test_duplicate_provenance_is_removed():
    a = create_memory("moh:a", "A", "person:1", "remembered")
    b = create_memory("moh:b", "B", "person:1", "reported")
    relationship = create_relationship("moh:r1", "moh:a", "moh:b", "about")

    result = explain_connection_with_provenance([a, b], [relationship], "moh:a", "moh:b")
    refs = result["paths"][0]["provenance"]
    assert refs.count("contributor:person:1") == 1
