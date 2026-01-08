"""
Script to fix managers for all branches
This script will:
1. Check which branches don't have managers
2. Create managers for those branches
3. Assign existing managers to branches if they're not assigned
"""
import sys
import os
import random
import time

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Branch, Manager
from utils.auth import hash_password
from datetime import datetime

# MongoDB connection - use same as app.py
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon')

# Manager names for each branch
MANAGER_NAMES = [
    {"first": "Arun", "last": "Mehta"},      # T. Nagar
    {"first": "Kavita", "last": "Desai"},    # Anna Nagar
    {"first": "Rahul", "last": "Sharma"},    # Velachery
    {"first": "Priya", "last": "Patel"},     # Adyar
    {"first": "Vikram", "last": "Iyer"},     # Porur
    {"first": "Anjali", "last": "Nair"},     # Chrompet
    {"first": "Suresh", "last": "Reddy"}     # Tambaram
]

def generate_unique_mobile():
    """Generate a unique mobile number"""
    max_attempts = 50
    for _ in range(max_attempts):
        mobile = f"91{random.randint(1000000000, 9999999999)}"
        existing = Manager.objects(mobile=mobile).first()
        if not existing:
            return mobile
    # If we can't find unique mobile, use timestamp
    return f"91{int(time.time() * 1000) % 10000000000:010d}"

def fix_managers_for_branches():
    """Fix managers for all branches"""
    try:
        print("Connecting to MongoDB...")
        # Build connection URI with database name (same logic as app.py)
        base_uri = MONGO_URI
        
        # If URI contains a database path, remove it (we'll add our own)
        if '@' in base_uri:
            parts = base_uri.split('@')
            if len(parts) == 2:
                credentials = parts[0]
                host_and_params = parts[1]
                
                # Remove database name from host part if present
                if '/' in host_and_params:
                    host = host_and_params.split('/')[0]
                    # Keep query parameters if they exist
                    if '?' in host_and_params:
                        params = '?' + host_and_params.split('?', 1)[1]
                    else:
                        params = ''
                    base_uri = f"{credentials}@{host}{params}"
        
        # Add database name to URI if not present
        if f'/{MONGODB_DB}' not in base_uri:
            if '?' in base_uri:
                base_uri = base_uri.replace('?', f'/{MONGODB_DB}?')
            else:
                base_uri = f"{base_uri}/{MONGODB_DB}"
        
        # Add retry parameters if not present
        if 'retryWrites' not in base_uri:
            separator = '&' if '?' in base_uri else '?'
            base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
        
        # Connect with database name
        connect(host=base_uri, alias='default', db=MONGODB_DB)
        print("Connected successfully!")
        
        # Get all branches
        branches = Branch.objects(is_active=True).order_by('name')
        
        if not branches:
            print("\nNo branches found. Please create branches first using create_branches_and_sample_data.py")
            return False
        
        print(f"\nFound {branches.count()} branches")
        print("="*60)
        
        # First, show current state
        print("\nCURRENT STATE:")
        print("-" * 60)
        all_managers = Manager.objects()
        print(f"Total managers in database: {all_managers.count()}")
        for manager in all_managers:
            branch_name = manager.branch.name if manager.branch else "No Branch"
            print(f"  - {manager.first_name} {manager.last_name} ({manager.email}) - {branch_name}")
        
        print("\n" + "="*60)
        print("PROCESSING BRANCHES")
        print("="*60)
        
        created_count = 0
        skipped_count = 0
        assigned_count = 0
        
        for idx, branch in enumerate(branches):
            print(f"\nProcessing branch: {branch.name}")
            
            # Check if branch already has a manager assigned
            existing_manager = Manager.objects(branch=branch, role='manager').first()
            if existing_manager:
                print(f"  ✓ Manager already exists: {existing_manager.first_name} {existing_manager.last_name} ({existing_manager.email})")
                skipped_count += 1
                continue
            
            # Check if there's an unassigned manager we can assign
            unassigned_manager = Manager.objects(branch__exists=False, role='manager').first()
            if unassigned_manager:
                print(f"  → Assigning existing unassigned manager: {unassigned_manager.first_name} {unassigned_manager.last_name}")
                unassigned_manager.branch = branch
                unassigned_manager.save()
                assigned_count += 1
                continue
            
            # Get manager name for this branch (or use default)
            manager_name = MANAGER_NAMES[idx] if idx < len(MANAGER_NAMES) else {
                "first": f"Manager{idx+1}",
                "last": "Branch"
            }
            
            # Generate unique email and mobile
            branch_name_clean = branch.name.lower().replace(' ', '').replace('.', '').replace('-', '')
            
            # Try to create unique email
            email = None
            for attempt in range(10):
                if attempt == 0:
                    test_email = f"{manager_name['first'].lower()}.{branch_name_clean}@salon.com"
                else:
                    test_email = f"{manager_name['first'].lower()}.{branch_name_clean}{attempt}@salon.com"
                
                existing = Manager.objects(email=test_email).first()
                if not existing:
                    email = test_email
                    break
            
            # If still no unique email, use branch ID
            if not email:
                email = f"manager.{str(branch.id)[:8]}@salon.com"
                existing = Manager.objects(email=email).first()
                if existing:
                    # Last resort: timestamp
                    email = f"manager.{int(time.time())}@salon.com"
            
            # Generate unique mobile
            mobile = generate_unique_mobile()
            
            # Create manager
            try:
                manager = Manager(
                    first_name=manager_name['first'],
                    last_name=manager_name['last'],
                    email=email,
                    mobile=mobile,
                    salon=f"Saloon - {branch.name}",
                    password_hash=hash_password('manager123'),  # Default password: manager123
                    role='manager',
                    permissions=[],
                    is_active=True,
                    status='active',
                    branch=branch,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                manager.save()
                created_count += 1
                print(f"  ✓ Created manager: {manager.first_name} {manager.last_name}")
                print(f"     Email: {manager.email}")
                print(f"     Mobile: {manager.mobile}")
                print(f"     Password: manager123")
            except Exception as e:
                print(f"  ✗ Error creating manager for {branch.name}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Created: {created_count} managers")
        print(f"Assigned: {assigned_count} existing managers to branches")
        print(f"Skipped: {skipped_count} branches (already have managers)")
        print(f"Total branches: {branches.count()}")
        
        # Show all managers with their branches
        print("\n" + "="*60)
        print("ALL MANAGERS BY BRANCH")
        print("="*60)
        all_managers = Manager.objects(role='manager').order_by('branch__name', 'first_name')
        for manager in all_managers:
            branch_name = manager.branch.name if manager.branch else "No Branch"
            print(f"  {manager.first_name} {manager.last_name} - {branch_name} ({manager.email})")
        
        # Show owners separately
        owners = Manager.objects(role='owner')
        if owners.count() > 0:
            print("\n" + "="*60)
            print("OWNERS (No Branch Assignment)")
            print("="*60)
            for owner in owners:
                branch_name = owner.branch.name if owner.branch else "All Branches"
                print(f"  {owner.first_name} {owner.last_name} - {branch_name} ({owner.email})")
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*60)
    print("Fix Managers for All Branches")
    print("="*60)
    print("\nThis script will:")
    print("  1. Check which branches don't have managers")
    print("  2. Assign existing unassigned managers to branches")
    print("  3. Create new managers for branches that need them")
    print("  4. Default password for all new managers: manager123")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    success = fix_managers_for_branches()
    if success:
        print("\n✓ Script completed successfully!")
    else:
        print("\n✗ Script failed. Please check the errors above.")
        sys.exit(1)

