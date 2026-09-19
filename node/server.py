from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from core.federation import create_envelope, validate_envelope
from core.federation_discovery import create_discovery
from core.federation_import import apply_sync_response
from core.federation_sync import create_sync_request, incremental_sync
from .store import COLLECTIONS, MemoryStore


class MemoryNode:
    def __init__(self, store: MemoryStore, *, instance_id: str, name: str):
        self.store = store
        self.instance_id = instance_id
        self.name = name

    def discovery(self) -> dict:
        record_types = sorted({record.get("record_type") for record in self.store.get_all("records") if record.get("record_type")})
        return create_discovery(
            instance_id=self.instance_id,
            name=self.name,
            current_cursor=self.store.current_cursor(),
            record_types=record_types,
            visibility=["public"],
            endpoints=[
                {"rel": "discovery", "method": "GET", "path": "/federation/discovery"},
                {"rel": "sync", "method": "POST", "path": "/federation/sync"},
            ],
        )

    def snapshot(self) -> dict:
        return {collection: self.store.get_all(collection) for collection in COLLECTIONS}

    def ingest_envelope(self, envelope: dict) -> dict:
        validate_envelope(envelope)
        if envelope["instance_id"] != self.instance_id:
            raise ValueError("envelope instance_id does not match this node")
        for collection in COLLECTIONS:
            for item in envelope.get(collection, []):
                self.store.upsert(collection, item)
        return envelope

    def export_change(self, *, envelope_id: str, records: list[dict] | None = None, **collections) -> int:
        envelope = create_envelope(
            envelope_id=envelope_id,
            instance_id=self.instance_id,
            records=records or [],
            **{key: collections.get(key, []) for key in COLLECTIONS if key != "tombstones"},
            tombstones=collections.get("tombstones", []),
        )
        return self.store.add_change(envelope)

    def sync(self, request: dict) -> dict:
        discovery = self.discovery()
        changes = self.store.changes_after(int(request["since_cursor"]), int(request.get("limit", 100)))
        return incremental_sync(discovery=discovery, request=request, changes=changes)

    def import_response(self, response: dict) -> dict:
        local = self.snapshot()
        local["_federation_cursors"] = {
            key: self.store.get_meta("cursor:" + key, "0") for key in []
        }
        result = apply_sync_response(local=local, response=response)
        for collection in COLLECTIONS:
            for item in result["accepted"]:
                for candidate in local[collection]:
                    try:
                        object_id = self.store._id(candidate)
                    except ValueError:
                        continue
                    if object_id == item:
                        self.store.upsert(collection, candidate)
        for tombstone_id in result["tombstones"]:
            for collection in COLLECTIONS:
                self.store.remove(collection, tombstone_id)
        source = result["source_instance"]
        self.store.set_meta("cursor:" + source, result["applied_cursor"])
        return result


class Handler(BaseHTTPRequestHandler):
    node: MemoryNode

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            return self._json(200, {"ok": True, "protocol": "memory-of-humanity", "instance_id": self.node.instance_id})
        if path == "/federation/discovery":
            return self._json(200, self.node.discovery())
        if path == "/records":
            return self._json(200, {"records": self.node.store.get_all("records")})
        return self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._body()
            if path == "/federation/sync":
                return self._json(200, self.node.sync(body))
            if path == "/federation/import":
                return self._json(200, self.node.import_response(body))
            if path == "/federation/publish":
                cursor = self.node.export_change(**body)
                return self._json(201, {"cursor": str(cursor)})
            return self._json(404, {"error": "not found"})
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})

    def log_message(self, format: str, *args) -> None:
        return


def serve(*, host: str = "127.0.0.1", port: int = 8787, db: str = "data/memory.db",
          instance_id: str = "moh:instance:local", name: str = "Local Memory of Humanity") -> None:
    store = MemoryStore(db)
    node = MemoryNode(store, instance_id=instance_id, name=name)
    handler = type("MemoryNodeHandler", (Handler,), {"node": node})
    try:
        ThreadingHTTPServer((host, port), handler).serve_forever()
    finally:
        store.close()


if __name__ == "__main__":
    serve()
