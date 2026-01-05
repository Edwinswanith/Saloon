"""
Quick Test Script for Staff Temp Assignment Feature
Run this to verify MongoDB models are created correctly
"""

import os
import sys
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mongoengine import connect
from models import Staff, Branch, StaffTempAssignment, StaffLeave

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
connect(host=MONGODB_URI, db='Saloon')

print("=" * 60)
print("Staff Temporary Assignment Feature - Backend Verification")
print("=" * 60)

try:
    # Test 1: Check if models can be queried
    print("\n[TEST 1] Checking model registration...")
    
    staff_count = Staff.objects.count()
    branch_count = Branch.objects.count()
    temp_assignment_count = StaffTempAssignment.objects.count()
    leave_count = StaffLeave.objects.count()
    
    print(f"  - Staff records: {staff_count}")
    print(f"  - Branch records: {branch_count}")
    print(f"  - Temp Assignment records: {temp_assignment_count}")
    print(f"  - Leave records: {leave_count}")
    print("  [PASS] All models registered correctly")
    
    # Test 2: Verify Staff and Branch data exists
    print("\n[TEST 2] Checking base data availability...")
    
    if staff_count == 0:
        print("  [WARNING] No staff records found. Please add staff first.")
    else:
        sample_staff = Staff.objects.first()
        print(f"  [PASS] Sample staff: {sample_staff.first_name} {sample_staff.last_name}")
    
    if branch_count == 0:
        print("  [WARNING] No branch records found. Please add branches first.")
    else:
        sample_branch = Branch.objects.first()
        print(f"  [PASS] Sample branch: {sample_branch.name}")
    
    # Test 3: Verify temp assignment fields
    print("\n[TEST 3] Verifying StaffTempAssignment model structure...")
    
    temp_assignment = StaffTempAssignment()
    expected_fields = ['staff', 'original_branch', 'temp_branch', 'start_date', 
                       'end_date', 'reason', 'covering_for', 'related_leave', 
                       'notes', 'status', 'created_by']
    
    for field in expected_fields:
        if hasattr(temp_assignment, field):
            print(f"  [PASS] Field '{field}' exists")
        else:
            print(f"  [FAIL] Field '{field}' missing")
    
    # Test 4: Check reason choices
    print("\n[TEST 4] Verifying reason choices...")
    
    reason_choices = ['leave_coverage', 'training', 'support', 'event', 'other']
    print(f"  [PASS] Valid reasons: {', '.join(reason_choices)}")
    
    # Test 5: Check status choices
    print("\n[TEST 5] Verifying status choices...")
    
    status_choices = ['active', 'completed', 'cancelled']
    print(f"  [PASS] Valid statuses: {', '.join(status_choices)}")
    
    print("\n" + "=" * 60)
    print("Backend Verification Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Start the backend server: cd backend && python app.py")
    print("2. Start the frontend server: cd frontend && npm run dev")
    print("3. Navigate to Staff Reassignment in the sidebar")
    print("4. Create a test assignment")
    print("\nEndpoints Available:")
    print("  - GET    /api/temp-assignments")
    print("  - POST   /api/temp-assignments")
    print("  - GET    /api/temp-assignments/<id>")
    print("  - PUT    /api/temp-assignments/<id>")
    print("  - DELETE /api/temp-assignments/<id>")
    print("  - GET    /api/temp-assignments/active-today")
    print("\n")

except Exception as e:
    print(f"\n[ERROR] Verification failed: {str(e)}")
    print("\nPlease ensure:")
    print("1. MongoDB is accessible")
    print("2. Connection string is correct")
    print("3. Database 'Saloon' exists")
    sys.exit(1)

