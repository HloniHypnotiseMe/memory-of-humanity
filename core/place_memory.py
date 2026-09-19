from __future__ import annotations

from typing import Any


def validate_place_memory(view: dict[str, Any]) -> None:
    if not view.get("id", "").startswith("moh:place-memory:"):
        raise ValueError("id must start with moh:place-memory:")
    if not view.get("place_id", "").startswith("moh:place:"):
        raise ValueError("place_id must be a moh:place identifier")
    if not isinstance(view.get("records"), list):
        raise ValueError("records must be a list")


def create_place_memory(*, view_id: str, place_id: str,
                        records: list[str]) -> dict[str, Any]:
    view = {
        "id": view_id,
        "place_id": place_id,
        "time": None,
        "records": records,
        "relationships": [],
        "include_private": False,
    }
    validate_place_memory(view)
    return view
