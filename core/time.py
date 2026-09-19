from __future__ import annotations

from typing import Any

TIME_TYPES = {"instant", "range", "period", "approximate", "unknown"}
PRECISIONS = {"day", "month", "year", "decade", "century", "unknown"}


def validate_time(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("type") not in TIME_TYPES:
        raise ValueError("unsupported time type")
    precision = value.get("precision")
    if precision is not None and precision not in PRECISIONS:
        raise ValueError("unsupported time precision")
    if value.get("type") == "range" and not value.get("start") and not value.get("end"):
        raise ValueError("range requires start or end")


def create_time(*, time_type: str, start: str | None = None,
                end: str | None = None, label: str | None = None,
                precision: str | None = None) -> dict[str, Any]:
    value = {
        "type": time_type,
        "start": start,
        "end": end,
        "label": label,
        "precision": precision,
        "calendar": None,
    }
    validate_time(value)
    return value
