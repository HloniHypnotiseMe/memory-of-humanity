from __future__ import annotations

from typing import Any, Iterable

from core.albums import validate_album
from core.lineage import validate_lineage
from core.media import validate_media
from core.records import validate_record
from core.relationships import validate_relationship


def _ids(values: Iterable[Any]) -> list[str]:
    return sorted({
        value if isinstance(value, str) else value.get("id")
        for value in values
        if (isinstance(value, str) and value.startswith("moh:"))
        or (isinstance(value, dict) and isinstance(value.get("id"), str) and value["id"].startswith("moh:"))
    })


def explore_album(
    album: dict[str, Any],
    *,
    records: Iterable[dict[str, Any]] = (),
    media: Iterable[dict[str, Any]] = (),
    relationships: Iterable[dict[str, Any]] = (),
    lineage: Iterable[dict[str, Any]] = (),
    exploration_id: str,
) -> dict[str, Any]:
    validate_album(album)
    if not exploration_id.startswith("moh:album-exploration:"):
        raise ValueError("exploration_id must start with moh:album-exploration:")

    record_list = list(records)
    media_list = list(media)
    relationship_list = list(relationships)
    lineage_list = list(lineage)

    for record in record_list:
        validate_record(record)
    for media_item in media_list:
        validate_media(media_item)
    for relationship in relationship_list:
        validate_relationship(relationship)
    for lineage_item in lineage_list:
        validate_lineage(lineage_item)

    item_ids = set(album["items"])
    record_ids = {record["id"] for record in record_list}
    media_ids = {item["id"] for item in media_list}
    people = set(album.get("people", []))
    places = set(album.get("places", []))
    records_in_album = item_ids & record_ids
    media_in_album = item_ids & media_ids

    relevant_relationships = [
        relationship for relationship in relationship_list
        if relationship["source"] in item_ids or relationship["target"] in item_ids
    ]
    relevant_lineage = [
        item for item in lineage_list
        if item["source"] in item_ids or item.get("target") in item_ids
    ]

    for record in record_list:
        if record["id"] not in records_in_album:
            continue
        for person_id in record.get("people", []):
            if isinstance(person_id, str) and person_id.startswith("moh:person:"):
                people.add(person_id)
        for place_ref in (record.get("place_id"),):
            if isinstance(place_ref, str) and place_ref.startswith("moh:place:"):
                places.add(place_ref)

    return {
        "id": exploration_id,
        "album": {
            "id": album["id"],
            "title": album["title"],
            "description": album.get("description"),
            "provenance": album["provenance"],
            "permissions": album.get("permissions"),
        },
        "items": sorted(item_ids),
        "people": sorted(people),
        "places": sorted(places),
        "records": sorted(records_in_album),
        "media": sorted(media_in_album),
        "relationships": relevant_relationships,
        "lineage": relevant_lineage,
        "notes": [
            "The album remains a first-class cultural object.",
            "Source records, media, relationships and lineage remain distinct from the album itself.",
            "No AI interpretation is promoted to source truth by this explorer.",
        ],
    }
