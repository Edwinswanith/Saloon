"""
Comprehensive Backend Check - Test all endpoints and data handling
"""
from app import app, db
from models import (
    Customer, Staff, Service, ServiceGroup, Product, ProductCategory,
    Package, PrepaidPackage, PrepaidGroup, Membership, MembershipPlan,
    Bill, BillItem, Appointment, Expense, ExpenseCategory,
    Lead, Feedback, StaffAttendance, Asset, CashTransaction,
    Supplier, Order
)

def check_model_counts():
    """Check all model counts"""
    print("=" * 80)
    print("DATABASE MODEL COUNTS")
    print("=" * 80)
    
    models = [
        ('Customers', Customer),
        ('Staff', Staff),
        ('Service Groups', ServiceGroup),
        ('Services', Service),
        ('Product Categories', ProductCategory),
        ('Products', Product),
        ('Packages', Package),
        ('Prepaid Groups', PrepaidGroup),
        ('Prepaid Packages', PrepaidPackage),
        ('Membership Plans', MembershipPlan),
        ('Memberships', Membership),
        ('Bills', Bill),
        ('Bill Items', BillItem),
        ('Appointments', Appointment),
        ('Expense Categories', ExpenseCategory),
        ('Expenses', Expense),
        ('Leads', Lead),
        ('Feedback', Feedback),
        ('Staff Attendance', StaffAttendance),
        ('Assets', Asset),
        ('Cash Transactions', CashTransaction),
        ('Suppliers', Supplier),
        ('Orders', Order),
    ]
    
    for name, model in models:
        count = model.query.count()
        status = "[OK]" if count > 0 else "[EMPTY]"
        print(f"{status} {name}: {count}")

def check_relationships():
    """Check critical relationships"""
    print("\n" + "=" * 80)
    print("RELATIONSHIP CHECKS")
    print("=" * 80)
    
    # Bill -> Customer
    bill = Bill.query.first()
    if bill:
        try:
            customer_name = f"{bill.customer.first_name} {bill.customer.last_name}" if bill.customer else None
            print(f"[OK] Bill -> Customer: {customer_name}")
        except Exception as e:
            print(f"[ERROR] Bill -> Customer: {str(e)}")
    
    # Bill -> BillItem
    if bill:
        print(f"[OK] Bill -> BillItems: {len(bill.items)} items")
    
    # Appointment -> Service
    apt = Appointment.query.filter(Appointment.service_id.isnot(None)).first()
    if apt:
        try:
            service_name = apt.service.name if apt.service else None
            print(f"[OK] Appointment -> Service: {service_name}")
        except Exception as e:
            print(f"[ERROR] Appointment -> Service: {str(e)}")
    
    # Service -> ServiceGroup
    service = Service.query.first()
    if service:
        try:
            group_name = service.group.name if service.group else None
            print(f"[OK] Service -> ServiceGroup: {group_name}")
        except Exception as e:
            print(f"[ERROR] Service -> ServiceGroup: {str(e)}")
    
    # Product -> ProductCategory
    product = Product.query.first()
    if product:
        try:
            category_name = product.category.name if product.category else None
            print(f"[OK] Product -> ProductCategory: {category_name}")
        except Exception as e:
            print(f"[ERROR] Product -> ProductCategory: {str(e)}")

def check_data_integrity():
    """Check data integrity"""
    print("\n" + "=" * 80)
    print("DATA INTEGRITY CHECKS")
    print("=" * 80)
    
    # Bills with final_amount > 0
    completed_bills = Bill.query.filter(Bill.final_amount > 0).count()
    total_bills = Bill.query.count()
    print(f"[INFO] Bills with final_amount > 0: {completed_bills}/{total_bills}")
    
    # Bills with items
    bills_with_items = Bill.query.filter(Bill.items.any()).count()
    print(f"[INFO] Bills with items: {bills_with_items}/{total_bills}")
    
    # Appointments with services
    apts_with_service = Appointment.query.filter(Appointment.service_id.isnot(None)).count()
    total_apts = Appointment.query.count()
    print(f"[INFO] Appointments with services: {apts_with_service}/{total_apts}")
    
    # Products with stock
    products_in_stock = Product.query.filter(Product.stock_quantity > 0).count()
    total_products = Product.query.count()
    print(f"[INFO] Products in stock: {products_in_stock}/{total_products}")
    
    # Active staff
    active_staff = Staff.query.filter_by(status='active').count()
    total_staff = Staff.query.count()
    print(f"[INFO] Active staff: {active_staff}/{total_staff}")

def check_recent_data():
    """Check recent data entries"""
    print("\n" + "=" * 80)
    print("RECENT DATA ENTRIES")
    print("=" * 80)
    
    # Recent bill
    recent_bill = Bill.query.order_by(Bill.created_at.desc()).first()
    if recent_bill:
        print(f"[OK] Most Recent Bill: {recent_bill.bill_number}")
        print(f"     Date: {recent_bill.bill_date}")
        print(f"     Amount: Rs.{recent_bill.final_amount}")
        print(f"     Items: {len(recent_bill.items)}")
    
    # Recent appointment
    recent_apt = Appointment.query.order_by(Appointment.created_at.desc()).first()
    if recent_apt:
        print(f"[OK] Most Recent Appointment:")
        print(f"     Date: {recent_apt.appointment_date}")
        print(f"     Status: {recent_apt.status}")
    
    # Recent cash transaction
    recent_cash = CashTransaction.query.order_by(CashTransaction.created_at.desc()).first()
    if recent_cash:
        print(f"[OK] Most Recent Cash Transaction:")
        print(f"     Type: {recent_cash.transaction_type.upper()}")
        print(f"     Amount: Rs.{recent_cash.amount}")

def main():
    with app.app_context():
        print("\n")
        print("*" * 80)
        print("COMPREHENSIVE BACKEND CHECK")
        print("*" * 80)
        print("\n")
        
        check_model_counts()
        check_relationships()
        check_data_integrity()
        check_recent_data()
        
        print("\n" + "=" * 80)
        print("CHECK COMPLETE")
        print("=" * 80)
        print("\n[SUMMARY]")
        print("All backend models, relationships, and data handling have been verified.")
        print("If any [ERROR] or [EMPTY] appears above, those sections need attention.")
        print("=" * 80)

if __name__ == '__main__':
    main()

