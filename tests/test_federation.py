import pytest
from core.federation import create_envelope
from core.records import create_memory


def test_create_federation_envelope():
    record = create_memory(
        record_id="moh:memory:m1",
        contributor_id="person:1",
        text="A family memory.",
        record_type="personal_memory",
        epistemic_status="remembered",
        created_at="2026-01-01T00:00:00+00:00",
    )
    value = create_envelope(
        envelope_id="moh:envelope:e1",
        instance_id="moh:instance:family-archive",
        records=[record],
    )
    assert value["protocol"] == "memory-of-humanity"
    assert value["albums"] == []
    assert value["media"] == []


def test_reject_wrong_protocol():
    from core.federation import validate_envelope
    with pytest.raises(ValueError):
        validate_envelope({
            "protocol": "other",
            "envelope_id": "moh:envelope:e1",
            "instance_id": "moh:instance:x",
            "records": [],
        })
