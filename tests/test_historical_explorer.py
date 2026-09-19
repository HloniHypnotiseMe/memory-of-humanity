from core.historical_explorer import explore_history
from core.records import create_memory
from core.relationships import create_relationship
from core.source_links import create_source_link


def memory(record_id, text, place_id, time, status="remembered", record_type="personal_memory"):
    record = create_memory(
        record_id=record_id,
        contributor_id="person:1",
        text=text,
        record_type=record_type,
        epistemic_status=status,
        created_at="2026-01-01T00:00:00+00:00",
    )
    record["place_id"] = place_id
    record["time"] = time
    return record


def source(source_id, title, place_id, date):
    return {
        "id": source_id,
        "source_type": "newspaper",
        "title": title,
        "place": place_id,
        "date": date,
        "access": {"status": "open"},
        "provenance": {"repository": "test"},
    }


def test_historical_place_and_time_explorer_combines_memories_and_sources():
    place = "moh:place:johannesburg"
    records = [
        memory("moh:memory:1", "Children played outside.", place, {"type": "period", "start": "1980", "end": "1989"}),
        memory("moh:memory:2", "A 2000 memory.", place, {"type": "instant", "start": "2000-01-01"}),
    ]
    sources = [source("moh:source:news1", "Johannesburg Daily", place, "1985-06-01")]
    link = create_source_link(
        "moh:sourcelink:1", "moh:memory:1", "moh:source:news1",
        "contextualizes", "curator:1"
    )

    result = explore_history(
        records, [], sources, [link],
        exploration_id="moh:historical-exploration:jhb-1980s",
        place_id=place,
        time={"type": "range", "start": "1980", "end": "1989"},
    )

    assert [r["id"] for r in result["records"]] == ["moh:memory:1"]
    assert [s["id"] for s in result["sources"]] == ["moh:source:news1"]
    assert [x["id"] for x in result["source_links"]] == ["moh:sourcelink:1"]


def test_historical_explorer_preserves_epistemic_distinction_and_contradictions():
    place = "moh:place:johannesburg"
    a = memory("moh:memory:a", "Grandmother told me there were giants.", place, {"type": "instant", "start": "1984"}, "reported")
    b = memory("moh:memory:b", "No giants were found in the excavation record.", place, {"type": "instant", "start": "1984"}, "documented", "historical_evidence")
    edge = create_relationship("moh:rel:1", a["id"], b["id"], "contradicts")

    result = explore_history(
        [a, b], [edge], [], [],
        exploration_id="moh:historical-exploration:jhb-1984",
        place_id=place,
        time={"type": "instant", "start": "1984"},
    )

    assert {r["epistemic_status"] for r in result["records"]} == {"reported", "documented"}
    assert result["contradictions"][0]["relationship_type"] == "contradicts"
