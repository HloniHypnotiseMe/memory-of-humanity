from __future__ import annotations
from typing import Any

from .federation import validate_envelope
from .federation_discovery import VISIBILITIES, validate_discovery


def _cursor(value: str) -> int:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError("cursor must be a non-negative numeric string")
    return int(value)


def validate_sync_request(request: dict[str, Any]) -> None:
    required = {"request_id", "protocol", "peer_instance_id", "since_cursor"}
    missing = required - request.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if request["protocol"] != "memory-of-humanity":
        raise ValueError("unsupported protocol")
    if not request["request_id"].startswith("moh:sync-request:"):
        raise ValueError("invalid request_id")
    if not request["peer_instance_id"].startswith("moh:instance:"):
        raise ValueError("invalid peer_instance_id")
    _cursor(request["since_cursor"])
    limit = request.get("limit", 100)
    if not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if not set(request.get("visibility", ["public"])).issubset(VISIBILITIES):
        raise ValueError("unsupported visibility")
    if not all(isinstance(value, str) and value.startswith("moh:") for value in request.get("known_ids", [])):
        raise ValueError("known_ids must contain moh: identifiers")


def create_sync_request(
    *,
    request_id: str,
    peer_instance_id: str,
    since_cursor: str = "0",
    limit: int = 100,
    visibility: list[str] | None = None,
    known_ids: list[str] | None = None,
) -> dict[str, Any]:
    request = {
        "request_id": request_id,
        "protocol": "memory-of-humanity",
        "peer_instance_id": peer_instance_id,
        "since_cursor": str(since_cursor),
        "limit": limit,
        "visibility": visibility or ["public"],
        "known_ids": known_ids or [],
    }
    validate_sync_request(request)
    return request


def incremental_sync(
    *,
    discovery: dict[str, Any],
    request: dict[str, Any],
    changes: list[dict[str, Any]],
) -> dict[str, Any]:
    validate_discovery(discovery)
    validate_sync_request(request)
    if request["peer_instance_id"] != discovery["instance_id"]:
        raise ValueError("request peer does not match discovery instance")

    since = _cursor(request["since_cursor"])
    limit = request.get("limit", 100)
    ordered = sorted(changes, key=lambda item: _cursor(item["cursor"]))
    selected: list[dict[str, Any]] = []

    for change in ordered:
        cursor = _cursor(change.get("cursor", ""))
        if cursor <= since:
            continue
        envelope = change.get("envelope")
        if not isinstance(envelope, dict):
            raise ValueError("each change must contain an envelope")
        validate_envelope(envelope)
        if envelope["instance_id"] != discovery["instance_id"]:
            raise ValueError("change envelope belongs to another instance")
        selected.append({"cursor": str(cursor), "envelope": envelope})
        if len(selected) >= limit:
            break

    next_cursor = str(_cursor(selected[-1]["cursor"])) if selected else str(since)
    current = _cursor(discovery["current_cursor"])
    has_more = next_cursor != str(current) and _cursor(next_cursor) < current

    return {
        "response_id": "moh:sync-response:" + request["request_id"].split(":", 2)[-1],
        "protocol": "memory-of-humanity",
        "source_instance": discovery["instance_id"],
        "since_cursor": str(since),
        "next_cursor": next_cursor,
        "has_more": has_more,
        "changes": selected,
    }
