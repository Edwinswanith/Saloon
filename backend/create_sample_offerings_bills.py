"""
Script to create sample bills with offerings (services, products, packages)
for testing the Top 10 Offerings dashboard section.
"""
from mongoengine import connect
from models import Bill, Customer, Branch, Service, Product, Package, Staff
from datetime import datetime, timedelta
import os

# Connect to MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/saloon')
connect(host=MONGODB_URI)

def create_sample_offerings_bills():
    """Create sample bills with services, products, and packages"""
    
    # Get existing data
    branch = Branch.objects.first()
    if not branch:
        print("No branch found. Please create a branch first.")
        return
    
    customer = Customer.objects.first()
    if not customer:
        print("No customer found. Please create a customer first.")
        return
    
    staff = Staff.objects(status='active').first()
    if not staff:
        print("No active staff found. Please create staff first.")
        return
    
    # Get current services, products, and packages
    services = list(Service.objects(status='active')[:5])
    products = list(Product.objects(status='active')[:5])
    packages = list(Package.objects(status='active')[:3])
    
    if not services and not products and not packages:
        print("No services, products, or packages found. Please create some first.")
        return
    
    print(f"Found {len(services)} services, {len(products)} products, {len(packages)} packages")
    
    # Get today's date in IST (noon IST = 06:30 UTC)
    today = datetime.utcnow()
    ist_offset = timedelta(hours=5, minutes=30)
    today_ist = today + ist_offset
    # Set to noon IST
    today_ist = today_ist.replace(hour=12, minute=0, second=0, microsecond=0)
    # Convert back to UTC
    today_utc = today_ist - ist_offset
    
    bills_created = 0
    
    # Create bills with services
    for i, service in enumerate(services[:3]):
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{1000 + i}"
        
        # Check if bill already exists
        if Bill.objects(bill_number=bill_number).first():
            continue
        
        bill = Bill(
            bill_number=bill_number,
            customer=customer,
            branch=branch,
            bill_date=today_utc - timedelta(days=i),  # Spread across last few days
            subtotal=service.price,
            discount_amount=0.0,
            tax_amount=service.price * 0.18,
            final_amount=service.price * 1.18,
            payment_mode='cash',
            payment_status='paid',
            is_deleted=False
        )
        
        # Add service item
        from models import BillItemEmbedded
        item = BillItemEmbedded(
            item_type='service',
            service=service,
            staff=staff,
            start_time='10:00:00',
            price=service.price,
            discount=0.0,
            quantity=1,
            total=service.price
        )
        bill.items = [item]
        bill.save()
        bills_created += 1
        print(f"Created bill {bill_number} with service: {service.name}")
    
    # Create bills with products
    for i, product in enumerate(products[:3]):
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{2000 + i}"
        
        # Check if bill already exists
        if Bill.objects(bill_number=bill_number).first():
            continue
        
        bill = Bill(
            bill_number=bill_number,
            customer=customer,
            branch=branch,
            bill_date=today_utc - timedelta(days=i),
            subtotal=product.price,
            discount_amount=0.0,
            tax_amount=product.price * 0.18,
            final_amount=product.price * 1.18,
            payment_mode='upi',
            payment_status='paid',
            is_deleted=False
        )
        
        # Add product item
        from models import BillItemEmbedded
        item = BillItemEmbedded(
            item_type='product',
            product=product,
            price=product.price,
            discount=0.0,
            quantity=2,  # Multiple quantities
            total=product.price * 2
        )
        bill.items = [item]
        bill.subtotal = product.price * 2
        bill.final_amount = bill.subtotal * 1.18
        bill.tax_amount = bill.subtotal * 0.18
        bill.save()
        bills_created += 1
        print(f"Created bill {bill_number} with product: {product.name}")
    
    # Create bills with packages
    for i, package in enumerate(packages[:2]):
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{3000 + i}"
        
        # Check if bill already exists
        if Bill.objects(bill_number=bill_number).first():
            continue
        
        bill = Bill(
            bill_number=bill_number,
            customer=customer,
            branch=branch,
            bill_date=today_utc - timedelta(days=i),
            subtotal=package.price,
            discount_amount=0.0,
            tax_amount=package.price * 0.18,
            final_amount=package.price * 1.18,
            payment_mode='card',
            payment_status='paid',
            is_deleted=False
        )
        
        # Add package item
        from models import BillItemEmbedded
        item = BillItemEmbedded(
            item_type='package',
            package=package,
            price=package.price,
            discount=0.0,
            quantity=1,
            total=package.price
        )
        bill.items = [item]
        bill.save()
        bills_created += 1
        print(f"Created bill {bill_number} with package: {package.name}")
    
    print(f"\nCreated {bills_created} sample bills with offerings.")
    print("The Top 10 Offerings section should now display data.")

if __name__ == '__main__':
    create_sample_offerings_bills()

