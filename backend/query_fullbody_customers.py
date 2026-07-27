"""List every full-body service transaction with full customer + branch detail."""
import os
import re
from collections import defaultdict
from pymongo import MongoClient

MONGODB_URI = os.environ.get(
    'MONGODB_URI',
    'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon'
)
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=30000, tls=True)
db = client[MONGODB_DB]

# Match "full body" as a phrase (allow extra spaces), case-insensitive
fb_regex_str = r'full\s*body'
fb_regex = re.compile(fb_regex_str, re.IGNORECASE)

# 1) Services whose name mentions "full body"
fb_services = list(db.services.find(
    {'name': {'$regex': fb_regex_str, '$options': 'i'}},
    {'_id': 1, 'name': 1}
))
fb_service_ids = {s['_id'] for s in fb_services}
service_name_map = {s['_id']: s.get('name', '') for s in fb_services}

print(f"DB: {MONGODB_DB}")
print(f"Full-body services in catalog: {len(fb_services)}")
if fb_services:
    sample = sorted({s['name'] for s in fb_services})
    for n in sample[:15]:
        print(f"  - {n}")
    if len(sample) > 15:
        print(f"  ... and {len(sample) - 15} more")

# 2) Bills with at least one full-body item
or_clauses = [{'items.name': {'$regex': fb_regex_str, '$options': 'i'}}]
if fb_service_ids:
    or_clauses.append({'items.service': {'$in': list(fb_service_ids)}})
bill_query = {'is_deleted': {'$ne': True}, '$or': or_clauses}

bills = list(db.bills.find(
    bill_query,
    {'customer': 1, 'branch': 1, 'bill_date': 1, 'bill_number': 1,
     'final_amount': 1, 'payment_mode': 1, 'items': 1}
))

# 3) Extract full-body line-items
transactions = []
customer_ids, branch_ids, staff_ids = set(), set(), set()
for bill in bills:
    bdate = bill.get('bill_date')
    bnum = bill.get('bill_number')
    pay = bill.get('payment_mode')
    cid = bill.get('customer')
    brid = bill.get('branch')
    if cid: customer_ids.add(cid)
    if brid: branch_ids.add(brid)

    for item in bill.get('items', []):
        iname = item.get('name') or ''
        svc_ref = item.get('service')
        is_fb = bool(fb_regex.search(iname)) or (svc_ref in fb_service_ids)
        if not is_fb:
            continue
        staff_ref = item.get('staff')
        if staff_ref: staff_ids.add(staff_ref)
        transactions.append({
            'bill_date': bdate, 'bill_number': bnum, 'payment_mode': pay,
            'customer_id': cid, 'branch_id': brid, 'staff_id': staff_ref,
            'service_name': iname or service_name_map.get(svc_ref, '<unknown>'),
            'price': item.get('price') or 0, 'discount': item.get('discount') or 0,
            'quantity': item.get('quantity') or 1, 'total': item.get('total') or 0,
        })

# 4) Batch-fetch refs
customer_map = {c['_id']: c for c in db.customers.find(
    {'_id': {'$in': list(customer_ids)}},
    {'first_name': 1, 'last_name': 1, 'mobile': 1, 'email': 1, 'gender': 1,
     'dob': 1, 'source': 1, 'branch': 1, 'created_at': 1}
)}
branch_map = {b['_id']: b for b in db.branches.find(
    {'_id': {'$in': list(branch_ids)}},
    {'name': 1, 'address': 1, 'city': 1, 'phone': 1}
)}
staff_map = {s['_id']: s for s in db.staffs.find(
    {'_id': {'$in': list(staff_ids)}},
    {'first_name': 1, 'last_name': 1, 'mobile': 1}
)}

transactions.sort(key=lambda t: t['bill_date'] or 0)

print(f"\nBills with full-body items : {len(bills)}")
print(f"Full-body line-items total : {len(transactions)}")
print(f"Distinct customers on bills: {len(customer_ids)}\n")
print("=" * 100)

for i, t in enumerate(transactions, 1):
    c = customer_map.get(t['customer_id'])
    b = branch_map.get(t['branch_id'])
    s = staff_map.get(t['staff_id'])
    bdate = t['bill_date'].isoformat() if t['bill_date'] else '-'

    print(f"\n#{i}  {bdate}   Bill: {t['bill_number']}   Payment: {t['payment_mode'] or '-'}")
    print(f"    Service : {t['service_name']}   qty={t['quantity']}  price={t['price']}  disc={t['discount']}  total={t['total']}")
    if b:
        print(f"    Branch  : {b.get('name', '-')}  |  {b.get('address') or ''}  {b.get('city') or ''}  |  phone {b.get('phone') or '-'}")
    else:
        print(f"    Branch  : <not found> (_id={t['branch_id']})")
    if s:
        sname = f"{s.get('first_name') or ''} {s.get('last_name') or ''}".strip()
        print(f"    Staff   : {sname}  ({s.get('mobile') or '-'})")
    else:
        print(f"    Staff   : -")
    if c:
        cname = f"{c.get('first_name') or ''} {c.get('last_name') or ''}".strip()
        print(f"    Customer: {cname}")
        print(f"              mobile={c.get('mobile') or '-'}   email={c.get('email') or '-'}")
        print(f"              gender={c.get('gender') or '-'}   dob={c.get('dob') or '-'}   source={c.get('source') or '-'}")
        print(f"              signed_up={c.get('created_at').isoformat() if c.get('created_at') else '-'}")
    else:
        print(f"    Customer: <not found in customers collection> (_id={t['customer_id']})")

# Per-customer summary
print("\n" + "=" * 100)
print("SUMMARY BY CUSTOMER")
print("=" * 100)
per_cust = defaultdict(list)
for t in transactions:
    per_cust[t['customer_id']].append(t)
for cid, items in per_cust.items():
    c = customer_map.get(cid)
    name = f"{(c or {}).get('first_name') or ''} {(c or {}).get('last_name') or ''}".strip() or '<deleted customer>'
    mobile = (c or {}).get('mobile') or '-'
    total = sum(t['total'] for t in items)
    print(f"\n- {name}  ({mobile})   [{len(items)} full-body line-item(s), Rs {total}]")
    for t in items:
        bdate = t['bill_date'].strftime('%Y-%m-%d') if t['bill_date'] else '-'
        bname = branch_map.get(t['branch_id'], {}).get('name', '-')
        print(f"    {bdate}  |  {bname:<12}  |  {t['service_name']:<35}  |  Rs {t['total']}")

client.close()
