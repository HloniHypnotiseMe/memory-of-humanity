import pytest
from core.exports import create_manifest


def test_create_export_manifest():
    value = create_manifest(
        manifest_id="moh:manifest:m1",
        records=["moh:memory:m1"],
    )
    assert value["protocol"] == "memory-of-humanity"


def test_reject_wrong_manifest_protocol():
    with pytest.raises(ValueError):
        from core.exports import validate_manifest
        validate_manifest({
            "manifest_id": "moh:manifest:m1",
            "protocol": "other",
            "records": [],
        })
