"""
Script to create 7 Chennai branches and generate sample data for each
"""
import sys
import os
import random
from datetime import datetime, timedelta, date

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import (
    Branch, Customer, Staff, Bill, Appointment, Expense, Lead, Feedback,
    ServiceGroup, Service, ProductCategory, Product, Package
)
from utils.auth import hash_password

# MongoDB connection - use same as app.py
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon')

# Chennai branch names
BRANCHES = [
    {"name": "T. Nagar", "address": "123 Main Street, T. Nagar", "phone": "044-12345678"},
    {"name": "Anna Nagar", "address": "456 Park Avenue, Anna Nagar", "phone": "044-23456789"},
    {"name": "Velachery", "address": "789 Velachery Main Road", "phone": "044-34567890"},
    {"name": "Adyar", "address": "321 Adyar Bridge Road", "phone": "044-45678901"},
    {"name": "Porur", "address": "654 Porur High Road", "phone": "044-56789012"},
    {"name": "Chrompet", "address": "987 Chrompet Main Road", "phone": "044-67890123"},
    {"name": "Tambaram", "address": "147 GST Road, Tambaram", "phone": "044-78901234"}
]

# Sample data
FIRST_NAMES = ["Raj", "Priya", "Karthik", "Anjali", "Suresh", "Meera", "Vikram", "Divya", "Arjun", "Kavya"]
LAST_NAMES = ["Kumar", "Sharma", "Patel", "Reddy", "Iyer", "Nair", "Menon", "Pillai", "Rao", "Singh"]
MOBILE_PREFIXES = ["91", "91", "91", "91", "91"]  # Indian mobile numbers

def generate_mobile():
    """Generate random mobile number"""
    prefix = random.choice(MOBILE_PREFIXES)
    number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return f"{prefix}{number}"

def create_branches():
    """Create 7 Chennai branches"""
    branches = []
    for branch_data in BRANCHES:
        branch = Branch.objects(name=branch_data["name"]).first()
        if not branch:
            branch = Branch(
                name=branch_data["name"],
                address=branch_data["address"],
                city="Chennai",
                phone=branch_data["phone"],
                email=f"{branch_data['name'].lower().replace(' ', '').replace('.', '')}@salon.com",
                is_active=True
            )
            branch.save()
            print(f"Created branch: {branch.name}")
        else:
            print(f"Branch already exists: {branch.name}")
        branches.append(branch)
    return branches

