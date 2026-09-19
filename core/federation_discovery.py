from __future__ import annotations
from typing import Any

from .records import RECORD_TYPES

VISIBILITIES = {"public", "private", "community", "trusted_custodian", "sealed"}


def validate_discovery(manifest: dict[str, Any]) -> None:
    required = {"instance_id", "protocol", "protocol_version", "name", "capabilities", "current_cursor"}
    missing = required - manifest.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if manifest["protocol"] != "memory-of-humanity":
        raise ValueError("unsupported protocol")
    if not manifest["instance_id"].startswith("moh:instance:"):
        raise ValueError("invalid instance_id")
    if not isinstance(manifest["capabilities"], dict):
        raise ValueError("capabilities must be an object")
    for key in ("discovery", "incremental_sync"):
        if not isinstance(manifest["capabilities"].get(key), bool):
            raise ValueError(f"capabilities.{key} must be a boolean")
    if not str(manifest["current_cursor"]).isdigit():
        raise ValueError("current_cursor must be a non-negative numeric string")
    if not isinstance(manifest.get("record_types", []), list):
        raise ValueError("record_types must be a list")
    unknown = set(manifest.get("record_types", [])) - RECORD_TYPES
    if unknown:
        raise ValueError(f"unsupported record types: {sorted(unknown)}")
    if not set(manifest.get("visibility", ["public"])).issubset(VISIBILITIES):
        raise ValueError("unsupported visibility")


def create_discovery(
    *,
    instance_id: str,
    name: str,
    current_cursor: str = "0",
    protocol_version: str = "1",
    description: str | None = None,
    operator: str | None = None,
    contact: str | None = None,
    endpoints: list[dict[str, Any]] | None = None,
    record_types: list[str] | None = None,
    visibility: list[str] | None = None,
    coverage: dict[str, Any] | None = None,
    updated_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = {
        "instance_id": instance_id,
        "protocol": "memory-of-humanity",
        "protocol_version": protocol_version,
        "name": name,
        "description": description,
        "operator": operator,
        "contact": contact,
        "endpoints": endpoints or [],
        "capabilities": {
            "discovery": True,
            "incremental_sync": True,
            "federation": True,
            "search": True,
            "historical_exploration": True,
        },
        "record_types": record_types or [],
        "visibility": visibility or ["public"],
        "coverage": coverage or {},
        "current_cursor": str(current_cursor),
        "updated_at": updated_at,
        "metadata": metadata or {},
    }
    validate_discovery(manifest)
    return manifest


def discover_instances(
    manifests: list[dict[str, Any]],
    *,
    capability: str | None = None,
    record_type: str | None = None,
    visibility: str | None = None,
) -> list[dict[str, Any]]:
    """Return matching peer manifests without requiring a central registry."""
    matches: list[dict[str, Any]] = []
    for manifest in manifests:
        validate_discovery(manifest)
        if capability is not None and manifest["capabilities"].get(capability) is not True:
            continue
        if record_type is not None and record_type not in manifest.get("record_types", []):
            continue
        if visibility is not None and visibility not in manifest.get("visibility", []):
            continue
        matches.append(manifest)
    return sorted(matches, key=lambda item: item["instance_id"])
