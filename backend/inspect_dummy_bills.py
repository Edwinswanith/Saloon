"""One-off diagnostic — read-only. Inspect the recent bills in Dummy Branch via raw PyMongo."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.env_config import load_env, get_mongodb_uri, get_mongodb_db
from pymongo import MongoClient
from setup_dummy_branch import build_mongo_uri
load_env()
mongo_uri = get_mongodb_uri()
mongo_db = os.environ.get("MONGODB_DB", "Saloon_prod")

client = MongoClient(build_mongo_uri(mongo_uri, mongo_db))
db = client[mongo_db]

dummy = db.branches.find_one({"name": "Dummy Branch"})
print(f"Dummy Branch: {dummy['_id']}\n")

print("--- last 5 bills in Dummy Branch (raw doc) ---")
for b in db.bills.find({"branch": dummy["_id"], "is_deleted": {"$ne": True}}).sort("created_at", -1).limit(5):
    print(f"\nbill={b.get('bill_number')}  id={b['_id']}")
    print(f"  created_at={b.get('created_at')}  booking_status={b.get('booking_status')}  payment={b.get('payment_mode')}")
    print(f"  subtotal={b.get('subtotal')}  final={b.get('final_amount')}")
    items = b.get("items")
    print(f"  items field type: {type(items).__name__}, len={len(items) if hasattr(items, '__len__') else 'n/a'}")
    if isinstance(items, list):
        for i, it in enumerate(items):
            print(f"    [{i}] type={type(it).__name__}  value={repr(it)[:200]}")

client.close()
