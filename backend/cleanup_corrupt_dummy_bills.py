"""One-off: hard-delete corrupt bills in Dummy Branch left over from the
push__items__each bug. These bills have items stored as a dict instead of a
list, so MongoEngine can't load them — the normal soft-delete endpoint 500s.

Scoped strictly to the Dummy Branch + bills whose items field is not a list.
Default is dry-run; pass --confirm to actually delete.
"""
import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.env_config import load_env, get_mongodb_uri, get_mongodb_db
from pymongo import MongoClient
from setup_dummy_branch import build_mongo_uri


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="actually delete (default: dry-run)")
    args = parser.parse_args()
load_env()
uri = get_mongodb_uri()
    db_name = os.environ.get("MONGODB_DB", "Saloon_prod")

    client = MongoClient(build_mongo_uri(uri, db_name))
    db = client[db_name]

    dummy = db.branches.find_one({"name": "Dummy Branch"})
    if not dummy:
        print("Dummy Branch not found — nothing to do.")
        return

    print(f"DB: {db_name}  Dummy Branch: {dummy['_id']}")
    print(f"Mode: {'LIVE DELETE' if args.confirm else 'DRY RUN'}\n")

    # Find bills whose items field is not a list — those are the corrupt ones.
    candidates = list(db.bills.find({
        "branch": dummy["_id"],
        "items": {"$not": {"$type": "array"}},
    }))

    if not candidates:
        print("No corrupt bills found in Dummy Branch.")
        client.close()
        return

    print(f"Found {len(candidates)} corrupt bill(s) in Dummy Branch:")
    for b in candidates:
        items = b.get("items")
        print(f"  - {b.get('bill_number')}  id={b['_id']}  items_type={type(items).__name__}")

    if not args.confirm:
        print("\n[dry-run] Re-run with --confirm to hard-delete these bills.")
        client.close()
        return

    ids = [b["_id"] for b in candidates]
    result = db.bills.delete_many({"_id": {"$in": ids}})
    print(f"\nDeleted {result.deleted_count} bill(s).")

    client.close()


if __name__ == "__main__":
    main()
