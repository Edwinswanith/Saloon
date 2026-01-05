"""
Script to create sample membership plans in MongoDB
This populates the Membership Plans section with tiered discount plans
"""

import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import MembershipPlan

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


def create_membership_plans():
    """Create sample membership plans with tiered discounts"""
    print("\n" + "="*60)
    print("Creating Membership Plans")
    print("="*60)
    
    # Define membership plans with tiered discounts
    plans_data = [
        {
            'name': 'Silver Membership',
            'validity_days': 30,
            'price': 999.00,
            'allocated_discount': 5.0,
            'status': 'active',
            'description': 'Basic membership with 5% discount on all services. Perfect for regular customers.'
        },
        {
            'name': 'Gold Membership',
            'validity_days': 90,
            'price': 2499.00,
            'allocated_discount': 10.0,
            'status': 'active',
            'description': 'Premium membership with 10% discount on all services. Great value for frequent visitors.'
        },
        {
            'name': 'Platinum Membership',
            'validity_days': 180,
            'price': 4499.00,
            'allocated_discount': 15.0,
            'status': 'active',
            'description': 'Elite membership with 15% discount on all services. Best for loyal customers.'
        },
        {
            'name': 'Diamond Membership',
            'validity_days': 365,
            'price': 7999.00,
            'allocated_discount': 20.0,
            'status': 'active',
            'description': 'Exclusive annual membership with 20% discount on all services. Maximum savings for VIP customers.'
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"\nCreating {len(plans_data)} membership plans...")
    
    for plan_data in plans_data:
        try:
            # Check if plan with same name already exists
            existing_plan = MembershipPlan.objects(name=plan_data['name']).first()
            
            if existing_plan:
                print(f"  [SKIP] Plan '{plan_data['name']}' already exists")
                skipped_count += 1
                continue
            
            # Create new plan
            plan = MembershipPlan(
                name=plan_data['name'],
                validity_days=plan_data['validity_days'],
                price=plan_data['price'],
                allocated_discount=plan_data['allocated_discount'],
                status=plan_data['status'],
                description=plan_data['description'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            plan.save()
            
            created_count += 1
            print(f"  [{created_count}/{len(plans_data)}] Created '{plan_data['name']}' - {plan_data['allocated_discount']}% discount, {plan_data['validity_days']} days, Rs.{plan_data['price']:.2f}")
            
        except Exception as e:
            print(f"  [ERROR] Failed to create plan '{plan_data['name']}': {str(e)}")
            skipped_count += 1
            continue
    
    print(f"\n[SUCCESS] Created {created_count} membership plans!")
    if skipped_count > 0:
        print(f"[INFO] Skipped {skipped_count} plans (already exist)")
    
    # Verify creation
    total_plans = MembershipPlan.objects.count()
    active_plans = MembershipPlan.objects(status='active').count()
    print(f"\n[VERIFICATION] Total plans in database: {total_plans}")
    print(f"[VERIFICATION] Active plans: {active_plans}")


if __name__ == '__main__':
    try:
        create_membership_plans()
        print("\n" + "="*60)
        print("Script completed successfully!")
        print("="*60)
    except Exception as e:
        print(f"\n[ERROR] Script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

