from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


def read_asset(name: str) -> tuple[bytes, str]:
    allowed = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/styles.css": ("styles.css", "text/css; charset=utf-8")}
    filename, content_type = allowed.get(name, allowed["/"])
    return (WEB_ROOT / filename).read_bytes(), content_type


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


def query_params(path: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(path).query, keep_blank_values=True)
