from core.records import create_memory
from core.search import search_records


def test_text_search_returns_matching_records():
    records = [
        create_memory("moh:a", "Johannesburg childhood memories", "p1", "remembered"),
        create_memory("moh:b", "Cape Town fishing story", "p2", "traditional"),
    ]
    result = search_records(records, text="Johannesburg")
    assert [item["id"] for item in result["results"]] == ["moh:a"]
    assert result["results"][0]["matched_fields"] == ["text"]


def test_filters_are_applied():
    records = [
        create_memory("moh:a", "old story", "p1", "remembered"),
        create_memory("moh:b", "old story", "p2", "documented"),
    ]
    result = search_records(records, text="old", epistemic_statuses={"documented"})
    assert [item["id"] for item in result["results"]] == ["moh:b"]


def test_limit_and_deterministic_order():
    records = [
        create_memory("moh:b", "same memory", "p1", "remembered"),
        create_memory("moh:a", "same memory", "p2", "remembered"),
    ]
    result = search_records(records, text="same", limit=1)
    assert [item["id"] for item in result["results"]] == ["moh:a"]


def test_empty_text_returns_all_records_up_to_limit():
    records = [
        create_memory("moh:a", "A", "p1", "remembered"),
        create_memory("moh:b", "B", "p2", "reported"),
    ]
    result = search_records(records, limit=1)
    assert len(result["results"]) == 1
