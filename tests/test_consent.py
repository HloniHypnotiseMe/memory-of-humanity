import pytest
from core.consent import create_consent


def test_create_consent():
    value = create_consent(
        consent_id="moh:consent:c1",
        subject_id="moh:person:alice",
        scope=["publication"],
        status="granted",
    )
    assert value["status"] == "granted"


def test_reject_consent_status():
    with pytest.raises(ValueError):
        create_consent(
            consent_id="moh:consent:c2",
            subject_id="moh:person:alice",
            scope=[],
            status="assumed",
        )
