import pytest
from core.time import create_time


def test_create_approximate_time():
    value = create_time(time_type="approximate", label="early 1980s", precision="decade")
    assert value["type"] == "approximate"


def test_range_requires_boundary():
    with pytest.raises(ValueError):
        create_time(time_type="range")
