"""
Create All MongoDB Collections Using Flask App Context
This uses the same connection method as the running Flask app
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app which handles MongoDB connection
print("Loading Flask app...")
from app import app

print("=" * 60)
print("Creating MongoDB Collections")
print("=" * 60)
print()

# Use Flask app context
with app.app_context():
    from models import (
        Customer, Staff, ServiceGroup, Service, ProductCategory, Product,
        Package, PrepaidGroup, PrepaidPackage, MembershipPlan, Membership,
        Bill, Appointment, ExpenseCategory, Expense, Supplier, Order,
        Lead, Feedback, StaffAttendance, Asset, CashTransaction,
        LoyaltyProgramSettings, ReferralProgramSettings, TaxSettings, TaxSlab, Manager,
        BillItemEmbedded
    )
    
    # Test MongoDB connection first
    print("Testing MongoDB connection...")
    try:
        from mongoengine import get_db
        db = get_db()
        # Try a simple operation to verify connection works
        db.list_collection_names()
        print("  [OK] Connection verified")
    except Exception as e:
        print(f"  [ERROR] Connection test failed: {str(e)[:200]}")
        print("\nPossible issues:")
        print("  1. Check if your IP is whitelisted in MongoDB Atlas")
        print("  2. Verify network connectivity")
        print("  3. Check MongoDB connection string credentials")
        print("\nContinuing anyway...\n")
    
    collections_created = []
    collections_skipped = []
    errors = []
    
    def create_collection(name, create_func):
        """Helper to create a collection"""
        try:
            # Check if collection already has data
            model = create_func.__self__ if hasattr(create_func, '__self__') else None
            if model and hasattr(model, 'objects'):
                count = model.objects.count()
                if count > 0:
                    collections_skipped.append(name)
                    return True
            
            # Try to create
            result = create_func()
            if result:
                collections_created.append(name)
                return True
            return False
        except Exception as e:
            error_msg = str(e)[:80]
            errors.append(f"{name}: {error_msg}")
            return False
    
    print("Creating base collections...")
    
    # 1. Service Groups
    try:
        if ServiceGroup.objects.count() == 0:
            sg = ServiceGroup(name='_init_')
            sg.save()
            ServiceGroup.objects(name='_init_').delete()
            collections_created.append('service_groups')
        else:
            collections_skipped.append('service_groups')
        print("  [OK] service_groups")
    except Exception as e:
        error_msg = str(e)
        errors.append(f"service_groups: {error_msg[:50]}")
        print(f"  [ERROR] service_groups: {error_msg}")
    
    # 2. Product Categories
    try:
        if ProductCategory.objects.count() == 0:
            pc = ProductCategory(name='_init_')
            pc.save()
            ProductCategory.objects(name='_init_').delete()
            collections_created.append('product_categories')
        else:
            collections_skipped.append('product_categories')
        print("  [OK] product_categories")
    except Exception as e:
        error_msg = str(e)
        errors.append(f"product_categories: {error_msg[:50]}")
        print(f"  [ERROR] product_categories: {error_msg}")
    
    # 3. Customers
    try:
        if Customer.objects.count() == 0:
            c = Customer(mobile='_init_', first_name='Init')
            c.save()
            Customer.objects(mobile='_init_').delete()
            collections_created.append('customers')
        else:
            collections_skipped.append('customers')
        print("  [OK] customers")
    except Exception as e:
        error_msg = str(e)
        errors.append(f"customers: {error_msg[:50]}")
        print(f"  [ERROR] customers: {error_msg}")
    
    # 4. Staff
    try:
        if Staff.objects.count() == 0:
            s = Staff(mobile='_init_', first_name='Init')
            s.save()
            Staff.objects(mobile='_init_').delete()
            collections_created.append('staffs')
        else:
            collections_skipped.append('staffs')
        print("  [OK] staffs")
    except Exception as e:
        error_msg = str(e)
        errors.append(f"staffs: {error_msg[:50]}")
        print(f"  [ERROR] staffs: {error_msg}")
    
    # 5. Services
    try:
        if Service.objects.count() == 0:
            sg = ServiceGroup.objects.first()
            if not sg:
                sg = ServiceGroup(name='Default')
                sg.save()
            s = Service(name='_init_', group=sg, price=0)
            s.save()
            Service.objects(name='_init_').delete()
            collections_created.append('services')
        else:
            collections_skipped.append('services')
        print("  [OK] services")
    except Exception as e:
        error_msg = str(e)
        errors.append(f"services: {error_msg[:50]}")
        print(f"  [ERROR] services: {error_msg}")
    
    # 6. Products
    try:
        if Product.objects.count() == 0:
            pc = ProductCategory.objects.first()
            if not pc:
                pc = ProductCategory(name='Default')
                pc.save()
            p = Product(name='_init_', category=pc, price=0)
            p.save()
            Product.objects(name='_init_').delete()
            collections_created.append('products')
        else:
            collections_skipped.append('products')
        print("  [OK] products")
    except Exception as e:
        error_msg = str(e)
        errors.append(f"products: {error_msg[:50]}")
        print(f"  [ERROR] products: {error_msg}")
    
    # 7. Packages
    try:
        if Package.objects.count() == 0:
            p = Package(name='_init_', price=0)
            p.save()
            Package.objects(name='_init_').delete()
            collections_created.append('packages')
        else:
            collections_skipped.append('packages')
        print("  [OK] packages")
    except Exception as e:
        errors.append(f"packages: {str(e)[:50]}")
        print(f"  [ERROR] packages")
    
    # 8. Prepaid Groups
    try:
        if PrepaidGroup.objects.count() == 0:
            pg = PrepaidGroup(name='_init_')
            pg.save()
            PrepaidGroup.objects(name='_init_').delete()
            collections_created.append('prepaid_groups')
        else:
            collections_skipped.append('prepaid_groups')
        print("  [OK] prepaid_groups")
    except Exception as e:
        errors.append(f"prepaid_groups: {str(e)[:50]}")
        print(f"  [ERROR] prepaid_groups")
    
    # 9. Prepaid Packages
    try:
        if PrepaidPackage.objects.count() == 0:
            pp = PrepaidPackage(name='_init_', price=0)
            pp.save()
            PrepaidPackage.objects(name='_init_').delete()
            collections_created.append('prepaid_packages')
        else:
            collections_skipped.append('prepaid_packages')
        print("  [OK] prepaid_packages")
    except Exception as e:
        errors.append(f"prepaid_packages: {str(e)[:50]}")
        print(f"  [ERROR] prepaid_packages")
    
    # 10. Membership Plans
    try:
        if MembershipPlan.objects.count() == 0:
            mp = MembershipPlan(name='_init_', validity_days=30, price=0)
            mp.save()
            MembershipPlan.objects(name='_init_').delete()
            collections_created.append('membership_plans')
        else:
            collections_skipped.append('membership_plans')
        print("  [OK] membership_plans")
    except Exception as e:
        errors.append(f"membership_plans: {str(e)[:50]}")
        print(f"  [ERROR] membership_plans")
    
    # 11. Memberships
    try:
        if Membership.objects.count() == 0:
            cust = Customer.objects.first()
            if not cust:
                cust = Customer(mobile='_temp_', first_name='Temp')
                cust.save()
            plan = MembershipPlan.objects.first()
            if not plan:
                plan = MembershipPlan(name='Temp', validity_days=30, price=0)
                plan.save()
            m = Membership(name='_init_', customer=cust, plan=plan, price=0,
                          purchase_date=datetime.utcnow(), expiry_date=datetime.utcnow())
            m.save()
            Membership.objects(name='_init_').delete()
            collections_created.append('memberships')
        else:
            collections_skipped.append('memberships')
        print("  [OK] memberships")
    except Exception as e:
        errors.append(f"memberships: {str(e)[:50]}")
        print(f"  [ERROR] memberships")
    
    # 12. Bills
    try:
        if Bill.objects.count() == 0:
            b = Bill(bill_number='_INIT_', final_amount=0)
            b.save()
            Bill.objects(bill_number='_INIT_').delete()
            collections_created.append('bills')
        else:
            collections_skipped.append('bills')
        print("  [OK] bills")
    except Exception as e:
        errors.append(f"bills: {str(e)[:50]}")
        print(f"  [ERROR] bills")
    
    # 13. Appointments
    try:
        if Appointment.objects.count() == 0:
            cust = Customer.objects.first()
            staff = Staff.objects.first()
            if not cust:
                cust = Customer(mobile='_temp_', first_name='Temp')
                cust.save()
            if not staff:
                staff = Staff(mobile='_temp_', first_name='Temp')
                staff.save()
            a = Appointment(customer=cust, staff=staff, appointment_date=datetime.now().date(),
                           start_time='00:00:00')
            a.save()
            Appointment.objects(customer=cust, start_time='00:00:00').delete()
            collections_created.append('appointments')
        else:
            collections_skipped.append('appointments')
        print("  [OK] appointments")
    except Exception as e:
        errors.append(f"appointments: {str(e)[:50]}")
        print(f"  [ERROR] appointments")
    
    # 14. Expense Categories
    try:
        if ExpenseCategory.objects.count() == 0:
            ec = ExpenseCategory(name='_init_')
            ec.save()
            ExpenseCategory.objects(name='_init_').delete()
            collections_created.append('expense_categories')
        else:
            collections_skipped.append('expense_categories')
        print("  [OK] expense_categories")
    except Exception as e:
        errors.append(f"expense_categories: {str(e)[:50]}")
        print(f"  [ERROR] expense_categories")
    
    # 15. Expenses
    try:
        if Expense.objects.count() == 0:
            ec = ExpenseCategory.objects.first()
            if not ec:
                ec = ExpenseCategory(name='Default')
                ec.save()
            e = Expense(category=ec, name='_init_', amount=0, expense_date=datetime.now().date())
            e.save()
            Expense.objects(name='_init_').delete()
            collections_created.append('expenses')
        else:
            collections_skipped.append('expenses')
        print("  [OK] expenses")
    except Exception as e:
        errors.append(f"expenses: {str(e)[:50]}")
        print(f"  [ERROR] expenses")
    
    # 16. Suppliers
    try:
        if Supplier.objects.count() == 0:
            s = Supplier(name='_init_')
            s.save()
            Supplier.objects(name='_init_').delete()
            collections_created.append('suppliers')
        else:
            collections_skipped.append('suppliers')
        print("  [OK] suppliers")
    except Exception as e:
        errors.append(f"suppliers: {str(e)[:50]}")
        print(f"  [ERROR] suppliers")
    
    # 17. Orders
    try:
        if Order.objects.count() == 0:
            sup = Supplier.objects.first()
            if not sup:
                sup = Supplier(name='Default')
                sup.save()
            o = Order(supplier=sup, order_date=datetime.now().date(), total_amount=0)
            o.save()
            Order.objects(supplier=sup, total_amount=0).delete()
            collections_created.append('orders')
        else:
            collections_skipped.append('orders')
        print("  [OK] orders")
    except Exception as e:
        errors.append(f"orders: {str(e)[:50]}")
        print(f"  [ERROR] orders")
    
    # 18. Leads
    try:
        if Lead.objects.count() == 0:
            l = Lead(name='_init_')
            l.save()
            Lead.objects(name='_init_').delete()
            collections_created.append('leads')
        else:
            collections_skipped.append('leads')
        print("  [OK] leads")
    except Exception as e:
        errors.append(f"leads: {str(e)[:50]}")
        print(f"  [ERROR] leads")
    
    # 19. Feedback
    try:
        if Feedback.objects.count() == 0:
            f = Feedback(rating=5, comment='_init_')
            f.save()
            Feedback.objects(comment='_init_').delete()
            collections_created.append('feedbacks')
        else:
            collections_skipped.append('feedbacks')
        print("  [OK] feedbacks")
    except Exception as e:
        errors.append(f"feedbacks: {str(e)[:50]}")
        print(f"  [ERROR] feedbacks")
    
    # 20. Staff Attendance
    try:
        if StaffAttendance.objects.count() == 0:
            staff = Staff.objects.first()
            if not staff:
                staff = Staff(mobile='_temp_', first_name='Temp')
                staff.save()
            sa = StaffAttendance(staff=staff, attendance_date=datetime.now().date(), status='present')
            sa.save()
            StaffAttendance.objects(staff=staff, attendance_date=datetime.now().date()).delete()
            collections_created.append('staff_attendance')
        else:
            collections_skipped.append('staff_attendance')
        print("  [OK] staff_attendance")
    except Exception as e:
        errors.append(f"staff_attendance: {str(e)[:50]}")
        print(f"  [ERROR] staff_attendance")
    
    # 21. Assets
    try:
        if Asset.objects.count() == 0:
            a = Asset(name='_init_')
            a.save()
            Asset.objects(name='_init_').delete()
            collections_created.append('assets')
        else:
            collections_skipped.append('assets')
        print("  [OK] assets")
    except Exception as e:
        errors.append(f"assets: {str(e)[:50]}")
        print(f"  [ERROR] assets")
    
    # 22. Cash Transactions
    try:
        if CashTransaction.objects.count() == 0:
            ct = CashTransaction(transaction_type='in', amount=0, 
                                transaction_date=datetime.now().date(), transaction_time='00:00:00')
            ct.save()
            CashTransaction.objects(transaction_date=datetime.now().date(), amount=0).delete()
            collections_created.append('cash_transactions')
        else:
            collections_skipped.append('cash_transactions')
        print("  [OK] cash_transactions")
    except Exception as e:
        errors.append(f"cash_transactions: {str(e)[:50]}")
        print(f"  [ERROR] cash_transactions")
    
    # 23. Tax Slabs
    try:
        if TaxSlab.objects.count() == 0:
            ts = TaxSlab(name='_init_', rate=0)
            ts.save()
            TaxSlab.objects(name='_init_').delete()
            collections_created.append('tax_slabs')
        else:
            collections_skipped.append('tax_slabs')
        print("  [OK] tax_slabs")
    except Exception as e:
        errors.append(f"tax_slabs: {str(e)[:50]}")
        print(f"  [ERROR] tax_slabs")
    
    # 24. Managers
    try:
        if Manager.objects.count() == 0:
            m = Manager(first_name='_init_', email='_init@_init.com', mobile='0000000000')
            m.save()
            Manager.objects(email='_init@_init.com').delete()
            collections_created.append('managers')
        else:
            collections_skipped.append('managers')
        print("  [OK] managers")
    except Exception as e:
        errors.append(f"managers: {str(e)[:50]}")
        print(f"  [ERROR] managers")
    
    # 25-27. Settings collections
    print("\nInitializing settings collections...")
    try:
        LoyaltyProgramSettings.get_settings()
        collections_created.append('loyalty_program_settings')
        print("  [OK] loyalty_program_settings")
    except Exception as e:
        errors.append(f"loyalty_program_settings: {str(e)[:50]}")
        print(f"  [ERROR] loyalty_program_settings")
    
    try:
        ReferralProgramSettings.get_settings()
        collections_created.append('referral_program_settings')
        print("  [OK] referral_program_settings")
    except Exception as e:
        errors.append(f"referral_program_settings: {str(e)[:50]}")
        print(f"  [ERROR] referral_program_settings")
    
    try:
        TaxSettings.get_settings()
        collections_created.append('tax_settings')
        print("  [OK] tax_settings")
    except Exception as e:
        errors.append(f"tax_settings: {str(e)[:50]}")
        print(f"  [ERROR] tax_settings")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created: {len(collections_created)} collections")
    if collections_created:
        for name in sorted(collections_created):
            print(f"  [OK] {name}")
    
    if collections_skipped:
        print(f"\nAlready existed: {len(collections_skipped)} collections")
        for name in sorted(collections_skipped)[:5]:
            print(f"  [SKIP] {name}")
        if len(collections_skipped) > 5:
            print(f"  ... and {len(collections_skipped) - 5} more")
    
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors[:10]:
            print(f"  [ERROR] {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    print("\n" + "=" * 60)
    print("Done! Check MongoDB Atlas Data Explorer to see collections.")
    print("=" * 60)

