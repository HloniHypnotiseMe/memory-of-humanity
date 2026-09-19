from __future__ import annotations
from typing import Any

REASONS = {"withdrawn", "privacy", "legal_request", "retention_expired", "duplicate", "other"}


def validate_tombstone(tombstone: dict[str, Any]) -> None:
    for field in ("record_id", "issued_by"):
        if not tombstone.get(field, "").startswith("moh:"):
            raise ValueError(f"{field} must be a moh: identifier")
    if tombstone.get("reason") not in REASONS:
        raise ValueError("unsupported tombstone reason")


def create_tombstone(*, record_id: str, reason: str,
                     issued_by: str) -> dict[str, Any]:
    tombstone = {
        "record_id": record_id,
        "reason": reason,
        "issued_by": issued_by,
        "issued_at": None,
        "replacement_id": None,
        "note": None,
    }
    validate_tombstone(tombstone)
    return tombstone
