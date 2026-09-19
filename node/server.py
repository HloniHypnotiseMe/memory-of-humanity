from __future__ import annotations
import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from core.albums import create_album, validate_album
from core.consent import create_consent, validate_consent
from core.federation import create_envelope, validate_envelope
from core.federation_discovery import create_discovery
from core.federation_import import apply_sync_response
from core.federation_sync import incremental_sync
from core.identity import create_identity, validate_identity
from core.place_history import build_place_history
from core.media import create_media, validate_media
from core.records import create_memory, validate_record, revise_record
from core.tombstones import create_tombstone, validate_tombstone
from core.search import search_records
from .store import COLLECTIONS, LOCAL_COLLECTIONS, MemoryStore
from .media_store import MediaBlobStore
from core.album_explorer import explore_album
from .web import read_asset, query_params


def _id(prefix: str) -> str: return f"moh:{prefix}:{uuid.uuid4().hex}"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _provenance_event(*, event_type: str, actor_id: str, record_id: str,
                      source_instance: str | None = None, details: dict | None = None) -> dict:
    return {
        "id": _id("provenance:event"),
        "record_id": record_id,
        "event_type": event_type,
        "actor_id": actor_id,
        "timestamp": _now(),
        "source_instance": source_instance,
        "details": details,
    }

def _publicly_visible(value: dict) -> bool:
    permissions = value.get("permissions")
    if not isinstance(permissions, dict):
        return True
    visibility = permissions.get("visibility", "public")
    if visibility == "public":
        return True
    if visibility != "sealed":
        return False
    sealed_until = permissions.get("sealed_until")
    if not sealed_until:
        return False
    try:
        return datetime.fromisoformat(sealed_until.replace("Z", "+00:00")) <= datetime.now(timezone.utc)
    except ValueError:
        return False

def _public_records(values: list[dict]) -> list[dict]:
    return [value for value in values if _publicly_visible(value)]

def _public_albums(values: list[dict]) -> list[dict]:
    return [value for value in values if _publicly_visible(value)]

