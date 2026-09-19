from node.media_store import MAX_MEDIA_BYTES, MediaBlobStore
import pytest


def test_media_store_is_content_addressed_and_verified(tmp_path):
    store = MediaBlobStore(tmp_path)
    data = b"memory bytes"
    import hashlib
    digest = hashlib.sha256(data).hexdigest()
    path = store.put(data, digest)
    assert path.name == digest
    assert store.get(digest) == data


def test_media_store_rejects_hash_mismatch(tmp_path):
    store = MediaBlobStore(tmp_path)
    with pytest.raises(ValueError, match="content_hash"):
        store.put(b"memory bytes", "00000000")


def test_media_store_rejects_oversize(tmp_path):
    store = MediaBlobStore(tmp_path)
    with pytest.raises(ValueError, match="25 MiB"):
        store.put(b"x" * (MAX_MEDIA_BYTES + 1), "00000000")
