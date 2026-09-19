import pytest
from core.query import create_query


def test_create_place_memory_query():
    value = create_query(query_id="moh:query:jhb", query_type="place_memory", place_id="moh:place:johannesburg")
    assert value["query_type"] == "place_memory"


def test_reject_invalid_query_type():
    with pytest.raises(ValueError):
        create_query(query_id="moh:query:x", query_type="unknown")
