"""
Read-only cash register audit script.

Finds:
  1. Duplicate bills — same customer + same final_amount + bill_date within a short window
                       (created by rapid Checkout double-clicks before today's guard)
  2. Bills whose CashTransaction.amount doesn't match Bill.final_amount
                       (likely a bill edit after checkout)
  3. Bills missing a CashTransaction entirely (checkout or save failed silently)
  4. Orphan CashTransactions whose bill_ref no longer exists in the bills collection

Usage:
    cd backend
    python audit_cash_register.py                   # default: last 90 days, all branches
    python audit_cash_register.py --days 30
    python audit_cash_register.py --branch <branch_id>
    python audit_cash_register.py --start-date 2026-04-01 --end-date 2026-05-01

Nothing is written. The script only reads and prints.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, date as date_type

# Ensure UTF-8 output on Windows consoles (default cp1252 chokes on ₹ etc.)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Make sure project root is on sys.path so `models` resolves
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from utils.env_config import load_env, get_mongodb_uri, get_mongodb_db

from mongoengine import connect
from bson import ObjectId


def connect_db():
    uri = os.environ.get(
        'MONGODB_URI',
        'get_mongodb_uri()',
    )
    db_name = os.environ.get('MONGODB_DB', 'Saloon_prod')

    base = uri
    if '@' in base and '/' in base.split('@', 1)[1]:
        creds, host_part = base.split('@', 1)
        host_only = host_part.split('?', 1)[0].split('/', 1)[0]
        params = ''
        if '?' in host_part:
            params = '?' + host_part.split('?', 1)[1]
        base = f'{creds}@{host_only}{params}'
    if f'/{db_name}' not in base:
        base = base.replace('?', f'/{db_name}?', 1) if '?' in base else f'{base}/{db_name}'
    sep = '&' if '?' in base else '?'
    extras = []
    if 'retryWrites' not in base:
        extras.append('retryWrites=true')
    if 'w=' not in base:
        extras.append('w=majority')
    if 'tls=' not in base and 'ssl=' not in base:
        extras.append('tls=true')
    if extras:
        base = f"{base}{sep}{'&'.join(extras)}"

    connect(host=base, alias='default', db=db_name,
            serverSelectionTimeoutMS=30000, connectTimeoutMS=30000, socketTimeoutMS=30000)
    print(f'✓ Connected to MongoDB: {db_name}\n')


def fmt_currency(amount: float) -> str:
    try:
        return f"₹{float(amount or 0):,.2f}"
    except Exception:
        return f"₹{amount}"


def fmt_bill_id(bill) -> str:
    try:
        return f"{getattr(bill, 'bill_number', None) or '?'} (id={bill.id})"
    except Exception:
        return '?'


def parse_args():
    parser = argparse.ArgumentParser(description='Audit cash register vs. bills')
    parser.add_argument('--days', type=int, default=90,
                        help='How many days back to scan (default: 90)')
    parser.add_argument('--start-date', help='YYYY-MM-DD (overrides --days)')
    parser.add_argument('--end-date', help='YYYY-MM-DD (overrides --days)')
    parser.add_argument('--branch', help='Limit to a single branch_id')
    parser.add_argument('--window-seconds', type=int, default=120,
                        help='Duplicate-bill detection window in seconds (default: 120)')
    return parser.parse_args()


def get_date_range(args):
    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, '%Y-%m-%d')
        end = datetime.strptime(args.end_date, '%Y-%m-%d').replace(
            hour=23, minute=59, second=59, microsecond=999999)
    else:
        end = datetime.utcnow()
        start = end - timedelta(days=args.days)
    return start, end


def section(title: str):
    print('\n' + '=' * 78)
    print(f'  {title}')
    print('=' * 78)


# ---------------------------------------------------------------------------
# Check 1: Duplicate bills (same customer + same final_amount + close in time)
# ---------------------------------------------------------------------------
def check_duplicate_bills(Bill, start, end, branch_id, window_seconds):
    section(f'1. DUPLICATE BILLS (within {window_seconds}s window)')

    query = {
        'is_deleted__ne': True,
        'bill_date__gte': start,
        'bill_date__lte': end,
    }
    if branch_id:
        query['branch'] = ObjectId(branch_id)

    bills = list(Bill.objects(**query).only(
        'id', 'bill_number', 'customer', 'branch', 'final_amount', 'bill_date'
    ).order_by('bill_date'))

    # Bucket by (customer_id, rounded final_amount)
    groups = defaultdict(list)
    for b in bills:
        cust_id = None
        try:
            raw_cust = b._data.get('customer')
            if raw_cust is not None:
                cust_id = str(raw_cust.id) if hasattr(raw_cust, 'id') else str(raw_cust)
        except Exception:
            cust_id = None
        if not cust_id:
            continue  # walk-ins without a customer aren't reliable signals
        amt = round(float(b.final_amount or 0), 2)
        if amt <= 0:
            continue
        groups[(cust_id, amt)].append(b)

    duplicate_groups = []
    duplicate_extra_total = 0.0
    for key, group in groups.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda x: x.bill_date or datetime.min)
        # Walk through chronologically; flag any pair within window
        i = 0
        while i < len(group):
            cluster = [group[i]]
            j = i + 1
            while j < len(group):
                gap = (group[j].bill_date - cluster[-1].bill_date).total_seconds()
                if gap <= window_seconds:
                    cluster.append(group[j])
                    j += 1
                else:
                    break
            if len(cluster) >= 2:
                duplicate_groups.append(cluster)
                # Conservative excess: every bill beyond the first is "extra"
                duplicate_extra_total += sum(float(b.final_amount or 0) for b in cluster[1:])
            i = j if j > i + 1 else i + 1

    if not duplicate_groups:
        print('  None found in scanned range.\n')
        return 0, 0.0

    for g in duplicate_groups:
        cust_id, amt = (str(g[0]._data.get('customer')) if g[0]._data.get('customer') else 'walk-in'), float(g[0].final_amount or 0)
        print(f'\n  Customer {cust_id}, amount {fmt_currency(amt)}, {len(g)} bills:')
        for b in g:
            print(f'      - {fmt_bill_id(b)}  bill_date={b.bill_date}  final={fmt_currency(b.final_amount)}')

    print(f'\n  Total: {len(duplicate_groups)} duplicate clusters; '
          f'{sum(len(g) - 1 for g in duplicate_groups)} extra bills; '
          f'inflated cash total ≈ {fmt_currency(duplicate_extra_total)}')
    return len(duplicate_groups), duplicate_extra_total


# ---------------------------------------------------------------------------
# Check 2: Bill.final_amount != CashTransaction.amount (post-checkout edits)
# ---------------------------------------------------------------------------
def check_amount_mismatch(Bill, CashTransaction, start, end, branch_id):
    section('2. BILL ↔ CASH TRANSACTION AMOUNT MISMATCH')

    query = {
        'is_deleted__ne': True,
        'bill_date__gte': start,
        'bill_date__lte': end,
        'final_amount__gt': 0,
    }
    if branch_id:
        query['branch'] = ObjectId(branch_id)

    bills = list(Bill.objects(**query).only(
        'id', 'bill_number', 'final_amount', 'payment_mode', 'booking_status'
    ))

    if not bills:
        print('  No bills in range.\n')
        return 0, 0.0

    bill_ids = [b.id for b in bills]
    txn_by_bill = defaultdict(list)
    for t in CashTransaction.objects(bill_ref__in=bill_ids, transaction_type='in').only(
            'id', 'bill_ref', 'amount', 'payment_method', 'transaction_date'):
        raw = t._data.get('bill_ref')
        bid = raw.id if hasattr(raw, 'id') else raw
        txn_by_bill[bid].append(t)

    mismatches = []
    for b in bills:
        # Skip bills that aren't in service-completed state — they may not have a txn yet
        if (b.booking_status or '') != 'service-completed':
            continue
        txns = txn_by_bill.get(b.id, [])
        if not txns:
            continue  # caught by the "missing" check below
        total_recorded = sum(float(t.amount or 0) for t in txns)
        bill_amt = float(b.final_amount or 0)
        if abs(total_recorded - bill_amt) > 0.5:  # half-rupee tolerance
            mismatches.append((b, txns, total_recorded))

    if not mismatches:
        print('  None — all bills match their cash transactions.\n')
        return 0, 0.0

    drift_total = 0.0
    for b, txns, recorded in mismatches:
        delta = recorded - float(b.final_amount or 0)
        drift_total += delta
        print(f'\n  {fmt_bill_id(b)}: bill={fmt_currency(b.final_amount)}  '
              f'cash_txn_total={fmt_currency(recorded)}  delta={fmt_currency(delta)}')
        for t in txns:
            print(f'      txn_id={t.id}  date={t.transaction_date}  '
                  f'amount={fmt_currency(t.amount)}  method={t.payment_method}')

    print(f'\n  Total: {len(mismatches)} bills with mismatched amounts; '
          f'net drift = {fmt_currency(drift_total)}')
    return len(mismatches), drift_total


# ---------------------------------------------------------------------------
# Check 3: Service-completed bills with no CashTransaction
# ---------------------------------------------------------------------------
def check_missing_transactions(Bill, CashTransaction, start, end, branch_id):
    section('3. CHECKED-OUT BILLS WITH NO CASH TRANSACTION')

    query = {
        'is_deleted__ne': True,
        'booking_status': 'service-completed',
        'bill_date__gte': start,
        'bill_date__lte': end,
        'final_amount__gt': 0,
    }
    if branch_id:
        query['branch'] = ObjectId(branch_id)

    bills = list(Bill.objects(**query).only(
        'id', 'bill_number', 'final_amount', 'payment_mode', 'bill_date'
    ))

    if not bills:
        print('  No checked-out bills in range.\n')
        return 0, 0.0

    bill_ids_with_txn = set()
    for t in CashTransaction.objects(bill_ref__in=[b.id for b in bills]).only('bill_ref'):
        raw = t._data.get('bill_ref')
        bid = raw.id if hasattr(raw, 'id') else raw
        if bid:
            bill_ids_with_txn.add(bid)

    missing = [b for b in bills if b.id not in bill_ids_with_txn]
    if not missing:
        print('  None — every checked-out bill has a cash transaction.\n')
        return 0, 0.0

    missing_total = 0.0
    for b in missing:
        amt = float(b.final_amount or 0)
        missing_total += amt
        print(f'  {fmt_bill_id(b)}  bill_date={b.bill_date}  '
              f'final={fmt_currency(amt)}  payment={b.payment_mode or "?"}')

    print(f'\n  Total: {len(missing)} bills missing cash entries; '
          f'unrecorded cash ≈ {fmt_currency(missing_total)}')
    return len(missing), missing_total


# ---------------------------------------------------------------------------
# Check 4: Orphan CashTransactions (bill_ref points to a deleted/missing bill)
# ---------------------------------------------------------------------------
def check_orphan_transactions(Bill, CashTransaction, start, end, branch_id):
    section('4. ORPHAN CASH TRANSACTIONS (bill_ref missing)')

    start_date = start.date() if isinstance(start, datetime) else start
    end_date = end.date() if isinstance(end, datetime) else end

    query = {
        'transaction_date__gte': start_date,
        'transaction_date__lte': end_date,
        'source': 'bill',
    }
    if branch_id:
        query['branch'] = ObjectId(branch_id)

    txns = list(CashTransaction.objects(**query).only(
        'id', 'bill_ref', 'amount', 'transaction_date', 'payment_method'))

    if not txns:
        print('  No bill-sourced cash transactions in range.\n')
        return 0, 0.0

    bill_ids = list({t._data.get('bill_ref') if hasattr(t._data.get('bill_ref'), 'id') is False
                     else t._data.get('bill_ref').id
                     for t in txns if t._data.get('bill_ref') is not None})
    bill_ids = [b for b in bill_ids if b]

    existing = set()
    if bill_ids:
        for b in Bill.objects(id__in=bill_ids).only('id'):
            existing.add(b.id)

    orphans = []
    for t in txns:
        raw = t._data.get('bill_ref')
        if raw is None:
            continue  # bill_ref absent entirely — not an orphan, just a manual entry mistagged
        bid = raw.id if hasattr(raw, 'id') else raw
        if bid not in existing:
            orphans.append((t, bid))

    if not orphans:
        print('  None — every bill-sourced txn points at a real bill.\n')
        return 0, 0.0

    orphan_total = 0.0
    for t, bid in orphans:
        amt = float(t.amount or 0)
        orphan_total += amt
        print(f'  txn_id={t.id}  date={t.transaction_date}  '
              f'amount={fmt_currency(amt)}  method={t.payment_method}  '
              f'dangling_bill_ref={bid}')

    print(f'\n  Total: {len(orphans)} orphan transactions; '
          f'phantom cash ≈ {fmt_currency(orphan_total)}')
    return len(orphans), orphan_total


def main():
    args = parse_args()
    connect_db()

    # Import after connection so MongoEngine resolves correctly
    from models import Bill, CashTransaction, Branch  # noqa: F401

    start, end = get_date_range(args)
    print(f'  Scanning {start.date()} → {end.date()}'
          + (f' for branch {args.branch}' if args.branch else ' (all branches)'))

    n_dup, dup_amt = check_duplicate_bills(Bill, start, end, args.branch, args.window_seconds)
    n_mis, mis_amt = check_amount_mismatch(Bill, CashTransaction, start, end, args.branch)
    n_missing, missing_amt = check_missing_transactions(Bill, CashTransaction, start, end, args.branch)
    n_orph, orph_amt = check_orphan_transactions(Bill, CashTransaction, start, end, args.branch)

    section('SUMMARY')
    print(f'  Duplicate bill clusters       : {n_dup:4d}   inflated cash ≈ {fmt_currency(dup_amt)}')
    print(f'  Amount-mismatched bills       : {n_mis:4d}   net drift     ≈ {fmt_currency(mis_amt)}')
    print(f'  Bills missing cash txn        : {n_missing:4d}   unrecorded    ≈ {fmt_currency(missing_amt)}')
    print(f'  Orphan cash transactions      : {n_orph:4d}   phantom cash  ≈ {fmt_currency(orph_amt)}')
    print('\n  (Read-only run. Nothing has been changed.)\n')


if __name__ == '__main__':
    main()
