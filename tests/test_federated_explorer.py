from core.albums import create_album
from core.federated_explorer import explore_federated_history
from core.media import create_media
from core.records import create_memory
from core.tombstones import create_tombstone


def record(record_id, text, place, visibility="public"):
    item = create_memory(
        record_id=record_id,
        contributor_id="person:1",
        text=text,
        record_type="personal_memory",
        epistemic_status="remembered",
        created_at="2026-01-01T00:00:00+00:00",
    )
    item["place_id"] = place
    item["time"] = {"type": "instant", "start": "1984"}
    item["permissions"] = {"visibility": visibility}
    return item


def envelope(instance, records=None, albums=None, media=None, tombstones=None):
    return {
        "protocol": "memory-of-humanity",
        "version": "1",
        "envelope_id": f"moh:envelope:{instance.split(':')[-1]}",
        "instance_id": instance,
        "records": records or [],
        "albums": albums or [],
        "media": media or [],
        "sources": [],
        "relationships": [],
        "source_links": [],
        "tombstones": tombstones or [],
        "signatures": [],
    }


def test_federated_history_combines_independent_instances_and_preserves_origin():
    place = "moh:place:johannesburg"
    a = record("moh:memory:a", "Family story from instance A.", place)
    b = record("moh:memory:b", "Community memory from instance B.", place)
    result = explore_federated_history(
        [envelope("moh:instance:family-a", [a]), envelope("moh:instance:community-b", [b])],
        exploration_id="moh:historical-exploration:jhb-1984-federated",
        place_id=place,
        time={"type": "instant", "start": "1984"},
    )
    assert {item["id"] for item in result["records"]} == {a["id"], b["id"]}
    assert {item["_federation"]["source_instance"] for item in result["records"]} == {
        "moh:instance:family-a", "moh:instance:community-b"
    }


def test_federated_history_honours_tombstones_and_visibility():
    place = "moh:place:johannesburg"
    public = record("moh:memory:public", "Public memory.", place)
    private = record("moh:memory:private", "Family-only memory.", place, "private")
    withdrawn = record("moh:memory:withdrawn", "Withdrawn memory.", place)
    tombstone = create_tombstone(record_id=withdrawn["id"], reason="withdrawn", issued_by="moh:instance:family-a")
    result = explore_federated_history(
        [envelope("moh:instance:family-a", [public, private, withdrawn], tombstones=[tombstone])],
        exploration_id="moh:historical-exploration:jhb-1984-private",
        place_id=place,
        time={"type": "instant", "start": "1984"},
    )
    assert [item["id"] for item in result["records"]] == [public["id"]]
    assert withdrawn["id"] in result["federation"]["tombstones"]
    authorized = explore_federated_history(
        [envelope("moh:instance:family-a", [public, private, withdrawn], tombstones=[tombstone])],
        exploration_id="moh:historical-exploration:jhb-1984-authorized",
        place_id=place,
        time={"type": "instant", "start": "1984"},
        allowed_visibilities={"public", "private"},
    )
    assert {item["id"] for item in authorized["records"]} == {public["id"], private["id"]}


def test_federated_history_keeps_divergent_same_id_visible_as_conflict():
    place = "moh:place:johannesburg"
    a = record("moh:memory:same", "Version from A.", place)
    b = record("moh:memory:same", "Version from B.", place)
    result = explore_federated_history(
        [envelope("moh:instance:a", [a]), envelope("moh:instance:b", [b])],
        exploration_id="moh:historical-exploration:jhb-conflict",
        place_id=place,
    )
    assert len(result["records"]) == 2
    assert result["federation"]["record_conflicts"][0]["id"] == "moh:memory:same"


def test_federated_history_surfaces_albums_and_media():
    place = "moh:place:johannesburg"
    album = create_album(album_id="moh:album:jhb", title="Family album", contributor_id="person:1")
    album["places"] = [place]
    album["time"] = {"type": "period", "start": "1980", "end": "1989"}
    photo = create_media(media_id="moh:media:jhb-photo", media_type="image", content_hash="abcdef12", contributor_id="person:1")
    album["items"] = [photo["id"]]
    result = explore_federated_history(
        [envelope("moh:instance:family-a", albums=[album], media=[photo])],
        exploration_id="moh:historical-exploration:jhb-album",
        place_id=place,
        time={"type": "range", "start": "1980", "end": "1989"},
    )
    assert [item["id"] for item in result["albums"]] == [album["id"]]
    assert [item["id"] for item in result["media"]] == [photo["id"]]
    assert result["albums"][0]["_federation"]["source_instance"] == "moh:instance:family-a"
