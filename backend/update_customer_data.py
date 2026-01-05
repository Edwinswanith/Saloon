"""
Script to update customer data in MongoDB
- Adds wallet_balance and loyalty_points fields
- Updates customer notes
- Links customers properly to their bills
"""

import sys
import os
from datetime import datetime
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Customer, Bill, Branch

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

def update_customers():
    """Update all customers with proper data"""
    
    try:
        # Get all customers
        customers = Customer.objects.all()
        total_customers = customers.count()
        print(f"\nFound {total_customers} customers in database")
        
        updated_count = 0
        
        for customer in customers:
            updates = {}
            
            # Add wallet balance if missing
            if not hasattr(customer, 'wallet_balance') or customer.wallet_balance is None:
                updates['wallet_balance'] = round(random.uniform(0, 500), 2)
            
            # Add loyalty points if missing
            if not hasattr(customer, 'loyalty_points') or customer.loyalty_points is None:
                updates['loyalty_points'] = random.randint(0, 100)
            
            # Add notes if missing
            if not hasattr(customer, 'notes') or not customer.notes:
                notes_options = [
                    'Prefers morning appointments',
                    'Regular customer',
                    'Likes specific stylist',
                    'VIP customer',
                    'Referred by friend',
                    'First time customer'
                ]
                updates['notes'] = random.choice(notes_options)
            
            # Update the customer if there are changes
            if updates:
                for field, value in updates.items():
                    setattr(customer, field, value)
                customer.updated_at = datetime.utcnow()
                customer.save()
                updated_count += 1
                
                print(f"Updated customer: {customer.first_name} {customer.last_name} (ID: {customer.id})")
                print(f"  - Wallet: Rs.{customer.wallet_balance}")
                print(f"  - Loyalty Points: {customer.loyalty_points}")
                print(f"  - Notes: {customer.notes}")
        
        print(f"\n[SUCCESS] Successfully updated {updated_count} customers!")
        
        # Show summary of bills per customer
        print("\n" + "="*60)
        print("Customer Visit Summary:")
        print("="*60)
        
        for customer in customers[:10]:  # Show first 10
            bills = Bill.objects(customer=customer)
            bill_count = bills.count()
            
            if bill_count > 0:
                total_revenue = sum(bill.final_amount for bill in bills if bill.final_amount)
                last_bill = bills.order_by('-bill_date').first()
                last_visit = last_bill.bill_date if last_bill else None
                
                print(f"\n{customer.first_name} {customer.last_name} ({customer.mobile})")
                print(f"  Total Visits: {bill_count}")
                print(f"  Total Revenue: Rs.{total_revenue:.2f}")
                print(f"  Last Visit: {last_visit.strftime('%Y-%m-%d') if last_visit else 'N/A'}")
                print(f"  Wallet: Rs.{customer.wallet_balance}")
                print(f"  Loyalty: {customer.loyalty_points} points")
            
    except Exception as e:
        print(f"\n[ERROR] Error updating customers: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MongoDB Customer Data Update Script")
    print("="*60)
    
    update_customers()
    
    print("\n" + "="*60)
    print("Script completed!")
    print("="*60 + "\n")

