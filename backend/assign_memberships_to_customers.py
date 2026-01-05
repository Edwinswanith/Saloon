"""
Script to check existing customer memberships and assign membership plans to customers for testing
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Customer, Membership, MembershipPlan, Branch

# Connect to MongoDB
try:
    connect(
        db='Saloon',
        host='mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon',
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit(1)


def check_existing_memberships():
    """Check existing memberships in the database"""
    print("\n" + "="*60)
    print("Checking Existing Memberships")
    print("="*60)
    
    all_memberships = list(Membership.objects())
    active_memberships = list(Membership.objects(status='active', expiry_date__gte=datetime.utcnow()))
    expired_memberships = list(Membership.objects(status='expired'))
    
    print(f"\nTotal memberships in database: {len(all_memberships)}")
    print(f"Active memberships: {len(active_memberships)}")
    print(f"Expired memberships: {len(expired_memberships)}")
    
    if active_memberships:
        print("\nActive Memberships:")
        for m in active_memberships:
            customer_name = f"{m.customer.first_name} {m.customer.last_name or ''}".strip() if m.customer else "Unknown"
            plan_name = m.plan.name if m.plan else "No Plan"
            expiry = m.expiry_date.strftime('%Y-%m-%d') if m.expiry_date else "N/A"
            print(f"  - {customer_name} ({m.customer.mobile if m.customer else 'N/A'})")
            print(f"    Plan: {plan_name}, Expires: {expiry}, Status: {m.status}")
    
    return len(active_memberships)


def fix_existing_memberships():
    """Fix existing memberships that don't have a plan reference"""
    print("\n" + "="*60)
    print("Fixing Existing Memberships (Linking to Plans)")
    print("="*60)
    
    # Get all active membership plans
    plans = list(MembershipPlan.objects(status='active'))
    if not plans:
        print("\n[ERROR] No active membership plans found. Please create membership plans first.")
        return 0
    
    # Get memberships without plan references
    memberships_without_plans = list(Membership.objects(plan__exists=False))
    memberships_with_null_plans = list(Membership.objects(plan=None))
    all_missing_plans = list(set(memberships_without_plans + memberships_with_null_plans))
    
    if not all_missing_plans:
        print("\n[INFO] All existing memberships have plan references.")
        return 0
    
    print(f"\nFound {len(all_missing_plans)} memberships without plan references")
    
    fixed_count = 0
    for m in all_missing_plans:
        try:
            # Assign a random plan based on membership name or default to Gold
            plan_name = m.name.lower() if m.name else ""
            assigned_plan = None
            
            # Try to match by name
            for plan in plans:
                if plan.name.lower() in plan_name or plan_name in plan.name.lower():
                    assigned_plan = plan
                    break
            
            # If no match, assign based on price or default to middle tier
            if not assigned_plan:
                if m.price >= 7000:
                    assigned_plan = next((p for p in plans if 'diamond' in p.name.lower()), None)
                elif m.price >= 4000:
                    assigned_plan = next((p for p in plans if 'platinum' in p.name.lower()), None)
                elif m.price >= 2000:
                    assigned_plan = next((p for p in plans if 'gold' in p.name.lower()), None)
                else:
                    assigned_plan = next((p for p in plans if 'silver' in p.name.lower()), None)
            
            # Default to first plan if still no match
            if not assigned_plan:
                assigned_plan = plans[0]
            
            m.plan = assigned_plan
            m.name = assigned_plan.name  # Update name to match plan
            m.price = assigned_plan.price  # Update price to match plan
            m.updated_at = datetime.utcnow()
            m.save()
            
            fixed_count += 1
            customer_name = f"{m.customer.first_name} {m.customer.last_name or ''}".strip() if m.customer else "Unknown"
            print(f"  [{fixed_count}] Fixed membership for {customer_name} ({m.customer.mobile if m.customer else 'N/A'})")
            print(f"      Assigned plan: {assigned_plan.name} ({assigned_plan.allocated_discount}% discount)")
            
        except Exception as e:
            print(f"  [ERROR] Failed to fix membership: {str(e)}")
            continue
    
    print(f"\n[SUCCESS] Fixed {fixed_count} memberships!")
    return fixed_count


