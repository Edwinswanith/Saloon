"""
Create MongoDB Collections via App
This script uses the app's MongoDB connection to create collections.
Collections are created automatically when you insert the first document.
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app which will establish MongoDB connection
from app import app
from models import (
    Customer, ServiceGroup, Service, ProductCategory, Product,
    Staff, Package, PrepaidGroup, PrepaidPackage, MembershipPlan,
    Bill, Appointment, ExpenseCategory, Expense, Supplier, Order,
    Lead, Feedback, StaffAttendance, Asset, CashTransaction,
    LoyaltyProgramSettings, ReferralProgramSettings, TaxSettings
)

with app.app_context():
    print("=" * 60)
    print("Creating MongoDB Collections")
    print("=" * 60)
    print("\nNote: Collections are created automatically when you insert data.")
    print("This script will insert and immediately delete a test document for each collection.\n")
    
    collections_to_create = [
        ('customers', Customer, lambda: Customer(mobile='_init_temp_', first_name='Temp')),
        ('staffs', Staff, lambda: Staff(mobile='_init_temp_', first_name='Temp')),
        ('service_groups', ServiceGroup, lambda: ServiceGroup(name='Temp Group')),
        ('product_categories', ProductCategory, lambda: ProductCategory(name='Temp Category')),
        ('packages', Package, lambda: Package(name='Temp Package', price=0)),
        ('prepaid_groups', PrepaidGroup, lambda: PrepaidGroup(name='Temp Group')),
        ('membership_plans', MembershipPlan, lambda: MembershipPlan(name='Temp Plan', validity_days=30, price=0)),
        ('expense_categories', ExpenseCategory, lambda: ExpenseCategory(name='Temp Category')),
        ('suppliers', Supplier, lambda: Supplier(name='Temp Supplier')),
        ('tax_slabs', None, None),  # Skip - need to handle separately
        ('assets', Asset, lambda: Asset(name='Temp Asset')),
    ]
    
    created = []
    skipped = []
    errors = []
    
    # First create simple collections that don't have dependencies
    for name, model, create_fn in collections_to_create:
        if not model or not create_fn:
            continue
        try:
            if model.objects.count() > 0:
                skipped.append(f"[SKIP] {name} (already has data)")
                continue
            
            temp = create_fn()
            temp.save()
            temp.delete()
            created.append(f"[OK] {name}")
        except Exception as e:
            errors.append(f"[ERROR] {name}: {str(e)[:60]}")
    
    # Create collections with dependencies
    dependency_collections = [
        ('services', Service, lambda: Service(
            name='Temp Service',
            group=ServiceGroup.objects.first() or ServiceGroup(name='Temp').save(),
            price=0
        )),
        ('products', Product, lambda: Product(
            name='Temp Product',
            category=ProductCategory.objects.first() or ProductCategory(name='Temp').save(),
            price=0
        )),
    ]
    
    for name, model, create_fn in dependency_collections:
        try:
            if model.objects.count() > 0:
                skipped.append(f"[SKIP] {name} (already has data)")
                continue
            temp = create_fn()
            temp.save()
            temp.delete()
            created.append(f"[OK] {name}")
        except Exception as e:
            errors.append(f"[ERROR] {name}: {str(e)[:60]}")
    
    # Initialize settings (these have get_settings() methods)
    print("\nInitializing settings collections...")
    try:
        LoyaltyProgramSettings.get_settings()
        created.append("[OK] loyalty_program_settings")
    except Exception as e:
        errors.append(f"[ERROR] loyalty_program_settings: {str(e)[:60]}")
    
    try:
        ReferralProgramSettings.get_settings()
        created.append("[OK] referral_program_settings")
    except Exception as e:
        errors.append(f"[ERROR] referral_program_settings: {str(e)[:60]}")
    
    try:
        TaxSettings.get_settings()
        created.append("[OK] tax_settings")
    except Exception as e:
        errors.append(f"[ERROR] tax_settings: {str(e)[:60]}")
    
    # Print results
    print(f"\nCreated: {len(created)}")
    for item in created:
        print(f"  {item}")
    
    if skipped:
        print(f"\nSkipped: {len(skipped)}")
        for item in skipped:
            print(f"  {item}")
    
    if errors:
        print(f"\nErrors: {len(errors)}")
        for item in errors[:10]:  # Show first 10 errors
            print(f"  {item}")
    
    print("\n" + "=" * 60)
    print("NOTE: Other collections (bills, appointments, etc.) will be")
    print("created automatically when you use those features in the app.")
    print("=" * 60)

print("\nDone!")

