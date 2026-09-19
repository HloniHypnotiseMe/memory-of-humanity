from __future__ import annotations

from typing import Any, Iterable

from .records import validate_record


def search_records(
    records: Iterable[dict[str, Any]],
    text: str | None = None,
    record_types: set[str] | None = None,
    epistemic_statuses: set[str] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be positive")

    query_text = (text or "").strip().casefold()
    all_records = list(records)
    for record in all_records:
        validate_record(record)

    results: list[dict[str, Any]] = []
    for record in all_records:
        if record_types and record["record_type"] not in record_types:
            continue
        if epistemic_statuses and record["epistemic_status"] not in epistemic_statuses:
            continue

        content = record.get("content", {})
        searchable = {
            "text": str(content.get("text", "")),
            "title": str(content.get("title", "")),
            "description": str(content.get("description", "")),
            "language": str(content.get("language", "")),
        }
        haystack = " ".join(searchable.values()).casefold()

        if query_text and query_text not in haystack:
            continue

        matched_fields = [
            field for field, value in searchable.items()
            if query_text and query_text in value.casefold()
        ]

        score = 1.0 if not query_text else sum(
            1.0 for field in matched_fields if field == "text"
        ) + 0.5 * sum(
            1.0 for field in matched_fields if field != "text"
        )

        results.append({
            "id": record["id"],
            "record_type": record["record_type"],
            "epistemic_status": record["epistemic_status"],
            "score": score,
            "matched_fields": matched_fields,
            "record": record,
        })

    results.sort(key=lambda item: (-item["score"], item["id"]))
    return {"query": {
        "text": text,
        "record_types": sorted(record_types) if record_types else [],
        "epistemic_statuses": sorted(epistemic_statuses) if epistemic_statuses else [],
        "limit": limit,
    }, "results": results[:limit]}
