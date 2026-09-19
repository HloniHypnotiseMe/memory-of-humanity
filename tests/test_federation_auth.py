from core.federation_auth import create_auth, validate_auth, verify_auth


def test_hmac_federation_auth_round_trip():
    auth = create_auth(secret="a-secret-that-is-long-enough", request_id="moh:sync-request:1", nonce="nonce-1")
    validate_auth(auth)
    assert verify_auth(secret="a-secret-that-is-long-enough", request_id="moh:sync-request:1", auth=auth)
    assert not verify_auth(secret="a-different-secret-long-enough", request_id="moh:sync-request:1", auth=auth)
