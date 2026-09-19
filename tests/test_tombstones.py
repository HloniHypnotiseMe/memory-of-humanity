import pytest
from core.tombstones import create_tombstone


def test_create_tombstone():
    value = create_tombstone(
        record_id="moh:memory:m1",
        reason="withdrawn",
        issued_by="moh:person:alice",
    )
    assert value["reason"] == "withdrawn"


def test_reject_bad_reason():
    with pytest.raises(ValueError):
        create_tombstone(
            record_id="moh:memory:m1",
            reason="erase_history",
            issued_by="moh:person:alice",
        )
