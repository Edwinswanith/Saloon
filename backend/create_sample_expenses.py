"""
Script to create sample expense data in MongoDB
This will create expense categories and sample expenses for all branches
"""
import sys
import os
from datetime import datetime, date, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Expense, ExpenseCategory, Branch
import os

# MongoDB Configuration (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

# Connect to MongoDB
base_uri = MONGODB_URI
if '@' in base_uri:
    parts = base_uri.split('@')
    if len(parts) == 2:
        credentials = parts[0]
        host_and_params = parts[1]
        if '/' in host_and_params:
            host = host_and_params.split('/')[0]
            if '?' in host_and_params:
                params = '?' + host_and_params.split('?')[1]
            else:
                params = ''
            connection_string = f"{credentials}@{host}/{MONGODB_DB}{params}"
        else:
            connection_string = f"{credentials}@{host_and_params}/{MONGODB_DB}"
    else:
        connection_string = f"{base_uri}/{MONGODB_DB}"
else:
    connection_string = f"{base_uri}/{MONGODB_DB}"

connect(host=connection_string)

def create_expense_categories():
    """Create expense categories if they don't exist"""
    categories = [
        {'name': 'Rent', 'description': 'Monthly rent for salon space'},
        {'name': 'Utilities', 'description': 'Electricity, water, internet bills'},
        {'name': 'Salaries', 'description': 'Staff salaries and wages'},
        {'name': 'Products', 'description': 'Hair products, cosmetics, supplies'},
        {'name': 'Equipment', 'description': 'Equipment maintenance and purchases'},
        {'name': 'Marketing', 'description': 'Advertising and promotional expenses'},
        {'name': 'Insurance', 'description': 'Business insurance premiums'},
        {'name': 'Maintenance', 'description': 'Salon maintenance and repairs'},
        {'name': 'Transportation', 'description': 'Delivery and transportation costs'},
        {'name': 'Other', 'description': 'Miscellaneous expenses'}
    ]
    
    created_categories = []
    for cat_data in categories:
        try:
            category = ExpenseCategory.objects.get(name=cat_data['name'])
            print(f"Category already exists: {category.name}")
        except ExpenseCategory.DoesNotExist:
            category = ExpenseCategory(
                name=cat_data['name'],
                description=cat_data['description']
            )
            category.save()
            print(f"Created category: {category.name}")
        created_categories.append(category)
    
    return created_categories

def create_sample_expenses(categories, branches):
    """Create sample expenses for all branches"""
    expense_names = [
        'Monthly Rent Payment',
        'Electricity Bill',
        'Water Bill',
        'Internet Subscription',
        'Staff Salary - January',
        'Hair Shampoo Purchase',
        'Hair Color Products',
        'Equipment Repair',
        'Facebook Ads Campaign',
        'Insurance Premium',
        'AC Maintenance',
        'Delivery Charges',
        'Cleaning Supplies',
        'Stationery Items',
        'Phone Bill'
    ]
    
    payment_modes = ['cash', 'card', 'upi', 'wallet']
    
    # Get current date
    today = date.today()
    
    # Create expenses for the last 3 months
    expenses_created = 0
    
    for branch in branches:
        print(f"\nCreating expenses for branch: {branch.name}")
        
        # Create 15-20 expenses per branch spread over last 3 months
        num_expenses = random.randint(15, 20)
        
        for i in range(num_expenses):
            # Random date within last 3 months
            days_ago = random.randint(0, 90)
            expense_date = today - timedelta(days=days_ago)
            
            # Random category
            category = random.choice(categories)
            
            # Random expense name
            expense_name = random.choice(expense_names)
            
            # Random amount (between 500 and 50000)
            amount = round(random.uniform(500, 50000), 2)
            
            # Random payment mode
            payment_mode = random.choice(payment_modes)
            
            # Create expense
            expense = Expense(
                name=expense_name,
                category=category,
                branch=branch,
                amount=amount,
                payment_mode=payment_mode,
                expense_date=expense_date,
                description=f"Sample expense for {branch.name} - {expense_name}"
            )
            
            try:
                expense.save()
                expenses_created += 1
                if expenses_created % 5 == 0:
                    print(f"  Created {expenses_created} expenses...")
            except Exception as e:
                print(f"  Error creating expense: {e}")
    
    return expenses_created

def assign_branches_to_expenses(branches, count):
    """Assign branches to expenses that don't have a branch"""
    expenses_without_branch = Expense.objects(branch=None)[:count]
    assigned = 0
    
    for i, expense in enumerate(expenses_without_branch):
        # Round-robin assignment
        branch = branches[i % len(branches)]
        expense.branch = branch
        expense.save()
        assigned += 1
        if assigned % 10 == 0:
            print(f"  Assigned {assigned} expenses...")
    
    print(f"  Assigned branches to {assigned} expenses")

def show_summary(branches):
    """Show expense summary"""
    total_expenses = Expense.objects.count()
    total_amount = sum(e.amount for e in Expense.objects())
    
    print("\n" + "=" * 60)
    print(f"Expense Summary")
    print("=" * 60)
    print(f"  Total expenses in database: {total_expenses}")
    print(f"  Total amount: Rs. {total_amount:,.2f}")
    
    # Show by branch
    print(f"\nExpenses by branch:")
    for branch in branches:
        branch_expenses = Expense.objects(branch=branch).count()
        branch_total = sum(e.amount for e in Expense.objects(branch=branch))
        if branch_expenses > 0:
            print(f"  {branch.name}: {branch_expenses} expenses, Rs. {branch_total:,.2f}")

def main():
    print("=" * 60)
    print("Creating Sample Expense Data")
    print("=" * 60)
    
    # Get all branches
    branches = list(Branch.objects())
    if not branches:
        print("ERROR: No branches found. Please create branches first.")
        return
    
    print(f"\nFound {len(branches)} branch(es)")
    
    # Create categories
    print("\n1. Creating expense categories...")
    categories = create_expense_categories()
    print(f"   Total categories: {len(categories)}")
    
    # Check if expenses already exist
    existing_count = Expense.objects.count()
    if existing_count > 0:
        print(f"\nINFO: {existing_count} expenses already exist in database.")
        # Check how many have branch assigned
        expenses_with_branch = Expense.objects(branch__ne=None).count()
        expenses_without_branch = existing_count - expenses_with_branch
        print(f"  Expenses with branch: {expenses_with_branch}")
        print(f"  Expenses without branch: {expenses_without_branch}")
        
        if expenses_without_branch > 0:
            print(f"\nAssigning branches to expenses without branch...")
            assign_branches_to_expenses(branches, expenses_without_branch)
        
        # Show summary and exit
        show_summary(branches)
        return
    
    # Create sample expenses
    print("\n2. Creating sample expenses...")
    expenses_created = create_sample_expenses(categories, branches)
    
    print("\n" + "=" * 60)
    print(f"SUCCESS: Created {expenses_created} sample expenses")
    print("=" * 60)
    
    # Show summary
    show_summary(branches)

if __name__ == '__main__':
    main()

