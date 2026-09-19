from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

from .federation import validate_envelope
from .federation_sync import _cursor, validate_sync_response


COLLECTIONS = ("records", "albums", "media", "sources", "relationships", "source_links")


def content_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _object_id(value: dict[str, Any]) -> str:
    for key in ("id", "album_id", "media_id", "source_id", "relationship_id", "link_id"):
        if isinstance(value.get(key), str) and value[key].startswith("moh:"):
            return value[key]
    raise ValueError("federated object has no stable moh: identifier")


def _version(value: dict[str, Any]) -> int:
    revision = value.get("revision")
    if isinstance(revision, dict) and isinstance(revision.get("version"), int):
        return revision["version"]
    return 1


def _merge_object(store: dict[str, dict[str, Any]], value: dict[str, Any], source_instance: str,
                  conflicts: list[dict[str, Any]], accepted: list[str], unchanged: list[str]) -> None:
    object_id = _object_id(value)
    incoming = deepcopy(value)
    incoming["_federation"] = {
        "source_instance": source_instance,
        "content_hash": content_hash(value),
    }
    current = store.get(object_id)
    if current is None:
        store[object_id] = incoming
        accepted.append(object_id)
        return

    if current.get("_federation", {}).get("content_hash") == content_hash(value):
        unchanged.append(object_id)
        return

    current_version = _version(current)
    incoming_version = _version(incoming)
    if incoming_version > current_version:
        store[object_id] = incoming
        accepted.append(object_id)
        return

    if incoming_version == current_version:
        conflicts.append({
            "object_id": object_id,
            "source_instance": source_instance,
            "reason": "same stable ID has divergent content at the same revision version",
            "existing_hash": current.get("_federation", {}).get("content_hash"),
            "incoming_hash": incoming["_federation"]["content_hash"],
        })
        return

    unchanged.append(object_id)


def apply_sync_response(
    *,
    local: dict[str, Any],
    response: dict[str, Any],
    source_instance: str | None = None,
) -> dict[str, Any]:
    if not isinstance(local, dict):
        raise ValueError("local state must be an object")
    if not isinstance(response, dict):
        raise ValueError("invalid sync response")
    validate_sync_response(response)
    source = source_instance or response.get("source_instance")
    if not isinstance(source, str) or not source.startswith("moh:instance:"):
        raise ValueError("source_instance must be a moh: identifier")

    applied_cursor = _cursor(response.get("next_cursor", ""))
    previous_cursor = _cursor(response.get("since_cursor", ""))
    if applied_cursor < previous_cursor:
        raise ValueError("next_cursor cannot move backwards")

    for collection in COLLECTIONS:
        local.setdefault(collection, [])
    local.setdefault("tombstones", [])
    local.setdefault("provenance_events", [])
    indexes = {
        collection: {
            _object_id(item): item for item in local[collection]
        }
        for collection in COLLECTIONS
    }
    tombstoned = {_object_id(item) if "id" in item else item["record_id"] for item in local["tombstones"]}

    accepted: list[str] = []
    unchanged: list[str] = []
    conflicts: list[dict[str, Any]] = []
    applied_tombstones: list[str] = []
    provenance_events: list[dict[str, Any]] = []

    for change in response.get("changes", []):
        cursor = _cursor(change.get("cursor", ""))
        if cursor <= previous_cursor or cursor > applied_cursor:
            raise ValueError("change cursor is outside response window")
        envelope = change.get("envelope")
        validate_envelope(envelope)
        if envelope["instance_id"] != source:
            raise ValueError("change envelope source does not match response")

        for collection in COLLECTIONS:
            for item in envelope.get(collection, []):
                object_id = _object_id(item)
                if object_id in tombstoned:
                    unchanged.append(object_id)
                    continue
                _merge_object(indexes[collection], item, source, conflicts, accepted, unchanged)

        for tombstone in envelope.get("tombstones", []):
            record_id = tombstone["record_id"]
            if record_id not in tombstoned:
                local["tombstones"].append(deepcopy(tombstone))
                tombstoned.add(record_id)
                applied_tombstones.append(record_id)
            for collection in COLLECTIONS:
                indexes[collection].pop(record_id, None)
            accepted = [item for item in accepted if item != record_id]
            provenance_events.append({
                "event_type": "withdrawn",
                "actor_id": tombstone["issued_by"],
                "source_instance": source,
                "record_id": record_id,
                "cursor": str(cursor),
            })

    for collection in COLLECTIONS:
        local[collection] = sorted(indexes[collection].values(), key=_object_id)

    local["tombstones"] = sorted(local["tombstones"], key=lambda item: item["record_id"])
    local["provenance_events"].extend(provenance_events)
    local["_federation_cursors"] = dict(local.get("_federation_cursors", {}))
    local["_federation_cursors"][source] = str(applied_cursor)

    return {
        "source_instance": source,
        "applied_cursor": str(applied_cursor),
        "accepted": sorted(set(accepted)),
        "unchanged": sorted(set(unchanged)),
        "conflicts": conflicts,
        "tombstones": sorted(set(applied_tombstones)),
        "provenance_events": provenance_events,
    }
