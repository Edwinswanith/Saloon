"""
Read-only export of every duplicate-bill cluster found in the database.

Produces a CSV at `duplicate_bills_report.csv` with one row per bill, grouped
by cluster. The owner / accountant reviews this file and decides which bills
to keep / delete. Use `cleanup_duplicate_bills.py` afterwards to apply
decisions.

Usage:
    cd backend
    python export_duplicate_bills.py                          # last 90 days, all branches
    python export_duplicate_bills.py --days 30
    python export_duplicate_bills.py --start-date 2026-01-01 --end-date 2026-05-05
    python export_duplicate_bills.py --output review.csv

This script reads only — no data is modified.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

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
    p = argparse.ArgumentParser(description='Export duplicate bills to a review CSV')
    p.add_argument('--days', type=int, default=90)
    p.add_argument('--start-date')
    p.add_argument('--end-date')
    p.add_argument('--branch')
    p.add_argument('--window-seconds', type=int, default=120,
                   help='Time window for grouping bills as duplicates (default 120)')
    p.add_argument('--output', default='duplicate_bills_report.csv')
    return p.parse_args()


def main():
    args = parse_args()
    connect_db()
    from models import Bill, Branch  # noqa
    from models import Customer, Staff  # noqa

    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, '%Y-%m-%d')
        end = datetime.strptime(args.end_date, '%Y-%m-%d').replace(
            hour=23, minute=59, second=59, microsecond=999999)
    else:
        end = datetime.utcnow()
        start = end - timedelta(days=args.days)

    print(f'Scanning {start.date()} -> {end.date()}'
          + (f' for branch {args.branch}' if args.branch else ' (all branches)'))

    query = {
        'is_deleted__ne': True,
        'bill_date__gte': start,
        'bill_date__lte': end,
    }
    if args.branch:
        query['branch'] = ObjectId(args.branch)

    bills = list(Bill.objects(**query).order_by('bill_date'))
    print(f'Loaded {len(bills)} bills')

    # Pre-fetch customer + branch + staff names in batches to avoid N+1
    cust_ids, branch_ids = set(), set()
    for b in bills:
        c = b._data.get('customer')
        if c is not None:
            cust_ids.add(c.id if hasattr(c, 'id') else c)
        br = b._data.get('branch')
        if br is not None:
            branch_ids.add(br.id if hasattr(br, 'id') else br)

    cust_map = {}
    if cust_ids:
        for c in Customer.objects(id__in=list(cust_ids)).only('id', 'first_name', 'last_name', 'mobile'):
            cust_map[c.id] = f"{(c.first_name or '').strip()} {(c.last_name or '').strip()}".strip() or c.mobile or 'walk-in'
    branch_map = {}
    if branch_ids:
        for b in Branch.objects(id__in=list(branch_ids)).only('id', 'name'):
            branch_map[b.id] = b.name or '?'

    # Group by (customer_id, rounded amount) and sub-cluster by time window
    groups = defaultdict(list)
    for b in bills:
        cust = b._data.get('customer')
        if cust is None:
            continue
        cust_id = cust.id if hasattr(cust, 'id') else cust
        amt = round(float(b.final_amount or 0), 2)
        if amt <= 0:
            continue
        groups[(cust_id, amt)].append(b)

    # Build clusters
    clusters = []
    for (cust_id, amt), grp in groups.items():
        grp.sort(key=lambda x: x.bill_date or datetime.min)
        i = 0
        while i < len(grp):
            cluster = [grp[i]]
            j = i + 1
            while j < len(grp):
                gap = (grp[j].bill_date - cluster[-1].bill_date).total_seconds()
                if gap <= args.window_seconds:
                    cluster.append(grp[j])
                    j += 1
                else:
                    break
            if len(cluster) >= 2:
                clusters.append((cust_id, amt, cluster))
            i = j if j > i + 1 else i + 1

    if not clusters:
        print('No duplicate clusters found in the scanned range.')
        return

    print(f'Found {len(clusters)} duplicate clusters covering {sum(len(c[2]) for c in clusters)} bills.')

    output_path = os.path.join(SCRIPT_DIR, args.output)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'cluster_id',
            'cluster_size',
            'is_first_in_cluster',
            'bill_number',
            'bill_id',
            'customer_name',
            'branch_name',
            'bill_date',
            'final_amount',
            'payment_mode',
            'item_count',
            'item_summary',
            'gap_seconds_from_first',
            'bill_number_timestamp',  # YYYYMMDDhhmmss part of bill_number
            'decision',  # owner fills in: keep / delete  (default empty)
        ])

        for cluster_idx, (cust_id, amt, cluster) in enumerate(clusters, 1):
            cust_name = cust_map.get(cust_id, '?')
            first_dt = cluster[0].bill_date
            for idx, b in enumerate(cluster):
                # Item summary: "[2x service] hair_cut@500, [1x product] shampoo@300 ..."
                items = []
                for it in (b.items or []):
                    name = (it.name or '?').strip()
                    typ = (it.item_type or 'service')
                    qty = it.quantity or 1
                    price = it.price or 0
                    items.append(f'{qty}x {typ}:{name}@{price:.0f}')
                item_summary = '; '.join(items[:6]) + ('; ...' if len(items) > 6 else '')
                bn = b.bill_number or ''
                # BILL-YYYYMMDDhhmmss-XXXX
                ts_part = bn.split('-')[1] if bn.startswith('BILL-') and bn.count('-') >= 2 else ''
                gap = (b.bill_date - first_dt).total_seconds() if b.bill_date and first_dt else 0
                br = b._data.get('branch')
                br_id = br.id if hasattr(br, 'id') else br
                w.writerow([
                    cluster_idx,
                    len(cluster),
                    'YES' if idx == 0 else '',
                    bn,
                    str(b.id),
                    cust_name,
                    branch_map.get(br_id, '?'),
                    b.bill_date.strftime('%Y-%m-%d %H:%M:%S') if b.bill_date else '',
                    f'{float(b.final_amount or 0):.2f}',
                    b.payment_mode or '',
                    len(b.items or []),
                    item_summary,
                    f'{gap:.1f}',
                    ts_part,
                    '',  # decision blank by default
                ])
            # Spacer row between clusters for readability
            w.writerow([])

    print(f'\nReport written: {output_path}')
    print('\nNext step: open this CSV in Excel/Sheets and review every cluster.')
    print('In the "decision" column, type one of:')
    print('  keep        -> this bill is real, do not delete')
    print('  delete      -> this is a duplicate, soft-delete it')
    print('Leave the column blank for "no action" (default).')
    print('\nOnce reviewed, run cleanup_duplicate_bills.py to apply the decisions.')


if __name__ == '__main__':
    main()
