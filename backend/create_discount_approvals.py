"""
Script to create sample discount approval requests in MongoDB
This populates the Discount Approvals section with test data
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import (
    DiscountApprovalRequest, Bill, Staff, Branch, Customer
)

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


def create_discount_approvals():
    """Create sample discount approval requests"""
    print("\n" + "="*60)
    print("Creating Sample Discount Approval Requests")
    print("="*60)
    
    # Fetch existing bills (non-deleted, with subtotals > 0)
    bills = list(Bill.objects(is_deleted=False, subtotal__gt=0))
    if not bills:
        print("\n[WARNING] No bills found with subtotal > 0. Cannot create approval requests.")
        print("Please ensure there are bills in the database first.")
        return
    
    print(f"\nFound {len(bills)} bills to use")
    
    # Fetch existing staff members
    staff_members = list(Staff.objects(status='active'))
    if not staff_members:
        print("\n[WARNING] No active staff members found. Cannot create approval requests.")
        print("Please ensure there are staff members in the database first.")
        return
    
    print(f"Found {len(staff_members)} active staff members")
    
    # Sample reasons for discount requests
    discount_reasons = [
        "Customer loyalty - Regular customer for over 2 years",
        "Special promotion - First-time customer discount",
        "Bulk service discount - Multiple services booked",
        "Referral discount - Customer referred by existing client",
        "Seasonal promotion - Holiday special offer",
        "Customer complaint resolution - Service recovery",
        "VIP customer - Premium membership holder",
        "Birthday special - Customer birthday month",
        "Anniversary discount - Customer anniversary",
        "Corporate discount - Business client"
    ]
    
    # Create 5-10 approval requests
    num_approvals = min(10, len(bills))
    created_count = 0
    skipped_count = 0
    
    # Get bills that don't already have pending approval requests
    bills_without_approvals = [b for b in bills if not b.discount_approval_request]
    
    if not bills_without_approvals:
        print("\n[INFO] All bills already have approval requests. Creating new ones anyway...")
        bills_without_approvals = bills
    
    num_approvals = min(num_approvals, len(bills_without_approvals))
    
    print(f"\nCreating {num_approvals} discount approval requests...")
    
    for i in range(num_approvals):
        try:
            # Select a random bill
            bill = random.choice(bills_without_approvals)
            bills_without_approvals.remove(bill)
            
            # Skip if bill already has a pending approval
            if bill.discount_approval_request:
                existing_approval = DiscountApprovalRequest.objects(id=bill.discount_approval_request.id).first()
                if existing_approval and existing_approval.approval_status == 'pending':
                    skipped_count += 1
                    continue
            
            # Select a random staff member
            staff = random.choice(staff_members)
            
            # Calculate discount (20-50% of subtotal)
            discount_percent = random.uniform(20, 50)
            discount_amount = (bill.subtotal * discount_percent) / 100.0
            
            # Select a random reason
            reason = random.choice(discount_reasons)
            
            # Create approval request with recent date (within last 7 days)
            days_ago = random.randint(0, 7)
            created_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Get bill's branch if available
            branch = bill.branch if hasattr(bill, 'branch') and bill.branch else None
            
            # Create the approval request
            approval_request = DiscountApprovalRequest(
                bill=bill,
                requested_by=staff,
                branch=branch,
                requested_discount_percent=round(discount_percent, 2),
                requested_discount_amount=round(discount_amount, 2),
                reason=reason,
                approval_status='pending',
                created_at=created_date,
                updated_at=created_date
            )
            approval_request.save()
            
            # Link to bill
            bill.discount_approval_request = approval_request
            bill.discount_approval_status = 'pending'
            bill.discount_requested_by = staff
            bill.save()
            
            created_count += 1
            
            print(f"  [{created_count}/{num_approvals}] Created approval for Bill {bill.bill_number} - {discount_percent:.1f}% discount (Rs.{discount_amount:.2f})")
            
        except Exception as e:
            print(f"  [ERROR] Failed to create approval request {i+1}: {str(e)}")
            skipped_count += 1
            continue
    
    print(f"\n[SUCCESS] Created {created_count} discount approval requests!")
    if skipped_count > 0:
        print(f"[INFO] Skipped {skipped_count} bills (already have pending approvals)")
    
    # Verify creation
    pending_approvals = DiscountApprovalRequest.objects(approval_status='pending')
    print(f"\n[VERIFICATION] Total pending approvals in database: {len(pending_approvals)}")


if __name__ == '__main__':
    try:
        create_discount_approvals()
        print("\n" + "="*60)
        print("Script completed successfully!")
        print("="*60)
    except Exception as e:
        print(f"\n[ERROR] Script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

