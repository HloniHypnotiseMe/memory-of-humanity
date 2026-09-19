import pytest
from core.federation import create_envelope


def test_create_federation_envelope():
    value = create_envelope(
        envelope_id="moh:envelope:e1",
        instance_id="moh:instance:family-archive",
        records=[{"id": "moh:memory:m1"}],
    )
    assert value["protocol"] == "memory-of-humanity"


def test_reject_wrong_protocol():
    from core.federation import validate_envelope
    with pytest.raises(ValueError):
        validate_envelope({
            "protocol": "other",
            "envelope_id": "moh:envelope:e1",
            "instance_id": "moh:instance:x",
            "records": [],
        })
