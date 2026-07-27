r"""
One-off diagnostic + password-reset script for the Saloon production MongoDB.

Usage:
    cd backend
    # activate venv first (myenv\Scripts\activate on Windows)

    # 1) List every staff / manager / owner in Saloon_prod:
    python reset_prod_password.py --list

    # 2) Reset a password (pick identifier from --list output):
    python reset_prod_password.py --reset owner   --identifier owner@salon.com --password NewOwner@2026 --confirm
    python reset_prod_password.py --reset manager --identifier 9876543220       --password NewPass@2026  --confirm
    python reset_prod_password.py --reset staff   --identifier 9876543210       --password NewPass@2026  --confirm

Target DB defaults to the same MONGODB_DB/MONGODB_URI env vars that app.py uses
(Saloon_prod fallback). Override with env vars if you need a different target.
"""

import argparse
import os
import sys
from datetime import datetime

from mongoengine import connect, disconnect
from models import Staff, Manager, Owner, Branch
from utils.auth import hash_password, verify_password
from utils.env_config import load_env, get_mongodb_uri, get_mongodb_db


def _branch_name(ref):
    try:
        if not ref:
            return '-'
        b = ref if isinstance(ref, Branch) else Branch.objects(id=ref.id).first()
        return b.name if b else '-'
    except Exception:
        return '-'


def build_uri(raw_uri, db_name):
    """Mirror the URI-building logic in app.py so we hit the same cluster/db."""
    base = raw_uri

    if '@' in base:
        creds, rest = base.split('@', 1)
        if '/' in rest:
            host = rest.split('/', 1)[0]
            params = '?' + rest.split('?', 1)[1] if '?' in rest else ''
            base = f"{creds}@{host}{params}"

    if f'/{db_name}' not in base:
        if '?' in base:
            base = base.replace('?', f'/{db_name}?', 1)
        else:
            base = f"{base}/{db_name}"

    extras = []
    if 'retryWrites' not in base:
        extras.append('retryWrites=true')
    if 'w=' not in base:
        extras.append('w=majority')
    if 'tls=' not in base and 'ssl=' not in base:
        extras.append('tls=true')
    if extras:
        sep = '&' if '?' in base else '?'
        base = f"{base}{sep}{'&'.join(extras)}"

    return base


def connect_db():
    uri = os.environ.get(
        'MONGODB_URI',
        'get_mongodb_uri()',
    )
    db_name = os.environ.get('MONGODB_DB', 'Saloon_prod')
    full = build_uri(uri, db_name)
    print(f"Connecting to DB: {db_name}")
    print(f"Host: {full.split('@')[0]}@*** / db={db_name}")
    connect(host=full, alias='default', db=db_name,
            serverSelectionTimeoutMS=30000, connectTimeoutMS=30000)
    return db_name


def fmt_row(label, _id, name, key_label, key_val, extras):
    pw = 'set' if extras.get('password_hash') else 'MISSING'
    active = extras.get('is_active', True)
    status = extras.get('status', 'active')
    role = extras.get('role')
    role_str = f" role={role}" if role else ''
    return (f"  [{label}] {name:<30} {key_label}={key_val:<25} "
            f"password_hash={pw:<7} is_active={active} status={status}{role_str} _id={_id}")


def list_users():
    print("\n=== BRANCHES (collection: branches) ===")
    for b in Branch.objects.all():
        print(f"  _id={b.id} name={b.name} city={b.city} is_active={b.is_active}")

    print("\n=== OWNERS (collection: owners) ===")
    owners = list(Owner.objects.all())
    if not owners:
        print("  (none)")
    for o in owners:
        print(fmt_row(
            'owner', o.id, f"{o.first_name or ''} {o.last_name or ''}".strip(),
            'email', o.email or '-',
            {'password_hash': o.password_hash, 'is_active': o.is_active,
             'status': o.status},
        ) + f" branch=ALL")

    print("\n=== MANAGERS (collection: managers) ===")
    managers = list(Manager.objects.all())
    if not managers:
        print("  (none)")
    for m in managers:
        print(fmt_row(
            'manager', m.id, f"{m.first_name or ''} {m.last_name or ''}".strip(),
            'email', m.email or '-',
            {'password_hash': m.password_hash, 'is_active': m.is_active,
             'status': m.status, 'role': m.role},
        ) + f" branch={_branch_name(m.branch)}")

    print("\n=== STAFF (collection: staffs) ===")
    staff_list = list(Staff.objects.all())
    if not staff_list:
        print("  (none)")
    for s in staff_list:
        print(fmt_row(
            'staff', s.id, f"{s.first_name or ''} {s.last_name or ''}".strip(),
            'mobile', s.mobile or '-',
            {'password_hash': getattr(s, 'password_hash', None),
             'is_active': s.is_active, 'status': s.status, 'role': s.role},
        ) + f" branch={_branch_name(s.branch)}")
    print()