class MemoryNode:
    def __init__(self, store: MemoryStore, *, instance_id: str, name: str, media_root: str = "data/media"): self.store,self.instance_id,self.name,self.media=store,instance_id,name,MediaBlobStore(media_root)
    def discovery(self)->dict:
        record_types=sorted({r.get("record_type") for r in self.store.get_all("records") if r.get("record_type")})
        return create_discovery(instance_id=self.instance_id,name=self.name,current_cursor=self.store.current_cursor(),record_types=record_types,visibility=["public"],endpoints=[{"rel":"discovery","method":"GET","path":"/federation/discovery"},{"rel":"sync","method":"POST","path":"/federation/sync"}])
    def snapshot(self)->dict: return {c:self.store.get_all(c) for c in COLLECTIONS}
    def ingest_envelope(self,envelope:dict)->dict:
        validate_envelope(envelope)
        if envelope["instance_id"]!=self.instance_id: raise ValueError("envelope instance_id does not match this node")
        for c in COLLECTIONS:
            for item in envelope.get(c,[]): self.store.upsert(c,item)
        return envelope
    def export_change(self,*,envelope_id:str,records:list[dict]|None=None,**collections)->int:
        envelope=create_envelope(envelope_id=envelope_id,instance_id=self.instance_id,records=records or [],**{k:collections.get(k,[]) for k in COLLECTIONS if k not in {"records","tombstones"}},tombstones=collections.get("tombstones",[])); return self.store.add_change(envelope)
    def sync(self,request:dict)->dict:
        changes=self.store.changes_after(int(request["since_cursor"]),int(request.get("limit",100))); return incremental_sync(discovery=self.discovery(),request=request,changes=changes)
    def import_response(self,response:dict)->dict:
        local=self.snapshot()
        result=apply_sync_response(local=local,response=response)
        accepted=set(result["accepted"])
        for collection in COLLECTIONS:
            for candidate in local[collection]:
                if self.store._id(candidate) in accepted:
                    self.store.upsert(collection,candidate)
        for tombstone_id in result["tombstones"]:
            for collection in COLLECTIONS:
                self.store.remove(collection,tombstone_id)
        for tombstone in local.get("tombstones", []):
            if tombstone["record_id"] in result["tombstones"]:
                self.store.upsert("tombstones",tombstone)
        self.store.set_meta("cursor:"+result["source_instance"],result["applied_cursor"])
        for conflict in result.get("conflicts", []):
            stored = dict(conflict)
            stored["id"] = _id("federation:conflict")
            self.store.upsert("federation_conflicts", stored)
        for event in result.get("provenance_events", []):
            event = dict(event)
            event["id"] = _id("provenance:event")
            self.store.upsert("provenance_events", event)
        for object_id in result.get("accepted", []):
            self.add_provenance_event(event_type="imported", actor_id=result["source_instance"], record_id=object_id, source_instance=result["source_instance"])
        return result
    def sync_peer(self,request:dict,fetcher)->dict:
        discovery=fetcher("GET","/federation/discovery",None)
        if discovery.get("instance_id") != request.get("peer_instance_id"):
            raise ValueError("peer discovery identity mismatch")
        response=fetcher("POST","/federation/sync",request)
        return self.import_response(response)

    def add_provenance_event(self, *, event_type: str, actor_id: str, record_id: str,
                            source_instance: str | None = None, details: dict | None = None) -> dict:
        event = _provenance_event(event_type=event_type, actor_id=actor_id, record_id=record_id,
                                  source_instance=source_instance, details=details)
        self.store.upsert("provenance_events", event)
        return event

    def peers(self) -> list[dict]:
        return self.store.get_all("peers")

    def conflicts(self) -> list[dict]:
        return self.store.get_all("federation_conflicts")

    def add_peer(self, body: dict) -> dict:
        peer_id = body.get("id") or _id("peer")
        instance_id = body["instance_id"]
        url = body["url"].rstrip("/")
        if not peer_id.startswith("moh:peer:"):
            raise ValueError("peer id must start with moh:peer:")
        if not instance_id.startswith("moh:instance:"):
            raise ValueError("instance_id must start with moh:instance:")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("peer url must use http:// or https://")
        value = {"id": peer_id, "instance_id": instance_id, "url": url,
                 "name": body.get("name") or instance_id, "enabled": bool(body.get("enabled", True))}
        self.store.upsert("peers", value)
        return value

    def sync_configured_peer(self, peer_id: str) -> dict:
        peer = self.store.get("peers", peer_id)
        if not peer or not peer.get("enabled"):
            raise ValueError("configured peer not found or disabled")
        peer_url = peer["url"].rstrip("/") + "/"
        import urllib.request
        from urllib.parse import urljoin

        def fetcher(method, endpoint, payload):
            data = json.dumps(payload).encode() if payload is not None else None
            request = urllib.request.Request(
                urljoin(peer_url, endpoint.lstrip("/")),
                data=data, method=method,
                headers={"Content-Type": "application/json"} if data else {},
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.loads(response.read())

        request = {
            "request_id": _id("sync-request"),
            "protocol": "memory-of-humanity",
            "peer_instance_id": peer["instance_id"],
            "since_cursor": self.store.get_meta("cursor:" + peer["instance_id"], "0") or "0",
            "limit": 100, "visibility": ["public"], "known_ids": [],
        }
        result = self.sync_peer(request, fetcher)
        return {"peer": peer, "request": request, "result": result}

    def create_identity(self,body:dict)->dict:
        value=create_identity(identity_id=body.get("id") or _id("person"),kind=body.get("kind","person"),display_name=body["display_name"]); value.update({k:body[k] for k in ("description","contact") if k in body}); validate_identity(value); self.store.upsert("identities",value); return value
    def create_consent(self,body:dict)->dict:
        value=create_consent(consent_id=body.get("id") or _id("consent"),subject_id=body["subject_id"],scope=body.get("scope",["memory_submission"]),status=body.get("status","granted")); validate_consent(value); self.store.upsert("consents",value); return value
    def create_memory(self,body:dict)->dict:
        contributor=body["contributor_id"]
        if not self.store.get("identities",contributor): raise ValueError("contributor identity must exist before submitting a memory")
        value=create_memory(
            record_id=body.get("id") or _id("memory"), contributor_id=contributor,
            text=body["text"], record_type=body.get("record_type","personal_memory"),
            epistemic_status=body.get("epistemic_status","remembered"),
            created_at=body.get("created_at") or datetime.now(timezone.utc).isoformat(),
            place_id=body.get("place_id"), time=body.get("time"), people=body.get("people"),
            media=body.get("media"), permissions=body.get("permissions"))
        self.store.upsert("records",value); self.export_change(envelope_id=_id("envelope"),records=[value]); self.add_provenance_event(event_type="created", actor_id=contributor, record_id=value["id"], details={"revision": value["revision"]["version"]}); return value
    def revise_memory(self,record_id:str,body:dict)->dict:
        original=self.store.get("records",record_id)
        if not original: raise ValueError("memory not found")
        contributor=body.get("contributor_id") or original["provenance"]["contributor_id"]
        if not self.store.get("identities",contributor): raise ValueError("contributor identity must exist before revising a memory")
        revised=revise_record(original,text=body.get("text"),contributor_id=contributor,change_type=body.get("change_type","correction"))
        self.store.upsert("records",revised)
        self.export_change(envelope_id=_id("envelope"),records=[revised])
        self.add_provenance_event(event_type="revised", actor_id=contributor, record_id=record_id, details={"revision": revised["revision"]["version"], "change_type": revised["revision"].get("change_type")})
        return revised

    def withdraw_memory(self,record_id:str,body:dict)->dict:
        original=self.store.get("records",record_id)
        if not original: raise ValueError("memory not found")
        issued_by=body.get("issued_by") or original["provenance"]["contributor_id"]
        tombstone=create_tombstone(record_id=record_id,reason=body.get("reason","withdrawn"),issued_by=issued_by)
        tombstone["issued_at"]=datetime.now(timezone.utc).isoformat()
        if body.get("replacement_id"): tombstone["replacement_id"]=body["replacement_id"]
        if body.get("note"): tombstone["note"]=body["note"]
        validate_tombstone(tombstone)
        self.store.upsert("tombstones",tombstone)
        self.store.remove("records",record_id)
        self.export_change(envelope_id=_id("envelope"),tombstones=[tombstone])
        self.add_provenance_event(event_type="withdrawn", actor_id=issued_by, record_id=record_id, details={"reason": tombstone["reason"]})
        return tombstone

    def create_media(self,body:dict)->dict:
        contributor=body["contributor_id"]
        if not self.store.get("identities",contributor): raise ValueError("contributor identity must exist before uploading media")
        raw=base64.b64decode(body["data_base64"],validate=True)
        content_hash=body.get("content_hash") or hashlib.sha256(raw).hexdigest()
        value=create_media(media_id=body.get("id") or _id("media"),media_type=body["media_type"],content_hash=content_hash,contributor_id=contributor,source_uri=body.get("source_uri"))
        for key in ("mime_type","captured_at","location","derivative_of","rights"):
            if key in body: value[key]=body[key]
        validate_media(value)
        self.media.put(raw,content_hash)
        self.store.upsert("media",value); self.export_change(envelope_id=_id("envelope"),media=[value]); self.add_provenance_event(event_type="created", actor_id=contributor, record_id=value["id"], details={"media": True}); return value

    def media_bytes(self,media_id:str)->tuple[dict,bytes]:
        value=self.store.get("media",media_id)
        if not value: raise ValueError("media not found")
        return value,self.media.get(value["content_hash"])

    def explore_album(self,album_id:str)->dict:
        album=self.store.get("albums",album_id)
        if not album: raise ValueError("album not found")
        if not _publicly_visible(album): raise ValueError("album not publicly available")
        return explore_album(album,records=self.store.get_all("records"),media=self.store.get_all("media"),relationships=self.store.get_all("relationships"),lineage=(),exploration_id=_id("album-exploration"))

    def create_album(self,body:dict)->dict:
        if not self.store.get("identities",body["contributor_id"]): raise ValueError("contributor identity must exist before creating an album")
        value=create_album(album_id=body.get("id") or _id("album"),title=body["title"],contributor_id=body["contributor_id"]); value.update({k:body[k] for k in ("description","items","people","places","time","permissions") if k in body}); validate_album(value); self.store.upsert("albums",value); self.export_change(envelope_id=_id("envelope"),albums=[value]); self.add_provenance_event(event_type="created", actor_id=body["contributor_id"], record_id=value["id"], details={"album": True}); return value

class Handler(BaseHTTPRequestHandler):
    node:MemoryNode
    def _json(self,status:int,payload:dict)->None:
        data=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def _body(self)->dict:
        length=int(self.headers.get("Content-Length","0")); return json.loads(self.rfile.read(length) or b"{}")
    def _serve_asset(self,path:str)->None:
        data,ctype=read_asset(path); self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self)->None:
        path=urlparse(self.path).path; q=query_params(self.path)
        try:
            if path in ("/","/app.js","/styles.css"): return self._serve_asset(path)
            if path=="/health": return self._json(200,{"ok":True,"protocol":"memory-of-humanity","instance_id":self.node.instance_id})
            if path in ("/federation/discovery","/api/discovery"): return self._json(200,self.node.discovery())
            if path == "/api/peers": return self._json(200, {"peers": self.node.peers()})
            if path == "/api/federation/conflicts": return self._json(200, {"conflicts": self.node.conflicts()})
            if path in ("/records","/api/records"): return self._json(200,{"records":_public_records(self.node.store.get_all("records"))})
            if path=="/api/identities": return self._json(200,{"identities":self.node.store.get_all("identities")})
            if path=="/api/consents": return self._json(200,{"consents":self.node.store.get_all("consents")})
            if path=="/api/albums": return self._json(200,{"albums":_public_albums(self.node.store.get_all("albums"))})
            if path.startswith("/api/albums/") and path.endswith("/explore"): return self._json(200,self.node.explore_album(path.split("/")[3]))
            if path=="/api/search":
                result=search_records(_public_records(self.node.store.get_all("records")),text=(q.get("q") or [""])[0],limit=min(int((q.get("limit") or [20])[0]),100)); return self._json(200,result)
            if path=="/api/media/": raise ValueError("media id is required")
            if path.startswith("/media/"):
                value,data=self.node.media_bytes(path.split("/")[2])
                if not _publicly_visible(value): return self._json(404,{"error":"media not publicly available"})
                self.send_response(200); self.send_header("Content-Type",value.get("mime_type","application/octet-stream")); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data); return
            if path=="/api/place-history":
                place=(q.get("place_id") or [None])[0]
                if not place: raise ValueError("place_id is required")
                result=build_place_history(self.node.store.get_all("records"),self.node.store.get_all("sources"),self.node.store.get_all("relationships"),history_id=_id("place-history"),place_id=place,start=(q.get("start") or [None])[0],end=(q.get("end") or [None])[0],albums=_public_albums(self.node.store.get_all("albums")),media=[m for m in self.node.store.get_all("media") if _publicly_visible(m)]); return self._json(200,result)
            return self._json(404,{"error":"not found"})
        except (ValueError,KeyError,TypeError,OverflowError) as exc: return self._json(400,{"error":str(exc)})
    def do_POST(self)->None:
        path=urlparse(self.path).path
        try:
            body=self._body()
            if path=="/federation/sync": return self._json(200,self.node.sync(body))
            if path=="/federation/import": return self._json(200,self.node.import_response(body))
            if path=="/federation/publish": return self._json(201,{"cursor":str(self.node.export_change(**body))})
            if path=="/federation/sync-peer":
                return self._json(200,self.node.sync_configured_peer(body["peer_id"]))
            if path=="/api/peers": return self._json(201,self.node.add_peer(body))
            if path=="/api/peers/sync": return self._json(200,self.node.sync_configured_peer(body["peer_id"]))
            if path=="/api/identities": return self._json(201,self.node.create_identity(body))
            if path=="/api/consents": return self._json(201,self.node.create_consent(body))
            if path=="/api/memories": return self._json(201,self.node.create_memory(body))
            if path=="/api/media": return self._json(201,self.node.create_media(body))
            if path.startswith("/api/memories/") and path.endswith("/revise"):
                return self._json(200,self.node.revise_memory(path.split("/")[3],body))
            if path.startswith("/api/memories/") and path.endswith("/withdraw"):
                return self._json(200,self.node.withdraw_memory(path.split("/")[3],body))
            if path=="/api/albums": return self._json(201,self.node.create_album(body))
            return self._json(404,{"error":"not found"})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc: return self._json(400,{"error":str(exc)})
    def log_message(self,format:str,*args)->None:return

def serve(*,host:str="127.0.0.1",port:int=8787,db:str="data/memory.db",instance_id:str="moh:instance:local",name:str="Local Memory of Humanity")->None:
    store=MemoryStore(db); node=MemoryNode(store,instance_id=instance_id,name=name); handler=type("MemoryNodeHandler",(Handler,),{"node":node})
    try: ThreadingHTTPServer((host,port),handler).serve_forever()
    finally: store.close()

if __name__=="__main__": serve()
