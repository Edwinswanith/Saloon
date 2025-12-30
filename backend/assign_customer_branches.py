"""
Assign branch_id to customers with null branch_id
Distributes customers evenly across all branches
"""
import os
import sys
from mongoengine import connect

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Customer, Branch

# MongoDB connection
MONGO_URI = 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon'

def assign_customer_branches():
    """Assign branch_id to customers with null branch_id"""
    
    # Connect to MongoDB
    connect(host=MONGO_URI, db='Saloon')
    print("Connected to MongoDB")
    
    # Get all branches
    branches = list(Branch.objects())
    if not branches:
        print("No branches found. Please create branches first.")
        return
    
    print(f"Found {len(branches)} branches")
    
    # Find all customers with null branch_id
    customers_without_branch = list(Customer.objects(branch=None))
    total_customers = len(customers_without_branch)
    
    if total_customers == 0:
        print("All customers already have branch assignments.")
        return
    
    print(f"Found {total_customers} customers without branch assignment")
    
    # Distribute customers evenly across branches
    customers_per_branch = total_customers // len(branches)
    remainder = total_customers % len(branches)
    
    print(f"Distributing {customers_per_branch} customers per branch (with {remainder} extra)")
    
    customer_index = 0
    total_assigned = 0
    
    for branch_index, branch in enumerate(branches):
        # Calculate how many customers to assign to this branch
        # Distribute remainder across first few branches
        num_to_assign = customers_per_branch + (1 if branch_index < remainder else 0)
        
        print(f"\nAssigning {num_to_assign} customers to branch: {branch.name}")
        
        # Assign customers to this branch
        for i in range(num_to_assign):
            if customer_index < total_customers:
                customer = customers_without_branch[customer_index]
                customer.branch = branch
                customer.save()
                total_assigned += 1
                customer_index += 1
                print(f"  - Assigned {customer.first_name} {customer.last_name} (ID: {customer.id})")
    
    print(f"\n=== SUCCESS ===")
    print(f"Total customers assigned to branches: {total_assigned}")
    print(f"Customers per branch distribution:")
    
    # Verify distribution
    for branch in branches:
        count = Customer.objects(branch=branch).count()
        print(f"  - {branch.name}: {count} customers")
    
    # Check if any customers still have null branch
    remaining_null = Customer.objects(branch=None).count()
    if remaining_null > 0:
        print(f"\nWARNING: {remaining_null} customers still have null branch_id")
    else:
        print(f"\nAll customers now have branch assignments!")

if __name__ == '__main__':
    assign_customer_branches()

