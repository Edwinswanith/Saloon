"""
Script to verify membership records in MongoDB and create them if they don't exist.
This script:
1. Checks if memberships collection exists
2. Verifies if there are any membership records
3. Creates sample membership records if collection is empty
4. Links memberships to membership plans and customers
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect, disconnect
from models import Customer, Membership, MembershipPlan, Branch

# MongoDB Configuration (using production database)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon_prod'  # Production database

# Connect to MongoDB
try:
    # Build connection URI with database name
    base_uri = MONGODB_URI
    
    # Remove any existing database name from URI
    if '@' in base_uri:
        parts = base_uri.split('@')
        if len(parts) == 2:
            credentials = parts[0]
            host_and_params = parts[1]
            
            if '/' in host_and_params:
                host = host_and_params.split('/')[0]
                if '?' in host_and_params:
                    params = '?' + host_and_params.split('?', 1)[1]
                else:
                    params = ''
                base_uri = f"{credentials}@{host}{params}"
    
    # Add database name to URI
    if f'/{MONGODB_DB}' not in base_uri:
        if '?' in base_uri:
            base_uri = base_uri.replace('?', f'/{MONGODB_DB}?')
        else:
            base_uri = f"{base_uri}/{MONGODB_DB}"
    
    # Add retry parameters if not present
    if 'retryWrites' not in base_uri:
        separator = '&' if '?' in base_uri else '?'
        base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
    
    connect(
        host=base_uri,
        alias='default',
        db=MONGODB_DB,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    print(f"[OK] Connected to MongoDB: {MONGODB_DB}")
except Exception as e:
    print(f"[ERROR] Error connecting to MongoDB: {e}")
    sys.exit(1)


def check_memberships_collection():
    """Check if memberships collection exists and has data"""
    print("\n" + "="*70)
    print("CHECKING MEMBERSHIPS COLLECTION")
    print("="*70)
    
    try:
        # Check if collection exists by trying to count documents
        total_count = Membership.objects().count()
        active_count = Membership.objects(status='active', expiry_date__gte=datetime.utcnow()).count()
        expired_count = Membership.objects(status='expired').count()
        
        print(f"\n[INFO] Collection Status:")
        print(f"   Collection Name: 'memberships'")
        print(f"   Total Records: {total_count}")
        print(f"   Active Memberships: {active_count}")
        print(f"   Expired Memberships: {expired_count}")
        
        if total_count > 0:
            print(f"\n[OK] Memberships collection exists and has {total_count} records")
            
            # Show sample records
            print(f"\n[INFO] Sample Membership Records:")
            sample_memberships = list(Membership.objects().limit(5))
            for i, m in enumerate(sample_memberships, 1):
                customer_name = f"{m.customer.first_name} {m.customer.last_name or ''}".strip() if m.customer else "Unknown"
                plan_name = m.plan.name if m.plan else "No Plan"
                expiry = m.expiry_date.strftime('%Y-%m-%d') if m.expiry_date else "N/A"
                status_icon = "[ACTIVE]" if m.status == 'active' and m.expiry_date and m.expiry_date >= datetime.utcnow() else "[EXPIRED]"
                print(f"   {i}. {status_icon} {customer_name} - {plan_name} (Expires: {expiry})")
            
            return True, total_count
        else:
            print(f"\n[WARNING] Memberships collection exists but is EMPTY")
            return True, 0
            
    except Exception as e:
        print(f"\n[ERROR] Error checking memberships collection: {e}")
        print(f"   Collection may not exist. Will create it.")
        return False, 0


def check_prerequisites():
    """Check if prerequisites (customers, membership plans) exist"""
    print("\n" + "="*70)
    print("CHECKING PREREQUISITES")
    print("="*70)
    
    # Check customers
    customer_count = Customer.objects().count()
    print(f"\n[INFO] Customers: {customer_count}")
    if customer_count == 0:
        print("   [WARNING] No customers found. Cannot create memberships without customers.")
        return False, None, None
    
    # Check membership plans
    plan_count = MembershipPlan.objects().count()
    active_plan_count = MembershipPlan.objects(status='active').count()
    print(f"[INFO] Membership Plans: {plan_count} total, {active_plan_count} active")
    
    if active_plan_count == 0:
        print("   [WARNING] No active membership plans found.")
        print("   [TIP] Run 'python create_membership_plans.py' first to create plans.")
        return False, None, None
    
    # Get customers and plans
    customers = list(Customer.objects())
    plans = list(MembershipPlan.objects(status='active'))
    
    print(f"\n[OK] Prerequisites met:")
    print(f"   - {len(customers)} customers available")
    print(f"   - {len(plans)} active membership plans available")
    
    return True, customers, plans


def create_membership_records(customers, plans):
    """Create membership records for customers"""
    print("\n" + "="*70)
    print("CREATING MEMBERSHIP RECORDS")
    print("="*70)
    
    # Get customers who already have active memberships
    existing_membership_customers = set()
    try:
        existing_memberships = list(Membership.objects(status='active', expiry_date__gte=datetime.utcnow()))
        for m in existing_memberships:
            try:
                if m.customer:
                    existing_membership_customers.add(str(m.customer.id))
            except:
                # Skip memberships with broken customer references
                continue
    except:
        # If there's an error, assume no existing memberships
        existing_memberships = []
    
    # Filter customers without memberships
    available_customers = [c for c in customers if str(c.id) not in existing_membership_customers]
    
    if not available_customers:
        print("\n[OK] All customers already have active memberships.")
        return 0
    
    # Create memberships for 10-20 customers (or all if less than 20)
    num_to_create = min(20, len(available_customers))
    selected_customers = random.sample(available_customers, num_to_create)
    
    print(f"\n[INFO] Creating {num_to_create} membership records...")
    print(f"   (Selected from {len(available_customers)} customers without memberships)")
    
    created_count = 0
    errors = []
    
    for i, customer in enumerate(selected_customers, 1):
        try:
            # Select a random plan
            plan = random.choice(plans)
            
            # Calculate dates
            # Purchase date: 0-60 days ago
            purchase_date = datetime.utcnow() - timedelta(days=random.randint(0, 60))
            # Expiry date: based on plan validity
            expiry_date = purchase_date + timedelta(days=plan.validity_days)
            
            # Ensure expiry is in the future (if not, extend it)
            if expiry_date <= datetime.utcnow():
                purchase_date = datetime.utcnow() - timedelta(days=random.randint(1, 10))
                expiry_date = purchase_date + timedelta(days=plan.validity_days)
            
            # Get customer's branch if available
            branch = customer.branch if hasattr(customer, 'branch') and customer.branch else None
            
            # Create membership
            membership = Membership(
                name=plan.name,
                customer=customer,
                plan=plan,
                branch=branch,
                price=float(plan.price),
                purchase_date=purchase_date,
                expiry_date=expiry_date,
                status='active',
                benefits=f"Discount: {plan.allocated_discount}% on all services",
                created_at=purchase_date,
                updated_at=datetime.utcnow()
            )
            membership.save()
            
            created_count += 1
            customer_name = f"{customer.first_name} {customer.last_name or ''}".strip()
            expiry_str = expiry_date.strftime('%Y-%m-%d')
            print(f"   [{i}/{num_to_create}] [OK] Created '{plan.name}' for {customer_name} ({customer.mobile})")
            print(f"       Purchase: {purchase_date.strftime('%Y-%m-%d')}, Expires: {expiry_str}, Discount: {plan.allocated_discount}%")
            
        except Exception as e:
            error_msg = f"Failed to create membership for customer {customer.mobile}: {str(e)}"
            errors.append(error_msg)
            print(f"   [{i}/{num_to_create}] [ERROR] {error_msg}")
            continue
    
    if errors:
        print(f"\n[WARNING] {len(errors)} errors occurred during creation")
    
    print(f"\n[SUCCESS] Successfully created {created_count} membership records!")
    return created_count


def display_summary():
    """Display final summary of memberships"""
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    total_memberships = Membership.objects().count()
    active_memberships = list(Membership.objects(status='active', expiry_date__gte=datetime.utcnow()))
    expired_memberships = list(Membership.objects(status='expired'))
    
    print(f"\n[INFO] Total Memberships: {total_memberships}")
    print(f"   [ACTIVE] Active: {len(active_memberships)}")
    print(f"   [EXPIRED] Expired: {len(expired_memberships)}")
    
    if active_memberships:
        # Group by plan
        plan_counts = {}
        for m in active_memberships:
            plan_name = m.plan.name if m.plan else "Unknown"
            plan_counts[plan_name] = plan_counts.get(plan_name, 0) + 1
        
        print(f"\n[INFO] Active Memberships by Plan:")
        for plan_name, count in sorted(plan_counts.items()):
            print(f"   - {plan_name}: {count} customers")
        
        # Show branch distribution
        branch_counts = {}
        for m in active_memberships:
            branch_name = m.branch.name if m.branch else "No Branch"
            branch_counts[branch_name] = branch_counts.get(branch_name, 0) + 1
        
        print(f"\n[INFO] Active Memberships by Branch:")
        for branch_name, count in sorted(branch_counts.items()):
            print(f"   - {branch_name}: {count} customers")


def main():
    """Main execution function"""
    try:
        print("\n" + "="*70)
        print("MEMBERSHIP VERIFICATION AND CREATION SCRIPT")
        print("="*70)
        print(f"Database: {MONGODB_DB}")
        print(f"Collection: memberships")
        
        # Step 1: Check if collection exists
        collection_exists, existing_count = check_memberships_collection()
        
        # Step 2: Check prerequisites
        prerequisites_ok, customers, plans = check_prerequisites()
        
        if not prerequisites_ok:
            print("\n[ERROR] Cannot proceed without prerequisites.")
            print("   Please ensure customers and membership plans exist.")
            return
        
        # Step 3: Create memberships if collection is empty or has few records
        if existing_count == 0:
            print("\n[INFO] Collection is empty. Creating membership records...")
            created = create_membership_records(customers, plans)
            if created > 0:
                print(f"\n[SUCCESS] Created {created} new membership records!")
        elif existing_count < 10:
            print(f"\n[INFO] Collection has only {existing_count} records. Creating more...")
            created = create_membership_records(customers, plans)
            if created > 0:
                print(f"\n[SUCCESS] Created {created} additional membership records!")
        else:
            print(f"\n[OK] Collection has {existing_count} records. No action needed.")
        
        # Step 4: Display final summary
        display_summary()
        
        print("\n" + "="*70)
        print("[SUCCESS] SCRIPT COMPLETED SUCCESSFULLY")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] Script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Disconnect from MongoDB
        try:
            disconnect()
        except:
            pass


if __name__ == '__main__':
    main()

