import pytest

from core.federation_discovery import create_discovery, validate_discovery


def test_create_discovery_advertises_capabilities_and_cursor():
    value = create_discovery(
        instance_id="moh:instance:johannesburg-family",
        name="Johannesburg Family Archive",
        current_cursor="12",
        record_types=["personal_memory", "oral_history"],
        visibility=["public", "private"],
    )
    assert value["protocol"] == "memory-of-humanity"
    assert value["current_cursor"] == "12"
    assert value["capabilities"]["incremental_sync"] is True
    assert "oral_history" in value["record_types"]


def test_discovery_rejects_unknown_record_type():
    with pytest.raises(ValueError):
        validate_discovery({
            "instance_id": "moh:instance:x",
            "protocol": "memory-of-humanity",
            "protocol_version": "1",
            "name": "x",
            "capabilities": {"discovery": True, "incremental_sync": True},
            "current_cursor": "0",
            "record_types": ["not_a_real_type"],
        })
