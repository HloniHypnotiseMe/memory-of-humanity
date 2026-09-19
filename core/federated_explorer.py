from __future__ import annotations

from copy import deepcopy
from typing import Any

from .albums import validate_album
from .federation import validate_envelope
from .historical_explorer import explore_history
from .media import validate_media
from .records import validate_record
from .relationships import validate_relationship
from .source_links import validate_source_link
from .tombstones import validate_tombstone

VISIBILITIES = {"public", "private", "community", "trusted_custodian", "sealed"}


def _visibility(obj: dict[str, Any]) -> str:
    permissions = obj.get("permissions")
    if not isinstance(permissions, dict):
        return "public"
    value = permissions.get("visibility", "public")
    return value if value in VISIBILITIES else "public"


def _allowed(obj: dict[str, Any], allowed_visibilities: set[str]) -> bool:
    return _visibility(obj) in allowed_visibilities


def _federated_copy(obj: dict[str, Any], instance_id: str) -> dict[str, Any]:
    copy = deepcopy(obj)
    copy["_federation"] = {"source_instance": instance_id}
    return copy


def _merge_by_id(items: list[tuple[dict[str, Any], str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for item, instance_id in items:
        grouped.setdefault(item["id"], []).append((item, instance_id))

    merged: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for object_id in sorted(grouped):
        candidates = grouped[object_id]
        if len({repr(item) for item, _ in candidates}) == 1:
            merged.append(_federated_copy(candidates[0][0], candidates[0][1]))
            continue
        max_version = max(
            int(item.get("revision", {}).get("version", 0))
            if isinstance(item.get("revision"), dict) else 0
            for item, _ in candidates
        )
        latest = [
            (item, instance) for item, instance in candidates
            if (int(item.get("revision", {}).get("version", 0))
                if isinstance(item.get("revision"), dict) else 0) == max_version
        ]
        if len({repr(item) for item, _ in latest}) == 1:
            merged.append(_federated_copy(latest[0][0], latest[0][1]))
        else:
            for item, instance in candidates:
                merged.append(_federated_copy(item, instance))
            conflicts.append({
                "id": object_id,
                "instances": sorted({instance for _, instance in candidates}),
                "revision": max_version,
                "reason": "same stable ID has divergent latest content",
            })
    return merged, conflicts


def explore_federated_history(
    envelopes: list[dict[str, Any]],
    *,
    exploration_id: str,
    place_id: str,
    time: dict[str, Any] | None = None,
    record_types: set[str] | None = None,
    relationship_types: set[str] | None = None,
    limit: int = 100,
    allowed_visibilities: set[str] | None = None,
) -> dict[str, Any]:
    if allowed_visibilities is None:
        allowed_visibilities = {"public"}
    if not allowed_visibilities <= VISIBILITIES:
        raise ValueError("unsupported visibility")
    if not envelopes:
        raise ValueError("at least one federation envelope is required")

    records: list[tuple[dict[str, Any], str]] = []
    albums: list[tuple[dict[str, Any], str]] = []
    media: list[tuple[dict[str, Any], str]] = []
    sources: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    source_links: list[dict[str, Any]] = []
    tombstones: dict[str, dict[str, Any]] = {}
    envelope_instances: set[str] = set()

    for envelope in envelopes:
        validate_envelope(envelope)
        instance_id = envelope["instance_id"]
        envelope_instances.add(instance_id)

        for tombstone in envelope.get("tombstones", []):
            validate_tombstone(tombstone)
            tombstones[tombstone["record_id"]] = tombstone

        for record in envelope.get("records", []):
            validate_record(record)
            if _allowed(record, allowed_visibilities):
                records.append((record, instance_id))

        for album in envelope.get("albums", []):
            validate_album(album)
            if _allowed(album, allowed_visibilities):
                albums.append((album, instance_id))

        for item in envelope.get("media", []):
            validate_media(item)
            if _allowed(item, allowed_visibilities):
                media.append((item, instance_id))

        for source in envelope.get("sources", []):
            if isinstance(source, dict) and source.get("id", "").startswith("moh:source:"):
                sources.append(_federated_copy(source, instance_id))

        for relationship in envelope.get("relationships", []):
            validate_relationship(relationship)
            relationships.append(_federated_copy(relationship, instance_id))

        for link in envelope.get("source_links", []):
            validate_source_link(link)
            source_links.append(_federated_copy(link, instance_id))

    record_list, record_conflicts = _merge_by_id(records)
    album_list, album_conflicts = _merge_by_id(albums)
    media_list, media_conflicts = _merge_by_id(media)

    blocked_ids = set(tombstones)
    record_list = [item for item in record_list if item["id"] not in blocked_ids]
    album_list = [item for item in album_list if item["id"] not in blocked_ids]
    media_list = [item for item in media_list if item["id"] not in blocked_ids]

    valid_ids = {item["id"] for item in record_list}
    relationships = [
        edge for edge in relationships
        if edge.get("source") in valid_ids and edge.get("target") in valid_ids
    ]
    source_ids = {source["id"] for source in sources}
    source_links = [
        link for link in source_links
        if link.get("record_id") in valid_ids and link.get("source_id") in source_ids
    ]

    history = explore_history(
        record_list,
        relationships,
        sources,
        source_links,
        exploration_id=exploration_id,
        place_id=place_id,
        time=time,
        record_types=record_types,
        relationship_types=relationship_types,
        limit=limit,
        albums=album_list,
        media=media_list,
    )

    history["federation"] = {
        "instances": sorted(envelope_instances),
        "record_conflicts": record_conflicts,
        "album_conflicts": album_conflicts,
        "media_conflicts": media_conflicts,
        "tombstones": sorted(tombstones),
        "visibility": sorted(allowed_visibilities),
    }
    return history
