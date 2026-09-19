from __future__ import annotations

from typing import Any

CONTEXT_TYPES = {"person", "place", "event"}


def validate_context(context: dict[str, Any]) -> None:
    required = {"id", "context_type", "label"}
    missing = required - context.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not isinstance(context["id"], str) or not context["id"].startswith("moh:"):
        raise ValueError("id must start with moh:")
    if context["context_type"] not in CONTEXT_TYPES:
        raise ValueError("unsupported context_type")
    if not isinstance(context["label"], str) or not context["label"].strip():
        raise ValueError("label is required")


def create_context(*, context_id: str, context_type: str, label: str,
                   description: str | None = None) -> dict[str, Any]:
    context = {
        "id": context_id,
        "context_type": context_type,
        "label": label,
        "description": description,
        "aliases": [],
        "time": None,
        "location": None,
        "uncertainty": None,
        "privacy": None,
    }
    validate_context(context)
    return context
