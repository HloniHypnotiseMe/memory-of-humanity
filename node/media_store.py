from __future__ import annotations

import hashlib
from pathlib import Path

MAX_MEDIA_BYTES = 25 * 1024 * 1024

class MediaBlobStore:
    def __init__(self, root: str | Path = "data/media"):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes, content_hash: str) -> Path:
        if len(data) > MAX_MEDIA_BYTES: raise ValueError("media exceeds 25 MiB reference-node limit")
        actual = hashlib.sha256(data).hexdigest()
        if actual != content_hash: raise ValueError("content_hash does not match uploaded bytes")
        path = self.root / content_hash
        if not path.exists(): path.write_bytes(data)
        return path

    def get(self, content_hash: str) -> bytes:
        return (self.root / content_hash).read_bytes()
