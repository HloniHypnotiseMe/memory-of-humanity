from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from .albums import validate_album\nfrom .graph import traverse\nfrom .media import validate_media
from .records import validate_record
from .source_links import validate_source_link


def _time_bounds(value: Any) -> tuple[date | None, date | None]:
    if not isinstance(value, dict):
        return None, None
    start = value.get("start")
    end = value.get("end") or start
    if not start and value.get("label"):
        start = value["label"]
        end = value["label"]
    def parse(raw: Any, end_of_period: bool = False) -> date | None:
        if not isinstance(raw, str):
            return None
        parts = raw.split("-")
        try:
            if len(parts) == 1:
                year = int(parts[0])
                return date(year, 12, 31) if end_of_period else date(year, 1, 1)
            if len(parts) == 2:
                year, month = map(int, parts)
                if end_of_period:
                    next_month = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
                    return next_month.fromordinal(next_month.toordinal() - 1)
                return date(year, month, 1)
            return date.fromisoformat(raw[:10])
        except (TypeError, ValueError):
            return None
    return parse(start), parse(end, True)


def _record_place_ids(record: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in ("place_id", "place"):
        value = record.get(key)
        if isinstance(value, str) and value.startswith("moh:place:"):
            values.add(value)
        elif isinstance(value, dict):
            place_id = value.get("id")
            if isinstance(place_id, str) and place_id.startswith("moh:place:"):
                values.add(place_id)
    context = record.get("context")
    if isinstance(context, dict):
        for key in ("place_id", "place"):
            value = context.get(key)
            if isinstance(value, str) and value.startswith("moh:place:"):
                values.add(value)
            elif isinstance(value, dict):
                place_id = value.get("id")
                if isinstance(place_id, str) and place_id.startswith("moh:place:"):
                    values.add(place_id)
    return values


def _record_time(record: dict[str, Any]) -> Any:
    if isinstance(record.get("time"), dict):
        return record["time"]
    context = record.get("context")
    if isinstance(context, dict) and isinstance(context.get("time"), dict):
        return context["time"]
    return None


def _matches(record: dict[str, Any], place_id: str, time_filter: dict[str, Any] | None) -> bool:
    if place_id not in _record_place_ids(record):
        return False
    if time_filter is None:
        return True
    wanted_start, wanted_end = _time_bounds(time_filter)
    actual_start, actual_end = _time_bounds(_record_time(record))
    if wanted_start is None or actual_start is None:
        return False
    return actual_start <= (wanted_end or wanted_start) and (actual_end or actual_start) >= wanted_start


def _album_matches(album: dict[str, Any], place_id: str, time_filter: dict[str, Any] | None) -> bool:\n    if place_id not in set(album.get("places", [])):\n        return False\n    if time_filter is None:\n        return True\n    wanted_start, wanted_end = _time_bounds(time_filter)\n    actual_start, actual_end = _time_bounds(album.get("time"))\n    if wanted_start is None or actual_start is None:\n        return False\n    return actual_start <= (wanted_end or wanted_start) and (actual_end or actual_start) >= wanted_start\n\n\ndef _source_matches(source: dict[str, Any], place_id: str, time_filter: dict[str, Any] | None) -> bool:
    place = source.get("place")
    if place and place_id not in {place}:
        return False
    if time_filter is None:
        return True
    source_date = source.get("date")
    if not source_date:
        return False
    return _matches({"place_id": place_id, "time": {"type": "instant", "start": source_date}}, place_id, time_filter)


def explore_history(
    records: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
    sources: Iterable[dict[str, Any]],
    source_links: Iterable[dict[str, Any]],
    *,
    exploration_id: str,
    place_id: str,
    time: dict[str, Any] | None = None,
    record_types: set[str] | None = None,
    relationship_types: set[str] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    if not exploration_id.startswith("moh:historical-exploration:"):
        raise ValueError("exploration_id must start with moh:historical-exploration:")
    if not place_id.startswith("moh:place:"):
        raise ValueError("place_id must start with moh:place:")
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")

    record_list = list(records)
    relationship_list = list(relationships)
    source_list = list(sources)
    link_list = list(source_links)
    for record in record_list:
        validate_record(record)
    for link in link_list:
        validate_source_link(link)

    selected = [
        record for record in record_list
        if _matches(record, place_id, time)
        and (not record_types or record["record_type"] in record_types)
    ][:limit]
    selected_ids = {record["id"] for record in selected}

    selected_relationships = [
        edge for edge in relationship_list
        if edge.get("source") in selected_ids and edge.get("target") in selected_ids
        and (not relationship_types or edge.get("type") in relationship_types)
    ]
    graph = {"nodes": [], "edges": [], "paths": []}
    if selected:
        graph = traverse(
            selected,
            selected_relationships,
            start_id=selected[0]["id"],
            max_depth=max(1, len(selected)),
            relationship_types=relationship_types,
        )

    selected_sources = [
        source for source in source_list
        if isinstance(source, dict)
        and source.get("id", "").startswith("moh:source:")
        and _source_matches(source, place_id, time)
    ]
    selected_source_ids = {source["id"] for source in selected_sources}
    selected_links = [
        link for link in link_list
        if link.get("record_id") in selected_ids and link.get("source_id") in selected_source_ids
    ]

    contradictions = [
        edge for edge in selected_relationships
        if edge.get("type") == "contradicts"
    ]
    timeline_items = [
        {
            "record_id": record["id"],
            "time": _record_time(record),
            "label": record["content"].get("text"),
            "relationship": None,
        }
        for record in selected
    ]

    return {
        "id": exploration_id,
        "place_id": place_id,
        "time": time,
        "records": selected,
        "sources": selected_sources,
        "source_links": selected_links,
        "relationships": selected_relationships,
        "contradictions": contradictions,
        "graph": graph,
        "timeline": {
            "subject_id": place_id,
            "start": time.get("start") if time else None,
            "end": time.get("end") if time else None,
            "items": timeline_items,
        },
        "limit": limit,
    }
