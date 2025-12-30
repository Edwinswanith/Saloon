from mongoengine import connect
from models import Supplier, Customer, Branch
from datetime import datetime, timedelta
import random
import os

# Connect to MongoDB
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
connect(host=MONGODB_URI, db='Saloon')

def populate_suppliers():
    """Create sample suppliers"""
    branches = list(Branch.objects())
    
    if not branches:
        print("ERROR: No branches found! Please create branches first.")
        return
    
    supplier_data = [
        ("Beauty Products India", "9876543210", "contact@beautyproducts.in", "Mumbai, Maharashtra"),
        ("Hair Care Wholesale", "9876543211", "sales@haircare.com", "Delhi"),
        ("Professional Salon Supplies", "9876543212", "info@salonsupplies.in", "Bangalore, Karnataka"),
        ("Cosmetics Direct", "9876543213", "orders@cosmeticsdirect.com", "Chennai, Tamil Nadu"),
        ("Spa Equipment Co", "9876543214", "support@spaequipment.in", "Hyderabad, Telangana"),
        ("Nail Art Supplies", "9876543215", "sales@nailart.in", "Pune, Maharashtra"),
        ("Hair Color Specialists", "9876543216", "info@haircolor.com", "Kolkata, West Bengal"),
        ("Salon Furniture Plus", "9876543217", "contact@salonfurniture.in", "Ahmedabad, Gujarat"),
        ("Beauty Tools Pvt Ltd", "9876543218", "sales@beautytools.co.in", "Jaipur, Rajasthan"),
        ("Hygiene Products Supply", "9876543219", "orders@hygiene.in", "Lucknow, Uttar Pradesh"),
    ]
    
    created_count = 0
    for idx, (name, phone, email, address) in enumerate(supplier_data):
        existing = Supplier.objects(name=name).first()
        if not existing:
            # Distribute suppliers across branches
            branch = branches[idx % len(branches)]
            
            Supplier(
                name=name,
                contact_no=phone,
                email=email,
                address=address,
                status='active',
                branch=branch
            ).save()
            created_count += 1
            print(f"  Created supplier: {name} ({branch.name})")
        else:
            print(f"  Skipped (exists): {name}")
    
    print(f"\nCreated {created_count} new suppliers")

def enhance_customer_lifecycle_data():
    """Enhance existing customers with lifecycle data"""
    customers = list(Customer.objects())
    
    # Categorize customers into segments
    total_customers = len(customers)
    
    print(f"Found {total_customers} customers")
    
    if total_customers < 10:
        print("WARNING: Not enough customers. Run populate_sample_data.py first!")
        print("Creating minimal lifecycle data with available customers...")
    
    # Update customer stats to create segments
    new_count = min(10, max(1, total_customers // 5))
    regular_count = min(15, max(2, total_customers // 3))
    loyal_count = min(10, max(1, total_customers // 5))
    high_spending_count = min(8, max(1, total_customers // 6))
    inactive_count = min(7, max(1, total_customers // 7))
    
    # Adjust counts to not exceed total
    total_needed = new_count + regular_count + loyal_count + high_spending_count + inactive_count
    if total_needed > total_customers:
        # Scale down proportionally
        scale = total_customers / total_needed
        new_count = max(1, int(new_count * scale))
        regular_count = max(1, int(regular_count * scale))
        loyal_count = max(1, int(loyal_count * scale))
        high_spending_count = max(1, int(high_spending_count * scale))
        inactive_count = max(1, int(inactive_count * scale))
    
    idx = 0
    
    # Create NEW customers (0 visits)
    print(f"\nCreating {new_count} NEW customers...")
    for i in range(new_count):
        if idx >= total_customers:
            break
        customer = customers[idx]
        customer.total_visits = 0
        customer.total_spent = 0.0
        customer.last_visit_date = None
        customer.save()
        idx += 1
    
    # Create REGULAR customers (5-9 visits)
    print(f"Creating {regular_count} REGULAR customers...")
    for i in range(regular_count):
        if idx >= total_customers:
            break
        customer = customers[idx]
        customer.total_visits = random.randint(5, 9)
        customer.total_spent = float(random.randint(1000, 2800))
        customer.last_visit_date = (datetime.now() - timedelta(days=random.randint(1, 60))).date()
        customer.save()
        idx += 1
    
    # Create LOYAL customers (10+ visits, 5000+ spent)
    print(f"Creating {loyal_count} LOYAL customers...")
    for i in range(loyal_count):
        if idx >= total_customers:
            break
        customer = customers[idx]
        customer.total_visits = random.randint(10, 25)
        customer.total_spent = float(random.randint(5000, 15000))
        customer.last_visit_date = (datetime.now() - timedelta(days=random.randint(1, 30))).date()
        customer.save()
        idx += 1
    
    # Create HIGH-SPENDING customers (3000+ spent, fewer visits)
    print(f"Creating {high_spending_count} HIGH-SPENDING customers...")
    for i in range(high_spending_count):
        if idx >= total_customers:
            break
        customer = customers[idx]
        customer.total_visits = random.randint(2, 4)
        customer.total_spent = float(random.randint(3000, 4800))
        customer.last_visit_date = (datetime.now() - timedelta(days=random.randint(1, 45))).date()
        customer.save()
        idx += 1
    
    # Create INACTIVE customers (90+ days since last visit)
    print(f"Creating {inactive_count} INACTIVE customers...")
    for i in range(inactive_count):
        if idx >= total_customers:
            break
        customer = customers[idx]
        customer.total_visits = random.randint(3, 8)
        customer.total_spent = float(random.randint(500, 2000))
        customer.last_visit_date = (datetime.now() - timedelta(days=random.randint(91, 180))).date()
        customer.save()
        idx += 1
    
    print(f"\n{'='*60}")
    print("Customer Lifecycle Summary:")
    print(f"{'='*60}")
    print(f"  New (0 visits): {new_count}")
    print(f"  Regular (5-9 visits): {regular_count}")
    print(f"  Loyal (10+ visits, 5000+ spent): {loyal_count}")
    print(f"  High-Spending (3000+ spent): {high_spending_count}")
    print(f"  Inactive (90+ days): {inactive_count}")
    print(f"  Total enhanced: {idx}/{total_customers}")

if __name__ == "__main__":
    print("="*60)
    print("Populating Inventory & Customer Lifecycle Data")
    print("="*60)
    
    print("\n1. Creating Suppliers...")
    print("-" * 60)
    populate_suppliers()
    
    print("\n2. Enhancing Customer Lifecycle Data...")
    print("-" * 60)
    enhance_customer_lifecycle_data()
    
    print("\n" + "="*60)
    print("COMPLETE! Data populated successfully.")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart the backend server")
    print("2. Refresh your browser")
    print("3. Check Inventory section for suppliers")
    print("4. Check Customer Lifecycle Report for segments")

