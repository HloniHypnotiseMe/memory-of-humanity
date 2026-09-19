import pytest

from core.records import create_memory, revise_record, validate_record


def test_create_and_validate_memory():
    record = create_memory(
        record_id="moh:memory-001",
        contributor_id="person:grandchild",
        text="My grandmother told me that children played in the street until sunset.",
        created_at="2026-09-19T09:00:00+00:00",
    )
    validate_record(record)
    assert record["revision"]["version"] == 1
    assert record["epistemic_status"] == "remembered"


def test_revision_preserves_original():
    original = create_memory(
        record_id="moh:memory-002",
        contributor_id="person:a",
        text="The shop stood beside the old station.",
        created_at="2026-09-19T09:00:00+00:00",
    )
    revised = revise_record(original, text="The shop stood opposite the old station.")
    validate_record(revised)

    assert original["content"]["text"] == "The shop stood beside the old station."
    assert revised["content"]["text"] == "The shop stood opposite the old station."
    assert revised["revision"]["previous"] == original["id"]
    assert revised["revision"]["version"] == 2


def test_invalid_id_is_rejected():
    record = create_memory(
        record_id="moh:memory-003",
        contributor_id="person:a",
        text="A memory.",
        created_at="2026-09-19T09:00:00+00:00",
    )
    record["id"] = "memory-003"
    with pytest.raises(ValueError, match="moh:"):
        validate_record(record)


def test_invalid_epistemic_status_is_rejected():
    record = create_memory(
        record_id="moh:memory-004",
        contributor_id="person:a",
        text="A memory.",
        created_at="2026-09-19T09:00:00+00:00",
    )
    record["epistemic_status"] = "fact"
    with pytest.raises(ValueError, match="epistemic_status"):
        validate_record(record)


def test_memory_can_carry_place_time_media_and_permissions():
    record = create_memory(
        record_id="moh:memory:context",
        contributor_id="moh:person:a",
        text="My grandfather told me this happened here.",
        place_id="moh:place:johannesburg",
        time={"type": "range", "start": "1980", "end": "1989"},
        people=["moh:person:grandfather"],
        media=["moh:media:photo"],
        permissions={"visibility": "private"},
        created_at="2026-09-19T09:00:00+00:00",
    )
    validate_record(record)
    assert record["place_id"] == "moh:place:johannesburg"
    assert record["time"]["end"] == "1989"
    assert record["permissions"]["visibility"] == "private"
