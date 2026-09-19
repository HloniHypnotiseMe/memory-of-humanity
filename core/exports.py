from __future__ import annotations
from typing import Any


def validate_manifest(manifest: dict[str, Any]) -> None:
    required = {"manifest_id", "protocol", "records"}
    missing = required - manifest.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if manifest["protocol"] != "memory-of-humanity":
        raise ValueError("unsupported protocol")
    if not manifest["manifest_id"].startswith("moh:manifest:"):
        raise ValueError("invalid manifest_id")
    if not isinstance(manifest["records"], list):
        raise ValueError("records must be a list")


def create_manifest(*, manifest_id: str,
                    records: list[str]) -> dict[str, Any]:
    manifest = {
        "manifest_id": manifest_id,
        "protocol": "memory-of-humanity",
        "version": "1",
        "created_at": None,
        "source_instance": None,
        "records": records,
        "media": [],
        "checksums": {},
        "notes": None,
    }
    validate_manifest(manifest)
    return manifest
