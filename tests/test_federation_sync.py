from core.federation import create_envelope
from core.federation_discovery import create_discovery
from core.federation_sync import create_sync_request, incremental_sync
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
    tombstone = {"tombstone_id": "moh:tombstone:t1", "record_id": "moh:memory:old", "reason": "withdrawn"}
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
