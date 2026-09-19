from __future__ import annotations

from typing import Any


def validate_place(place: dict[str, Any]) -> None:
    required = {"id", "label"}
    missing = required - place.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(place["id"], str) or not place["id"].startswith("moh:place:"):
        raise ValueError("id must start with moh:place:")
    if not isinstance(place["label"], str) or not place["label"].strip():
        raise ValueError("label is required")


def create_place(*, place_id: str, label: str,
                 contributor_id: str) -> dict[str, Any]:
    place = {
        "id": place_id,
        "label": label,
        "historical_names": [],
        "region": None,
        "country": None,
        "coordinates": None,
        "precision": "unknown",
        "privacy": None,
        "provenance": {"contributor_id": contributor_id},
    }
    validate_place(place)
    return place
