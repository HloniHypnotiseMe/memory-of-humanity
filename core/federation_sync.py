from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .federation import validate_envelope
from .federation_auth import validate_auth
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
    if "auth" in request:
        validate_auth(request["auth"])


def create_sync_request(
    *,
    request_id: str,
    peer_instance_id: str,
    since_cursor: str = "0",
    limit: int = 100,
    visibility: list[str] | None = None,
    known_ids: list[str] | None = None,
    auth: dict[str, Any] | None = None,
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
    if auth is not None:
        request["auth"] = auth
    validate_sync_request(request)
    return request



def _federation_allowed(value: dict[str, Any], requested_visibility: set[str]) -> bool:
    permissions = value.get("permissions")
    if not isinstance(permissions, dict):
        return "public" in requested_visibility
    visibility = permissions.get("visibility", "public")
    if visibility not in requested_visibility:
        return False
    if permissions.get("allow_federation") is False:
        return False
    if visibility == "sealed":
        sealed_until = permissions.get("sealed_until")
        if not sealed_until:
            return False
        try:
            return datetime.fromisoformat(sealed_until.replace("Z", "+00:00")) <= datetime.now(timezone.utc)
        except ValueError:
            return False
    return visibility == "public"

def _filter_envelope(envelope: dict[str, Any], requested_visibility: set[str]) -> dict[str, Any]:
    filtered = deepcopy(envelope)
    for collection in ("records", "albums", "media"):
        filtered[collection] = [item for item in envelope.get(collection, []) if _federation_allowed(item, requested_visibility)]
    visible_ids = {
        item.get("id") for collection in ("records", "albums", "media", "sources")
        for item in filtered.get(collection, [])
        if isinstance(item, dict)
    }
    filtered["relationships"] = [
        item for item in envelope.get("relationships", [])
        if item.get("source") in visible_ids and item.get("target") in visible_ids
    ]
    filtered["source_links"] = [
        item for item in envelope.get("source_links", [])
        if item.get("record_id") in visible_ids and item.get("source_id") in visible_ids
    ]
    return filtered

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
        filtered_envelope = _filter_envelope(envelope, set(request.get("visibility", ["public"])))
        selected.append({"cursor": str(cursor), "envelope": filtered_envelope})
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


def validate_sync_response(response: dict[str, Any]) -> None:
    required = {"response_id", "protocol", "source_instance", "since_cursor", "next_cursor", "changes"}
    missing = required - response.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if response["protocol"] != "memory-of-humanity":
        raise ValueError("unsupported protocol")
    if not response["response_id"].startswith("moh:sync-response:"):
        raise ValueError("invalid response_id")
    if not response["source_instance"].startswith("moh:instance:"):
        raise ValueError("invalid source_instance")
    since = _cursor(response["since_cursor"])
    next_cursor = _cursor(response["next_cursor"])
    if next_cursor < since:
        raise ValueError("next_cursor cannot move backwards")
    if not isinstance(response["changes"], list):
        raise ValueError("changes must be a list")
    previous = since
    for change in response["changes"]:
        cursor = _cursor(change.get("cursor", ""))
        if cursor <= previous or cursor > next_cursor:
            raise ValueError("change cursors must be ordered within response window")
        envelope = change.get("envelope")
        if not isinstance(envelope, dict):
            raise ValueError("change must contain an envelope")
        validate_envelope(envelope)
        if envelope["instance_id"] != response["source_instance"]:
            raise ValueError("change envelope source does not match response")
        previous = cursor
