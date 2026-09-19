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


def test_discover_instances_filters_and_sorts_peers():
    first = create_discovery(
        instance_id="moh:instance:zulu",
        name="Zulu Archive",
        record_types=["oral_history"],
    )
    second = create_discovery(
        instance_id="moh:instance:alpha",
        name="Alpha Archive",
        record_types=["oral_history", "personal_memory"],
    )
    result = __import__("core.federation_discovery", fromlist=["discover_instances"]).discover_instances(
        [first, second],
        capability="incremental_sync",
        record_type="oral_history",
        visibility="public",
    )
    assert [item["instance_id"] for item in result] == [
        "moh:instance:alpha",
        "moh:instance:zulu",
    ]
