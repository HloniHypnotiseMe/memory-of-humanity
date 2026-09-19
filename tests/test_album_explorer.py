from core.albums import create_album
from core.lineage import create_lineage
from core.media import create_media
from core.records import create_memory
from core.relationships import create_relationship
from core.album_explorer import explore_album


def test_album_is_explorable_as_a_first_class_object():
    album = create_album(
        album_id="moh:album:jhb-1980s",
        title="Johannesburg Childhood",
        contributor_id="person:1",
    )
    album["people"] = ["moh:person:grandmother"]
    album["places"] = ["moh:place:johannesburg"]

    story = create_memory(
        record_id="moh:memory:story",
        contributor_id="person:1",
        text="Grandmother told us stories after school.",
        record_type="story",
        created_at="2026-01-01T00:00:00+00:00",
    )
    photo = create_media(
        media_id="moh:media:photo",
        media_type="image",
        content_hash="abcdef12",
        contributor_id="person:1",
    )
    album["items"] = [story["id"], photo["id"]]

    edge = create_relationship("moh:rel:album-story", story["id"], photo["id"], "depicts")
    lineage = create_lineage(
        lineage_id="moh:lineage:story-variant",
        source=story["id"],
        target="moh:memory:later-retelling",
        relationship="retelling",
        contributor_id="person:2",
    )

    result = explore_album(
        album,
        records=[story],
        media=[photo],
        relationships=[edge],
        lineage=[lineage],
        exploration_id="moh:album-exploration:jhb-1980s",
    )

    assert result["album"]["id"] == album["id"]
    assert result["records"] == [story["id"]]
    assert result["media"] == [photo["id"]]
    assert result["people"] == ["moh:person:grandmother"]
    assert result["places"] == ["moh:place:johannesburg"]
    assert result["relationships"][0]["id"] == edge["id"]
    assert result["lineage"][0]["id"] == lineage["id"]


def test_album_explorer_does_not_import_unrelated_objects():
    album = create_album(
        album_id="moh:album:one",
        title="One",
        contributor_id="person:1",
    )
    album["items"] = ["moh:media:inside"]
    inside = create_media(
        media_id="moh:media:inside",
        media_type="audio",
        content_hash="12345678",
        contributor_id="person:1",
    )
    outside = create_media(
        media_id="moh:media:outside",
        media_type="audio",
        content_hash="87654321",
        contributor_id="person:1",
    )
    result = explore_album(
        album,
        media=[inside, outside],
        exploration_id="moh:album-exploration:one",
    )
    assert result["media"] == ["moh:media:inside"]
    assert result["items"] == ["moh:media:inside"]
