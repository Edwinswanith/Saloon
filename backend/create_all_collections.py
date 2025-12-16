"""
Create All MongoDB Collections
Uses the same connection method as app.py to ensure compatibility
"""
from mongoengine import connect
import os
from datetime import datetime

# Same MongoDB configuration as app.py
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

# Parse connection string (same logic as app.py)
if MONGODB_DB not in MONGODB_URI:
    if '?' in MONGODB_URI:
        MONGODB_URI = MONGODB_URI.replace('?', f'/{MONGODB_DB}?')
    else:
        MONGODB_URI = f"{MONGODB_URI}/{MONGODB_DB}"

print("Connecting to MongoDB...")
try:
    connect(host=MONGODB_URI, alias='default')
    print(f"[OK] Connected to MongoDB: {MONGODB_DB}\n")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

# Import models after connection
from models import (
    Customer, Staff, ServiceGroup, Service, ProductCategory, Product,
    Package, PrepaidGroup, PrepaidPackage, MembershipPlan, Membership,
    Bill, Appointment, ExpenseCategory, Expense, Supplier, Order,
    Lead, Feedback, StaffAttendance, Asset, CashTransaction,
    LoyaltyProgramSettings, ReferralProgramSettings, TaxSettings, TaxSlab, Manager
)

print("=" * 60)
print("Creating Collections")
print("=" * 60)
print()

created = []
skipped = []

# Create simple collections first
print("Step 1: Creating base collections...")
try:
    # Customer
    if Customer.objects.count() == 0:
        Customer(mobile='_init_', first_name='Init').save()
        Customer.objects(mobile='_init_').delete()
        created.append('customers')
    else:
        skipped.append('customers')
    print("  [OK] customers")
except Exception as e:
    print(f"  [ERROR] customers: {str(e)[:50]}")

try:
    # Staff
    if Staff.objects.count() == 0:
        Staff(mobile='_init_', first_name='Init').save()
        Staff.objects(mobile='_init_').delete()
        created.append('staffs')
    else:
        skipped.append('staffs')
    print("  ✓ staffs")
except Exception as e:
    print(f"  ✗ staffs: {str(e)[:50]}")

try:
    # ServiceGroup
    if ServiceGroup.objects.count() == 0:
        ServiceGroup(name='_Init_').save()
        ServiceGroup.objects(name='_Init_').delete()
        created.append('service_groups')
    else:
        skipped.append('service_groups')
    print("  ✓ service_groups")
except Exception as e:
    print(f"  ✗ service_groups: {str(e)[:50]}")

try:
    # ProductCategory
    if ProductCategory.objects.count() == 0:
        ProductCategory(name='_Init_').save()
        ProductCategory.objects(name='_Init_').delete()
        created.append('product_categories')
    else:
        skipped.append('product_categories')
    print("  ✓ product_categories")
except Exception as e:
    print(f"  ✗ product_categories: {str(e)[:50]}")

try:
    # Package
    if Package.objects.count() == 0:
        Package(name='_Init_', price=0).save()
        Package.objects(name='_Init_').delete()
        created.append('packages')
    else:
        skipped.append('packages')
    print("  ✓ packages")
except Exception as e:
    print(f"  ✗ packages: {str(e)[:50]}")

try:
    # PrepaidGroup
    if PrepaidGroup.objects.count() == 0:
        PrepaidGroup(name='_Init_').save()
        PrepaidGroup.objects(name='_Init_').delete()
        created.append('prepaid_groups')
    else:
        skipped.append('prepaid_groups')
    print("  ✓ prepaid_groups")
except Exception as e:
    print(f"  ✗ prepaid_groups: {str(e)[:50]}")

try:
    # MembershipPlan
    if MembershipPlan.objects.count() == 0:
        MembershipPlan(name='_Init_', validity_days=30, price=0).save()
        MembershipPlan.objects(name='_Init_').delete()
        created.append('membership_plans')
    else:
        skipped.append('membership_plans')
    print("  ✓ membership_plans")
except Exception as e:
    print(f"  ✗ membership_plans: {str(e)[:50]}")

try:
    # ExpenseCategory
    if ExpenseCategory.objects.count() == 0:
        ExpenseCategory(name='_Init_').save()
        ExpenseCategory.objects(name='_Init_').delete()
        created.append('expense_categories')
    else:
        skipped.append('expense_categories')
    print("  ✓ expense_categories")
