from __future__ import annotations

from typing import Any


def validate_album(album: dict[str, Any]) -> None:
    required = {"id", "title", "items", "provenance"}
    missing = required - album.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not album["id"].startswith("moh:album:"):
        raise ValueError("id must start with moh:album:")
    if not isinstance(album["title"], str) or not album["title"].strip():
        raise ValueError("title is required")
    if not isinstance(album["items"], list):
        raise ValueError("items must be a list")
    if not album["provenance"].get("contributor_id"):
        raise ValueError("provenance.contributor_id is required")


def create_album(*, album_id: str, title: str,
                 contributor_id: str) -> dict[str, Any]:
    album = {
        "id": album_id,
        "title": title,
        "description": None,
        "items": [],
        "people": [],
        "places": [],
        "time": None,
        "provenance": {"contributor_id": contributor_id},
        "permissions": None,
    }
    validate_album(album)
    return album
