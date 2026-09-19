from __future__ import annotations
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
from core.records import create_memory, validate_record
from core.search import search_records
from .store import COLLECTIONS, LOCAL_COLLECTIONS, MemoryStore
from .web import read_asset, query_params


def _id(prefix: str) -> str: return f"moh:{prefix}:{uuid.uuid4().hex}"

class MemoryNode:
    def __init__(self, store: MemoryStore, *, instance_id: str, name: str): self.store,self.instance_id,self.name=store,instance_id,name
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
        envelope=create_envelope(envelope_id=envelope_id,instance_id=self.instance_id,records=records or [],**{k:collections.get(k,[]) for k in COLLECTIONS if k!="tombstones"},tombstones=collections.get("tombstones",[])); return self.store.add_change(envelope)
    def sync(self,request:dict)->dict:
        changes=self.store.changes_after(int(request["since_cursor"]),int(request.get("limit",100))); return incremental_sync(discovery=self.discovery(),request=request,changes=changes)
    def import_response(self,response:dict)->dict:
        local=self.snapshot(); result=apply_sync_response(local=local,response=response)
        for collection in COLLECTIONS:
            for candidate in local[collection]:
                if self.store._id(candidate) in result["accepted"]: self.store.upsert(collection,candidate)
        for tombstone_id in result["tombstones"]:
            for collection in COLLECTIONS: self.store.remove(collection,tombstone_id)
        self.store.set_meta("cursor:"+result["source_instance"],result["applied_cursor"]); return result
    def create_identity(self,body:dict)->dict:
        value=create_identity(identity_id=body.get("id") or _id("person"),kind=body.get("kind","person"),display_name=body["display_name"]); value.update({k:body[k] for k in ("description","contact") if k in body}); validate_identity(value); self.store.upsert("identities",value); return value
    def create_consent(self,body:dict)->dict:
        value=create_consent(consent_id=body.get("id") or _id("consent"),subject_id=body["subject_id"],scope=body.get("scope",["memory_submission"]),status=body.get("status","granted")); validate_consent(value); self.store.upsert("consents",value); return value
    def create_memory(self,body:dict)->dict:
        contributor=body["contributor_id"]
        if not self.store.get("identities",contributor): raise ValueError("contributor identity must exist before submitting a memory")
        value=create_memory(record_id=body.get("id") or _id("memory"),contributor_id=contributor,text=body["text"],record_type=body.get("record_type","personal_memory"),epistemic_status=body.get("epistemic_status","remembered"),created_at=body.get("created_at") or datetime.now(timezone.utc).isoformat())
        self.store.upsert("records",value); self.export_change(envelope_id=_id("envelope"),records=[value]); return value
    def create_album(self,body:dict)->dict:
        value=create_album(album_id=body.get("id") or _id("album"),title=body["title"],contributor_id=body["contributor_id"]); value.update({k:body[k] for k in ("description","items","people","places","time","permissions") if k in body}); validate_album(value); self.store.upsert("albums",value); self.export_change(envelope_id=_id("envelope"),albums=[value]); return value

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
            if path in ("/records","/api/records"): return self._json(200,{"records":self.node.store.get_all("records")})
            if path=="/api/identities": return self._json(200,{"identities":self.node.store.get_all("identities")})
            if path=="/api/albums": return self._json(200,{"albums":self.node.store.get_all("albums")})
            if path=="/api/search":
                result=search_records(self.node.store.get_all("records"),text=(q.get("q") or [""])[0],limit=min(int((q.get("limit") or [20])[0]),100)); return self._json(200,result)
            if path=="/api/place-history":
                place=(q.get("place_id") or [None])[0]
                if not place: raise ValueError("place_id is required")
                result=build_place_history(self.node.store.get_all("records"),self.node.store.get_all("sources"),self.node.store.get_all("relationships"),history_id=_id("place-history"),place_id=place,albums=self.node.store.get_all("albums"),media=self.node.store.get_all("media")); return self._json(200,result)
            return self._json(404,{"error":"not found"})
        except (ValueError,KeyError,TypeError,OverflowError) as exc: return self._json(400,{"error":str(exc)})
    def do_POST(self)->None:
        path=urlparse(self.path).path
        try:
            body=self._body()
            if path=="/federation/sync": return self._json(200,self.node.sync(body))
            if path=="/federation/import": return self._json(200,self.node.import_response(body))
            if path=="/federation/publish": return self._json(201,{"cursor":str(self.node.export_change(**body))})
            if path=="/api/identities": return self._json(201,self.node.create_identity(body))
            if path=="/api/consents": return self._json(201,self.node.create_consent(body))
            if path=="/api/memories": return self._json(201,self.node.create_memory(body))
            if path=="/api/albums": return self._json(201,self.node.create_album(body))
            return self._json(404,{"error":"not found"})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc: return self._json(400,{"error":str(exc)})
    def log_message(self,format:str,*args)->None:return

def serve(*,host:str="127.0.0.1",port:int=8787,db:str="data/memory.db",instance_id:str="moh:instance:local",name:str="Local Memory of Humanity")->None:
    store=MemoryStore(db); node=MemoryNode(store,instance_id=instance_id,name=name); handler=type("MemoryNodeHandler",(Handler,),{"node":node})
    try: ThreadingHTTPServer((host,port),handler).serve_forever()
    finally: store.close()

if __name__=="__main__": serve()
