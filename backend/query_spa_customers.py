"""List every spa transaction with full customer + branch detail."""
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

# Word-boundary match so "spa" doesn't accidentally match "space", "spanish", etc.
spa_regex = re.compile(r'\bspa\b', re.IGNORECASE)
spa_regex_str = r'\bspa\b'

# 1) Services containing "spa" as a word
spa_services = list(db.services.find(
    {'name': {'$regex': spa_regex_str, '$options': 'i'}},
    {'_id': 1, 'name': 1}
))
spa_service_ids = {s['_id'] for s in spa_services}
service_name_map = {s['_id']: s.get('name', '') for s in spa_services}

print(f"DB: {MONGODB_DB}")
print(f"Spa services in catalog     : {len(spa_services)}")
if spa_services:
    sample = ', '.join(sorted({s['name'] for s in spa_services})[:10])
    print(f"  (sample: {sample}{'...' if len(spa_services) > 10 else ''})")

# 2) Bills with at least one spa-related item
or_clauses = [{'items.name': {'$regex': spa_regex_str, '$options': 'i'}}]
if spa_service_ids:
    or_clauses.append({'items.service': {'$in': list(spa_service_ids)}})
bill_query = {'is_deleted': {'$ne': True}, '$or': or_clauses}

bills = list(db.bills.find(
    bill_query,
    {'customer': 1, 'branch': 1, 'bill_date': 1, 'bill_number': 1,
     'final_amount': 1, 'payment_mode': 1, 'items': 1}
))

# 3) Extract spa line-items
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
        is_spa = bool(spa_regex.search(iname)) or (svc_ref in spa_service_ids)
        if not is_spa:
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

print(f"Bills with spa items        : {len(bills)}")
print(f"Spa line-items total        : {len(transactions)}")
print(f"Distinct customers on bills : {len(customer_ids)}\n")
print("=" * 100)

# 5) Per-transaction detail
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

# 6) Per-customer summary
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
    print(f"\n- {name}  ({mobile})   [{len(items)} spa line-item(s)]")
    for t in items:
        bdate = t['bill_date'].strftime('%Y-%m-%d') if t['bill_date'] else '-'
        bname = branch_map.get(t['branch_id'], {}).get('name', '-')
        print(f"    {bdate}  |  {bname:<12}  |  {t['service_name']:<30}  |  Rs {t['total']}")

client.close()