def create_sample_data_for_branch(branch, num_staff=1, num_customers=75, num_bills=150, num_appointments=75):
    """Create sample data for a branch"""
    print(f"\nCreating sample data for {branch.name}...")
    
    # Create Staff
    staff_list = []
    for i in range(num_staff):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        mobile = generate_mobile()
        
        # Check if staff with this mobile exists
        existing = Staff.objects(mobile=mobile).first()
        if existing:
            continue
        
        # With reduced staff count, create only regular staff (no manager/owner roles)
        role = 'staff'
        
        staff = Staff(
            mobile=mobile,
            first_name=first_name,
            last_name=last_name,
            email=f"{first_name.lower()}.{last_name.lower()}@{branch.name.lower().replace(' ', '')}.com",
            salary=random.randint(15000, 50000),
            commission_rate=random.uniform(5, 15),
            status='active',
            role=role,
            is_active=True,
            branch=branch
        )
        
        # No password for regular staff (they use role selection login)
        
        staff.save()
        staff_list.append(staff)
        if i < 3:
            print(f"  Created {role}: {first_name} {last_name}")
    
    print(f"  Created {len(staff_list)} staff members")
    
    # Create Customers
    customers = []
    for i in range(num_customers):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        mobile = generate_mobile()
        
        # Check if customer with this mobile exists in this branch
        existing = Customer.objects(mobile=mobile, branch=branch).first()
        if existing:
            continue
        
        customer = Customer(
            mobile=mobile,
            first_name=first_name,
            last_name=last_name,
            email=f"{first_name.lower()}.{last_name.lower()}@example.com",
            source=random.choice(['Walk-in', 'Facebook', 'Instagram', 'Referral', 'Google']),
            gender=random.choice(['Male', 'Female', 'Other']),
            loyalty_points=random.randint(0, 500),
            wallet_balance=random.uniform(0, 5000),
            branch=branch
        )
        customer.save()
        customers.append(customer)
    
    print(f"  Created {len(customers)} customers")
    
    # Create Bills (need services first)
    services = Service.objects()[:10]  # Get first 10 services
    if not services:
        print("  Warning: No services found. Skipping bills creation.")
        return
    
    bills = []
    for i in range(num_bills):
        customer = random.choice(customers) if customers else None
        staff = random.choice(staff_list) if staff_list else None
        
        bill_date = datetime.now() - timedelta(days=random.randint(0, 90))
        
        bill = Bill(
            bill_number=f"BILL-{branch.name[:3].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i:04d}",
            customer=customer,
            branch=branch,
            bill_date=bill_date,
            subtotal=random.uniform(500, 5000),
            discount_amount=random.uniform(0, 500),
            tax_amount=random.uniform(50, 500),
            final_amount=random.uniform(500, 5500),
            payment_mode=random.choice(['cash', 'upi', 'card', 'wallet']),
            booking_status='service-completed',
            is_deleted=False
        )
        bill.save()
        bills.append(bill)
    
    print(f"  Created {len(bills)} bills")
    
    # Create Appointments
    appointments = []
    for i in range(num_appointments):
        customer = random.choice(customers) if customers else None
        staff = random.choice(staff_list) if staff_list else None
        
        if not customer or not staff:
            continue
        
        appointment_date = date.today() + timedelta(days=random.randint(-30, 30))
        start_hour = random.randint(9, 18)
        start_time = f"{start_hour:02d}:00:00"
        
        appointment = Appointment(
            customer=customer,
            staff=staff,
            branch=branch,
            appointment_date=appointment_date,
            start_time=start_time,
            status=random.choice(['confirmed', 'completed', 'cancelled']),
            notes=f"Appointment for {branch.name}"
        )
        appointment.save()
        appointments.append(appointment)
    
    print(f"  Created {len(appointments)} appointments")
    
    # Create some Expenses
    expenses = []
    for i in range(20):
        expense_date = date.today() - timedelta(days=random.randint(0, 60))
        
        # Get or create expense category
        from models import ExpenseCategory
        category = ExpenseCategory.objects().first()
        if not category:
            category = ExpenseCategory(name="General")
            category.save()
        
        expense = Expense(
            category=category,
            branch=branch,
            name=f"Expense {i+1}",
            amount=random.uniform(100, 5000),
            payment_mode=random.choice(['cash', 'card', 'upi']),
            expense_date=expense_date
        )
        expense.save()
        expenses.append(expense)
    
    print(f"  Created {len(expenses)} expenses")
    
    print(f"✓ Completed sample data for {branch.name}")

def main():
    """Main function"""
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
        
        print("\n" + "="*50)
        print("Creating Branches and Sample Data")
        print("="*50)
        
        # Create branches
        branches = create_branches()
        
        # Create sample data for each branch
        for branch in branches:
            create_sample_data_for_branch(branch)
        
        print("\n" + "="*50)
        print("Sample data generation completed!")
        print("="*50)
        print(f"\nCreated {len(branches)} branches with sample data")
        print("\nDefault login credentials:")
        print("  Manager: Use any manager mobile/email with password: password123")
        print("  Owner: Use any owner mobile/email with password: password123")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("="*50)
    print("Branch and Sample Data Creation Script")
    print("="*50)
    print("\nThis script will create 7 Chennai branches and sample data for each")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    success = main()
    if success:
        print("\n✓ Script completed successfully!")
    else:
        print("\n✗ Script failed. Please check the errors above.")
        sys.exit(1)

