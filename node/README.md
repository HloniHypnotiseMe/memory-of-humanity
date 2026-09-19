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
