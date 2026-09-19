import json
from urllib.request import Request, urlopen

from node.server import MemoryNode
from node.store import MemoryStore


def test_node_discovery_and_incremental_sync(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    node = MemoryNode(store, instance_id="moh:instance:test", name="Test Node")
    assert node.discovery()["instance_id"] == "moh:instance:test"

    from core.records import create_memory
    record = create_memory(
        record_id="moh:memory:test",
        contributor_id="moh:person:test",
        text="A remembered street.",
        created_at="2026-09-19T00:00:00+00:00",
    )
    cursor = node.export_change(envelope_id="moh:envelope:test", records=[record])
    assert cursor == 1
    request = {
        "request_id": "moh:sync-request:test",
        "protocol": "memory-of-humanity",
        "peer_instance_id": "moh:instance:test",
        "since_cursor": "0",
        "limit": 10,
        "visibility": ["public"],
        "known_ids": [],
    }
    response = node.sync(request)
    assert response["next_cursor"] == "1"
    assert response["changes"][0]["envelope"]["records"][0]["id"] == "moh:memory:test"
    store.close()
