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


def test_peer_sync_transfers_changes(tmp_path):
    from core.records import create_memory
    store_a = MemoryStore(tmp_path/"a.db")
    store_b = MemoryStore(tmp_path/"b.db")
    a = MemoryNode(store_a, instance_id="moh:instance:a", name="A")
    b = MemoryNode(store_b, instance_id="moh:instance:b", name="B")
    b.create_identity({"id":"moh:person:b","kind":"person","display_name":"B"})
    record = create_memory(record_id="moh:memory:peer",contributor_id="moh:person:b",text="Remembered by B.",created_at="2026-09-19T00:00:00+00:00")
    b.export_change(envelope_id="moh:envelope:peer",records=[record])
    def fetcher(method,path,payload):
        if method=="GET": return b.discovery()
        return b.sync(payload)
    request={"request_id":"moh:sync-request:peer","protocol":"memory-of-humanity","peer_instance_id":"moh:instance:b","since_cursor":"0","limit":100,"visibility":["public"],"known_ids":[]}
    result=a.sync_peer(request,fetcher)
    assert "moh:memory:peer" in result["accepted"]
    assert store_a.get("records","moh:memory:peer")["content"]["text"]=="Remembered by B."
    store_a.close(); store_b.close()
