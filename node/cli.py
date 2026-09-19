from __future__ import annotations
import argparse
from .server import MemoryNode, serve
from .store import MemoryStore
from .demo import seed_demo

def main() -> None:
    parser=argparse.ArgumentParser(description="Run a Memory of Humanity reference node.")
    parser.add_argument("--host",default="127.0.0.1"); parser.add_argument("--port",type=int,default=8787)
    parser.add_argument("--db",default="data/memory.db"); parser.add_argument("--instance-id",default="moh:instance:local")
    parser.add_argument("--name",default="Local Memory of Humanity")
    parser.add_argument("--seed-demo",action="store_true",help="seed the clearly labelled synthetic Johannesburg demonstration corpus before serving")
    args=parser.parse_args()
    if args.seed_demo:
        store=MemoryStore(args.db)
        try: print(seed_demo(MemoryNode(store,instance_id=args.instance_id,name=args.name)))
        finally: store.close()
    serve(host=args.host,port=args.port,db=args.db,instance_id=args.instance_id,name=args.name)

if __name__=="__main__":
    main()
