import pytest
from core.lineage import create_lineage


def test_create_story_lineage():
    lineage = create_lineage(
        lineage_id="moh:lineage:anansi-001",
        source="moh:story:source",
        relationship="retelling",
        target="moh:story:retelling",
        contributor_id="moh:person:alice",
    )
    assert lineage["relationship"] == "retelling"


def test_reject_invalid_lineage_relationship():
    with pytest.raises(ValueError):
        create_lineage(
            lineage_id="moh:lineage:x",
            source="moh:story:a",
            relationship="invented",
            contributor_id="alice",
        )
