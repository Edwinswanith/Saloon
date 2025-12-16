"""
Seed Membership Plans data
"""
from app import app, db
from models import MembershipPlan

def seed_membership_plans():
    """Add membership plans"""
    print("Seeding membership plans...")
    
    with app.app_context():
        # Check if plans already exist
        existing_count = MembershipPlan.query.count()
        if existing_count > 0:
            print(f"[INFO] {existing_count} membership plans already exist. Skipping.")
            return
        
        plans_data = [
            {
                'name': 'Silver Membership',
                'validity_days': 30,
                'price': 999.00,
                'allocated_discount': 5.0,
                'status': 'active',
                'description': 'Basic membership with 5% discount on all services'
            },
            {
                'name': 'Gold Membership',
                'validity_days': 90,
                'price': 2499.00,
                'allocated_discount': 10.0,
                'status': 'active',
                'description': 'Premium membership with 10% discount on all services'
            },
            {
                'name': 'Platinum Membership',
                'validity_days': 180,
                'price': 4499.00,
                'allocated_discount': 15.0,
                'status': 'active',
                'description': 'Elite membership with 15% discount on all services'
            },
            {
                'name': 'Diamond Membership',
                'validity_days': 365,
                'price': 7999.00,
                'allocated_discount': 20.0,
                'status': 'active',
                'description': 'Exclusive annual membership with 20% discount on all services'
            },
        ]
        
        plans = []
        for data in plans_data:
            plan = MembershipPlan(**data)
            plans.append(plan)
            db.session.add(plan)
        
        db.session.commit()
        print(f"[SUCCESS] Added {len(plans)} membership plans")
        
        # Display added plans
        for plan in plans:
            print(f"  - {plan.name}: Rs.{plan.price} ({plan.validity_days} days, {plan.allocated_discount}% discount)")

if __name__ == '__main__':
    seed_membership_plans()