def assign_memberships_to_customers():
    """Assign membership plans to customers for testing"""
    print("\n" + "="*60)
    print("Assigning Membership Plans to Customers")
    print("="*60)
    
    # Get all active membership plans
    plans = list(MembershipPlan.objects(status='active'))
    if not plans:
        print("\n[ERROR] No active membership plans found. Please create membership plans first.")
        return
    
    print(f"\nFound {len(plans)} active membership plans:")
    for plan in plans:
        print(f"  - {plan.name}: {plan.allocated_discount}% discount, {plan.validity_days} days, Rs.{plan.price}")
    
    # Get all customers
    customers = list(Customer.objects())
    if not customers:
        print("\n[ERROR] No customers found in database.")
        return
    
    print(f"\nFound {len(customers)} customers")
    
    # Get customers who already have active memberships
    customers_with_memberships = set()
    existing_memberships = list(Membership.objects(status='active', expiry_date__gte=datetime.utcnow()))
    for m in existing_memberships:
        if m.customer:
            customers_with_memberships.add(str(m.customer.id))
    
    print(f"Customers with active memberships: {len(customers_with_memberships)}")
    
    # Filter out customers who already have memberships
    available_customers = [c for c in customers if str(c.id) not in customers_with_memberships]
    
    if not available_customers:
        print("\n[INFO] All customers already have active memberships.")
        return
    
    print(f"Available customers for membership assignment: {len(available_customers)}")
    
    # Assign memberships to 10-15 customers (or all if less than 15)
    num_to_assign = min(15, len(available_customers))
    selected_customers = random.sample(available_customers, num_to_assign)
    
    print(f"\nAssigning memberships to {num_to_assign} customers...")
    
    created_count = 0
    
    for i, customer in enumerate(selected_customers, 1):
        try:
            # Select a random plan
            plan = random.choice(plans)
            
            # Calculate dates
            purchase_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))  # Purchased 0-30 days ago
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
                price=plan.price,
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
            print(f"  [{i}/{num_to_assign}] Assigned '{plan.name}' to {customer_name} ({customer.mobile})")
            print(f"      Purchase: {purchase_date.strftime('%Y-%m-%d')}, Expires: {expiry_date.strftime('%Y-%m-%d')}, Discount: {plan.allocated_discount}%")
            
        except Exception as e:
            print(f"  [ERROR] Failed to assign membership to customer {customer.mobile}: {str(e)}")
            continue
    
    print(f"\n[SUCCESS] Created {created_count} new memberships!")
    
    # Display summary
    print("\n" + "="*60)
    print("Membership Assignment Summary")
    print("="*60)
    
    all_active = list(Membership.objects(status='active', expiry_date__gte=datetime.utcnow()))
    print(f"\nTotal active memberships: {len(all_active)}")
    
    # Group by plan
    plan_counts = {}
    for m in all_active:
        plan_name = m.plan.name if m.plan else "Unknown"
        plan_counts[plan_name] = plan_counts.get(plan_name, 0) + 1
    
    print("\nMemberships by plan:")
    for plan_name, count in plan_counts.items():
        print(f"  - {plan_name}: {count} customers")
    
    # List customers with memberships
    print("\nCustomers with active memberships:")
    for m in sorted(all_active, key=lambda x: x.customer.first_name if x.customer else ""):
        if m.customer:
            customer_name = f"{m.customer.first_name} {m.customer.last_name or ''}".strip()
            plan_name = m.plan.name if m.plan else "Unknown"
            discount = m.plan.allocated_discount if m.plan else 0
            expiry = m.expiry_date.strftime('%Y-%m-%d') if m.expiry_date else "N/A"
            print(f"  - {customer_name} ({m.customer.mobile}): {plan_name} - {discount}% discount, expires {expiry}")


if __name__ == '__main__':
    try:
        # First check existing memberships
        existing_count = check_existing_memberships()
        
        # Fix existing memberships that don't have plan references
        fixed_count = fix_existing_memberships()
        
        # Assign memberships to customers who don't have any
        print("\n[INFO] Assigning memberships to customers without memberships...")
        assign_memberships_to_customers()
        
        # Final summary
        print("\n" + "="*60)
        print("Final Summary")
        print("="*60)
        final_active = list(Membership.objects(status='active', expiry_date__gte=datetime.utcnow()))
        print(f"\nTotal active memberships: {len(final_active)}")
        
        # Group by plan
        plan_counts = {}
        for m in final_active:
            if m.plan:
                plan_name = m.plan.name
                plan_counts[plan_name] = plan_counts.get(plan_name, 0) + 1
        
        print("\nMemberships by plan:")
        for plan_name, count in sorted(plan_counts.items()):
            print(f"  - {plan_name}: {count} customers")
        
        print("\n" + "="*60)
        print("Script completed successfully!")
        print("="*60)
    except Exception as e:
        print(f"\n[ERROR] Script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

