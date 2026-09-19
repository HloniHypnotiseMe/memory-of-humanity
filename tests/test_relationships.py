import pytest

from core.relationships import create_relationship, validate_relationship


def test_relationship_connects_two_records():
    relation = create_relationship(
        relationship_id="moh:rel:001",
        relationship_type="contradicts",
        source="moh:memory:a",
        target="moh:evidence:b",
    )
    validate_relationship(relation)
    assert relation["type"] == "contradicts"


def test_invalid_relationship_type_is_rejected():
    relation = {
        "id": "moh:rel:002",
        "type": "proves",
        "source": "moh:a",
        "target": "moh:b",
    }
    with pytest.raises(ValueError, match="relationship type"):
        validate_relationship(relation)


def test_invalid_endpoint_is_rejected():
    with pytest.raises(ValueError, match="moh:"):
        create_relationship(
            relationship_id="moh:rel:003",
            relationship_type="supports",
            source="memory:a",
            target="moh:b",
        )
