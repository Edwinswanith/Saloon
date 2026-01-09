"""
Script to set passwords for all users (staff, managers, owners) across all branches.

Password Generation Rules:
- Staff: staff{BranchName}{Number} (e.g., staffAdyar1, staffT.Nagar2)
- Managers: manager{BranchName} (e.g., managerAdyar, managerT.Nagar)
- Owners: owner123 (common for all owners)

Usage:
    python set_all_user_passwords.py
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Staff, Manager, Owner, Branch
from utils.auth import hash_password, verify_password

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables directly

# MongoDB connection string (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

def sanitize_branch_name(branch_name):
    """
    Sanitize branch name for use in password.
    Remove spaces and special characters, keep alphanumeric.
    """
    if not branch_name:
        return 'Unknown'
    # Remove spaces and dots, keep alphanumeric
    sanitized = ''.join(c for c in branch_name if c.isalnum() or c == '.')
    return sanitized if sanitized else 'Unknown'


def set_staff_passwords():
    """Set passwords for all staff members."""
    print("\n" + "="*60)
    print("Setting Staff Passwords")
    print("="*60)

    # Get all branches
    branches = Branch.objects()
    staff_credentials = []

    for branch in branches:
        branch_name = sanitize_branch_name(branch.name)
        print(f"\nBranch: {branch.name} ({branch.city})")
        print("-" * 40)

        # Get staff for this branch
        staff_list = Staff.objects(branch=branch)

        if staff_list.count() == 0:
            print("  No staff members found")
            continue

        for idx, staff in enumerate(staff_list, 1):
            # Generate password: staff{BranchName}{Number}
            password = f"staff{branch_name}{idx}"

            # Hash and save password
            staff.password_hash = hash_password(password)
            staff.save()

            # Verify password was set correctly
            if verify_password(password, staff.password_hash):
                status = "OK"
            else:
                status = "FAILED"

            full_name = f"{staff.first_name} {staff.last_name or ''}".strip()
            print(f"  [{status}] {full_name} ({staff.mobile})")
            print(f"       Password: {password}")

            staff_credentials.append({
                'type': 'Staff',
                'branch': branch.name,
                'name': full_name,
                'identifier': staff.mobile,
                'password': password,
                'status': status
            })

    # Also handle staff without a branch
    staff_no_branch = Staff.objects(branch=None)
    if staff_no_branch.count() > 0:
        print(f"\nStaff without branch assignment:")
        print("-" * 40)
        for idx, staff in enumerate(staff_no_branch, 1):
            password = f"staffNoBranch{idx}"
            staff.password_hash = hash_password(password)
            staff.save()

            if verify_password(password, staff.password_hash):
                status = "OK"
            else:
                status = "FAILED"

            full_name = f"{staff.first_name} {staff.last_name or ''}".strip()
            print(f"  [{status}] {full_name} ({staff.mobile})")
            print(f"       Password: {password}")

            staff_credentials.append({
                'type': 'Staff',
                'branch': 'No Branch',
                'name': full_name,
                'identifier': staff.mobile,
                'password': password,
                'status': status
            })

    return staff_credentials


def set_manager_passwords():
    """Set passwords for all managers."""
    print("\n" + "="*60)
    print("Setting Manager Passwords")
    print("="*60)

    # Get all branches
    branches = Branch.objects()
    manager_credentials = []

    for branch in branches:
        branch_name = sanitize_branch_name(branch.name)
        print(f"\nBranch: {branch.name} ({branch.city})")
        print("-" * 40)

        # Get managers for this branch
        manager_list = Manager.objects(branch=branch, role='manager')

        if manager_list.count() == 0:
            print("  No managers found")
            continue

        for idx, manager in enumerate(manager_list, 1):
            # Generate password: manager{BranchName} or manager{BranchName}{Number} if multiple
            if manager_list.count() > 1:
                password = f"manager{branch_name}{idx}"
            else:
                password = f"manager{branch_name}"

            # Hash and save password
            manager.password_hash = hash_password(password)
            manager.save()

            # Verify password was set correctly
            if verify_password(password, manager.password_hash):
                status = "OK"
            else:
                status = "FAILED"

            full_name = f"{manager.first_name} {manager.last_name or ''}".strip()
            print(f"  [{status}] {full_name} ({manager.email})")
            print(f"       Password: {password}")

            manager_credentials.append({
                'type': 'Manager',
                'branch': branch.name,
                'name': full_name,
                'identifier': manager.email,
                'password': password,
                'status': status
            })

    # Also handle managers without a branch
    managers_no_branch = Manager.objects(branch=None, role='manager')
    if managers_no_branch.count() > 0:
        print(f"\nManagers without branch assignment:")
        print("-" * 40)
        for idx, manager in enumerate(managers_no_branch, 1):
            password = f"managerNoBranch{idx}"
            manager.password_hash = hash_password(password)
            manager.save()

            if verify_password(password, manager.password_hash):
                status = "OK"
            else:
                status = "FAILED"

            full_name = f"{manager.first_name} {manager.last_name or ''}".strip()
            print(f"  [{status}] {full_name} ({manager.email})")
            print(f"       Password: {password}")

            manager_credentials.append({
                'type': 'Manager',
                'branch': 'No Branch',
                'name': full_name,
                'identifier': manager.email,
                'password': password,
                'status': status
            })

    return manager_credentials


def set_owner_passwords():
    """Set passwords for all owners."""
    print("\n" + "="*60)
    print("Setting Owner Passwords")
    print("="*60)

    owner_credentials = []

    # Get all owners
    owners = Owner.objects()

    if owners.count() == 0:
        print("No owners found")
        return owner_credentials

    # Common password for all owners
    password = "owner123"

    for owner in owners:
        # Hash and save password
        owner.password_hash = hash_password(password)
        owner.save()

        # Verify password was set correctly
        if verify_password(password, owner.password_hash):
            status = "OK"
        else:
            status = "FAILED"

        full_name = f"{owner.first_name} {owner.last_name or ''}".strip()
        print(f"  [{status}] {full_name} ({owner.email})")
        print(f"       Password: {password}")

        owner_credentials.append({
            'type': 'Owner',
            'branch': 'All Branches',
            'name': full_name,
            'identifier': owner.email,
            'password': password,
            'status': status
        })

    return owner_credentials


def print_summary(staff_creds, manager_creds, owner_creds):
    """Print a summary of all credentials."""
    print("\n" + "="*60)
    print("CREDENTIALS SUMMARY")
    print("="*60)

    all_creds = staff_creds + manager_creds + owner_creds

    # Count successful and failed
    success_count = sum(1 for c in all_creds if c['status'] == 'OK')
    failed_count = sum(1 for c in all_creds if c['status'] == 'FAILED')

    print(f"\nTotal users processed: {len(all_creds)}")
    print(f"  - Staff: {len(staff_creds)}")
    print(f"  - Managers: {len(manager_creds)}")
    print(f"  - Owners: {len(owner_creds)}")
    print(f"\nResults:")
    print(f"  - Successful: {success_count}")
    print(f"  - Failed: {failed_count}")

    # Print all credentials in a table format
    print("\n" + "-"*80)
    print(f"{'Type':<10} {'Branch':<15} {'Name':<20} {'Login ID':<25} {'Password':<15}")
    print("-"*80)

    for cred in all_creds:
        # Truncate long values
        branch = cred['branch'][:13] + '..' if len(cred['branch']) > 15 else cred['branch']
        name = cred['name'][:18] + '..' if len(cred['name']) > 20 else cred['name']
        identifier = cred['identifier'][:23] + '..' if len(cred['identifier']) > 25 else cred['identifier']

        print(f"{cred['type']:<10} {branch:<15} {name:<20} {identifier:<25} {cred['password']:<15}")

    print("-"*80)


def main():
    """Main function to set all passwords."""
    print("="*60)
    print("PASSWORD GENERATION SCRIPT")
    print("="*60)
    print("\nConnecting to MongoDB...")

    # Connect to MongoDB (same connection logic as app.py)
    base_uri = MONGODB_URI

    # Handle URI formatting for database name
    # Check if the URI already has a database in the path
    if 'mongodb+srv://' in base_uri or 'mongodb://' in base_uri:
        # Split URI to check path
        if '?' in base_uri:
            uri_parts = base_uri.split('?')
            host_and_path = uri_parts[0]
            query = uri_parts[1]

            # Check if there's already a database in path
            if host_and_path.endswith('.net') or host_and_path.endswith('.net/'):
                # No database in path, add it
                if host_and_path.endswith('/'):
                    base_uri = f"{host_and_path}{MONGODB_DB}?{query}"
                else:
                    base_uri = f"{host_and_path}/{MONGODB_DB}?{query}"

    connect(host=base_uri, db=MONGODB_DB,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000)
    print("Connected successfully!")

    # Count existing users
    print(f"\nDatabase statistics:")
    print(f"  - Branches: {Branch.objects.count()}")
    print(f"  - Staff: {Staff.objects.count()}")
    print(f"  - Managers: {Manager.objects(role='manager').count()}")
    print(f"  - Owners: {Owner.objects.count()}")

    # Set passwords for all user types
    staff_creds = set_staff_passwords()
    manager_creds = set_manager_passwords()
    owner_creds = set_owner_passwords()

    # Print summary
    print_summary(staff_creds, manager_creds, owner_creds)

    print("\n" + "="*60)
    print("PASSWORD GENERATION COMPLETE!")
    print("="*60)
    print("\nIMPORTANT: Please save these credentials securely.")
    print("Users can now log in with their new passwords.")
    print("\nPassword Rules Used:")
    print("  - Staff: staff{BranchName}{Number}")
    print("  - Managers: manager{BranchName}")
    print("  - Owners: owner123")


if __name__ == '__main__':
    main()
