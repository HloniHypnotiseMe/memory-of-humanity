from core.federation import create_envelope
from core.federation_import import apply_sync_response, content_hash
from core.records import create_memory


def _record(record_id, text, version=1):
    record = create_memory(
        record_id=record_id,
        contributor_id="moh:person:1",
        text=text,
        created_at="2026-01-01T00:00:00+00:00",
    )
    record["revision"]["version"] = version
    return record


def _response(envelopes):
    return {
        "response_id": "moh:sync-response:test",
        "protocol": "memory-of-humanity",
        "source_instance": "moh:instance:archive-a",
        "since_cursor": "0",
        "next_cursor": str(len(envelopes)),
        "changes": [
            {"cursor": str(i), "envelope": envelope}
            for i, envelope in enumerate(envelopes, 1)
        ],
    }


def test_import_applies_new_revision_and_persists_cursor():
    instance = "moh:instance:archive-a"
    response = _response([
        create_envelope(
            envelope_id="moh:envelope:1", instance_id=instance,
            records=[_record("moh:memory:1", "original")],
        ),
        create_envelope(
            envelope_id="moh:envelope:2", instance_id=instance,
            records=[_record("moh:memory:1", "revised", version=2)],
        ),
    ])
    local = {"records": [], "albums": [], "media": [], "sources": [], "relationships": [], "source_links": [], "tombstones": []}
    result = apply_sync_response(local=local, response=response)
    assert local["records"][0]["content"]["text"] == "revised"
    assert local["_federation_cursors"][instance] == "2"
    assert "moh:memory:1" in result["accepted"]


def test_import_surfaces_same_version_divergence_without_picking_winner():
    instance = "moh:instance:archive-a"
    first = _record("moh:memory:1", "one")
    second = _record("moh:memory:1", "different")
    response = _response([
        create_envelope(envelope_id="moh:envelope:1", instance_id=instance, records=[first]),
        create_envelope(envelope_id="moh:envelope:2", instance_id=instance, records=[second]),
    ])
    local = {"records": []}
    result = apply_sync_response(local=local, response=response)
    assert len(result["conflicts"]) == 1
    assert local["records"][0]["content"]["text"] == "one"


def test_import_propagates_tombstone_and_blocks_resurrection():
    instance = "moh:instance:archive-a"
    tombstone = {"record_id": "moh:memory:1", "reason": "withdrawn", "issued_by": "moh:person:1"}
    response = _response([
        create_envelope(envelope_id="moh:envelope:1", instance_id=instance,
                        records=[_record("moh:memory:1", "memory")]),
        create_envelope(envelope_id="moh:envelope:2", instance_id=instance,
                        records=[], tombstones=[tombstone]),
        create_envelope(envelope_id="moh:envelope:3", instance_id=instance,
                        records=[_record("moh:memory:1", "resurrection", version=3)]),
    ])
    local = {"records": []}
    result = apply_sync_response(local=local, response=response)
    assert local["records"] == []
    assert local["tombstones"][0]["record_id"] == "moh:memory:1"
    assert result["tombstones"] == ["moh:memory:1"]


def test_content_hash_is_deterministic():
    record = _record("moh:memory:1", "stable")
    assert content_hash(record) == content_hash(dict(record))
