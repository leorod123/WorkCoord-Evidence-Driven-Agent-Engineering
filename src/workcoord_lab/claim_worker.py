"""One test-only SQLite client process.

This module uses synthetic work IDs and never accesses operational systems.
"""
import json
import os
import sys
import time
from pathlib import Path
from .ledger import GateError, Ledger


def main():
    mode, database = sys.argv[1:3]
    if mode == "compete":
        _, _, _, agent, ready, start = sys.argv
        db = Ledger(database)
        try:
            Path(ready).touch()
            deadline = time.monotonic() + 12
            while not Path(start).exists():
                if time.monotonic() >= deadline:
                    raise RuntimeError("test start flag timeout")
                time.sleep(0.005)
            try:
                generation = db.claim("one", agent, 1, 100)
                result = {"status": "CLAIMED", "generation": generation}
            except GateError:
                result = {"status": "REJECTED"}
            print(json.dumps(result), flush=True)
        finally:
            db.close()
        return
    db = Ledger(database)
    if mode == "abort-before-commit":
        db.db.execute("BEGIN IMMEDIATE")
        db.db.execute(
            "UPDATE work SET status='CLAIMED', owner='ghost',generation=777,expires=99 WHERE id='one'"
        )
        os._exit(17)  # Deliberately no COMMIT; SQLite must roll back.
    if mode == "abort-after-commit":
        db.claim("one", "ghost", 1, 20)
        os._exit(18)  # The transaction committed, even if the caller heard nothing.
    raise RuntimeError("unknown test worker mode")


if __name__ == "__main__":
    main()
