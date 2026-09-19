from __future__ import annotations
from typing import Any

IDENTITY_KINDS = {"person", "community", "institution"}


def validate_identity(identity: dict[str, Any]) -> None:
    required = {"id", "kind", "display_name"}
    missing = required - identity.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(identity["id"], str) or not identity["id"].startswith("moh:"):
        raise ValueError("id must start with moh:")
    if identity["kind"] not in IDENTITY_KINDS:
        raise ValueError("unsupported identity kind")
    if not isinstance(identity["display_name"], str) or not identity["display_name"].strip():
        raise ValueError("display_name is required")


def create_identity(*, identity_id: str, kind: str,
                    display_name: str) -> dict[str, Any]:
    identity = {
        "id": identity_id,
        "kind": kind,
        "display_name": display_name,
        "description": None,
        "public_key": None,
        "contact": None,
        "created_at": None,
    }
    validate_identity(identity)
    return identity
