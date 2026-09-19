import pytest
from core.timeline import create_timeline


def test_create_timeline():
    value = create_timeline(
        timeline_id="moh:timeline:jhb",
        subject_id="moh:place:johannesburg",
        items=[{"record_id": "moh:memory:m1"}],
    )
    assert value["subject_id"] == "moh:place:johannesburg"


def test_reject_invalid_subject():
    with pytest.raises(ValueError):
        create_timeline(timeline_id="moh:timeline:x", subject_id="alice", items=[])
