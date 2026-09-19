import pytest
from core.places import create_place


def test_create_place():
    place = create_place(place_id="moh:place:johannesburg", label="Johannesburg", contributor_id="moh:person:alice")
    assert place["id"] == "moh:place:johannesburg"


def test_reject_invalid_place_id():
    with pytest.raises(ValueError):
        create_place(place_id="moh:person:x", label="X", contributor_id="alice")
