"""
Verification script to check if Staff Temporary Assignment data is correctly stored and updated in MongoDB
"""
from mongoengine import connect, DoesNotExist
from models import StaffTempAssignment, StaffLeave, Staff, Branch
from datetime import datetime, date
import os

# MongoDB connection
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/Saloon?appName=Saloon')
connect(host=MONGODB_URI)

def verify_assignments():
    print("=" * 60)
    print("Verifying Staff Temporary Assignment Data")
    print("=" * 60)
    
    # 1. Check all assignments
    assignments = StaffTempAssignment.objects()
    print(f"\n1. Total Assignments: {assignments.count()}")
    
    for assignment in assignments:
        print(f"\n   Assignment ID: {assignment.id}")
        print(f"   Staff: {assignment.staff.first_name} {assignment.staff.last_name}")
        print(f"   Original Branch: {assignment.original_branch.name if assignment.original_branch else 'None'}")
        print(f"   Temp Branch: {assignment.temp_branch.name if assignment.temp_branch else 'None'}")
        print(f"   Dates: {assignment.start_date} to {assignment.end_date}")
        print(f"   Status: {assignment.status}")
        print(f"   Reason: {assignment.reason}")
        print(f"   Covering For: {assignment.covering_for.first_name} {assignment.covering_for.last_name}" if assignment.covering_for else "   Covering For: None")
        print(f"   Related Leave: {assignment.related_leave.id if assignment.related_leave else 'None'}")
        print(f"   Created At: {assignment.created_at}")
        print(f"   Updated At: {assignment.updated_at}")
        
        # Verify related leave link
        if assignment.related_leave:
            leave = assignment.related_leave
            print(f"   -> Related Leave Status: {leave.status}")
            print(f"   -> Leave Covered By: {leave.covered_by.id if leave.covered_by else 'None'}")
            if leave.covered_by and str(leave.covered_by.id) != str(assignment.id):
                print(f"   [WARNING] Leave covered_by doesn't match assignment ID!")
    
    # 2. Check all leaves
    leaves = StaffLeave.objects()
    print(f"\n2. Total Leaves: {leaves.count()}")
    
    covered_count = 0
    uncovered_count = 0
    for leave in leaves:
        if leave.covered_by:
            covered_count += 1
            print(f"\n   Leave ID: {leave.id}")
            print(f"   Staff: {leave.staff.first_name} {leave.staff.last_name}")
            print(f"   Status: {leave.status}")
            print(f"   Coverage Required: {leave.coverage_required}")
            print(f"   Covered By Assignment: {leave.covered_by.id if leave.covered_by else 'None'}")
            
            # Verify assignment link back
            if leave.covered_by:
                assignment = leave.covered_by
                if assignment.related_leave and str(assignment.related_leave.id) != str(leave.id):
                    print(f"   [WARNING] Assignment related_leave doesn't match leave ID!")
        else:
            if leave.status == 'approved' and leave.coverage_required:
                uncovered_count += 1
    
    print(f"\n3. Coverage Summary:")
    print(f"   Covered Leaves: {covered_count}")
    print(f"   Uncovered Leaves (approved, requires coverage): {uncovered_count}")
    
    # 3. Check for data consistency issues
    print(f"\n4. Data Consistency Checks:")
    issues = []
    
    for assignment in assignments:
        # Check if covering_for staff exists
        if assignment.covering_for:
            try:
                staff = Staff.objects.get(id=assignment.covering_for.id)
            except DoesNotExist:
                issues.append(f"Assignment {assignment.id}: covering_for staff not found")
        
        # Check if related_leave exists and is linked back
        if assignment.related_leave:
            leave = assignment.related_leave
            if not leave.covered_by or str(leave.covered_by.id) != str(assignment.id):
                issues.append(f"Assignment {assignment.id}: related_leave not linked back correctly")
    
    if issues:
        print(f"   [ISSUES FOUND]:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"   [OK] No data consistency issues found")
    
    print("\n" + "=" * 60)
    print("Verification Complete")
    print("=" * 60)

if __name__ == "__main__":
    verify_assignments()

