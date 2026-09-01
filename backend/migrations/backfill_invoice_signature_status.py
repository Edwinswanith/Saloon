"""
Customer Signature Feature — one-time backfill for pre-existing Invoice documents.

Before this feature shipped, `Invoice` had no `invoice_status`/`signature_status`/
`pdf_status` fields at all. This script sets every pre-existing invoice to
invoice_status='finalized', signature_status='not_required' — so a historical
invoice NEVER reads as "awaiting customer confirmation" or "customer declined
to sign". Matched by the field genuinely being absent (`__exists=False`), not
by a guessed launch date, since the field is unambiguously absent on every
document created before this migration runs.

IMPORTANT ordering requirement: run this once, immediately after deploying the
code that adds these fields, BEFORE any new checkout happens against the new
code. Do not run against a live production database without first backing it
up and testing against a copy — this script is not run automatically on boot
(see backend/app.py's startup migration block for what IS run automatically;
this follows the existing backend/migrations/ convention of manual scripts).

Run: python backend/migrations/backfill_invoice_signature_status.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pymongo import MongoClient
from utils.env_config import load_env, get_mongodb_uri, get_mongodb_db

load_env()
MONGODB_URI = get_mongodb_uri()
MONGODB_DB = get_mongodb_db()


def backfill_invoice_signature_status():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    print(f"Connected to database: {MONGODB_DB}")
    print("=" * 60)

    invoices = db.invoices

    total_missing = invoices.count_documents({'invoice_status': {'$exists': False}})
    print(f"Found {total_missing} invoice(s) missing invoice_status (pre-feature).")

    if total_missing == 0:
        print("Nothing to backfill.")
        return

    result = invoices.update_many(
        {'invoice_status': {'$exists': False}},
        {'$set': {
            'invoice_status': 'finalized',
            'signature_status': 'not_required',
        }}
    )
    print(f"Set invoice_status='finalized', signature_status='not_required' on {result.modified_count} invoice(s).")

    # pdf_status: 'ready' if a PDF is already cached, 'not_generated' otherwise.
    # The existing on-demand-generation fallback already works for the latter —
    # this just makes the status field track what was previously an implicit,
    # untracked behavior.
    ready_result = invoices.update_many(
        {
            'pdf_status': {'$exists': False},
            'pdf_file_id': {'$ne': None, '$exists': True},
        },
        {'$set': {'pdf_status': 'ready'}}
    )
    print(f"Set pdf_status='ready' on {ready_result.modified_count} invoice(s) with an existing cached PDF.")

    not_generated_result = invoices.update_many(
        {'pdf_status': {'$exists': False}},
        {'$set': {'pdf_status': 'not_generated'}}
    )
    print(f"Set pdf_status='not_generated' on {not_generated_result.modified_count} remaining invoice(s).")

    print("=" * 60)
    print("Backfill complete.")


if __name__ == '__main__':
    backfill_invoice_signature_status()
