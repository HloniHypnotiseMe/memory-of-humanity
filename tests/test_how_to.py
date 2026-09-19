import pytest

from core.how_to import create_how_to, validate_how_to


def test_create_how_to_record():
    record = create_how_to(
        record_id="moh:howto:radio-repair",
        title="Valve radio repair",
        knowledge_type="repair",
        contributor_id="moh:person:alice",
    )
    assert record["knowledge_type"] == "repair"


def test_reject_invalid_knowledge_type():
    with pytest.raises(ValueError):
        create_how_to(
            record_id="moh:howto:x",
            title="X",
            knowledge_type="fiction",
            contributor_id="alice",
        )
