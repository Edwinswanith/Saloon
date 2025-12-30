"""
Test script to verify branch filtering is working correctly
"""
import os
import sys
from mongoengine import connect

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Customer, Branch
from utils.branch_filter import filter_by_branch

# MongoDB connection
MONGO_URI = 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon'

def test_branch_filtering():
    """Test branch filtering logic"""
    
    # Connect to MongoDB
    connect(host=MONGO_URI, db='Saloon')
    print("Connected to MongoDB\n")
    
    # Get all branches
    branches = list(Branch.objects())
    print(f"Found {len(branches)} branches:\n")
    
    for branch in branches:
        print(f"Branch: {branch.name} (ID: {branch.id})")
        
        # Test 1: Direct query with branch filter
        direct_count = Customer.objects(branch=branch).count()
        print(f"  Direct query: {direct_count} customers")
        
        # Test 2: Using filter_by_branch utility
        filtered_query = filter_by_branch(Customer.objects(), branch)
        filtered_count = filtered_query.count()
        print(f"  filter_by_branch: {filtered_count} customers")
        
        # Test 3: Check for null branch customers
        null_branch_count = Customer.objects(branch=None).count()
        
        # Test 4: Get sample customer names
        sample_customers = list(filtered_query.limit(3))
        if sample_customers:
            print(f"  Sample customers:")
            for customer in sample_customers:
                customer_branch_id = str(customer.branch.id) if customer.branch else 'NULL'
                print(f"    - {customer.first_name} {customer.last_name} (Branch: {customer_branch_id})")
        
        print()
    
    print(f"\n=== SUMMARY ===")
    print(f"Total customers with NULL branch: {null_branch_count}")
    print(f"Total customers: {Customer.objects().count()}")
    
    # Test 5: Verify no customer appears in multiple branches
    print(f"\n=== VERIFYING UNIQUE BRANCH ASSIGNMENTS ===")
    all_customer_ids = set()
    for branch in branches:
        branch_customer_ids = set([str(c.id) for c in Customer.objects(branch=branch)])
        
        # Check for duplicates
        duplicates = all_customer_ids.intersection(branch_customer_ids)
        if duplicates:
            print(f"ERROR: Found {len(duplicates)} duplicate customers in {branch.name}")
        else:
            print(f"OK: {branch.name} has {len(branch_customer_ids)} unique customers")
        
        all_customer_ids.update(branch_customer_ids)
    
    print(f"\nTotal unique customers across all branches: {len(all_customer_ids)}")

if __name__ == '__main__':
    test_branch_filtering()

