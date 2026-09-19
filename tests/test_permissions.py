import pytest
from core.permissions import create_permissions


def test_public_permissions():
    value = create_permissions(visibility="public")
    assert value["visibility"] == "public"


def test_sealed_requires_date():
    with pytest.raises(ValueError):
        create_permissions(visibility="sealed")
