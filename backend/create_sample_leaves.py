"""
Script to create sample leave data for testing the coverage dashboard
"""
import os
import sys
from datetime import datetime, date, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mongoengine import connect
from models import Staff, Branch, StaffLeave, StaffTempAssignment

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
connect(host=MONGODB_URI, db='Saloon')

print("=" * 60)
print("Creating Sample Leave Data for Coverage Dashboard")
print("=" * 60)

try:
    # Get all branches and staff
    branches = list(Branch.objects(is_active=True))
    all_staff = list(Staff.objects(status='active'))
    
    if not branches:
        print("ERROR: No active branches found. Please create branches first.")
        sys.exit(1)
    
    if not all_staff:
        print("ERROR: No active staff found. Please create staff first.")
        sys.exit(1)
    
    print(f"\nFound {len(branches)} branches and {len(all_staff)} staff members")
    
    # Get today's date
    today = date.today()
    
    # Create sample leaves
    leaves_created = 0
    leaves_updated = 0
    
    # Create leaves for today and next few days
    for i, staff in enumerate(all_staff[:min(10, len(all_staff))]):  # Create leaves for up to 10 staff
        if not staff.branch:
            continue
        
        # Alternate between today, tomorrow, and day after
        start_offset = i % 3
        start_date = today + timedelta(days=start_offset)
        end_date = start_date + timedelta(days=2)  # 3-day leaves
        
        # Check if leave already exists
        existing_leave = StaffLeave.objects(
            staff=staff,
            start_date=start_date,
            end_date=end_date
        ).first()
        
        if existing_leave:
            # Update existing leave to approved status if pending
            if existing_leave.status == 'pending':
                existing_leave.status = 'approved'
                existing_leave.save()
                leaves_updated += 1
                print(f"  [UPDATED] Leave for {staff.first_name} {staff.last_name} ({start_date} to {end_date})")
            else:
                print(f"  [SKIP] Leave already exists for {staff.first_name} {staff.last_name}")
            continue
        
        # Create new leave
        leave_types = ['casual', 'sick', 'vacation', 'emergency']
        leave = StaffLeave(
            staff=staff,
            branch=staff.branch,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_types[i % len(leave_types)],
            reason=f'Sample leave request for testing coverage dashboard',
            status='approved',
            coverage_required=True
        )
        leave.save()
        leaves_created += 1
        print(f"  [CREATED] Leave for {staff.first_name} {staff.last_name} at {staff.branch.name} ({start_date} to {end_date})")
    
    # Create some pending leaves for future dates
    future_date = today + timedelta(days=7)
    for i, staff in enumerate(all_staff[5:min(8, len(all_staff))]):  # 3 more staff
        if not staff.branch:
            continue
        
        end_date = future_date + timedelta(days=1)
        
        existing_leave = StaffLeave.objects(
            staff=staff,
            start_date=future_date,
            end_date=end_date
        ).first()
        
        if existing_leave:
            continue
        
        leave = StaffLeave(
            staff=staff,
            branch=staff.branch,
            start_date=future_date,
            end_date=end_date,
            leave_type='vacation',
            reason='Future leave request',
            status='pending',
            coverage_required=True
        )
        leave.save()
        leaves_created += 1
        print(f"  [CREATED] Future leave for {staff.first_name} {staff.last_name} ({future_date} to {end_date})")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  - Leaves created: {leaves_created}")
    print(f"  - Leaves updated: {leaves_updated}")
    
    # Count leaves by status
    approved_today = StaffLeave.objects(
        status='approved',
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    pending_count = StaffLeave.objects(status='pending').count()
    
    print(f"  - Approved leaves active today: {approved_today}")
    print(f"  - Pending leaves: {pending_count}")
    print("=" * 60)
    print("\nSample leave data created successfully!")
    print("You can now test the coverage dashboard in the Staff Reassignment section.")
    print("\n")

except Exception as e:
    print(f"\n[ERROR] Failed to create sample leaves: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

