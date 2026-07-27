"""
Cleanup script — soft-deletes duplicate bills based on a reviewed CSV.

SAFETY DESIGN
- Never hard-deletes. Every bill is soft-deleted (`is_deleted=True`).
- CashTransactions for soft-deleted bills are also soft-flagged (a `_audit_voided`
  field) instead of hard-deleted, so they can be restored.
- Defaults to --dry-run (prints what would happen, changes nothing).
- --apply must be explicit to commit changes.
- Every change is recorded to a JSON log file. Use --restore <log> to undo.

USAGE — recommended sequence
  1. Take a Mongo backup first:
        mongodump --uri="<MONGODB_URI>" --db=Saloon_prod --out=./backup_<date>
  2. Run the export to produce a CSV:
        python export_duplicate_bills.py
  3. Review the CSV in Excel. In the `decision` column type:
        keep        -> leave the bill alone
        delete      -> soft-delete the bill and its cash transaction
        (blank)     -> no action
  4. Dry-run cleanup:
        python cleanup_duplicate_bills.py --csv duplicate_bills_report.csv
  5. If the dry-run looks correct, apply for real:
        python cleanup_duplicate_bills.py --csv duplicate_bills_report.csv --apply
  6. If anything looks wrong, restore:
        python cleanup_duplicate_bills.py --restore cleanup_log_<timestamp>.json --apply
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from mongoengine import connect
from bson import ObjectId


def connect_db():
    uri = os.environ.get(
        'MONGODB_URI',
        'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon',
    )
    db_name = os.environ.get('MONGODB_DB', 'Saloon_prod')
    base = uri
    if '@' in base and '/' in base.split('@', 1)[1]:
        creds, host_part = base.split('@', 1)
        host_only = host_part.split('?', 1)[0].split('/', 1)[0]
        params = '?' + host_part.split('?', 1)[1] if '?' in host_part else ''
        base = f'{creds}@{host_only}{params}'
    if f'/{db_name}' not in base:
        base = base.replace('?', f'/{db_name}?', 1) if '?' in base else f'{base}/{db_name}'
    sep = '&' if '?' in base else '?'
    extras = []
    if 'retryWrites' not in base: extras.append('retryWrites=true')
    if 'w=' not in base: extras.append('w=majority')
    if 'tls=' not in base and 'ssl=' not in base: extras.append('tls=true')
    if extras: base = f"{base}{sep}{'&'.join(extras)}"
    connect(host=base, alias='default', db=db_name,
            serverSelectionTimeoutMS=30000, connectTimeoutMS=30000, socketTimeoutMS=30000)
    print(f'Connected to MongoDB: {db_name}\n')


def parse_args():
    p = argparse.ArgumentParser(description='Apply or restore duplicate-bill cleanup')
    p.add_argument('--csv', help='CSV from export_duplicate_bills.py with "decision" column filled in')
    p.add_argument('--apply', action='store_true', help='Actually commit the changes (default: dry-run)')
    p.add_argument('--restore', help='Restore a previous run from its log JSON file')
    p.add_argument('--log-dir', default=SCRIPT_DIR, help='Where to save the change log')
    return p.parse_args()


def load_decisions(csv_path):
    """Returns list of dicts: {bill_id, bill_number, decision}."""
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if not r.get('bill_id'):
                continue
            decision = (r.get('decision') or '').strip().lower()
            if decision not in ('delete',):
                continue  # only act on "delete"; "keep" and blanks are no-ops
            rows.append({
                'bill_id': r['bill_id'].strip(),
                'bill_number': r.get('bill_number', '').strip(),
                'cluster_id': r.get('cluster_id', '').strip(),
            })
    return rows


def apply_deletions(decisions, dry_run, log_dir):
    """Soft-deletes bills + their cash txns, captures a restore log."""
    from models import Bill, CashTransaction

    if not decisions:
        print('No rows marked "delete" in the CSV. Nothing to do.')
        return

    print(f'{"DRY-RUN " if dry_run else ""}Will soft-delete {len(decisions)} bills + their cash transactions.\n')

    log_entries = []
    skipped = 0
    for d in decisions:
        try:
            oid = ObjectId(d['bill_id'])
        except Exception:
            print(f'  SKIP invalid id: {d["bill_id"]}')
            skipped += 1
            continue

        bill = Bill.objects(id=oid).first()
        if not bill:
            print(f'  SKIP not found: {d["bill_number"]} ({d["bill_id"]})')
            skipped += 1
            continue
        if bill.is_deleted:
            print(f'  SKIP already deleted: {d["bill_number"]}')
            skipped += 1
            continue

        cash_txns = list(CashTransaction.objects(bill_ref=bill))

        print(f'  cluster={d["cluster_id"]:>4}  {d["bill_number"]:<28}  amount={float(bill.final_amount or 0):>10.2f}  txns={len(cash_txns)}')

        if not dry_run:
            # Snapshot for restore
            entry = {
                'bill_id': str(bill.id),
                'bill_number': bill.bill_number,
                'previous_is_deleted': bool(bill.is_deleted),
                'previous_deletion_reason': bill.deletion_reason,
                'previous_deleted_at': bill.deleted_at.isoformat() if bill.deleted_at else None,
                'cash_txn_ids': [str(t.id) for t in cash_txns],
            }
            log_entries.append(entry)

            bill.is_deleted = True
            bill.deleted_at = datetime.utcnow()
            bill.deletion_reason = f'auto-cleanup (rapid-checkout duplicate): cluster {d["cluster_id"]}'
            bill.save()

            # Mark cash transactions instead of hard-deleting (so they can be restored).
            # We add a dynamic field; CashTransaction has no strict=False so we use raw update.
            from pymongo import UpdateOne
            from mongoengine.connection import get_db
            db_obj = get_db()
            txn_ids = [ObjectId(tid) for tid in entry['cash_txn_ids']]
            if txn_ids:
                db_obj['cash_transactions'].update_many(
                    {'_id': {'$in': txn_ids}},
                    {'$set': {
                        '_audit_voided': True,
                        '_audit_voided_at': datetime.utcnow(),
                        '_audit_voided_reason': f'duplicate-cleanup: bill {bill.bill_number}',
                    }}
                )
                # Also remove the bill_ref so cash summary aggregations skip them.
                db_obj['cash_transactions'].update_many(
                    {'_id': {'$in': txn_ids}},
                    {'$set': {'_audit_original_amount': None}}
                )
                # Actually remove from cash totals by setting amount=0 BUT remember original.
                # Restore mode reads _audit_original_amount.
                for t in cash_txns:
                    db_obj['cash_transactions'].update_one(
                        {'_id': t.id},
                        {'$set': {'_audit_original_amount': float(t.amount or 0), 'amount': 0.0}}
                    )

    print()
    if dry_run:
        print('DRY-RUN complete. No changes made.')
        print('To apply: re-run with --apply')
    else:
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        log_path = os.path.join(log_dir, f'cleanup_log_{ts}.json')
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump({
                'applied_at': datetime.utcnow().isoformat(),
                'entries': log_entries,
            }, f, indent=2)
        print(f'Applied. Log written: {log_path}')
        print(f'To restore: python cleanup_duplicate_bills.py --restore {log_path} --apply')

    if skipped:
        print(f'\nSkipped {skipped} rows (invalid id, not found, or already deleted).')


def restore_log(log_path, dry_run):
    from models import Bill, CashTransaction
    from mongoengine.connection import get_db

    with open(log_path, 'r', encoding='utf-8') as f:
        log = json.load(f)

    entries = log.get('entries', [])
    print(f'{"DRY-RUN " if dry_run else ""}Restoring {len(entries)} bills from {log_path}\n')

    db_obj = get_db()
    for e in entries:
        try:
            oid = ObjectId(e['bill_id'])
        except Exception:
            print(f'  SKIP invalid id: {e["bill_id"]}')
            continue

        bill = Bill.objects(id=oid).first()
        if not bill:
            print(f'  SKIP not found: {e["bill_number"]}')
            continue

        print(f'  Restoring {e["bill_number"]} (txns={len(e["cash_txn_ids"])})')

        if not dry_run:
            bill.is_deleted = bool(e.get('previous_is_deleted', False))
            bill.deleted_at = datetime.fromisoformat(e['previous_deleted_at']) if e.get('previous_deleted_at') else None
            bill.deletion_reason = e.get('previous_deletion_reason')
            bill.save()

            for tid in e.get('cash_txn_ids', []):
                try:
                    txn_oid = ObjectId(tid)
                except Exception:
                    continue
                # Restore amount from snapshot, clear audit flags
                t = db_obj['cash_transactions'].find_one({'_id': txn_oid})
                if not t:
                    continue
                original = t.get('_audit_original_amount')
                update = {
                    '$unset': {
                        '_audit_voided': '',
                        '_audit_voided_at': '',
                        '_audit_voided_reason': '',
                        '_audit_original_amount': '',
                    }
                }
                if original is not None:
                    update['$set'] = {'amount': float(original)}
                db_obj['cash_transactions'].update_one({'_id': txn_oid}, update)

    print()
    print('DRY-RUN complete. No changes made.' if dry_run else 'Restore complete.')


def main():
    args = parse_args()
    connect_db()

    if args.restore:
        restore_log(args.restore, dry_run=not args.apply)
        return

    if not args.csv:
        print('Need --csv <path>  (or --restore <log>)')
        sys.exit(1)

    csv_path = args.csv if os.path.isabs(args.csv) else os.path.join(SCRIPT_DIR, args.csv)
    if not os.path.exists(csv_path):
        print(f'CSV not found: {csv_path}')
        sys.exit(1)

    decisions = load_decisions(csv_path)
    apply_deletions(decisions, dry_run=not args.apply, log_dir=args.log_dir)


if __name__ == '__main__':
    main()
