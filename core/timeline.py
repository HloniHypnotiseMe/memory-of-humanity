from __future__ import annotations

from typing import Any


def validate_timeline(view: dict[str, Any]) -> None:
    if not view.get("id", "").startswith("moh:timeline:"):
        raise ValueError("id must start with moh:timeline:")
    if not view.get("subject_id", "").startswith("moh:"):
        raise ValueError("subject_id must be a moh: identifier")
    if not isinstance(view.get("items"), list):
        raise ValueError("items must be a list")


def create_timeline(*, timeline_id: str, subject_id: str,
                    items: list[dict[str, Any]]) -> dict[str, Any]:
    view = {
        "id": timeline_id,
        "subject_id": subject_id,
        "start": None,
        "end": None,
        "items": items,
    }
    validate_timeline(view)
    return view
