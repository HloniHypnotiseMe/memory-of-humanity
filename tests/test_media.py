import pytest

from core.media import create_media, validate_media


def test_create_media_reference():
    record = create_media(
        media_id="moh:media:photo-001",
        media_type="image",
        content_hash="sha256:abc12345",
        contributor_id="moh:person:alice",
    )
    assert record["media_type"] == "image"


def test_reject_invalid_media_type():
    with pytest.raises(ValueError):
        create_media(
            media_id="moh:media:x",
            media_type="unknown",
            content_hash="sha256:abc12345",
            contributor_id="alice",
        )
