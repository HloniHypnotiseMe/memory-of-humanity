from __future__ import annotations
from typing import Any

EVENT_TYPES = {"created", "revised", "annotated", "exported", "imported", "federated", "withdrawn", "restored"}


def validate_provenance_chain(chain: dict[str, Any]) -> None:
    if not isinstance(chain, dict) or not chain.get("record_id", "").startswith("moh:"):
        raise ValueError("record_id must be a moh: identifier")
    events = chain.get("events")
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    for event in events:
        if event.get("event_type") not in EVENT_TYPES:
            raise ValueError("unsupported provenance event")
        if not event.get("actor_id", "").startswith("moh:"):
            raise ValueError("actor_id must be a moh: identifier")


def create_provenance_chain(*, record_id: str,
                            actor_id: str,
                            event_type: str = "created") -> dict[str, Any]:
    chain = {
        "record_id": record_id,
        "events": [{"event_type": event_type, "actor_id": actor_id, "timestamp": None,
                    "source_instance": None, "details": None}],
    }
    validate_provenance_chain(chain)
    return chain
