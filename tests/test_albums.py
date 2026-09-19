import pytest
from core.albums import create_album


def test_create_album():
    album = create_album(album_id="moh:album:family-001", title="Our Family", contributor_id="moh:person:alice")
    assert album["items"] == []


def test_reject_invalid_album_id():
    with pytest.raises(ValueError):
        create_album(album_id="moh:story:x", title="X", contributor_id="alice")
