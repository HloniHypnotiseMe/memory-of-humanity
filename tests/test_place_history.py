from core.albums import create_album
from core.media import create_media
from core.place_history import build_place_history
from core.records import create_memory
from core.relationships import create_relationship


def record(record_id, text, place, year, record_type="personal_memory"):
    item = create_memory(
        record_id=record_id,
        contributor_id="person:1",
        text=text,
        record_type=record_type,
        created_at="2026-01-01T00:00:00+00:00",
    )
    item["place_id"] = place
    item["time"] = {"type": "instant", "start": str(year)}
    return item


def test_place_history_builds_temporal_layers():
    place = "moh:place:johannesburg"
    memories = [
        record("moh:memory:1984", "Childhood story", place, 1984, "story"),
        record("moh:memory:1986", "Old machine", place, 1986, "how_to"),
        record("moh:memory:1995", "Old object", place, 1995, "artefact"),
    ]
    sources = [{
        "id": "moh:source:1985-paper",
        "source_type": "newspaper",
        "title": "Daily Paper",
        "date": "1985-06-01",
    }]
    result = build_place_history(
        memories, sources, [],
        history_id="moh:place-history:jhb",
        place_id=place,
    )
    periods = {item["period"]: item["layers"] for item in result["layers"]}
    assert "moh:memory:1984" in periods["1980"]["stories"]
    assert "moh:memory:1986" in periods["1980"]["technologies"]
    assert "moh:source:1985-paper" in periods["1980"]["newspapers"]
    assert "moh:memory:1995" in periods["1990"]["artefacts"]


def test_place_history_surfaces_disagreements():
    place = "moh:place:johannesburg"
    a = record("moh:memory:a", "Story", place, 1984)
    b = record("moh:memory:b", "Evidence", place, 1984, "historical_evidence")
    edge = create_relationship("moh:rel:1", a["id"], b["id"], "contradicts")
    result = build_place_history(
        [a, b], [], [edge],
        history_id="moh:place-history:jhb",
        place_id=place,
    )
    assert result["layers"][0]["layers"]["disagreements"] == ["moh:rel:1"]
    assert result["totals"]["disagreements"] == 1


def test_place_history_surfaces_albums_and_first_class_media():
    place = "moh:place:johannesburg"
    album = create_album(
        album_id="moh:album:jhb-childhood-1980s",
        title="Johannesburg Childhood",
        contributor_id="person:1",
    )
    album["places"] = [place]
    album["time"] = {"type": "period", "start": "1980", "end": "1989"}
    photo = create_media(
        media_id="moh:media:photo-1",
        media_type="image",
        content_hash="abcdef12",
        contributor_id="person:1",
    )
    audio = create_media(
        media_id="moh:media:voice-1",
        media_type="audio",
        content_hash="12345678",
        contributor_id="person:1",
    )
    album["items"] = [photo["id"], audio["id"]]

    result = build_place_history(
        [], [], [],
        history_id="moh:place-history:jhb",
        place_id=place,
        albums=[album],
        media=[photo, audio],
    )
    layers = {item["period"]: item["layers"] for item in result["layers"]}

    assert layers["1980"]["albums"] == [album["id"]]
    assert photo["id"] in layers["1980"]["media"]
    assert audio["id"] in layers["1980"]["media"]
    assert photo["id"] in layers["1980"]["photographs"]
    assert result["totals"]["albums"] == 1
    assert result["totals"]["media"] == 2


def test_place_history_excludes_other_places_and_respects_time_window():
    target = "moh:place:johannesburg"
    other = "moh:place:cape-town"
    memories = [
        record("moh:memory:target-1984", "Target", target, 1984),
        record("moh:memory:target-1995", "Later", target, 1995),
        record("moh:memory:other-1984", "Other", other, 1984),
    ]
    result = build_place_history(
        memories, [], [],
        history_id="moh:place-history:filtered",
        place_id=target,
        start="1980",
        end="1989",
    )
    ids = [rid for period in result["layers"] for values in period["layers"].values() for rid in values]
    assert "moh:memory:target-1984" in ids
    assert "moh:memory:target-1995" not in ids
    assert "moh:memory:other-1984" not in ids
