import pytest
from core.provenance import create_provenance_chain


def test_create_provenance_chain():
    value = create_provenance_chain(record_id="moh:memory:m1", actor_id="moh:person:alice")
    assert value["events"][0]["event_type"] == "created"


def test_reject_bad_actor():
    with pytest.raises(ValueError):
        create_provenance_chain(record_id="moh:memory:m1", actor_id="alice")
