"""
Set up an isolated "Dummy Branch" for testing in the production database.

Why this is safe:
- The Saloon app is branch-scoped via the X-Branch-Id header. Live staff are
  locked to their assigned branches and will never see Dummy Branch data.
- Owners can opt-in to it via the branch switcher.
- Cloning services creates NEW Service documents with branch=Dummy. Existing
  branches and their services are not modified.

What this script does (idempotent — safe to re-run):
1. Creates a branch named "Dummy Branch" if it doesn't already exist.
2. Creates one dummy staff user assigned to Dummy Branch.
3. Picks the source branch with the largest active service catalog and clones
   every active service into Dummy Branch (skipping any already-cloned).

Defaults to DRY-RUN. Pass --confirm to actually write.

Usage (PowerShell):
    cd backend
    myenv/Scripts/Activate.ps1
    python setup_dummy_branch.py              # dry run, no writes
    python setup_dummy_branch.py --confirm    # perform writes

Override target DB / source branch via env or CLI:
    $env:MONGODB_DB = "Saloon_prod"           # default
    python setup_dummy_branch.py --source "T. Nagar" --confirm
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect, disconnect
from models import Branch, Staff, Service, ServiceGroup
from utils.auth import hash_password


DUMMY_BRANCH_NAME = "Dummy Branch"
DUMMY_STAFF = {
    "mobile": "9000000001",
    "first_name": "Test",
    "last_name": "Staff",
    "email": "test.staff@dummy.local",
    "salary": 0,
    "commission_rate": 0.0,
    "role": "staff",
    "password": "Dummy@123",  # plaintext — hashed before save
}


def build_mongo_uri(uri: str, db: str) -> str:
    base_uri = uri
    if '@' in base_uri:
        creds, host_and_params = base_uri.split('@', 1)
        if '/' in host_and_params:
            host = host_and_params.split('/')[0]
            params = '?' + host_and_params.split('?', 1)[1] if '?' in host_and_params else ''
            base_uri = f"{creds}@{host}{params}"
    if f'/{db}' not in base_uri:
        if '?' in base_uri:
            base_uri = base_uri.replace('?', f'/{db}?')
        else:
            base_uri = f"{base_uri}/{db}"
    if 'retryWrites' not in base_uri:
        sep = '&' if '?' in base_uri else '?'
        base_uri = f"{base_uri}{sep}retryWrites=true&w=majority"
    return base_uri


def find_or_create_dummy_branch(dry_run: bool):
    existing = Branch.objects(name=DUMMY_BRANCH_NAME).first()
    if existing:
        print(f"  [skip] Dummy Branch already exists (id={existing.id})")
        return existing
    if dry_run:
        print(f"  [dry-run] WOULD create Branch '{DUMMY_BRANCH_NAME}'")
        return None
    branch = Branch(
        name=DUMMY_BRANCH_NAME,
        address="Internal — testing only",
        city="Test",
        phone="0000000000",
        email="dummy@internal.test",
        is_active=True,
    )
    branch.save()
    print(f"  [created] Dummy Branch (id={branch.id})")
    return branch


def find_or_create_dummy_staff(branch, dry_run: bool):
    existing = Staff.objects(mobile=DUMMY_STAFF["mobile"], status="active").first()
    if existing:
        if existing.branch and existing.branch.id == (branch.id if branch else None):
            print(f"  [skip] Dummy staff already exists in Dummy Branch (id={existing.id})")
        else:
            other_branch = existing.branch.name if existing.branch else "no branch"
            print(
                f"  [warn] Active staff with mobile {DUMMY_STAFF['mobile']} already exists "
                f"in '{other_branch}'. Pick a different mobile in DUMMY_STAFF or deactivate the existing one."
            )
        return existing
    if dry_run or branch is None:
        print(
            f"  [dry-run] WOULD create staff "
            f"({DUMMY_STAFF['first_name']} {DUMMY_STAFF['last_name']}, mobile {DUMMY_STAFF['mobile']}) "
            f"assigned to Dummy Branch"
        )
        return None
    staff = Staff(
        mobile=DUMMY_STAFF["mobile"],
        first_name=DUMMY_STAFF["first_name"],
        last_name=DUMMY_STAFF["last_name"],
        email=DUMMY_STAFF["email"],
        salary=DUMMY_STAFF["salary"],
        commission_rate=DUMMY_STAFF["commission_rate"],
        status="active",
        role=DUMMY_STAFF["role"],
        password_hash=hash_password(DUMMY_STAFF["password"]),
        is_active=True,
        branch=branch,
    )
    staff.save()
    print(f"  [created] Dummy staff (id={staff.id})")
    return staff


def pick_source_branch(explicit_name):
    if explicit_name:
        branch = Branch.objects(name=explicit_name).first()
        if not branch:
            raise SystemExit(f"  [fatal] --source branch '{explicit_name}' not found")
        if branch.name == DUMMY_BRANCH_NAME:
            raise SystemExit("  [fatal] --source cannot be the Dummy Branch itself")
        return branch
    counts = []
    for br in Branch.objects(is_active=True):
        if br.name == DUMMY_BRANCH_NAME:
            continue
        n = Service.objects(branch=br, status="active").count()
        counts.append((n, br))
    counts.sort(key=lambda x: x[0], reverse=True)
    if not counts or counts[0][0] == 0:
        return None
    return counts[0][1]


def clone_services(source_branch, dummy_branch, dry_run: bool):
    if not source_branch:
        print("  [skip] no source branch with active services available — nothing to clone")
        return 0, 0
    if not dummy_branch:
        # Dry-run before Dummy Branch exists. Estimate count from the source.
        estimated = Service.objects(branch=source_branch, status="active").count()
        print(
            f"  [dry-run] WOULD clone up to {estimated} active services from "
            f"'{source_branch.name}' into Dummy Branch (skipping any already cloned by name)"
        )
        return 0, 0

    existing_names = set(
        s.name for s in Service.objects(branch=dummy_branch).only("name")
    )

    cloned = 0
    skipped = 0
    for src in Service.objects(branch=source_branch, status="active"):
        if src.name in existing_names:
            skipped += 1
            continue
        if dry_run:
            cloned += 1
            continue
        new_svc = Service(
            name=src.name,
            group=src.group,  # ServiceGroup is global — reuse the reference
            price=src.price,
            duration=src.duration,
            description=src.description,
            branch=dummy_branch,
            status="active",
        )
        new_svc.save()
        cloned += 1
    label = "[dry-run] WOULD clone" if dry_run else "[created] cloned"
    print(
        f"  {label} {cloned} services from '{source_branch.name}'; "
        f"{skipped} already present in Dummy Branch (skipped)"
    )
    return cloned, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--confirm", action="store_true", help="Perform writes. Without this flag, dry-run only.")
    parser.add_argument("--source", default=None, help="Source branch name to clone services from. Default: branch with most active services.")
    args = parser.parse_args()

    dry_run = not args.confirm
    mongo_uri = os.environ.get(
        "MONGODB_URI",
        "mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon",
    )
    mongo_db = os.environ.get("MONGODB_DB", "Saloon_prod")

    print("=" * 70)
    print(f"Dummy Branch Setup — DB: {mongo_db}")
    print(f"Mode: {'DRY RUN (no writes)' if dry_run else 'LIVE (will write)'}")
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print("=" * 70)

    full_uri = build_mongo_uri(mongo_uri, mongo_db)
    connect(host=full_uri, alias="default", db=mongo_db)

    try:
        print("\n[1/4] Inspecting current state…")
        all_branches = list(Branch.objects())
        print(f"  branches in DB: {len(all_branches)}")
        for br in all_branches:
            n = Service.objects(branch=br, status="active").count()
            print(f"    - {br.name!r}  (active services: {n}, is_active={br.is_active})")

        print("\n[2/4] Ensuring Dummy Branch exists…")
        dummy_branch = find_or_create_dummy_branch(dry_run)

        print("\n[3/4] Ensuring dummy staff exists…")
        find_or_create_dummy_staff(dummy_branch, dry_run)

        print("\n[4/4] Cloning services into Dummy Branch…")
        source = pick_source_branch(args.source)
        if source:
            print(f"  source branch chosen: '{source.name}'")
        clone_services(source, dummy_branch, dry_run)

        print("\n" + "=" * 70)
        if dry_run:
            print("Dry run complete. Re-run with --confirm to apply changes.")
        else:
            print("Done. Test login:")
            print(f"  mobile:   {DUMMY_STAFF['mobile']}")
            print(f"  password: {DUMMY_STAFF['password']}")
            print(f"  branch:   {DUMMY_BRANCH_NAME}")
            print(f"  role:     {DUMMY_STAFF['role']}")
        print("=" * 70)
    finally:
        disconnect(alias="default")


if __name__ == "__main__":
    main()
