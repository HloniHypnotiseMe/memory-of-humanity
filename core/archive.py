from __future__ import annotations

from typing import Any


SOURCE_TYPES = {
    "newspaper", "periodical", "book", "manual", "photograph", "map",
    "archive", "oral_archive", "government_record", "other",
}
ACCESS_STATUSES = {"open", "restricted", "subscription", "onsite", "unknown"}


def validate_archive_source(source: dict[str, Any]) -> None:
    required = {"id", "source_type", "title", "provenance", "access"}
    missing = required - source.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(source["id"], str) or not source["id"].startswith("moh:source:"):
        raise ValueError("id must start with moh:source:")
    if source["source_type"] not in SOURCE_TYPES:
        raise ValueError("unsupported source_type")
    if not isinstance(source["title"], str) or not source["title"].strip():
        raise ValueError("title is required")
    provenance = source["provenance"]
    if not isinstance(provenance, dict) or not provenance.get("repository"):
        raise ValueError("provenance.repository is required")
    access = source["access"]
    if not isinstance(access, dict) or access.get("status") not in ACCESS_STATUSES:
        raise ValueError("unsupported access status")


def create_archive_source(
    source_id: str,
    title: str,
    repository: str,
    source_type: str = "newspaper",
    **metadata: Any,
) -> dict[str, Any]:
    source = {
        "id": source_id,
        "source_type": source_type,
        "title": title,
        "provenance": {"repository": repository},
        "access": {"status": metadata.pop("access_status", "unknown")},
        **metadata,
    }
    validate_archive_source(source)
    return source
