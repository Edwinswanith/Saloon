"""
Seed a dummy branch plus staff, manager, and owner for local/testing use.

Run from backend/:  python seed_dummy_branch.py

Safe to re-run: updates existing records keyed by name/email/mobile.
Owner has no branch field in the model; after login pick branch "Dummy Branch".
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from mongoengine import connect, disconnect

from utils.auth import hash_password

MONGODB_URI = os.environ.get(
    "MONGODB_URI",
    "mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon",
)
MONGODB_DB = os.environ.get("MONGODB_DB", "Saloon_prod")

BRANCH_NAME = "Dummy Branch"
PASSWORD = "test123"

STAFF_MOBILE = "0999999001"
MGR_EMAIL = "dummy.manager@dummybranch.test"
MGR_MOBILE = "0999999002"
OWNER_EMAIL = "dummy.owner@dummybranch.test"
OWNER_MOBILE = "0999999003"


def main():
    connect(db=MONGODB_DB, host=MONGODB_URI)
    from models import Branch, Staff, Manager, Owner

    now = datetime.utcnow()
    pw = hash_password(PASSWORD)

    branch = Branch.objects(name=BRANCH_NAME).first()
    if not branch:
        branch = Branch(
            name=BRANCH_NAME,
            address="Dummy branch for QA (not a real location)",
            city="Chennai",
            phone="0999999000",
            email="dummy.branch@test.saloon",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        branch.save()
        print(f"Created branch: {branch.name} ({branch.id})")
    else:
        branch.is_active = True
        branch.updated_at = now
        branch.save()
        print(f"Using existing branch: {branch.name} ({branch.id})")

    staff = Staff.objects(mobile=STAFF_MOBILE).first()
    if staff:
        staff.first_name = "Dummy"
        staff.last_name = "Staff"
        staff.email = "dummy.staff@dummybranch.test"
        staff.role = "staff"
        staff.password_hash = pw
        staff.is_active = True
        staff.status = "active"
        staff.branch = branch
        staff.updated_at = now
        staff.save()
        print("Updated staff")
    else:
        staff = Staff(
            mobile=STAFF_MOBILE,
            first_name="Dummy",
            last_name="Staff",
            email="dummy.staff@dummybranch.test",
            role="staff",
            password_hash=pw,
            is_active=True,
            status="active",
            branch=branch,
            created_at=now,
            updated_at=now,
        )
        staff.save()
        print("Created staff")

    mgr = Manager.objects(email=MGR_EMAIL).first()
    if mgr:
        mgr.first_name = "Dummy"
        mgr.last_name = "Manager"
        mgr.mobile = MGR_MOBILE
        mgr.salon = BRANCH_NAME
        mgr.password_hash = pw
        mgr.role = "manager"
        mgr.is_active = True
        mgr.status = "active"
        mgr.branch = branch
        mgr.updated_at = now
        mgr.save()
        print("Updated manager")
    else:
        mgr = Manager(
            first_name="Dummy",
            last_name="Manager",
            email=MGR_EMAIL,
            mobile=MGR_MOBILE,
            salon=BRANCH_NAME,
            password_hash=pw,
            role="manager",
            is_active=True,
            status="active",
            branch=branch,
            created_at=now,
            updated_at=now,
        )
        mgr.save()
        print("Created manager")

    owner = Owner.objects(email=OWNER_EMAIL).first()
    if owner:
        owner.first_name = "Dummy"
        owner.last_name = "Owner"
        owner.mobile = OWNER_MOBILE
        owner.salon = BRANCH_NAME
        owner.password_hash = pw
        owner.is_active = True
        owner.status = "active"
        owner.updated_at = now
        owner.save()
        print("Updated owner")
    else:
        owner = Owner(
            first_name="Dummy",
            last_name="Owner",
            email=OWNER_EMAIL,
            mobile=OWNER_MOBILE,
            salon=BRANCH_NAME,
            password_hash=pw,
            is_active=True,
            status="active",
            created_at=now,
            updated_at=now,
        )
        owner.save()
        print("Created owner")

    print("\n--- Dummy Branch test logins (password for all: %s) ---" % PASSWORD)
    print("Branch ID for X-Branch-Id / branch picker: %s" % branch.id)
    print(
        "Staff   | user_type: staff   | identifier: %s | branch: %s"
        % (STAFF_MOBILE, BRANCH_NAME)
    )
    print(
        "Manager | user_type: manager | identifier: %s | role: manager | branch_id when logging in: %s"
        % (MGR_EMAIL, branch.id)
    )
    print(
        "Owner   | user_type: manager | identifier: %s | role: owner | then switch to branch %s if needed"
        % (OWNER_EMAIL, BRANCH_NAME)
    )
    print("(Owners are not stored on a branch; pick Dummy Branch in the UI after login.)")

    disconnect()


if __name__ == "__main__":
    main()
