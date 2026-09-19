from core.federation import create_envelope
from core.federation_discovery import create_discovery
from core.federation_sync import create_sync_request, incremental_sync, validate_sync_response
from core.records import create_memory


def _envelope(envelope_id, instance_id, text):
    return create_envelope(
        envelope_id=envelope_id,
        instance_id=instance_id,
        records=[create_memory(
            record_id="moh:memory:" + envelope_id.rsplit(":", 1)[-1],
            contributor_id="moh:person:1",
            text=text,
            record_type="personal_memory",
            epistemic_status="remembered",
            created_at="2026-01-01T00:00:00+00:00",
        )],
    )


def test_incremental_sync_returns_only_changes_after_cursor():
    instance = "moh:instance:archive-a"
    discovery = create_discovery(instance_id=instance, name="Archive A", current_cursor="3")
    changes = [
        {"cursor": "1", "envelope": _envelope("moh:envelope:1", instance, "one")},
        {"cursor": "2", "envelope": _envelope("moh:envelope:2", instance, "two")},
        {"cursor": "3", "envelope": _envelope("moh:envelope:3", instance, "three")},
    ]
    request = create_sync_request(
        request_id="moh:sync-request:r1",
        peer_instance_id=instance,
        since_cursor="1",
        limit=1,
    )
    response = incremental_sync(discovery=discovery, request=request, changes=changes)
    assert [item["cursor"] for item in response["changes"]] == ["2"]
    assert response["next_cursor"] == "2"
    assert response["has_more"] is True


def test_incremental_sync_preserves_tombstone_envelopes():
    instance = "moh:instance:archive-a"
    discovery = create_discovery(instance_id=instance, name="Archive A", current_cursor="2")
    tombstone = {"record_id": "moh:memory:old", "reason": "withdrawn", "issued_by": "moh:person:1"}
    changes = [
        {"cursor": "2", "envelope": create_envelope(
            envelope_id="moh:envelope:tombstone",
            instance_id=instance,
            records=[],
            tombstones=[tombstone],
        )}
    ]
    request = create_sync_request(
        request_id="moh:sync-request:r2",
        peer_instance_id=instance,
        since_cursor="0",
    )
    response = incremental_sync(discovery=discovery, request=request, changes=changes)
    assert response["changes"][0]["envelope"]["tombstones"][0]["record_id"] == "moh:memory:old"


def test_sync_response_validation_rejects_backwards_cursor():
    response = {
        "response_id": "moh:sync-response:r3",
        "protocol": "memory-of-humanity",
        "source_instance": "moh:instance:archive-a",
        "since_cursor": "5",
        "next_cursor": "4",
        "changes": [],
    }
    import pytest
    with pytest.raises(ValueError, match="backwards"):
        validate_sync_response(response)


def test_incremental_sync_does_not_federate_private_records():
    instance = "moh:instance:archive-a"
    private_record = create_memory(
        record_id="moh:memory:private",
        contributor_id="moh:person:1",
        text="Private family memory",
        permissions={"visibility": "private", "allow_federation": True},
        created_at="2026-01-01T00:00:00+00:00",
    )
    public_record = create_memory(
        record_id="moh:memory:public",
        contributor_id="moh:person:1",
        text="Public memory",
        permissions={"visibility": "public", "allow_federation": True},
        created_at="2026-01-01T00:00:00+00:00",
    )
    discovery = create_discovery(instance_id=instance, name="Archive A", current_cursor="1")
    request = create_sync_request(request_id="moh:sync-request:privacy", peer_instance_id=instance)
    response = incremental_sync(
        discovery=discovery,
        request=request,
        changes=[{"cursor": "1", "envelope": create_envelope(
            envelope_id="moh:envelope:privacy",
            instance_id=instance,
            records=[private_record, public_record],
        )}],
    )
    ids = [item["id"] for item in response["changes"][0]["envelope"]["records"]]
    assert ids == ["moh:memory:public"]