except Exception as e:
    print(f"  ✗ expense_categories: {str(e)[:50]}")

try:
    # Supplier
    if Supplier.objects.count() == 0:
        Supplier(name='_Init_').save()
        Supplier.objects(name='_Init_').delete()
        created.append('suppliers')
    else:
        skipped.append('suppliers')
    print("  ✓ suppliers")
except Exception as e:
    print(f"  ✗ suppliers: {str(e)[:50]}")

try:
    # TaxSlab
    if TaxSlab.objects.count() == 0:
        TaxSlab(name='_Init_', rate=0).save()
        TaxSlab.objects(name='_Init_').delete()
        created.append('tax_slabs')
    else:
        skipped.append('tax_slabs')
    print("  ✓ tax_slabs")
except Exception as e:
    print(f"  ✗ tax_slabs: {str(e)[:50]}")

try:
    # Asset
    if Asset.objects.count() == 0:
        Asset(name='_Init_').save()
        Asset.objects(name='_Init_').delete()
        created.append('assets')
    else:
        skipped.append('assets')
    print("  ✓ assets")
except Exception as e:
    print(f"  ✗ assets: {str(e)[:50]}")

try:
    # Manager
    if Manager.objects.count() == 0:
        Manager(first_name='_Init_', email='_init@_init.com', mobile='0000000000').save()
        Manager.objects(email='_init@_init.com').delete()
        created.append('managers')
    else:
        skipped.append('managers')
    print("  ✓ managers")
except Exception as e:
    print(f"  ✗ managers: {str(e)[:50]}")

# Create collections with dependencies
print("\nStep 2: Creating collections with dependencies...")

try:
    # Service (needs ServiceGroup)
    if Service.objects.count() == 0:
        sg = ServiceGroup.objects.first()
        if not sg:
            sg = ServiceGroup(name='Default').save()
        Service(name='_Init_', group=sg, price=0).save()
        Service.objects(name='_Init_').delete()
        created.append('services')
    else:
        skipped.append('services')
    print("  ✓ services")
except Exception as e:
    print(f"  ✗ services: {str(e)[:50]}")

try:
    # Product (needs ProductCategory)
    if Product.objects.count() == 0:
        pc = ProductCategory.objects.first()
        if not pc:
            pc = ProductCategory(name='Default').save()
        Product(name='_Init_', category=pc, price=0).save()
        Product.objects(name='_Init_').delete()
        created.append('products')
    else:
        skipped.append('products')
    print("  ✓ products")
except Exception as e:
    print(f"  ✗ products: {str(e)[:50]}")

try:
    # PrepaidPackage
    if PrepaidPackage.objects.count() == 0:
        PrepaidPackage(name='_Init_', price=0).save()
        PrepaidPackage.objects(name='_Init_').delete()
        created.append('prepaid_packages')
    else:
        skipped.append('prepaid_packages')
    print("  ✓ prepaid_packages")
except Exception as e:
    print(f"  ✗ prepaid_packages: {str(e)[:50]}")

try:
    # Membership (needs Customer and MembershipPlan)
    if Membership.objects.count() == 0:
        cust = Customer.objects.first()
        if not cust:
            cust = Customer(mobile='_temp_', first_name='Temp').save()
        plan = MembershipPlan.objects.first()
        if not plan:
            plan = MembershipPlan(name='Temp', validity_days=30, price=0).save()
        Membership(name='_Init_', customer=cust, plan=plan, price=0,
                  purchase_date=datetime.utcnow(), expiry_date=datetime.utcnow()).save()
        Membership.objects(name='_Init_').delete()
        created.append('memberships')
    else:
        skipped.append('memberships')
    print("  ✓ memberships")
except Exception as e:
    print(f"  ✗ memberships: {str(e)[:50]}")

try:
    # Bill
    if Bill.objects.count() == 0:
        Bill(bill_number='_INIT_', final_amount=0).save()
        Bill.objects(bill_number='_INIT_').delete()
        created.append('bills')
    else:
        skipped.append('bills')
    print("  ✓ bills")
except Exception as e:
    print(f"  ✗ bills: {str(e)[:50]}")

