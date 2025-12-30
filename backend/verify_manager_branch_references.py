"""
Verify and fix manager-branch reference integrity

This script will:
1. Check all managers and their branch references
2. Identify managers with invalid/missing branch references
3. Report detailed statistics
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Manager, Branch
from bson import ObjectId

# Use the same MongoDB configuration as app.py
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon')

def verify_manager_branches():
    """Verify manager-branch reference integrity"""
    connect(db=MONGODB_DB, host=MONGO_URI)

    print("="*60)
    print("Manager-Branch Reference Verification")
    print("="*60)

    all_managers = Manager.objects(role='manager')
    all_branches = Branch.objects()
    branches_dict = {str(b.id): b for b in all_branches}

    print(f"\nTotal Managers: {all_managers.count()}")
    print(f"Total Branches: {len(branches_dict)}")
    print("\n" + "-"*60)

    issues = []
    valid = []

    for manager in all_managers:
        print(f"\nManager: {manager.first_name} {manager.last_name} ({manager.email})")
        print(f"  Role: {manager.role}")
        print(f"  Is Active: {manager.is_active}")
        print(f"  Status: {manager.status}")

        if not manager.branch:
            print(f"  [ERROR] No branch assigned")
            issues.append({
                'manager': manager,
                'issue': 'no_branch',
                'fix': 'Assign a branch to this manager'
            })
            continue

        # Check if branch reference is valid
        try:
            branch_id = str(manager.branch.id)
            branch_name = manager.branch.name
            print(f"  Branch ID: {branch_id}")
            print(f"  Branch Name: {branch_name}")

            # Verify branch exists in database
            if branch_id not in branches_dict:
                print(f"  [ERROR] Branch ID {branch_id} not found in branches collection")
                issues.append({
                    'manager': manager,
                    'issue': 'invalid_branch_ref',
                    'branch_id': branch_id,
                    'fix': 'Re-assign to valid branch (branch was deleted)'
                })
            else:
                print(f"  [OK] Valid branch reference")
                valid.append({
                    'manager': manager,
                    'branch': branches_dict[branch_id]
                })

        except Exception as e:
            print(f"  [ERROR] Error accessing branch - {type(e).__name__}: {e}")
            issues.append({
                'manager': manager,
                'issue': 'corrupted_ref',
                'error': str(e),
                'fix': 'Re-assign branch reference (data corruption)'
            })

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Valid: {len(valid)} managers")
    print(f"Issues: {len(issues)} managers")

    if valid:
        print("\n" + "="*60)
        print("VALID MANAGERS BY BRANCH")
        print("="*60)

        # Group by branch
        by_branch = {}
        for item in valid:
            branch_name = item['branch'].name
            if branch_name not in by_branch:
                by_branch[branch_name] = []
            by_branch[branch_name].append(item['manager'])

        for branch_name in sorted(by_branch.keys()):
            managers = by_branch[branch_name]
            print(f"\n{branch_name}: {len(managers)} manager(s)")
            for mgr in managers:
                print(f"  - {mgr.first_name} {mgr.last_name} ({mgr.email})")

    if issues:
        print("\n" + "="*60)
        print("ISSUES FOUND")
        print("="*60)
        for idx, issue in enumerate(issues, 1):
            manager = issue['manager']
            print(f"\n{idx}. {manager.first_name} {manager.last_name} ({manager.email})")
            print(f"   Issue Type: {issue['issue']}")
            print(f"   Recommended Fix: {issue['fix']}")
            if 'branch_id' in issue:
                print(f"   Invalid Branch ID: {issue['branch_id']}")
            if 'error' in issue:
                print(f"   Error Details: {issue['error']}")

    print("\n" + "="*60)

    if len(issues) == 0:
        print("[SUCCESS] All manager-branch references are valid!")
        print("The filtering issue is likely in the query logic, not data corruption.")
    else:
        print(f"[WARNING] Found {len(issues)} issue(s) that need to be fixed.")
        print("Run fix_manager_branch_references.py to repair (after creating it).")

    print("="*60 + "\n")

    return len(issues) == 0

if __name__ == '__main__':
    try:
        is_valid = verify_manager_branches()
        sys.exit(0 if is_valid else 1)
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
