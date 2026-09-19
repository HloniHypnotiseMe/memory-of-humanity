from __future__ import annotations
from typing import Any

ANNOTATION_TYPES = {
    "correction", "context", "translation", "transcription",
    "interpretation", "evidence_link", "community_note", "ai_interpretation",
}


def validate_annotation(annotation: dict[str, Any]) -> None:
    required = {"id", "target", "annotator_id", "annotation_type", "content"}
    missing = required - annotation.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if not annotation["id"].startswith("moh:annotation:"):
        raise ValueError("id must start with moh:annotation:")
    if not annotation["target"].startswith("moh:"):
        raise ValueError("target must be a moh: identifier")
    if annotation["annotation_type"] not in ANNOTATION_TYPES:
        raise ValueError("unsupported annotation_type")
    if not annotation["content"].strip():
        raise ValueError("annotation content is required")


def create_annotation(*, annotation_id: str, target: str,
                      annotator_id: str, annotation_type: str,
                      content: str) -> dict[str, Any]:
    annotation = {
        "id": annotation_id,
        "target": target,
        "annotator_id": annotator_id,
        "annotation_type": annotation_type,
        "content": content,
        "created_at": None,
        "supports": None,
        "contradicts": None,
    }
    validate_annotation(annotation)
    return annotation
