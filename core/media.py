from __future__ import annotations

from typing import Any

MEDIA_TYPES = {"image", "audio", "video", "document", "scan", "map", "diagram", "other"}


def validate_media(media: dict[str, Any]) -> None:
    required = {"id", "media_type", "content_hash", "provenance"}
    missing = required - media.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(media["id"], str) or not media["id"].startswith("moh:media:"):
        raise ValueError("id must start with moh:media:")
    if media["media_type"] not in MEDIA_TYPES:
        raise ValueError("unsupported media_type")
    if not isinstance(media["content_hash"], str) or len(media["content_hash"]) < 8:
        raise ValueError("content_hash is required")
    if not isinstance(media["provenance"], dict) or not media["provenance"].get("contributor_id"):
        raise ValueError("provenance.contributor_id is required")


def create_media(*, media_id: str, media_type: str, content_hash: str,
                 contributor_id: str, source_uri: str | None = None) -> dict[str, Any]:
    media = {
        "id": media_id,
        "media_type": media_type,
        "content_hash": content_hash,
        "source_uri": source_uri,
        "provenance": {"contributor_id": contributor_id},
    }
    validate_media(media)
    return media
