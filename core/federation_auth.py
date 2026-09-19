from __future__ import annotations

import hashlib
import hmac
from typing import Any


AUTH_METHOD = "hmac-sha256"


def create_auth(*, secret: str, request_id: str, nonce: str) -> dict[str, str]:
    message = f"{request_id}:{nonce}".encode("utf-8")
    mac = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return {"method": AUTH_METHOD, "nonce": nonce, "mac": mac}


def validate_auth(auth: dict[str, Any]) -> None:
    if not isinstance(auth, dict):
        raise ValueError("auth must be an object")
    if auth.get("method") != AUTH_METHOD:
        raise ValueError("unsupported federation auth method")
    if not isinstance(auth.get("nonce"), str) or not auth["nonce"]:
        raise ValueError("auth.nonce is required")
    if not isinstance(auth.get("mac"), str) or len(auth["mac"]) != 64:
        raise ValueError("auth.mac must be a SHA-256 hex digest")


def verify_auth(*, secret: str, request_id: str, auth: dict[str, Any]) -> bool:
    validate_auth(auth)
    expected = create_auth(secret=secret, request_id=request_id, nonce=auth["nonce"])["mac"]
    return hmac.compare_digest(expected, auth["mac"])
