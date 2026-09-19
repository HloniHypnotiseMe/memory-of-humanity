from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable

from core.albums import validate_album
from core.media import validate_media

LAYER_TYPES = {
    "people", "stories", "photographs", "newspapers",
    "artefacts", "technologies", "events", "disagreements", "albums",
    "media", "other",
}


def _year(value: Any) -> int | None:
    if not isinstance(value, dict):
        return None
    raw = value.get("start") or value.get("label")
    if not isinstance(raw, str):
        return None
    try:
        return int(raw[:4])
    except ValueError:
        return None


def _year_from_media(media: dict[str, Any]) -> int | None:
    captured_at = media.get("captured_at")
    if not isinstance(captured_at, str):
        return None
    try:
        return int(captured_at[:4])
    except ValueError:
        return None


def _period(year: int | None) -> str:
    return str(year // 10 * 10) if year is not None else "unknown"


def _time_years(value: Any) -> set[int] | None:
    if not isinstance(value, dict):
        return None
    start = value.get("start") or value.get("label")
    end = value.get("end") or start
    if not isinstance(start, str) or not start[:4].isdigit():
        return None
    if not isinstance(end, str) or not end[:4].isdigit():
        end = start
    return set(range(int(start[:4]), int(end[:4]) + 1))


def _overlaps(value: Any, start: str | None, end: str | None) -> bool:
    if not start and not end:
        return True
    years = _time_years(value)
    if years is None:
        return True
    lo = int((start or "0000")[:4])
    hi = int((end or "9999")[:4])
    return any(lo <= year <= hi for year in years)


def _layer_for_record(record: dict[str, Any]) -> str:
    record_type = record.get("record_type")
    if record_type in {"story", "oral_history", "cultural_practice", "collective_memory"}:
        return "stories"
    if record_type == "artefact":
        return "artefacts"
    if record_type == "how_to":
        return "technologies"
    if record_type == "historical_evidence":
        return "other"
    if record.get("people"):
        return "people"
    if record.get("record_type") == "place_memory":
        return "events"
    media = record.get("media", [])
    if any(isinstance(item, dict) and item.get("media_type") == "image" for item in media):
        return "photographs"
    return "other"


def _media_ids(record: dict[str, Any]) -> list[str]:
    media = record.get("media", [])
    if not isinstance(media, list):
        return []
    return [
        item if isinstance(item, str) else item.get("id")
        for item in media
        if (isinstance(item, str) and item.startswith("moh:media:"))
        or (isinstance(item, dict) and isinstance(item.get("id"), str))
    ]


def _record_at_place(record: dict[str, Any], place_id: str) -> bool:
    if record.get("place_id") == place_id:
        return True
    if place_id in record.get("places", []):
        return True
    context = record.get("context")
    if isinstance(context, dict):
        return context.get("id") == place_id or context.get("place_id") == place_id
    if isinstance(context, list):
        return any(isinstance(item, dict) and item.get("id") == place_id for item in context)
    return False


def build_place_history(
    records: Iterable[dict[str, Any]],
    sources: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
    *,
    history_id: str,
    place_id: str,
    start: str | None = None,
    end: str | None = None,
    albums: Iterable[dict[str, Any]] | None = None,
    media: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not history_id.startswith("moh:place-history:"):
        raise ValueError("history_id must start with moh:place-history:")
    if not place_id.startswith("moh:place:"):
        raise ValueError("place_id must start with moh:place:")

    record_list = list(records)
    source_list = list(sources)
    relationship_list = list(relationships)
    album_list = list(albums or [])
    media_list = list(media or [])
    for album in album_list:
        validate_album(album)
    for media_item in media_list:
        validate_media(media_item)

    selected_records = [r for r in record_list if _record_at_place(r, place_id) and _overlaps(r.get("time"), start, end)]
    selected_ids = {r["id"] for r in selected_records}
    selected_albums = [
        a for a in album_list
        if place_id in a.get("places", []) and _overlaps(a.get("time"), start, end)
    ]
    selected_album_ids = {a["id"] for a in selected_albums}
    album_media_ids = {
        item for album in selected_albums for item in album.get("items", [])
        if isinstance(item, str) and item.startswith("moh:media:")
    }
    referenced_media_ids = {mid for record in selected_records for mid in _media_ids(record)}
    selected_media = [
        m for m in media_list
        if m["id"] in referenced_media_ids or m["id"] in album_media_ids
    ]
    selected_media_ids = {m["id"] for m in selected_media}

    layers: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    def add(period: str, layer: str, value: str) -> None:
        if value not in layers[period][layer]:
            layers[period][layer].append(value)

    for record in selected_records:
        key = _period(_year(record.get("time")))
        add(key, _layer_for_record(record), record["id"])
        for media_id in _media_ids(record):
            if media_id in selected_media_ids:
                add(key, "media", media_id)
                media_item = next((m for m in selected_media if m["id"] == media_id), None)
                if media_item and media_item.get("media_type") == "image":
                    add(key, "photographs", media_id)

    for album in selected_albums:
        key = _period(_year(album.get("time")))
        add(key, "albums", album["id"])
        for item_id in album.get("items", []):
            if item_id in selected_media_ids:
                add(key, "media", item_id)
                media_item = next((m for m in selected_media if m["id"] == item_id), None)
                if media_item and media_item.get("media_type") == "image":
                    add(key, "photographs", item_id)

    for media_item in selected_media:
        key = _period(_year_from_media(media_item))
        add(key, "media", media_item["id"])
        if media_item.get("media_type") == "image":
            add(key, "photographs", media_item["id"])

    for source in source_list:
        if source.get("source_type") != "newspaper":
            continue
        source_place = source.get("place_id") or source.get("place")
        if source_place != place_id:
            continue
        source_date = source.get("date")
        try:
            year = int(str(source_date)[:4])
        except (TypeError, ValueError):
            continue
        if start and year < int(start[:4]):
            continue
        if end and year > int(end[:4]):
            continue
        add(_period(year), "newspapers", source["id"])

    for relationship in relationship_list:
        if relationship.get("type") != "contradicts":
            continue
        if relationship.get("source") not in selected_ids and relationship.get("target") not in selected_ids:
            continue
        key = "unknown"
        for candidate in (relationship.get("source"), relationship.get("target")):
            record = next((r for r in selected_records if r.get("id") == candidate), None)
            if record:
                year = _year(record.get("time"))
                if year is not None:
                    key = _period(year)
                    break
        add(key, "disagreements", relationship["id"])

    ordered = [
        {"period": period, "layers": {layer: values for layer, values in sorted(layers[period].items()) if values}}
        for period in sorted(layers, key=lambda value: (value == "unknown", value))
    ]
    totals = {layer: 0 for layer in LAYER_TYPES}
    for period in ordered:
        for layer, values in period["layers"].items():
            totals[layer] = totals.get(layer, 0) + len(values)
    return {"id": history_id, "place_id": place_id, "start": start, "end": end, "layers": ordered, "totals": totals}
