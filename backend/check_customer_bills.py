"""
Script to check customer bills and create sample bills if needed
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Customer, Bill, Branch, Service, Staff
from bson import ObjectId

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

def check_bills():
    """Check existing bills for customers"""
    
    try:
        # Get some customers
        customers = Customer.objects.limit(5)
        
        print("\n" + "="*60)
        print("Checking Customer Bills")
        print("="*60)
        
        for customer in customers:
            bills = Bill.objects(customer=customer)
            bill_count = bills.count()
            
            print(f"\nCustomer: {customer.first_name} {customer.last_name} (ID: {customer.id})")
            print(f"  Mobile: {customer.mobile}")
            print(f"  Bills Count: {bill_count}")
            
            if bill_count > 0:
                for bill in bills[:3]:  # Show first 3 bills
                    print(f"    - Bill #{bill.bill_number}: Rs.{bill.final_amount:.2f} ({bill.bill_date.strftime('%Y-%m-%d')})")
        
        # Check total bills
        total_bills = Bill.objects.count()
        print(f"\n\nTotal Bills in Database: {total_bills}")
        
        if total_bills == 0:
            print("\nNo bills found! Creating sample bills...")
            create_sample_bills()
        
    except Exception as e:
        print(f"\nError checking bills: {str(e)}")
        import traceback
        traceback.print_exc()

def create_sample_bills():
    """Create sample bills for testing"""
    
    try:
        # Get required data
        customers = list(Customer.objects.limit(10))
        branches = list(Branch.objects.all())
        services = list(Service.objects.all())
        staffs = list(Staff.objects.all())
        
        if not customers:
            print("No customers found!")
            return
        
        if not branches:
            print("No branches found!")
            return
        
        print(f"\nFound {len(customers)} customers, {len(branches)} branches, {len(services)} services")
        
        bills_created = 0
        
        for customer in customers[:5]:  # Create bills for first 5 customers
            # Create 2-5 bills per customer
            num_bills = random.randint(2, 5)
            
            for i in range(num_bills):
                # Generate bill data
                bill_date = datetime.now() - timedelta(days=random.randint(1, 180))
                subtotal = random.uniform(500, 5000)
                discount = random.uniform(0, subtotal * 0.2)
                tax = (subtotal - discount) * 0.18
                final_amount = subtotal - discount + tax
                
                # Create bill
                bill = Bill(
                    bill_number=f"BILL-TEST-{ObjectId()}",
                    customer=customer,
                    branch=random.choice(branches) if branches else None,
                    bill_date=bill_date,
                    subtotal=subtotal,
                    discount_amount=discount,
                    discount_type='fix',
                    tax_amount=tax,
                    tax_rate=18.0,
                    final_amount=final_amount,
                    payment_mode=random.choice(['cash', 'upi', 'card', 'wallet']),
                    booking_status='service-completed',
                    is_deleted=False
                )
                bill.save()
                bills_created += 1
                
                print(f"Created bill for {customer.first_name}: Rs.{final_amount:.2f}")
        
        print(f"\n[SUCCESS] Created {bills_created} sample bills!")
        
    except Exception as e:
        print(f"\n[ERROR] Error creating sample bills: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Customer Bills Check Script")
    print("="*60)
    
    check_bills()
    
    print("\n" + "="*60)
    print("Script completed!")
    print("="*60 + "\n")

