from __future__ import annotations
from typing import Any


def validate_envelope(envelope: dict[str, Any]) -> None:
    required = {"protocol", "envelope_id", "instance_id", "records"}
    missing = required - envelope.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if envelope["protocol"] != "memory-of-humanity":
        raise ValueError("unsupported protocol")
    if not envelope["envelope_id"].startswith("moh:envelope:"):
        raise ValueError("invalid envelope_id")
    if not envelope["instance_id"].startswith("moh:instance:"):
        raise ValueError("invalid instance_id")
    if not isinstance(envelope["records"], list):
        raise ValueError("records must be a list")


def create_envelope(*, envelope_id: str, instance_id: str,
                    records: list[dict[str, Any]]) -> dict[str, Any]:
    envelope = {
        "protocol": "memory-of-humanity",
        "version": "1",
        "envelope_id": envelope_id,
        "instance_id": instance_id,
        "created_at": None,
        "records": records,
        "tombstones": [],
        "signatures": [],
    }
    validate_envelope(envelope)
    return envelope
