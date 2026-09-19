from node.server import MemoryNode
from node.store import MemoryStore


def test_local_contributor_consent_memory_and_album_flow(tmp_path):
    store=MemoryStore(tmp_path/"memory.db")
    node=MemoryNode(store,instance_id="moh:instance:test",name="Test")
    identity=node.create_identity({"id":"moh:person:test","kind":"person","display_name":"Test Contributor"})
    assert identity["id"]=="moh:person:test"
    consent=node.create_consent({"id":"moh:consent:test","subject_id":"moh:person:test","scope":["memory_submission"],"status":"granted"})
    assert consent["status"]=="granted"
    record=node.create_memory({"id":"moh:memory:test-app","contributor_id":"moh:person:test","text":"My grandmother told me this story in Johannesburg.","record_type":"oral_history","epistemic_status":"reported"})
    assert store.get("records",record["id"])["epistemic_status"]=="reported"
    album=node.create_album({"id":"moh:album:test","title":"Family memories","contributor_id":"moh:person:test","items":[record["id"]]})
    assert album["items"]==[record["id"]]
    assert node.discovery()["instance_id"]=="moh:instance:test"
    store.close()
