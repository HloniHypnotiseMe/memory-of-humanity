from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

RECORD_TYPES = {
    "personal_memory", "oral_history", "story", "cultural_practice",
    "collective_memory", "historical_evidence", "place_memory",
    "artefact", "how_to", "ai_interpretation",
}

EPISTEMIC_STATUSES = {
    "remembered", "reported", "traditional", "observed",
    "documented", "evidenced", "interpreted", "uncertain",
}


def validate_record(record: dict[str, Any]) -> None:
    required = {"id", "record_type", "content", "provenance", "epistemic_status", "revision"}
    missing = required - record.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(record["id"], str) or not record["id"].startswith("moh:"):
        raise ValueError("id must start with moh:")
    if record["record_type"] not in RECORD_TYPES:
        raise ValueError("unsupported record_type")
    if not isinstance(record["content"], dict) or not record["content"].get("text"):
        raise ValueError("content.text is required")
    provenance = record["provenance"]
    if not isinstance(provenance, dict) or not provenance.get("contributor_id"):
        raise ValueError("provenance.contributor_id is required")
    if not provenance.get("created_at"):
        raise ValueError("provenance.created_at is required")
    try:
        datetime.fromisoformat(provenance["created_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("provenance.created_at must be ISO-8601") from exc
    if record["epistemic_status"] not in EPISTEMIC_STATUSES:
        raise ValueError("unsupported epistemic_status")
    revision = record["revision"]
    if not isinstance(revision, dict) or not isinstance(revision.get("version"), int) or revision["version"] < 1:
        raise ValueError("revision.version must be a positive integer")
    previous = revision.get("previous")
    if previous is not None and (not isinstance(previous, str) or not previous.startswith("moh:")):
        raise ValueError("revision.previous must be a moh: identifier or null")
    if "people" in record and not isinstance(record["people"], list):
        raise ValueError("people must be a list")
    if "place_id" in record and record["place_id"] is not None and not str(record["place_id"]).startswith("moh:place:"):
        raise ValueError("place_id must be a moh:place: identifier or null")
    if "time" in record and record["time"] is not None and not isinstance(record["time"], dict):
        raise ValueError("time must be an object or null")
    if "media" in record and not isinstance(record["media"], list):
        raise ValueError("media must be a list")
    if "permissions" in record and record["permissions"] is not None and not isinstance(record["permissions"], dict):
        raise ValueError("permissions must be an object or null")


def create_memory(record_id: str, contributor_id: str, text: str,
                  record_type: str = "personal_memory",
                  epistemic_status: str = "remembered",
                  created_at: str | None = None,
                  place_id: str | None = None,
                  time: dict[str, Any] | None = None,
                  people: list[str] | None = None,
                  media: list[str | dict[str, Any]] | None = None,
                  permissions: dict[str, Any] | None = None) -> dict[str, Any]:
    now = created_at or datetime.now(timezone.utc).isoformat()
    record = {
        "id": record_id,
        "record_type": record_type,
        "content": {"text": text},
        "provenance": {"contributor_id": contributor_id, "created_at": now},
        "epistemic_status": epistemic_status,
        "revision": {"version": 1, "previous": None, "change_type": "original"},
        "place_id": place_id,
        "time": time,
        "people": people or [],
        "media": media or [],
        "permissions": permissions,
    }
    validate_record(record)
    return record


def revise_record(original: dict[str, Any], *, text: str | None = None,
                  contributor_id: str | None = None,
                  change_type: str = "correction") -> dict[str, Any]:
    validate_record(original)
    revised = deepcopy(original)
    revised["revision"] = {
        "version": original["revision"]["version"] + 1,
        "previous": original["id"],
        "change_type": change_type,
    }
    if text is not None:
        revised["content"]["text"] = text
    if contributor_id is not None:
        revised["provenance"]["contributor_id"] = contributor_id
    validate_record(revised)
    return revised
