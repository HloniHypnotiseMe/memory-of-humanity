from __future__ import annotations
from typing import Any

CONSENT_STATUSES = {"granted", "withdrawn", "expired", "unknown", "not_applicable"}


def validate_consent(consent: dict[str, Any]) -> None:
    required = {"id", "subject_id", "scope", "status"}
    missing = required - consent.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not consent["id"].startswith("moh:consent:"):
        raise ValueError("id must start with moh:consent:")
    if not consent["subject_id"].startswith("moh:"):
        raise ValueError("subject_id must be a moh: identifier")
    if not isinstance(consent["scope"], list):
        raise ValueError("scope must be a list")
    if consent["status"] not in CONSENT_STATUSES:
        raise ValueError("unsupported consent status")


def create_consent(*, consent_id: str, subject_id: str,
                   scope: list[str], status: str) -> dict[str, Any]:
    consent = {
        "id": consent_id,
        "subject_id": subject_id,
        "scope": scope,
        "status": status,
        "granted_by": None,
        "created_at": None,
        "expires_at": None,
    }
    validate_consent(consent)
    return consent
