import pytest
from core.place_memory import create_place_memory


def test_create_place_memory():
    value = create_place_memory(
        view_id="moh:place-memory:jhb",
        place_id="moh:place:johannesburg",
        records=["moh:memory:m1", "moh:media:photo1"],
    )
    assert len(value["records"]) == 2


def test_reject_invalid_place():
    with pytest.raises(ValueError):
        create_place_memory(view_id="moh:place-memory:x", place_id="moh:person:alice", records=[])