try:
    # Appointment (needs Customer and Staff)
    if Appointment.objects.count() == 0:
        cust = Customer.objects.first()
        staff = Staff.objects.first()
        if not cust:
            cust = Customer(mobile='_temp_', first_name='Temp').save()
        if not staff:
            staff = Staff(mobile='_temp_', first_name='Temp').save()
        Appointment(customer=cust, staff=staff, appointment_date=datetime.now().date(),
                   start_time='00:00:00').save()
        Appointment.objects(customer=cust, start_time='00:00:00').delete()
        created.append('appointments')
    else:
        skipped.append('appointments')
    print("  ✓ appointments")
except Exception as e:
    print(f"  ✗ appointments: {str(e)[:50]}")

try:
    # Expense (needs ExpenseCategory)
    if Expense.objects.count() == 0:
        ec = ExpenseCategory.objects.first()
        if not ec:
            ec = ExpenseCategory(name='Default').save()
        Expense(category=ec, name='_Init_', amount=0, expense_date=datetime.now().date()).save()
        Expense.objects(name='_Init_').delete()
        created.append('expenses')
    else:
        skipped.append('expenses')
    print("  ✓ expenses")
except Exception as e:
    print(f"  ✗ expenses: {str(e)[:50]}")

try:
    # Order (needs Supplier)
    if Order.objects.count() == 0:
        sup = Supplier.objects.first()
        if not sup:
            sup = Supplier(name='Default').save()
        Order(supplier=sup, order_date=datetime.now().date(), total_amount=0).save()
        Order.objects(supplier=sup, total_amount=0).delete()
        created.append('orders')
    else:
        skipped.append('orders')
    print("  ✓ orders")
except Exception as e:
    print(f"  ✗ orders: {str(e)[:50]}")

try:
    # Lead
    if Lead.objects.count() == 0:
        Lead(name='_Init_').save()
        Lead.objects(name='_Init_').delete()
        created.append('leads')
    else:
        skipped.append('leads')
    print("  ✓ leads")
except Exception as e:
    print(f"  ✗ leads: {str(e)[:50]}")

try:
    # Feedback
    if Feedback.objects.count() == 0:
        Feedback(rating=5, comment='_Init_').save()
        Feedback.objects(comment='_Init_').delete()
        created.append('feedbacks')
    else:
        skipped.append('feedbacks')
    print("  ✓ feedbacks")
except Exception as e:
    print(f"  ✗ feedbacks: {str(e)[:50]}")

try:
    # StaffAttendance (needs Staff)
    if StaffAttendance.objects.count() == 0:
        staff = Staff.objects.first()
        if not staff:
            staff = Staff(mobile='_temp_', first_name='Temp').save()
        StaffAttendance(staff=staff, attendance_date=datetime.now().date(), status='present').save()
        StaffAttendance.objects(staff=staff, attendance_date=datetime.now().date()).delete()
        created.append('staff_attendance')
    else:
        skipped.append('staff_attendance')
    print("  ✓ staff_attendance")
except Exception as e:
    print(f"  ✗ staff_attendance: {str(e)[:50]}")

try:
    # CashTransaction
    if CashTransaction.objects.count() == 0:
        CashTransaction(transaction_type='in', amount=0, transaction_date=datetime.now().date(),
                       transaction_time='00:00:00').save()
        CashTransaction.objects(transaction_date=datetime.now().date(), amount=0).delete()
        created.append('cash_transactions')
    else:
        skipped.append('cash_transactions')
    print("  ✓ cash_transactions")
except Exception as e:
    print(f"  ✗ cash_transactions: {str(e)[:50]}")

# Initialize settings
print("\nStep 3: Initializing settings collections...")
try:
    LoyaltyProgramSettings.get_settings()
    created.append('loyalty_program_settings')
    print("  ✓ loyalty_program_settings")
except Exception as e:
    print(f"  ✗ loyalty_program_settings: {str(e)[:50]}")

try:
    ReferralProgramSettings.get_settings()
    created.append('referral_program_settings')
    print("  ✓ referral_program_settings")
except Exception as e:
    print(f"  ✗ referral_program_settings: {str(e)[:50]}")

try:
    TaxSettings.get_settings()
    created.append('tax_settings')
    print("  ✓ tax_settings")
except Exception as e:
    print(f"  ✗ tax_settings: {str(e)[:50]}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Created: {len(created)} collections")
if created:
    for name in sorted(created):
        print(f"  [OK] {name}")
if skipped:
    print(f"\nAlready existed: {len(skipped)} collections")
print("\n" + "=" * 60)
print("Done! Check MongoDB Atlas Data Explorer to see all collections.")
print("=" * 60)

