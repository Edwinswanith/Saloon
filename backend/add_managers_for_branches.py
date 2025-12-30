"""
Script to add managers for all branches
Creates one manager per branch if they don't already exist
"""
import sys
import os
import random

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
    while True:
        mobile = f"91{random.randint(1000000000, 9999999999)}"
        existing = Manager.objects(mobile=mobile).first()
        if not existing:
            return mobile

def add_managers_for_branches():
    """Add managers for all branches"""
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
        
        created_count = 0
        skipped_count = 0
        
        for idx, branch in enumerate(branches):
            print(f"\nProcessing branch: {branch.name}")
            
            # Check if branch already has a manager assigned
            existing_manager = Manager.objects(branch=branch, role='manager').first()
            if existing_manager:
                print(f"  ✓ Manager already exists: {existing_manager.first_name} {existing_manager.last_name} ({existing_manager.email})")
                skipped_count += 1
                continue
            
            # Get manager name for this branch (or use default)
            manager_name = MANAGER_NAMES[idx] if idx < len(MANAGER_NAMES) else {
                "first": f"Manager{idx+1}",
                "last": "Branch"
            }
            
            # Generate unique email and mobile - try multiple times if needed
            branch_name_clean = branch.name.lower().replace(' ', '').replace('.', '').replace('-', '')
            email = None
            mobile = None
            max_attempts = 10
            
            for attempt in range(max_attempts):
                # Try different email formats
                if attempt == 0:
                    email = f"{manager_name['first'].lower()}.{branch_name_clean}@salon.com"
                elif attempt == 1:
                    email = f"{manager_name['first'].lower()}{manager_name['last'].lower()}.{branch_name_clean}@salon.com"
                else:
                    email = f"{manager_name['first'].lower()}.{branch_name_clean}{attempt}@salon.com"
                
                mobile = generate_unique_mobile()
                
                # Check if email or mobile already exists
                existing = Manager.objects(
                    (Manager.email == email) | (Manager.mobile == mobile)
                ).first()
                
                if not existing:
                    break  # Found unique email and mobile
            
            if existing:
                print(f"  ✗ Could not generate unique email/mobile after {max_attempts} attempts - skipping")
                skipped_count += 1
                continue
            
            # Create manager
            try:
                manager = Manager(
                    first_name=manager_name['first'],
                    last_name=manager_name['last'],
                    email=email,
                    mobile=mobile,
                    salon=f"Salon - {branch.name}",
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
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Created: {created_count} managers")
        print(f"Skipped: {skipped_count} managers (already exist)")
        print(f"Total branches: {branches.count()}")
        
        # Show all managers with their branches
        print("\n" + "="*60)
        print("ALL MANAGERS BY BRANCH")
        print("="*60)
        all_managers = Manager.objects(role='manager').order_by('branch__name', 'first_name')
        for manager in all_managers:
            branch_name = manager.branch.name if manager.branch else "No Branch"
            print(f"  {manager.first_name} {manager.last_name} - {branch_name} ({manager.email})")
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*60)
    print("Add Managers for All Branches")
    print("="*60)
    print("\nThis script will create one manager for each branch")
    print("Default password for all managers: manager123")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    success = add_managers_for_branches()
    if success:
        print("\n✓ Script completed successfully!")
    else:
        print("\n✗ Script failed. Please check the errors above.")
        sys.exit(1)