def _is_dummy(email, mobile):
    for v in (email or '', mobile or ''):
        if 'dummy' in v.lower() or v.startswith('0999999'):
            return True
    return False


def reset_all_active(owner_pw, manager_pw, staff_pw, confirm):
    """Reset every ACTIVE owner/manager/staff to the per-role password."""
    if not confirm:
        print("Dry run (no --confirm). Nothing will be written.")
    changed = []
    skipped = []

    now = datetime.utcnow()

    for o in Owner.objects.all():
        if _is_dummy(o.email, o.mobile):
            skipped.append(('owner', o.email, 'dummy'))
            continue
        is_active = o.is_active if o.is_active is not None else True
        is_active = is_active and (o.status or 'active') == 'active'
        if not is_active:
            skipped.append(('owner', o.email, 'inactive'))
            continue
        if confirm:
            o.password_hash = hash_password(owner_pw)
            o.is_active = True
            o.status = 'active'
            o.updated_at = now
            o.save()
        changed.append(('owner', 'ALL', f"{o.first_name or ''} {o.last_name or ''}".strip(),
                        'email', o.email, owner_pw))

    for m in Manager.objects.all():
        if _is_dummy(m.email, m.mobile):
            skipped.append(('manager', m.email, 'dummy'))
            continue
        is_active = m.is_active if m.is_active is not None else True
        is_active = is_active and (m.status or 'active') == 'active'
        if not is_active:
            skipped.append(('manager', m.email, 'inactive'))
            continue
        if confirm:
            m.password_hash = hash_password(manager_pw)
            m.is_active = True
            m.status = 'active'
            m.updated_at = now
            m.save()
        changed.append(('manager', _branch_name(m.branch),
                        f"{m.first_name or ''} {m.last_name or ''}".strip(),
                        'email', m.email, manager_pw))

    for s in Staff.objects.all():
        if _is_dummy(getattr(s, 'email', None), s.mobile):
            skipped.append(('staff', s.mobile, 'dummy'))
            continue
        is_active = s.is_active if s.is_active is not None else True
        is_active = is_active and (s.status or 'active') == 'active'
        if not is_active:
            skipped.append(('staff', s.mobile, 'inactive'))
            continue
        if confirm:
            s.password_hash = hash_password(staff_pw)
            s.is_active = True
            s.status = 'active'
            s.updated_at = now
            s.save()
        changed.append(('staff', _branch_name(s.branch),
                        f"{s.first_name or ''} {s.last_name or ''}".strip(),
                        'mobile', s.mobile, staff_pw))

    print("\n=== RESULT ===")
    print(f"{'Role':<8} {'Branch':<25} {'Name':<25} {'Key':<7} {'Identifier':<28} Password")
    for role, branch, name, keylabel, key, pw in changed:
        print(f"{role:<8} {branch:<25} {name:<25} {keylabel:<7} {str(key):<28} {pw}")
    print(f"\nSkipped ({len(skipped)} inactive accounts): "
          + ", ".join(f"{r}:{k}" for r, k, _ in skipped))


def find_matches(kind, identifier):
    """Return list of matching docs for the target kind."""
    if kind == 'owner':
        # Owner lives in `owners`; but the seeder historically put role='owner'
        # into `managers`. Check both so we don't miss legacy records.
        hits = []
        hits += list(Owner.objects(email=identifier)) + list(Owner.objects(mobile=identifier))
        hits += list(Manager.objects(role='owner', email=identifier))
        hits += list(Manager.objects(role='owner', mobile=identifier))
        return hits
    if kind == 'manager':
        hits = list(Manager.objects(email=identifier)) + list(Manager.objects(mobile=identifier))
        return hits
    if kind == 'staff':
        return list(Staff.objects(mobile=identifier))
    raise ValueError(f"unknown kind: {kind}")


