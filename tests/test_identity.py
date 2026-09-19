import pytest
from core.identity import create_identity


def test_create_identity():
    value = create_identity(identity_id="moh:person:alice", kind="person", display_name="Alice")
    assert value["kind"] == "person"


def test_reject_identity_kind():
    with pytest.raises(ValueError):
        create_identity(identity_id="moh:x:a", kind="robot", display_name="A")
