from __future__ import annotations

import hashlib

from core.albums import create_album
from core.archive import create_archive_source
from core.media import create_media
from core.records import create_memory
from core.relationships import create_relationship
from core.source_links import create_source_link

PLACE = "moh:place:johannesburg"
CONTRIBUTOR = "moh:person:demo"

def _memory(node, record_id, year, text, record_type="personal_memory", status="remembered"):
    value = create_memory(
        record_id=record_id, contributor_id=CONTRIBUTOR,
        text=f"DEMONSTRATION MEMORY — NOT HISTORICAL EVIDENCE. {text}",
        record_type=record_type, epistemic_status=status,
        created_at="2026-09-19T00:00:00+00:00", place_id=PLACE,
        time={"type":"instant","start":str(year),"precision":"year"},
        permissions={"visibility":"public","allow_annotation":True,"allow_derivatives":True,"allow_federation":True,"allow_export":True},
    )
    node.store.upsert("records", value)
    node.export_change(envelope_id=f"moh:envelope:demo:{record_id.split(':')[-1]}", records=[value])
    return value

def seed_demo(node) -> dict:
    if node.store.get("identities", CONTRIBUTOR):
        return {"seeded":False,"reason":"demo corpus already exists","place_id":PLACE}
    node.create_identity({"id":CONTRIBUTOR,"kind":"person","display_name":"Memory of Humanity Demonstration",
                          "description":"Synthetic records used only to demonstrate the protocol and UI."})
    memories=[
        _memory(node,"moh:memory:demo-1978",1978,"A family remembers weekend walks and the sounds of a busy city."),
        _memory(node,"moh:memory:demo-1984",1984,"A childhood recollection describes school games, television, food and neighbourhood routines.","oral_history","reported"),
        _memory(node,"moh:memory:demo-1987",1987,"One remembered account places a community celebration in a particular park.","collective_memory"),
        _memory(node,"moh:memory:demo-1987-alt",1987,"A second remembered account gives a different location for that same celebration.","collective_memory","uncertain"),
        _memory(node,"moh:memory:demo-1994",1994,"A family memory describes changing transport, shopping and communication habits."),
        _memory(node,"moh:memory:demo-2001",2001,"A remembered repair practice describes keeping an old household appliance working.","how_to","reported"),
    ]
    contradiction=create_relationship("moh:rel:demo-contradiction","moh:memory:demo-1987","moh:memory:demo-1987-alt","contradicts")
    node.store.upsert("relationships",contradiction)
    node.export_change(envelope_id="moh:envelope:demo-contradiction",relationships=[contradiction])
    source=create_archive_source("moh:source:demo-newspaper-1987","Synthetic demonstration newspaper — not a historical source",
        "Memory of Humanity reference corpus",source_type="newspaper",date="1987-06-01",place=PLACE,access_status="open",
        rights="Synthetic demonstration material; not a reproduction of a real newspaper.")
    node.store.upsert("sources",source)
    link=create_source_link("moh:sourcelink:demo-1987","moh:memory:demo-1987",source["id"],"contextualizes",CONTRIBUTOR,locator={"page":"demo-1"})
    node.store.upsert("source_links",link)
    node.export_change(envelope_id="moh:envelope:demo-source",sources=[source],source_links=[link])
    raw=b"MOH-DEMO-PHOTO"
    content_hash=hashlib.sha256(raw).hexdigest()
    media=create_media(media_id="moh:media:demo-photo",media_type="image",content_hash=content_hash,contributor_id=CONTRIBUTOR)
    media.update({"mime_type":"application/octet-stream","captured_at":"1984-01-01T00:00:00+00:00","location":PLACE,"rights":"Synthetic demonstration material."})
    node.media.put(raw,content_hash)
    node.store.upsert("media",media)
    node.export_change(envelope_id="moh:envelope:demo-media",media=[media])
    album=create_album(album_id="moh:album:demo-johannesburg-1980s",title="Johannesburg — Demonstration Memories, 1980s",contributor_id=CONTRIBUTOR)
    album.update({"description":"A synthetic, clearly labelled corpus demonstrating how a place can be explored through memories, media and disagreement.",
        "items":[memories[1]["id"],memories[2]["id"],memories[3]["id"],media["id"]],"people":[],"places":[PLACE],
        "time":{"type":"period","start":"1980","end":"1989","precision":"decade"},
        "permissions":{"visibility":"public","allow_annotation":True,"allow_derivatives":True,"allow_federation":True,"allow_export":True}})
    node.store.upsert("albums",album)
    node.export_change(envelope_id="moh:envelope:demo-album",albums=[album])
    return {"seeded":True,"place_id":PLACE,"records":len(memories),"albums":1,"media":1,"sources":1,"relationships":1,
            "notice":"All seeded content is synthetic demonstration material, not historical evidence."}
