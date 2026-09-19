from __future__ import annotations
from typing import Any

VISIBILITIES = {"public", "private", "community", "trusted_custodian", "sealed"}


def validate_permissions(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("visibility") not in VISIBILITIES:
        raise ValueError("unsupported visibility")
    if value["visibility"] == "sealed" and value.get("sealed_until") is None:
        raise ValueError("sealed records require sealed_until")


def create_permissions(*, visibility: str,
                        allow_annotation: bool = True,
                        allow_derivatives: bool = False,
                        allow_federation: bool = False,
                        allow_export: bool = True) -> dict[str, Any]:
    value = {
        "visibility": visibility,
        "allow_annotation": allow_annotation,
        "allow_derivatives": allow_derivatives,
        "allow_federation": allow_federation,
        "allow_export": allow_export,
        "sealed_until": None,
        "retention": None,
        "notes": None,
    }
    validate_permissions(value)
    return value
