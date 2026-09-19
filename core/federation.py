from __future__ import annotations
from typing import Any

from .albums import validate_album
from .media import validate_media
from .records import validate_record
from .tombstones import validate_tombstone


def validate_envelope(envelope: dict[str, Any]) -> None:
    required = {"protocol", "envelope_id", "instance_id", "records"}
    missing = required - envelope.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if envelope["protocol"] != "memory-of-humanity":
        raise ValueError("unsupported protocol")
    if not envelope["envelope_id"].startswith("moh:envelope:"):
        raise ValueError("invalid envelope_id")
    if not envelope["instance_id"].startswith("moh:instance:"):
        raise ValueError("invalid instance_id")
    for field in ("records", "albums", "media", "sources", "relationships", "source_links", "tombstones", "signatures"):
        if field in envelope and not isinstance(envelope[field], list):
            raise ValueError(f"{field} must be a list")
    for record in envelope["records"]:
        validate_record(record)
    for album in envelope.get("albums", []):
        validate_album(album)
    for item in envelope.get("media", []):
        validate_media(item)
    for tombstone in envelope.get("tombstones", []):
        validate_tombstone(tombstone)


def create_envelope(*, envelope_id: str, instance_id: str,
                    records: list[dict[str, Any]],
                    albums: list[dict[str, Any]] | None = None,
                    media: list[dict[str, Any]] | None = None,
                    sources: list[dict[str, Any]] | None = None,
                    relationships: list[dict[str, Any]] | None = None,
                    source_links: list[dict[str, Any]] | None = None,
                    tombstones: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    envelope = {
        "protocol": "memory-of-humanity",
        "version": "1",
        "envelope_id": envelope_id,
        "instance_id": instance_id,
        "created_at": None,
        "records": records,
        "albums": albums or [],
        "media": media or [],
        "sources": sources or [],
        "relationships": relationships or [],
        "source_links": source_links or [],
        "tombstones": tombstones or [],
        "signatures": [],
    }
    validate_envelope(envelope)
    return envelope
