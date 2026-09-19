import pytest
from core.annotations import create_annotation


def test_create_annotation():
    value = create_annotation(
        annotation_id="moh:annotation:a1",
        target="moh:memory:m1",
        annotator_id="moh:person:alice",
        annotation_type="community_note",
        content="Context supplied by the family.",
    )
    assert value["target"] == "moh:memory:m1"


def test_reject_annotation_type():
    with pytest.raises(ValueError):
        create_annotation(
            annotation_id="moh:annotation:a2",
            target="moh:memory:m1",
            annotator_id="alice",
            annotation_type="guess",
            content="X",
        )
