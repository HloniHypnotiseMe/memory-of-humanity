# Reference Node

This is the minimal runnable reference node for the protocol.

## Run

From the repository root:

    python -m node.cli --port 8787

Then:

    GET  /health
    GET  /federation/discovery
    GET  /records
    POST /federation/publish
    POST /federation/sync
    POST /federation/import

The node uses SQLite by default. The database is implementation storage; stable IDs, provenance and protocol records remain portable.

The HTTP layer is intentionally small and transport-specific concerns are kept outside the protocol contracts.


## Configured federation peers

Register a peer locally before syncing:

    POST /api/peers

Example body:

    {"id":"moh:peer:archive","instance_id":"moh:instance:archive","url":"http://127.0.0.1:8788","name":"Archive","shared_secret":"use-a-random-secret-of-at-least-16-characters"}

Then:

    POST /api/peers/sync
    {"peer_id":"moh:peer:archive"}

The node fetches the peer discovery document, verifies the advertised instance ID matches the configured identity, requests incremental changes from the last stored cursor, validates the response, and imports only changes permitted by the public federation profile.

Inspect:

    GET /api/peers
    GET /api/federation/conflicts

Private/community/trusted-custodian records are not exported through the public federation profile. Same-version divergent content is retained as a conflict rather than overwritten.

## Reference-node security boundary

The node is a protocol reference implementation, not a production internet service. It has no built-in user authentication, TLS termination, cryptographic peer signatures, rate limiting, or administrator authorization. Put those controls at the deployment boundary before exposing a node to untrusted networks.


If a shared secret is configured, outgoing sync requests use HMAC-SHA256 and the receiving node verifies the request before exporting its configured public changes. The secret is never returned by `GET /api/peers`. Keep it outside source control and use HTTPS for real deployments.
