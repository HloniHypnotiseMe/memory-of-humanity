import pytest

from core.context import create_context, validate_context


def test_create_person_context():
    record = create_context(context_id="moh:person:alice", context_type="person", label="Alice")
    assert record["context_type"] == "person"


def test_reject_invalid_context_type():
    with pytest.raises(ValueError):
        create_context(context_id="moh:thing:x", context_type="thing", label="X")
