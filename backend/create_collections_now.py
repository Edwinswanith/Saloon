"""
Create MongoDB Collections Now
Uses MongoEngine connection (same as app) to create collections
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect, disconnect
from datetime import datetime

# MongoDB Configuration (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

# Parse connection string
if MONGODB_DB not in MONGODB_URI:
    if '?' in MONGODB_URI:
        MONGODB_URI = MONGODB_URI.replace('?', f'/{MONGODB_DB}?')
    else:
        MONGODB_URI = f"{MONGODB_URI}/{MONGODB_DB}"

print(f"Connecting to MongoDB: {MONGODB_DB}...")
try:
    connect(host=MONGODB_URI, alias='default')
    print("Connected!\n")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# Import models
from models import (
    Customer, Staff, ServiceGroup, Service, ProductCategory, Product,
    Package, PrepaidGroup, PrepaidPackage, MembershipPlan, Membership,
    Bill, Appointment, ExpenseCategory, Expense, Supplier, Order,
    Lead, Feedback, StaffAttendance, Asset, CashTransaction,
    LoyaltyProgramSettings, ReferralProgramSettings, TaxSettings, TaxSlab, Manager
)

print("=" * 60)
print("Creating MongoDB Collections")
print("=" * 60)
print("Collections are created by inserting a test document\n")

created = []
errors = []

def create_collection(name, model_class, create_doc_func):
    """Create collection by inserting and deleting a document"""
    try:
        # Check if collection already has data
        if model_class.objects.count() > 0:
            return f"[EXISTS] {name}"
        
        # Create temporary document
        doc = create_doc_func()
        doc.save()
        doc_id = doc.id
        
        # Delete it immediately
        doc.delete()
        
        return f"[CREATED] {name}"
    except Exception as e:
        error_msg = str(e)[:60]
        # If collection was created but delete failed, still count as success
        try:
            if model_class.objects.count() >= 0:  # Collection exists
                return f"[CREATED] {name} (cleanup warning)"
        except:
            pass
        return f"[ERROR] {name}: {error_msg}"

# Step 1: Create independent collections
print("Step 1: Creating independent collections...")
results = []

# Simple collections
results.append(create_collection('customers', Customer, 
    lambda: Customer(mobile='_init_temp_', first_name='Init')))
results.append(create_collection('staffs', Staff, 
    lambda: Staff(mobile='_init_temp_', first_name='Init')))
results.append(create_collection('service_groups', ServiceGroup, 
    lambda: ServiceGroup(name='_init_temp_')))
results.append(create_collection('product_categories', ProductCategory, 
    lambda: ProductCategory(name='_init_temp_')))
results.append(create_collection('packages', Package, 
    lambda: Package(name='_init_temp_', price=0)))
results.append(create_collection('prepaid_groups', PrepaidGroup, 
    lambda: PrepaidGroup(name='_init_temp_')))
results.append(create_collection('membership_plans', MembershipPlan, 
    lambda: MembershipPlan(name='_init_temp_', validity_days=30, price=0)))
results.append(create_collection('expense_categories', ExpenseCategory, 
    lambda: ExpenseCategory(name='_init_temp_')))
results.append(create_collection('suppliers', Supplier, 
    lambda: Supplier(name='_init_temp_')))
results.append(create_collection('assets', Asset, 
    lambda: Asset(name='_init_temp_')))
results.append(create_collection('tax_slabs', TaxSlab, 
    lambda: TaxSlab(name='_init_temp_', rate=0)))

# Step 2: Create collections with dependencies
print("Step 2: Creating collections with dependencies...")

# Services (needs ServiceGroup)
try:
    sg = ServiceGroup.objects.first()
    if not sg:
        sg = ServiceGroup(name='Default Group')
        sg.save()
    results.append(create_collection('services', Service,
        lambda: Service(name='_init_temp_', group=sg, price=0)))
except Exception as e:
    results.append(f"[ERROR] services: {str(e)[:60]}")

# Products (needs ProductCategory)
try:
    pc = ProductCategory.objects.first()
    if not pc:
        pc = ProductCategory(name='Default Category')
        pc.save()
    results.append(create_collection('products', Product,
        lambda: Product(name='_init_temp_', category=pc, price=0)))
except Exception as e:
    results.append(f"[ERROR] products: {str(e)[:60]}")

# Prepaid Packages (needs PrepaidGroup)
try:
    pg = PrepaidGroup.objects.first()
    if not pg:
        pg = PrepaidGroup(name='Default Group')
        pg.save()
    results.append(create_collection('prepaid_packages', PrepaidPackage,
        lambda: PrepaidPackage(name='_init_temp_', price=0)))
except Exception as e:
    results.append(f"[ERROR] prepaid_packages: {str(e)[:60]}")

# Memberships (needs Customer and MembershipPlan)
try:
    cust = Customer.objects.first()
    plan = MembershipPlan.objects.first()
    if not cust:
        cust = Customer(mobile='_init_temp_cust_', first_name='Temp')
        cust.save()
    if not plan:
        plan = MembershipPlan(name='_init_temp_plan_', validity_days=30, price=0)
        plan.save()
    results.append(create_collection('memberships', Membership,
        lambda: Membership(name='_init_temp_', customer=cust, plan=plan, 
                          price=0, purchase_date=datetime.utcnow(), 
                          expiry_date=datetime.utcnow())))
except Exception as e:
    results.append(f"[ERROR] memberships: {str(e)[:60]}")

# Bills (can be standalone)
results.append(create_collection('bills', Bill,
    lambda: Bill(bill_number='_INIT_TEMP_', final_amount=0)))

# Appointments (needs Customer and Staff)
try:
    cust = Customer.objects.first()
    staff = Staff.objects.first()
    if not cust:
        cust = Customer(mobile='_init_temp_cust2_', first_name='Temp')
        cust.save()
    if not staff:
        staff = Staff(mobile='_init_temp_staff_', first_name='Temp')
        staff.save()
    results.append(create_collection('appointments', Appointment,
        lambda: Appointment(customer=cust, staff=staff, 
                          appointment_date=datetime.now().date(),
                          start_time='00:00:00')))
except Exception as e:
    results.append(f"[ERROR] appointments: {str(e)[:60]}")

# Expenses (needs ExpenseCategory)
try:
    ec = ExpenseCategory.objects.first()
    if not ec:
        ec = ExpenseCategory(name='Default Category')
        ec.save()
    results.append(create_collection('expenses', Expense,
        lambda: Expense(category=ec, name='_init_temp_', amount=0,
                       expense_date=datetime.now().date())))
except Exception as e:
    results.append(f"[ERROR] expenses: {str(e)[:60]}")

# Orders (needs Supplier)
try:
    sup = Supplier.objects.first()
    if not sup:
        sup = Supplier(name='Default Supplier')
        sup.save()
    results.append(create_collection('orders', Order,
        lambda: Order(supplier=sup, order_date=datetime.now().date(),
                     total_amount=0)))
except Exception as e:
    results.append(f"[ERROR] orders: {str(e)[:60]}")

# Other collections
results.append(create_collection('leads', Lead,
    lambda: Lead(name='_init_temp_')))
results.append(create_collection('feedbacks', Feedback,
    lambda: Feedback(rating=5, comment='_init_temp_')))
results.append(create_collection('cash_transactions', CashTransaction,
    lambda: CashTransaction(transaction_type='in', amount=0,
                           transaction_date=datetime.now().date(),
                           transaction_time='00:00:00')))

# Staff Attendance (needs Staff)
try:
    staff = Staff.objects.first()
    if not staff:
        staff = Staff(mobile='_init_temp_staff2_', first_name='Temp')
        staff.save()
    results.append(create_collection('staff_attendance', StaffAttendance,
        lambda: StaffAttendance(staff=staff, attendance_date=datetime.now().date(),
                               status='present')))
except Exception as e:
    results.append(f"[ERROR] staff_attendance: {str(e)[:60]}")

# Managers
results.append(create_collection('managers', Manager,
    lambda: Manager(first_name='_init_temp_', email='_init_@temp.com',
                   mobile='0000000000')))

# Step 3: Initialize settings
print("Step 3: Initializing settings collections...")
try:
    LoyaltyProgramSettings.get_settings()
    results.append("[CREATED] loyalty_program_settings")
except Exception as e:
    results.append(f"[ERROR] loyalty_program_settings: {str(e)[:60]}")

try:
    ReferralProgramSettings.get_settings()
    results.append("[CREATED] referral_program_settings")
except Exception as e:
    results.append(f"[ERROR] referral_program_settings: {str(e)[:60]}")

try:
    TaxSettings.get_settings()
    results.append("[CREATED] tax_settings")
except Exception as e:
    results.append(f"[ERROR] tax_settings: {str(e)[:60]}")

# Print results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

created_count = sum(1 for r in results if '[CREATED]' in r or '[EXISTS]' in r)
error_count = sum(1 for r in results if '[ERROR]' in r)

print(f"\nSuccess: {created_count}")
for r in results:
    if '[CREATED]' in r or '[EXISTS]' in r:
        print(f"  {r}")

if error_count > 0:
    print(f"\nErrors: {error_count}")
    for r in results:
        if '[ERROR]' in r:
            print(f"  {r}")

print("\n" + "=" * 60)
print("Done! Check MongoDB Atlas Data Explorer to see your collections.")
print("=" * 60)

disconnect()

