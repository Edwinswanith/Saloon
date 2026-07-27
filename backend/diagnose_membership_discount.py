"""
Read-only diagnostic — for the most recent N bills, prints the saved discount
fields and which membership plans were involved (and whether those plans have
services ticked).

Run this when an invoice shows Discount = 0 unexpectedly. It tells you
whether the bill was saved with a real discount or not, and if not, why
(usually because the plan has no `applicable_services`).

Usage:
    cd backend
    python diagnose_membership_discount.py            # last 10 bills
    python diagnose_membership_discount.py --limit 25
    python diagnose_membership_discount.py --bill BILL-20260505-XXXX
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from utils.env_config import load_env, get_mongodb_uri, get_mongodb_db

from mongoengine import connect


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
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--bill', help='Specific bill_number to inspect')
    return p.parse_args()


def main():
    args = parse_args()
    connect_db()

    from models import Bill, MembershipPlan, Membership

    if args.bill:
        bills = list(Bill.objects(bill_number=args.bill))
        if not bills:
            print(f'No bill found with number {args.bill}')
            return
    else:
        bills = list(Bill.objects(is_deleted__ne=True).order_by('-bill_date').limit(args.limit))

    if not bills:
        print('No bills.')
        return

    for b in bills:
        print('=' * 76)
        print(f'Bill: {b.bill_number}   date={b.bill_date}')
        print(f'  subtotal              = ₹{float(b.subtotal or 0):,.2f}')
        print(f'  discount_amount       = ₹{float(b.discount_amount or 0):,.2f}    <-- this drives the invoice "Discount" line')
        print(f'  discount_type         = {b.discount_type or "-"}')
        print(f'  final_amount          = ₹{float(b.final_amount or 0):,.2f}')

        applied_offer = getattr(b, 'applied_offer', None) or {}
        if applied_offer.get('id'):
            print(f'  applied_offer         = {applied_offer.get("name")} ({applied_offer.get("percentage")}%)')

        # Show membership plans referenced on this bill
        plan_names = set()
        item_summary = []
        for it in (b.items or []):
            row = f'    - [{it.item_type}] {it.name or "?"}  price=₹{float(it.price or 0):,.2f}  total=₹{float(it.total or 0):,.2f}'
            md = getattr(it, 'membership_discount', 0) or 0
            if md:
                row += f'  membership_discount=₹{float(md):,.2f}'
            item_summary.append(row)
            if it.item_type == 'membership' and it.name:
                plan_names.add(it.name)

        # Customer's active membership at the time of bill (best effort lookup)
        if b.customer:
            try:
                ms = list(Membership.objects(customer=b.customer).order_by('-purchase_date'))
                for m in ms[:2]:  # last 2 memberships per customer
                    if m.plan:
                        plan_names.add(m.plan.name if hasattr(m.plan, 'name') else str(m.plan))
            except Exception:
                pass

        print(f'  items ({len(b.items or [])}):')
        for row in item_summary:
            print(row)

        # Look up each plan and report applicable_services state
        if plan_names:
            print('  Plans referenced on this bill:')
            for name in plan_names:
                plan = MembershipPlan.objects(name=name).first() or MembershipPlan.objects(name__iexact=name).first()
                if not plan:
                    print(f'    - "{name}": NOT FOUND in DB')
                    continue
                refs = plan._data.get('applicable_services') or []
                print(
                    f'    - "{plan.name}":  allocated_discount={plan.allocated_discount}%   '
                    f'applicable_services={len(refs)} service(s)'
                    + ('   <-- EMPTY: strict mapping = no discount' if not refs else '')
                )

        print()


if __name__ == '__main__':
    main()
