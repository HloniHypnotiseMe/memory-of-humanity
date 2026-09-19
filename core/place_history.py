from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

LAYER_TYPES = {
    "people", "stories", "photographs", "newspapers",
    "artefacts", "technologies", "events", "disagreements", "other",
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
    context_types = record.get("context_types", [])
    if "person" in context_types:
        return "people"
    if "event" in context_types:
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


def build_place_history(
    records: Iterable[dict[str, Any]],
    sources: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
    *,
    history_id: str,
    place_id: str,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    if not history_id.startswith("moh:place-history:"):
        raise ValueError("history_id must start with moh:place-history:")
    if not place_id.startswith("moh:place:"):
        raise ValueError("place_id must start with moh:place:")

    record_list = list(records)
    source_list = list(sources)
    relationship_list = list(relationships)
    layers: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for record in record_list:
        year = _year(record.get("time"))
        key = str(year // 10 * 10) if year is not None else "unknown"
        layers[key][_layer_for_record(record)].append(record["id"])
        for media_id in _media_ids(record):
            layers[key]["photographs"].append(media_id)

    for source in source_list:
        if source.get("source_type") != "newspaper":
            continue
        source_date = source.get("date")
        try:
            year = int(str(source_date)[:4])
        except ValueError:
            key = "unknown"
        else:
            key = str(year // 10 * 10)
        layers[key]["newspapers"].append(source["id"])

    for relationship in relationship_list:
        if relationship.get("type") != "contradicts":
            continue
        key = "unknown"
        for candidate in (relationship.get("source"), relationship.get("target")):
            for record in record_list:
                if record.get("id") == candidate:
                    year = _year(record.get("time"))
                    if year is not None:
                        key = str(year // 10 * 10)
                        break
            if key != "unknown":
                break
        layers[key]["disagreements"].append(relationship["id"])

    ordered = []
    for period in sorted(layers, key=lambda value: (value == "unknown", value)):
        ordered.append({
            "period": period,
            "layers": {
                layer: values
                for layer, values in sorted(layers[period].items())
                if values
            },
        })

    totals = {layer: 0 for layer in LAYER_TYPES}
    for period in ordered:
        for layer, values in period["layers"].items():
            totals[layer] = totals.get(layer, 0) + len(values)

    return {
        "id": history_id,
        "place_id": place_id,
        "start": start,
        "end": end,
        "layers": ordered,
        "totals": totals,
    }
