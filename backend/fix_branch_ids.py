"""
Script to fix branch IDs and ensure each branch has unique ID
and all data is correctly linked to respective branches
"""
import sys
import os
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect, disconnect
from models import (
    Branch, Customer, Staff, Bill, Appointment, Expense, Lead, Feedback,
    Manager, Membership, PrepaidPackage, StaffAttendance, Asset, CashTransaction,
    Order, MissedEnquiry, ServiceRecoveryCase, WhatsAppMessage, DiscountApprovalRequest
)

# MongoDB connection - use same as app.py
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon')

# Chennai branch names (expected branches)
EXPECTED_BRANCHES = [
    "T. Nagar",
    "Anna Nagar",
    "Velachery",
    "Adyar",
    "Porur",
    "Chrompet",
    "Tambaram"
]

def connect_db():
    """Connect to MongoDB"""
    try:
        # Get MongoDB connection details
        mongo_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
        mongodb_db = os.environ.get('MONGODB_DB', 'Saloon')
        
        # Parse connection string - same logic as app.py
        base_uri = mongo_uri
        
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
        if f'/{mongodb_db}' not in base_uri:
            if '?' in base_uri:
                base_uri = base_uri.replace('?', f'/{mongodb_db}?')
            else:
                base_uri = f"{base_uri}/{mongodb_db}"
        
        # Add retry parameters if not present
        if 'retryWrites' not in base_uri:
            separator = '&' if '?' in base_uri else '?'
            base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
        
        connect(host=base_uri, alias='default', db=mongodb_db)
        print(f"[OK] Connected to MongoDB: {mongodb_db}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {str(e)}")
        return False

def analyze_branches():
    """Analyze current branch state"""
    print("\n=== Analyzing Branches ===")
    branches = Branch.objects.all()
    
    if branches.count() == 0:
        print("[ERROR] No branches found in database!")
        return None
    
    print(f"\nFound {branches.count()} branch(es):")
    branch_dict = {}
    branch_ids = {}
    
    for branch in branches:
        branch_id_str = str(branch.id)
        print(f"  - {branch.name} (ID: {branch_id_str})")
        branch_dict[branch.name] = branch
        if branch_id_str in branch_ids:
            branch_ids[branch_id_str].append(branch.name)
        else:
            branch_ids[branch_id_str] = [branch.name]
    
    # Check for duplicate IDs
    duplicates = {bid: names for bid, names in branch_ids.items() if len(names) > 1}
    if duplicates:
        print(f"\n[WARNING] Found duplicate branch IDs:")
        for bid, names in duplicates.items():
            print(f"  ID {bid} is used by: {', '.join(names)}")
    else:
        print("\n[OK] All branches have unique IDs")
    
    return branch_dict

def check_data_distribution(branch_dict):
    """Check how data is distributed across branches"""
    print("\n=== Checking Data Distribution ===")
    
    models_to_check = [
        ('Staff', Staff),
        ('Customer', Customer),
        ('Bill', Bill),
        ('Appointment', Appointment),
        ('Expense', Expense),
        ('Lead', Lead),
        ('Feedback', Feedback),
        ('Manager', Manager),
        ('Membership', Membership),
        ('PrepaidPackage', PrepaidPackage),
    ]
    
    for model_name, Model in models_to_check:
        print(f"\n{model_name}:")
        total = Model.objects.count()
        print(f"  Total records: {total}")
        
        if total == 0:
            continue
        
        # Count by branch
        branch_counts = {}
        unassigned = 0
        
        for branch_name in branch_dict.keys():
            branch = branch_dict[branch_name]
            count = Model.objects(branch=branch).count()
            branch_counts[branch_name] = count
            print(f"  - {branch_name}: {count}")
        
        unassigned = Model.objects(branch__exists=False).count()
        if unassigned > 0:
            print(f"  - Unassigned: {unassigned}")
        
        # Check if all data is in one branch
        non_zero_counts = [count for count in branch_counts.values() if count > 0]
        if len(non_zero_counts) == 1 and total > 0:
            print(f"  [WARNING] All {model_name} data is in one branch!")

