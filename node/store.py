from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any

COLLECTIONS = ("records", "albums", "media", "sources", "relationships", "source_links", "tombstones")
LOCAL_COLLECTIONS = ("identities", "consents", "provenance_events", "peers")

class MemoryStore:
    def __init__(self, path: str | Path = "data/memory.db"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE IF NOT EXISTS objects (collection TEXT NOT NULL, object_id TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(collection, object_id))")
        self.db.execute("CREATE TABLE IF NOT EXISTS changes (cursor INTEGER PRIMARY KEY AUTOINCREMENT, envelope TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.db.commit()

    def close(self) -> None: self.db.close()
    def _id(self, value: dict[str, Any]) -> str:
        for key in ("id", "album_id", "media_id", "source_id", "relationship_id", "link_id"):
            if isinstance(value.get(key), str) and value[key].startswith("moh:"): return value[key]
        if isinstance(value.get("record_id"), str) and value["record_id"].startswith("moh:"): return value["record_id"]
        raise ValueError("object has no stable moh: identifier")
    def get_all(self, collection: str) -> list[dict[str, Any]]:
        rows=self.db.execute("SELECT payload FROM objects WHERE collection=? ORDER BY object_id",(collection,)).fetchall(); return [json.loads(r["payload"]) for r in rows]
    def get(self, collection: str, object_id: str) -> dict[str, Any] | None:
        row=self.db.execute("SELECT payload FROM objects WHERE collection=? AND object_id=?",(collection,object_id)).fetchone(); return json.loads(row["payload"]) if row else None
    def upsert(self, collection: str, value: dict[str, Any]) -> None:
        oid=self._id(value); self.db.execute("INSERT INTO objects(collection,object_id,payload) VALUES(?,?,?) ON CONFLICT(collection,object_id) DO UPDATE SET payload=excluded.payload",(collection,oid,json.dumps(value,sort_keys=True,ensure_ascii=False))); self.db.commit()
    def remove(self, collection: str, object_id: str) -> None: self.db.execute("DELETE FROM objects WHERE collection=? AND object_id=?",(collection,object_id)); self.db.commit()
    def add_change(self, envelope: dict[str, Any]) -> int:
        cur=self.db.execute("INSERT INTO changes(envelope) VALUES(?)",(json.dumps(envelope,sort_keys=True,ensure_ascii=False),)); self.db.commit(); return int(cur.lastrowid)
    def changes_after(self, cursor: int, limit: int = 100) -> list[dict[str, Any]]:
        rows=self.db.execute("SELECT cursor,envelope FROM changes WHERE cursor>? ORDER BY cursor LIMIT ?",(cursor,limit)).fetchall(); return [{"cursor":str(r["cursor"]),"envelope":json.loads(r["envelope"])} for r in rows]
    def current_cursor(self) -> str:
        row=self.db.execute("SELECT COALESCE(MAX(cursor),0) AS cursor FROM changes").fetchone(); return str(row["cursor"])
    def set_meta(self,key:str,value:str)->None: self.db.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,value)); self.db.commit()
    def get_meta(self,key:str,default:str|None=None)->str|None:
        row=self.db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone(); return row["value"] if row else default