def try_password(kind, identifier, candidate):
    matches = find_matches(kind, identifier)
    if not matches:
        print(f"ERROR: no {kind} found with identifier '{identifier}'.")
        sys.exit(2)
    if len(matches) > 1:
        print(f"WARNING: {len(matches)} records match — testing each.")
    for doc in matches:
        h = getattr(doc, 'password_hash', None)
        label = (f"{doc.__class__.__name__} _id={doc.id} "
                 f"email={getattr(doc, 'email', '-')} "
                 f"mobile={getattr(doc, 'mobile', '-')}")
        if not h:
            print(f"NO MATCH (no password_hash stored): {label}")
            continue
        if verify_password(candidate, h):
            print(f"MATCH: '{candidate}' is the correct password for {label}")
            return
        print(f"NO MATCH: {label}")


def reset_password(kind, identifier, new_password, confirm):
    matches = find_matches(kind, identifier)
    if not matches:
        print(f"ERROR: no {kind} found with identifier '{identifier}'.")
        print("Run with --list to see available accounts.")
        sys.exit(2)
    if len(matches) > 1:
        print(f"ERROR: {len(matches)} records match — refusing to reset ambiguously.")
        for m in matches:
            print(f"  - {m.__class__.__name__} _id={m.id} email={getattr(m, 'email', '-')}"
                  f" mobile={getattr(m, 'mobile', '-')}")
        sys.exit(3)

    doc = matches[0]
    print(f"Matched: {doc.__class__.__name__} _id={doc.id} "
          f"email={getattr(doc, 'email', '-')} mobile={getattr(doc, 'mobile', '-')}")

    if not confirm:
        print("Dry run (no --confirm). Nothing was written.")
        return

    doc.password_hash = hash_password(new_password)
    doc.is_active = True
    doc.status = 'active'
    doc.updated_at = datetime.utcnow()
    doc.save()
    print("OK: password_hash updated, is_active=True, status='active'.")
    print(f"Login with: identifier='{identifier}' password='{new_password}'")


def main():
    parser = argparse.ArgumentParser(description="Saloon prod password reset tool")
    parser.add_argument('--list', action='store_true',
                        help='List all users in staffs/managers/owners')
    parser.add_argument('--reset', choices=['owner', 'manager', 'staff'],
                        help='Reset a single user')
    parser.add_argument('--reset-all', action='store_true',
                        help='Reset every ACTIVE owner/manager/staff password')
    parser.add_argument('--owner-password', default='Owner@2026')
    parser.add_argument('--manager-password', default='Manager@2026')
    parser.add_argument('--staff-password', default='Staff@2026')
    parser.add_argument('--try', dest='try_kind',
                        choices=['owner', 'manager', 'staff'],
                        help='Read-only: test whether --password matches the stored hash')
    parser.add_argument('--identifier',
                        help='Email (owner/manager) or mobile (staff/manager/owner)')
    parser.add_argument('--password',
                        help='Plaintext password (new for --reset, candidate for --try)')
    parser.add_argument('--confirm', action='store_true',
                        help='Actually write the change (without this, it is a dry run)')
    args = parser.parse_args()

    if not (args.list or args.reset or args.try_kind or args.reset_all):
        parser.print_help()
        sys.exit(1)

    if args.reset and not (args.identifier and args.password):
        print("ERROR: --reset requires --identifier and --password")
        sys.exit(1)

    if args.try_kind and not (args.identifier and args.password):
        print("ERROR: --try requires --identifier and --password")
        sys.exit(1)

    connect_db()
    try:
        if args.list:
            list_users()
        if args.try_kind:
            try_password(args.try_kind, args.identifier, args.password)
        if args.reset:
            reset_password(args.reset, args.identifier, args.password, args.confirm)
        if args.reset_all:
            reset_all_active(args.owner_password, args.manager_password,
                             args.staff_password, args.confirm)
    finally:
        disconnect(alias='default')


if __name__ == '__main__':
    main()
