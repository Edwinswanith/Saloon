"""
Migration script to assign existing data to a default branch
Run this script once to migrate existing data to branch system
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import (
    Branch, Customer, Staff, Manager, Bill, Appointment, Expense, Lead,
    Feedback, MissedEnquiry, ServiceRecoveryCase, WhatsAppMessage,
    DiscountApprovalRequest, StaffAttendance, Asset, CashTransaction,
    Order, Membership, PrepaidPackage
)
from datetime import datetime

# MongoDB connection - use same as app.py
# Get from environment variable or use default Atlas connection
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon')

def migrate_to_branches():
    """Migrate all existing data to default branch"""
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
        
        # Create default branch if it doesn't exist
        default_branch = Branch.objects(name="T. Nagar").first()
        if not default_branch:
            print("Creating default branch (T. Nagar)...")
            default_branch = Branch(
                name="T. Nagar",
                address="123 Main Street, T. Nagar",
                city="Chennai",
                phone="044-12345678",
                email="tnagar@salon.com",
                is_active=True
            )
            default_branch.save()
            print(f"Created default branch: {default_branch.name} (ID: {default_branch.id})")
        else:
            print(f"Using existing default branch: {default_branch.name} (ID: {default_branch.id})")
        
        # Migrate Customers
        print("\nMigrating Customers...")
        customers = Customer.objects(branch__exists=False)
        count = 0
        for customer in customers:
            customer.branch = default_branch
            customer.save()
            count += 1
        print(f"Migrated {count} customers")
        
        # Migrate Staff
        print("\nMigrating Staff...")
        staff_members = Staff.objects(branch__exists=False)
        count = 0
        for staff in staff_members:
            staff.branch = default_branch
            staff.save()
            count += 1
        print(f"Migrated {count} staff members")
        
        # Migrate Managers (except Owner)
        print("\nMigrating Managers...")
        managers = Manager.objects(branch__exists=False, role__ne='owner')
        count = 0
        for manager in managers:
            manager.branch = default_branch
            manager.save()
            count += 1
        print(f"Migrated {count} managers (Owner role excluded)")
        
        # Migrate Bills
        print("\nMigrating Bills...")
        bills = Bill.objects(branch__exists=False)
        count = 0
        for bill in bills:
            bill.branch = default_branch
            bill.save()
            count += 1
        print(f"Migrated {count} bills")
        
        # Migrate Appointments
        print("\nMigrating Appointments...")
        appointments = Appointment.objects(branch__exists=False)
        count = 0
        for appointment in appointments:
            appointment.branch = default_branch
            appointment.save()
            count += 1
        print(f"Migrated {count} appointments")
        
        # Migrate Expenses
        print("\nMigrating Expenses...")
        expenses = Expense.objects(branch__exists=False)
        count = 0
        for expense in expenses:
            expense.branch = default_branch
            expense.save()
            count += 1
        print(f"Migrated {count} expenses")
        
        # Migrate Leads
        print("\nMigrating Leads...")
        leads = Lead.objects(branch__exists=False)
        count = 0
        for lead in leads:
            lead.branch = default_branch
            lead.save()
            count += 1
        print(f"Migrated {count} leads")
        
        # Migrate Feedback
        print("\nMigrating Feedback...")
        feedbacks = Feedback.objects(branch__exists=False)
        count = 0
        for feedback in feedbacks:
            feedback.branch = default_branch
            feedback.save()
            count += 1
        print(f"Migrated {count} feedback entries")
        
        # Migrate Missed Enquiries
        print("\nMigrating Missed Enquiries...")
        missed_enquiries = MissedEnquiry.objects(branch__exists=False)
        count = 0
        for enquiry in missed_enquiries:
            enquiry.branch = default_branch
            enquiry.save()
            count += 1
        print(f"Migrated {count} missed enquiries")
        
        # Migrate Service Recovery Cases
        print("\nMigrating Service Recovery Cases...")
        cases = ServiceRecoveryCase.objects(branch__exists=False)
        count = 0
        for case in cases:
            case.branch = default_branch
            case.save()
            count += 1
        print(f"Migrated {count} service recovery cases")
        
        # Migrate WhatsApp Messages
        print("\nMigrating WhatsApp Messages...")
        messages = WhatsAppMessage.objects(branch__exists=False)
        count = 0
        for message in messages:
            message.branch = default_branch
            message.save()
            count += 1
        print(f"Migrated {count} WhatsApp messages")
        
        # Migrate Discount Approval Requests
        print("\nMigrating Discount Approval Requests...")
        approvals = DiscountApprovalRequest.objects(branch__exists=False)
        count = 0
        for approval in approvals:
            approval.branch = default_branch
            approval.save()
            count += 1
        print(f"Migrated {count} discount approval requests")
        
        # Migrate Staff Attendance
        print("\nMigrating Staff Attendance...")
        attendance = StaffAttendance.objects(branch__exists=False)
        count = 0
        for record in attendance:
            record.branch = default_branch
            record.save()
            count += 1
        print(f"Migrated {count} attendance records")
        
        # Migrate Assets
        print("\nMigrating Assets...")
        assets = Asset.objects(branch__exists=False)
        count = 0
        for asset in assets:
            asset.branch = default_branch
            asset.save()
            count += 1
        print(f"Migrated {count} assets")
        
        # Migrate Cash Transactions
        print("\nMigrating Cash Transactions...")
        transactions = CashTransaction.objects(branch__exists=False)
        count = 0
        for transaction in transactions:
            transaction.branch = default_branch
            transaction.save()
            count += 1
        print(f"Migrated {count} cash transactions")
        
        # Migrate Orders
        print("\nMigrating Orders...")
        orders = Order.objects(branch__exists=False)
        count = 0
        for order in orders:
            order.branch = default_branch
            order.save()
            count += 1
        print(f"Migrated {count} orders")
        
        # Migrate Memberships
        print("\nMigrating Memberships...")
        memberships = Membership.objects(branch__exists=False)
        count = 0
        for membership in memberships:
            membership.branch = default_branch
            membership.save()
            count += 1
        print(f"Migrated {count} memberships")
        
        # Migrate Prepaid Packages
        print("\nMigrating Prepaid Packages...")
        prepaids = PrepaidPackage.objects(branch__exists=False)
        count = 0
        for prepaid in prepaids:
            prepaid.branch = default_branch
            prepaid.save()
            count += 1
        print(f"Migrated {count} prepaid packages")
        
        print("\n" + "="*50)
        print("Migration completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("="*50)
    print("Branch Migration Script")
    print("="*50)
    print("\nThis script will assign all existing data to the default branch (T. Nagar)")
    print("Make sure you have a backup of your database before running this script!")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nMigration cancelled.")
        sys.exit(0)
    
    success = migrate_to_branches()
    if success:
        print("\nMigration completed successfully!")
    else:
        print("\nMigration failed. Please check the errors above.")
        sys.exit(1)

