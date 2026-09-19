from __future__ import annotations
import argparse
from .server import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Memory of Humanity reference node.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--db", default="data/memory.db")
    parser.add_argument("--instance-id", default="moh:instance:local")
    parser.add_argument("--name", default="Local Memory of Humanity")
    args = parser.parse_args()
    serve(host=args.host, port=args.port, db=args.db, instance_id=args.instance_id, name=args.name)


if __name__ == "__main__":
    main()