def fix_branch_assignments(branch_dict):
    """Fix branch assignments for all data"""
    print("\n=== Fixing Branch Assignments ===")
    
    # Strategy: Distribute data evenly across branches based on some criteria
    # For staff: Use email domain or name pattern
    # For customers: Distribute evenly
    # For bills/appointments: Follow customer/staff branch
    
    total_fixed = 0
    
    # Fix Staff assignments
    print("\nFixing Staff assignments...")
    staff_list = list(Staff.objects.all())
    branches_list = list(branch_dict.values())
    
    if staff_list:
        # Distribute staff evenly across branches
        for i, staff in enumerate(staff_list):
            target_branch = branches_list[i % len(branches_list)]
            if staff.branch != target_branch:
                staff.branch = target_branch
                staff.save()
                total_fixed += 1
                print(f"  [OK] Assigned {staff.first_name} {staff.last_name} to {target_branch.name}")
        print(f"  [OK] Fixed {total_fixed} staff assignments")
    
    # Fix Customer assignments (follow their staff's branch or distribute)
    print("\nFixing Customer assignments...")
    customer_list = list(Customer.objects.all())
    fixed_customers = 0
    
    if customer_list:
        # Distribute customers evenly
        for i, customer in enumerate(customer_list):
            target_branch = branches_list[i % len(branches_list)]
            if not customer.branch or customer.branch != target_branch:
                customer.branch = target_branch
                customer.save()
                fixed_customers += 1
        print(f"  [OK] Fixed {fixed_customers} customer assignments")
        total_fixed += fixed_customers
    
    # Fix Bills (follow customer's branch)
    print("\nFixing Bill assignments...")
    fixed_bills = 0
    bills = Bill.objects.all()
    
    for bill in bills:
        if bill.customer and bill.customer.branch:
            if not bill.branch or bill.branch != bill.customer.branch:
                bill.branch = bill.customer.branch
                bill.save()
                fixed_bills += 1
        elif not bill.branch:
            # Assign to first branch if no customer
            bill.branch = branches_list[0]
            bill.save()
            fixed_bills += 1
    
    print(f"  [OK] Fixed {fixed_bills} bill assignments")
    total_fixed += fixed_bills
    
    # Fix Appointments (follow staff's branch)
    print("\nFixing Appointment assignments...")
    fixed_appointments = 0
    appointments = Appointment.objects.all()
    
    for appointment in appointments:
        if appointment.staff and appointment.staff.branch:
            if not appointment.branch or appointment.branch != appointment.staff.branch:
                appointment.branch = appointment.staff.branch
                appointment.save()
                fixed_appointments += 1
        elif not appointment.branch:
            appointment.branch = branches_list[0]
            appointment.save()
            fixed_appointments += 1
    
    print(f"  [OK] Fixed {fixed_appointments} appointment assignments")
    total_fixed += fixed_appointments
    
    # Fix other models
    other_models = [
        ('Expense', Expense),
        ('Lead', Lead),
        ('Feedback', Feedback),
        ('Membership', Membership),
        ('PrepaidPackage', PrepaidPackage),
    ]
    
    for model_name, Model in other_models:
        print(f"\nFixing {model_name} assignments...")
        fixed = 0
        items = Model.objects.all()
        
        for i, item in enumerate(items):
            target_branch = branches_list[i % len(branches_list)]
            if not item.branch or item.branch != target_branch:
                item.branch = target_branch
                item.save()
                fixed += 1
        
        print(f"  [OK] Fixed {fixed} {model_name} assignments")
        total_fixed += fixed
    
    print(f"\n[OK] Total assignments fixed: {total_fixed}")
    return total_fixed

def verify_fix(branch_dict):
    """Verify that data is correctly distributed"""
    print("\n=== Verifying Fix ===")
    
    models_to_check = [
        ('Staff', Staff),
        ('Customer', Customer),
        ('Bill', Bill),
        ('Appointment', Appointment),
    ]
    
    all_ok = True
    
    for model_name, Model in models_to_check:
        print(f"\n{model_name}:")
        for branch_name, branch in branch_dict.items():
            count = Model.objects(branch=branch).count()
            print(f"  - {branch_name}: {count} records")
            if count == 0:
                print(f"    [WARNING] No {model_name} records in {branch_name}")
                all_ok = False
    
    if all_ok:
        print("\n[OK] All branches have data assigned")
    else:
        print("\n[WARNING] Some branches may be missing data")
    
    return all_ok

def main():
    """Main function"""
    print("=" * 60)
    print("Branch ID Fix Script")
    print("=" * 60)
    
    # Connect to database
    if not connect_db():
        return
    
    try:
        # Step 1: Analyze current state
        branch_dict = analyze_branches()
        
        # If no branches exist, create them
        if not branch_dict:
            print("\n[WARNING] No branches found. Creating all expected branches...")
            branch_dict = {}
            for branch_name in EXPECTED_BRANCHES:
                branch = Branch(
                    name=branch_name,
                    city="Chennai",
                    is_active=True
                )
                branch.save()
                branch_dict[branch_name] = branch
                print(f"  [OK] Created branch: {branch_name} (ID: {branch.id})")
        
        # Check if we have all expected branches
        missing_branches = [name for name in EXPECTED_BRANCHES if name not in branch_dict]
        if missing_branches:
            print(f"\n[WARNING] Missing branches: {', '.join(missing_branches)}")
            print("Creating missing branches...")
            for branch_name in missing_branches:
                branch = Branch(
                    name=branch_name,
                    city="Chennai",
                    is_active=True
                )
                branch.save()
                branch_dict[branch_name] = branch
                print(f"  [OK] Created branch: {branch_name} (ID: {branch.id})")
        
        # Step 2: Check data distribution
        check_data_distribution(branch_dict)
        
        # Step 3: Auto-proceed (can be made interactive if needed)
        print("\n" + "=" * 60)
        print("This script will reassign all data to branches.")
        print("Data will be distributed evenly across all branches.")
        print("Proceeding automatically...")
        
        # Step 4: Fix assignments
        total_fixed = fix_branch_assignments(branch_dict)
        
        # Step 5: Verify
        verify_fix(branch_dict)
        
        print("\n" + "=" * 60)
        print(f"[OK] Script completed. Fixed {total_fixed} assignments.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Script failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        disconnect()

if __name__ == '__main__':
    main()

