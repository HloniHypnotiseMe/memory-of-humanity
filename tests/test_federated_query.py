from core.albums import create_album
from core.federated_query import federated_query
from core.media import create_media
from core.records import create_memory


def envelope(instance, records=None, albums=None, media=None):
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
        "tombstones": [],
        "signatures": [],
    }


def memory(record_id, text, place):
    value = create_memory(record_id, text, "person:1", "remembered")
    value["place_id"] = place
    value["time"] = {"type": "instant", "start": "1984"}
    return value


def test_text_query_spans_independent_instances():
    place = "moh:place:johannesburg"
    result = federated_query(
        [envelope("moh:instance:a", [memory("moh:memory:a", "school games", place)]),
         envelope("moh:instance:b", [memory("moh:memory:b", "school games and songs", place)])],
        {"query_id": "moh:query:games", "query_type": "text", "text": "games"},
    )
    assert {x["id"] for x in result["results"]} == {"moh:memory:a", "moh:memory:b"}


def test_place_query_surfaces_album_and_media():
    place = "moh:place:johannesburg"
    album = create_album(album_id="moh:album:1", title="1980s Family", contributor_id="person:1")
    album["places"] = [place]
    album["time"] = {"type": "period", "start": "1980", "end": "1989"}
    photo = create_media(media_id="moh:media:1", media_type="image", content_hash="abcdef12", contributor_id="person:1")
    album["items"] = [photo["id"]]
    result = federated_query(
        [envelope("moh:instance:family", albums=[album], media=[photo])],
        {"query_id": "moh:query:jhb", "query_type": "place_memory", "place_id": place,
         "time": {"type": "range", "start": "1980", "end": "1989"}},
    )
    assert result["albums"][0]["id"] == album["id"]
    assert result["media"][0]["id"] == photo["id"]
