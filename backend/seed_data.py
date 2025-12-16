"""
Seed script to populate the salon database with dummy data
Run this file to add sample data for testing
"""

from app import app, db
from models import (
    Customer, Staff, ServiceGroup, Service, ProductCategory, Product,
    Package, PrepaidGroup, PrepaidPackage, Membership, Bill, BillItem,
    Appointment, ExpenseCategory, Expense, Supplier, Order, OrderItem,
    Lead, Feedback, StaffAttendance, Asset, CashTransaction
)
from datetime import datetime, date, time, timedelta
import random
import json

def clear_database():
    """Clear all data from database"""
    print("Clearing existing data...")
    with app.app_context():
        db.drop_all()
        db.create_all()
    print("Database cleared and tables recreated!")

def seed_customers():
    """Add sample customers"""
    print("Seeding customers...")

    customers_data = [
        {"mobile": "9876543210", "first_name": "Priya", "last_name": "Sharma", "email": "priya.sharma@email.com", "source": "Instagram", "gender": "Female", "dob": date(1995, 3, 15), "dob_range": "Young", "loyalty_points": 250, "wallet_balance": 500.0},
        {"mobile": "9876543211", "first_name": "Rahul", "last_name": "Kumar", "email": "rahul.kumar@email.com", "source": "Walk-in", "gender": "Male", "dob": date(1988, 7, 22), "dob_range": "Mid", "loyalty_points": 150, "wallet_balance": 200.0},
        {"mobile": "9876543212", "first_name": "Anjali", "last_name": "Patel", "email": "anjali.patel@email.com", "source": "Facebook", "gender": "Female", "dob": date(1992, 11, 8), "dob_range": "Young", "loyalty_points": 320, "wallet_balance": 750.0},
        {"mobile": "9876543213", "first_name": "Vikram", "last_name": "Singh", "email": "vikram.singh@email.com", "source": "Referral", "gender": "Male", "dob": date(1985, 5, 30), "dob_range": "Mid", "loyalty_points": 180, "wallet_balance": 300.0},
        {"mobile": "9876543214", "first_name": "Neha", "last_name": "Gupta", "email": "neha.gupta@email.com", "source": "Instagram", "gender": "Female", "dob": date(1998, 1, 12), "dob_range": "Young", "loyalty_points": 420, "wallet_balance": 1000.0},
        {"mobile": "9876543215", "first_name": "Amit", "last_name": "Verma", "email": "amit.verma@email.com", "source": "Walk-in", "gender": "Male", "dob": date(1990, 9, 5), "dob_range": "Young", "loyalty_points": 90, "wallet_balance": 100.0},
        {"mobile": "9876543216", "first_name": "Pooja", "last_name": "Reddy", "email": "pooja.reddy@email.com", "source": "Facebook", "gender": "Female", "dob": date(1987, 4, 18), "dob_range": "Mid", "loyalty_points": 280, "wallet_balance": 450.0},
        {"mobile": "9876543217", "first_name": "Arjun", "last_name": "Nair", "email": "arjun.nair@email.com", "source": "Instagram", "gender": "Male", "dob": date(1993, 12, 25), "dob_range": "Young", "loyalty_points": 195, "wallet_balance": 350.0},
        {"mobile": "9876543218", "first_name": "Sneha", "last_name": "Desai", "email": "sneha.desai@email.com", "source": "Referral", "gender": "Female", "dob": date(1991, 6, 14), "dob_range": "Young", "loyalty_points": 310, "wallet_balance": 600.0},
        {"mobile": "9876543219", "first_name": "Karthik", "last_name": "Iyer", "email": "karthik.iyer@email.com", "source": "Walk-in", "gender": "Male", "dob": date(1989, 8, 9), "dob_range": "Mid", "loyalty_points": 140, "wallet_balance": 250.0},
        # Additional customers
        {"mobile": "9876543220", "first_name": "Riya", "last_name": "Kapoor", "email": "riya.kapoor@email.com", "source": "Instagram", "gender": "Female", "dob": date(1996, 2, 20), "dob_range": "Young", "loyalty_points": 380, "wallet_balance": 800.0},
        {"mobile": "9876543221", "first_name": "Siddharth", "last_name": "Bhatia", "email": "siddharth.bhatia@email.com", "source": "Facebook", "gender": "Male", "dob": date(1986, 10, 3), "dob_range": "Mid", "loyalty_points": 220, "wallet_balance": 400.0},
        {"mobile": "9876543222", "first_name": "Kavya", "last_name": "Menon", "email": "kavya.menon@email.com", "source": "Referral", "gender": "Female", "dob": date(1994, 7, 11), "dob_range": "Young", "loyalty_points": 450, "wallet_balance": 900.0},
        {"mobile": "9876543223", "first_name": "Rohit", "last_name": "Malik", "email": "rohit.malik@email.com", "source": "Walk-in", "gender": "Male", "dob": date(1991, 4, 28), "dob_range": "Young", "loyalty_points": 120, "wallet_balance": 150.0},
        {"mobile": "9876543224", "first_name": "Isha", "last_name": "Chopra", "email": "isha.chopra@email.com", "source": "Instagram", "gender": "Female", "dob": date(1997, 9, 16), "dob_range": "Young", "loyalty_points": 290, "wallet_balance": 550.0},
        {"mobile": "9876543225", "first_name": "Aditya", "last_name": "Saxena", "email": "aditya.saxena@email.com", "source": "Google", "gender": "Male", "dob": date(1987, 12, 5), "dob_range": "Mid", "loyalty_points": 170, "wallet_balance": 280.0},
        {"mobile": "9876543226", "first_name": "Meera", "last_name": "Krishnan", "email": "meera.krishnan@email.com", "source": "Facebook", "gender": "Female", "dob": date(1993, 5, 22), "dob_range": "Young", "loyalty_points": 340, "wallet_balance": 680.0},
        {"mobile": "9876543227", "first_name": "Varun", "last_name": "Agarwal", "email": "varun.agarwal@email.com", "source": "Walk-in", "gender": "Male", "dob": date(1990, 11, 8), "dob_range": "Young", "loyalty_points": 95, "wallet_balance": 120.0},
        {"mobile": "9876543228", "first_name": "Tanvi", "last_name": "Joshi", "email": "tanvi.joshi@email.com", "source": "Instagram", "gender": "Female", "dob": date(1995, 8, 14), "dob_range": "Young", "loyalty_points": 410, "wallet_balance": 850.0},
        {"mobile": "9876543229", "first_name": "Nikhil", "last_name": "Pandey", "email": "nikhil.pandey@email.com", "source": "Referral", "gender": "Male", "dob": date(1988, 3, 19), "dob_range": "Mid", "loyalty_points": 200, "wallet_balance": 380.0},
        {"mobile": "9876543230", "first_name": "Shreya", "last_name": "Banerjee", "email": "shreya.banerjee@email.com", "source": "Facebook", "gender": "Female", "dob": date(1992, 6, 7), "dob_range": "Young", "loyalty_points": 360, "wallet_balance": 720.0},
        {"mobile": "9876543231", "first_name": "Kunal", "last_name": "Sharma", "email": "kunal.sharma@email.com", "source": "Walk-in", "gender": "Male", "dob": date(1989, 1, 25), "dob_range": "Mid", "loyalty_points": 130, "wallet_balance": 180.0},
        {"mobile": "9876543232", "first_name": "Aishwarya", "last_name": "Nair", "email": "aishwarya.nair@email.com", "source": "Instagram", "gender": "Female", "dob": date(1996, 10, 12), "dob_range": "Young", "loyalty_points": 480, "wallet_balance": 950.0},
        {"mobile": "9876543233", "first_name": "Rajesh", "last_name": "Kumar", "email": "rajesh.kumar@email.com", "source": "Google", "gender": "Male", "dob": date(1985, 7, 30), "dob_range": "Mid", "loyalty_points": 160, "wallet_balance": 220.0},
        {"mobile": "9876543234", "first_name": "Divya", "last_name": "Srinivasan", "email": "divya.srinivasan@email.com", "source": "Referral", "gender": "Female", "dob": date(1994, 4, 18), "dob_range": "Young", "loyalty_points": 330, "wallet_balance": 650.0},
    ]

    customers = []
    for data in customers_data:
        customer = Customer(**data, referral_code=f"REF{random.randint(1000, 9999)}")
        customers.append(customer)
        db.session.add(customer)

    db.session.commit()
    print(f"Added {len(customers)} customers")
    return customers

def seed_staff():
    """Add sample staff members"""
    print("Seeding staff...")

    staff_data = [
        {"mobile": "9999888877", "first_name": "Meera", "last_name": "Shah", "email": "meera@salon.com", "salary": 25000, "commission_rate": 10, "status": "active"},
        {"mobile": "9999888878", "first_name": "Rohan", "last_name": "Mehta", "email": "rohan@salon.com", "salary": 22000, "commission_rate": 8, "status": "active"},
        {"mobile": "9999888879", "first_name": "Kavita", "last_name": "Rao", "email": "kavita@salon.com", "salary": 28000, "commission_rate": 12, "status": "active"},
        {"mobile": "9999888880", "first_name": "Suresh", "last_name": "Joshi", "email": "suresh@salon.com", "salary": 20000, "commission_rate": 7, "status": "active"},
        {"mobile": "9999888881", "first_name": "Divya", "last_name": "Pillai", "email": "divya@salon.com", "salary": 26000, "commission_rate": 10, "status": "active"},
        {"mobile": "9999888882", "first_name": "Ajay", "last_name": "Kumar", "email": "ajay@salon.com", "salary": 24000, "commission_rate": 9, "status": "active"},
        {"mobile": "9999888883", "first_name": "Ashok", "last_name": "Reddy", "email": "ashok@salon.com", "salary": 21000, "commission_rate": 8, "status": "active"},
        {"mobile": "9999888884", "first_name": "Deepika", "last_name": "Patel", "email": "deepika@salon.com", "salary": 27000, "commission_rate": 11, "status": "active"},
        {"mobile": "9999888885", "first_name": "Bhanu", "last_name": "Sharma", "email": "bhanu@salon.com", "salary": 23000, "commission_rate": 9, "status": "active"},
        {"mobile": "9999888886", "first_name": "Anupama", "last_name": "Nair", "email": "anupama@salon.com", "salary": 25000, "commission_rate": 10, "status": "active"},
    ]

    staff_members = []
    for data in staff_data:
        staff = Staff(**data)
        staff_members.append(staff)
        db.session.add(staff)

    db.session.commit()
    print(f"Added {len(staff_members)} staff members")
    return staff_members

def seed_service_groups_and_services():
    """Add service groups and services"""
    print("Seeding services...")

    # Service Groups
    groups_data = [
        {"name": "Hair Care", "display_order": 1},
        {"name": "Skin Care", "display_order": 2},
        {"name": "Nail Care", "display_order": 3},
        {"name": "Spa & Massage", "display_order": 4},
        {"name": "Bridal Services", "display_order": 5},
    ]

    groups = []
    for data in groups_data:
        group = ServiceGroup(**data)
        groups.append(group)
        db.session.add(group)

    db.session.commit()

    # Services
    services_data = [
        # Hair Care
        {"name": "Haircut (Men)", "group_id": 1, "price": 300, "duration": 30, "status": "active"},
        {"name": "Haircut (Women)", "group_id": 1, "price": 500, "duration": 45, "status": "active"},
        {"name": "Hair Color", "group_id": 1, "price": 2500, "duration": 120, "status": "active"},
        {"name": "Hair Spa", "group_id": 1, "price": 1500, "duration": 60, "status": "active"},
        {"name": "Keratin Treatment", "group_id": 1, "price": 5000, "duration": 180, "status": "active"},

        # Skin Care
        {"name": "Facial (Basic)", "group_id": 2, "price": 800, "duration": 45, "status": "active"},
        {"name": "Facial (Gold)", "group_id": 2, "price": 2000, "duration": 60, "status": "active"},
        {"name": "Clean Up", "group_id": 2, "price": 600, "duration": 30, "status": "active"},
        {"name": "Bleach", "group_id": 2, "price": 500, "duration": 30, "status": "active"},

        # Nail Care
        {"name": "Manicure", "group_id": 3, "price": 400, "duration": 30, "status": "active"},
        {"name": "Pedicure", "group_id": 3, "price": 500, "duration": 45, "status": "active"},
        {"name": "Gel Nails", "group_id": 3, "price": 1200, "duration": 60, "status": "active"},

        # Spa & Massage
        {"name": "Swedish Massage", "group_id": 4, "price": 2000, "duration": 60, "status": "active"},
        {"name": "Deep Tissue Massage", "group_id": 4, "price": 2500, "duration": 60, "status": "active"},
        {"name": "Aromatherapy", "group_id": 4, "price": 1800, "duration": 45, "status": "active"},

        # Bridal Services
        {"name": "Bridal Makeup", "group_id": 5, "price": 15000, "duration": 180, "status": "active"},
        {"name": "Pre-Bridal Package", "group_id": 5, "price": 25000, "duration": 240, "status": "active"},
    ]

    services = []
    for data in services_data:
        service = Service(**data, description=f"Professional {data['name']} service")
        services.append(service)
        db.session.add(service)

    db.session.commit()
    print(f"Added {len(groups)} service groups and {len(services)} services")
    return groups, services

def seed_product_categories_and_products():
    """Add product categories and products"""
    print("Seeding products...")

    # Product Categories
    categories_data = [
        {"name": "Hair Care Products", "display_order": 1},
        {"name": "Skin Care Products", "display_order": 2},
        {"name": "Nail Care Products", "display_order": 3},
        {"name": "Styling Tools", "display_order": 4},
    ]

    categories = []
    for data in categories_data:
        category = ProductCategory(**data)
        categories.append(category)
        db.session.add(category)

    db.session.commit()

    # Products
    products_data = [
        {"name": "Shampoo - Anti Dandruff", "category_id": 1, "price": 450, "cost": 300, "stock_quantity": 25, "min_stock_level": 10, "sku": "SHMP001", "status": "active"},
        {"name": "Conditioner - Smooth & Shine", "category_id": 1, "price": 500, "cost": 350, "stock_quantity": 20, "min_stock_level": 10, "sku": "COND001", "status": "active"},
        {"name": "Hair Serum", "category_id": 1, "price": 800, "cost": 550, "stock_quantity": 15, "min_stock_level": 8, "sku": "SER001", "status": "active"},
        {"name": "Hair Oil - Herbal", "category_id": 1, "price": 350, "cost": 200, "stock_quantity": 30, "min_stock_level": 15, "sku": "OIL001", "status": "active"},

        {"name": "Face Wash", "category_id": 2, "price": 400, "cost": 250, "stock_quantity": 18, "min_stock_level": 10, "sku": "FW001", "status": "active"},
        {"name": "Moisturizer", "category_id": 2, "price": 600, "cost": 400, "stock_quantity": 22, "min_stock_level": 10, "sku": "MOIST001", "status": "active"},
        {"name": "Sunscreen SPF 50", "category_id": 2, "price": 550, "cost": 380, "stock_quantity": 12, "min_stock_level": 8, "sku": "SUN001", "status": "active"},

        {"name": "Nail Polish - Red", "category_id": 3, "price": 250, "cost": 150, "stock_quantity": 8, "min_stock_level": 10, "sku": "NP001", "status": "active"},
        {"name": "Nail Polish Remover", "category_id": 3, "price": 180, "cost": 100, "stock_quantity": 15, "min_stock_level": 10, "sku": "NPR001", "status": "active"},

        {"name": "Hair Dryer Professional", "category_id": 4, "price": 3500, "cost": 2500, "stock_quantity": 5, "min_stock_level": 3, "sku": "HD001", "status": "active"},
        {"name": "Hair Straightener", "category_id": 4, "price": 4000, "cost": 3000, "stock_quantity": 4, "min_stock_level": 2, "sku": "HS001", "status": "active"},
    ]

    products = []
    for data in products_data:
        product = Product(**data, description=f"Premium quality {data['name']}")
        products.append(product)
        db.session.add(product)

    db.session.commit()
    print(f"Added {len(categories)} product categories and {len(products)} products")
    return categories, products

def seed_packages():
    """Add service packages"""
    print("Seeding packages...")

    packages_data = [
        {"name": "Hair Care Combo", "price": 3500, "services": json.dumps([1, 2, 4]), "description": "Haircut + Hair Spa + Styling", "status": "active"},
        {"name": "Bridal Special", "price": 35000, "services": json.dumps([16, 17]), "description": "Complete bridal package", "status": "active"},
        {"name": "Spa Relaxation", "price": 5000, "services": json.dumps([13, 14, 15]), "description": "Full body massage and aromatherapy", "status": "active"},
        {"name": "Beauty Essentials", "price": 2500, "services": json.dumps([6, 8, 10, 11]), "description": "Facial + Manicure + Pedicure", "status": "active"},
    ]

    packages = []
    for data in packages_data:
        package = Package(**data)
        packages.append(package)
        db.session.add(package)

    db.session.commit()
    print(f"Added {len(packages)} packages")
    return packages

def seed_prepaid_packages(customers):
    """Add prepaid packages"""
    print("Seeding prepaid packages...")

    # Prepaid Groups
    groups_data = [
        {"name": "Value Pack", "display_order": 1},
        {"name": "Premium Pack", "display_order": 2},
        {"name": "VIP Pack", "display_order": 3},
    ]

    groups = []
    for data in groups_data:
        group = PrepaidGroup(**data)
        groups.append(group)
        db.session.add(group)

    db.session.commit()

    # Prepaid Packages
    prepaid_data = [
        {"name": "₹5000 Prepaid", "group_id": 1, "price": 5000, "customer_id": customers[0].id, "remaining_balance": 3500, "purchase_date": datetime.now() - timedelta(days=30), "expiry_date": datetime.now() + timedelta(days=335), "status": "active"},
        {"name": "₹10000 Prepaid", "group_id": 2, "price": 10000, "customer_id": customers[2].id, "remaining_balance": 8200, "purchase_date": datetime.now() - timedelta(days=15), "expiry_date": datetime.now() + timedelta(days=350), "status": "active"},
        {"name": "₹3000 Prepaid", "group_id": 1, "price": 3000, "customer_id": customers[4].id, "remaining_balance": 1500, "purchase_date": datetime.now() - timedelta(days=45), "expiry_date": datetime.now() + timedelta(days=320), "status": "active"},
        {"name": "₹8000 Prepaid", "group_id": 2, "price": 8000, "customer_id": customers[6].id, "remaining_balance": 5200, "purchase_date": datetime.now() - timedelta(days=20), "expiry_date": datetime.now() + timedelta(days=345), "status": "active"},
        {"name": "₹5000 Prepaid", "group_id": 1, "price": 5000, "customer_id": customers[8].id, "remaining_balance": 2800, "purchase_date": datetime.now() - timedelta(days=60), "expiry_date": datetime.now() + timedelta(days=305), "status": "active"},
        {"name": "₹15000 Prepaid", "group_id": 3, "price": 15000, "customer_id": customers[10].id, "remaining_balance": 12000, "purchase_date": datetime.now() - timedelta(days=10), "expiry_date": datetime.now() + timedelta(days=355), "status": "active"},
        {"name": "₹4000 Prepaid", "group_id": 1, "price": 4000, "customer_id": customers[12].id, "remaining_balance": 4000, "purchase_date": datetime.now() - timedelta(days=5), "expiry_date": datetime.now() + timedelta(days=360), "status": "active"},
    ]

    prepaids = []
    for data in prepaid_data:
        prepaid = PrepaidPackage(**data)
        prepaids.append(prepaid)
        db.session.add(prepaid)

    db.session.commit()
    print(f"Added {len(groups)} prepaid groups and {len(prepaids)} prepaid packages")
    return groups, prepaids

def seed_memberships(customers):
    """Add memberships"""
    print("Seeding memberships...")

    memberships_data = [
        {"name": "Gold Membership", "customer_id": customers[1].id, "price": 10000, "purchase_date": datetime.now() - timedelta(days=60), "expiry_date": datetime.now() + timedelta(days=305), "benefits": json.dumps(["20% off on all services", "Free birthday service"]), "status": "active"},
        {"name": "Platinum Membership", "customer_id": customers[3].id, "price": 20000, "purchase_date": datetime.now() - timedelta(days=30), "expiry_date": datetime.now() + timedelta(days=335), "benefits": json.dumps(["30% off on all services", "Free birthday service", "Priority booking"]), "status": "active"},
        {"name": "Gold Membership", "customer_id": customers[5].id, "price": 10000, "purchase_date": datetime.now() - timedelta(days=45), "expiry_date": datetime.now() + timedelta(days=320), "benefits": json.dumps(["20% off on all services", "Free birthday service"]), "status": "active"},
        {"name": "Silver Membership", "customer_id": customers[7].id, "price": 5000, "purchase_date": datetime.now() - timedelta(days=20), "expiry_date": datetime.now() + timedelta(days=345), "benefits": json.dumps(["10% off on all services"]), "status": "active"},
        {"name": "Platinum Membership", "customer_id": customers[9].id, "price": 20000, "purchase_date": datetime.now() - timedelta(days=15), "expiry_date": datetime.now() + timedelta(days=350), "benefits": json.dumps(["30% off on all services", "Free birthday service", "Priority booking"]), "status": "active"},
        {"name": "Gold Membership", "customer_id": customers[11].id, "price": 10000, "purchase_date": datetime.now() - timedelta(days=70), "expiry_date": datetime.now() + timedelta(days=295), "benefits": json.dumps(["20% off on all services", "Free birthday service"]), "status": "active"},
    ]

    memberships = []
    for data in memberships_data:
        membership = Membership(**data)
        memberships.append(membership)
        db.session.add(membership)

    db.session.commit()
    print(f"Added {len(memberships)} memberships")
    return memberships

def seed_bills(customers, staff, services, products, packages, prepaids, memberships):
    """Add sample bills with items"""
    print("Seeding bills...")

    bills = []

    # Generate bills for last 90 days
    for i in range(200):
        days_ago = random.randint(0, 90)
        bill_date = datetime.now() - timedelta(days=days_ago)

        # Random customer (80% chance) or walk-in (20% chance)
        customer_id = random.choice(customers).id if random.random() > 0.2 else None

        bill = Bill(
            bill_number=f"BILL-{bill_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            customer_id=customer_id,
            bill_date=bill_date,
            subtotal=0,
            discount_amount=0,
            discount_type='fix',
            tax_amount=0,
            tax_rate=18,
            final_amount=0,
            payment_mode=random.choice(['cash', 'upi', 'card']),
            booking_status='service-completed',
            is_deleted=False
        )

        db.session.add(bill)
        db.session.flush()

        # Add 1-4 items to the bill
        num_items = random.randint(1, 4)
        subtotal = 0

        for _ in range(num_items):
            item_type_choice = random.random()
            
            if item_type_choice > 0.5:  # 50% services
                service = random.choice(services)
                staff_member = random.choice(staff)

                item = BillItem(
                    bill_id=bill.id,
                    item_type='service',
                    service_id=service.id,
                    staff_id=staff_member.id,
                    start_time=time(random.randint(9, 17), random.choice([0, 30])),
                    price=service.price,
                    discount=0,
                    quantity=1,
                    total=service.price
                )
            elif item_type_choice > 0.2:  # 30% products
                product = random.choice(products)
                quantity = random.randint(1, 2)

                item = BillItem(
                    bill_id=bill.id,
                    item_type='product',
                    product_id=product.id,
                    price=product.price,
                    discount=0,
                    quantity=quantity,
                    total=product.price * quantity
                )
            elif item_type_choice > 0.1:  # 10% packages
                if packages:
                    package = random.choice(packages)
                    staff_member = random.choice(staff)
                    
                    item = BillItem(
                        bill_id=bill.id,
                        item_type='package',
                        package_id=package.id,
                        staff_id=staff_member.id,
                        price=package.price,
                        discount=0,
                        quantity=1,
                        total=package.price
                    )
                else:
                    # Fallback to service if no packages
                    service = random.choice(services)
                    staff_member = random.choice(staff)
                    item = BillItem(
                        bill_id=bill.id,
                        item_type='service',
                        service_id=service.id,
                        staff_id=staff_member.id,
                        start_time=time(random.randint(9, 17), random.choice([0, 30])),
                        price=service.price,
                        discount=0,
                        quantity=1,
                        total=service.price
                    )
            elif item_type_choice > 0.05:  # 5% prepaid
                if prepaids:
                    prepaid = random.choice(prepaids)
                    if prepaid.remaining_balance > 0:
                        # Use service as fallback since prepaid is typically used as payment method, not bill item
                        service = random.choice(services)
                        staff_member = random.choice(staff)
                        item = BillItem(
                            bill_id=bill.id,
                            item_type='service',
                            service_id=service.id,
                            staff_id=staff_member.id,
                            start_time=time(random.randint(9, 17), random.choice([0, 30])),
                            price=service.price,
                            discount=0,
                            quantity=1,
                            total=service.price
                        )
                    else:
                        # Fallback to service
                        service = random.choice(services)
                        staff_member = random.choice(staff)
                        item = BillItem(
                            bill_id=bill.id,
                            item_type='service',
                            service_id=service.id,
                            staff_id=staff_member.id,
                            start_time=time(random.randint(9, 17), random.choice([0, 30])),
                            price=service.price,
                            discount=0,
                            quantity=1,
                            total=service.price
                        )
                else:
                    # Fallback to service
                    service = random.choice(services)
                    staff_member = random.choice(staff)
                    item = BillItem(
                        bill_id=bill.id,
                        item_type='service',
                        service_id=service.id,
                        staff_id=staff_member.id,
                        start_time=time(random.randint(9, 17), random.choice([0, 30])),
                        price=service.price,
                        discount=0,
                        quantity=1,
                        total=service.price
                    )
            else:  # 5% membership
                if memberships:
                    # Use service as fallback since membership is typically purchased separately
                    service = random.choice(services)
                    staff_member = random.choice(staff)
                    item = BillItem(
                        bill_id=bill.id,
                        item_type='service',
                        service_id=service.id,
                        staff_id=staff_member.id,
                        start_time=time(random.randint(9, 17), random.choice([0, 30])),
                        price=service.price,
                        discount=0,
                        quantity=1,
                        total=service.price
                    )
                else:
                    # Fallback to service
                    service = random.choice(services)
                    staff_member = random.choice(staff)
                    item = BillItem(
                        bill_id=bill.id,
                        item_type='service',
                        service_id=service.id,
                        staff_id=staff_member.id,
                        start_time=time(random.randint(9, 17), random.choice([0, 30])),
                        price=service.price,
                        discount=0,
                        quantity=1,
                        total=service.price
                    )

            db.session.add(item)
            subtotal += item.total

        # Calculate totals
        discount = random.choice([0, 0, 0, 100, 200, 500])  # Most bills have no discount
        tax_amount = (subtotal - discount) * 0.18
        final_amount = subtotal - discount + tax_amount

        bill.subtotal = subtotal
        bill.discount_amount = discount
        bill.tax_amount = tax_amount
        bill.final_amount = final_amount

        bills.append(bill)

    db.session.commit()
    print(f"Added {len(bills)} bills with items")
    return bills

def seed_appointments(customers, staff, services):
    """Add appointments"""
    print("Seeding appointments...")

    appointments = []

    # Past appointments (last 90 days)
    for i in range(100):
        days_ago = random.randint(1, 90)
        appt_date = date.today() - timedelta(days=days_ago)

        appointment = Appointment(
            customer_id=random.choice(customers).id,
            staff_id=random.choice(staff).id,
            service_id=random.choice(services).id,
            appointment_date=appt_date,
            start_time=time(random.randint(9, 17), random.choice([0, 30])),
            end_time=time(random.randint(10, 18), random.choice([0, 30])),
            status=random.choice(['completed', 'completed', 'completed', 'no-show', 'cancelled']),
            notes="Regular appointment"
        )
        appointments.append(appointment)
        db.session.add(appointment)

    # Future appointments (next 14 days)
    for i in range(20):
        days_ahead = random.randint(1, 14)
        appt_date = date.today() + timedelta(days=days_ahead)

        appointment = Appointment(
            customer_id=random.choice(customers).id,
            staff_id=random.choice(staff).id,
            service_id=random.choice(services).id,
            appointment_date=appt_date,
            start_time=time(random.randint(9, 17), random.choice([0, 30])),
            end_time=time(random.randint(10, 18), random.choice([0, 30])),
            status='confirmed',
            notes="Upcoming appointment"
        )
        appointments.append(appointment)
        db.session.add(appointment)

    db.session.commit()
    print(f"Added {len(appointments)} appointments")
    return appointments

def seed_expenses():
    """Add expense categories and expenses"""
    print("Seeding expenses...")

    # Expense Categories
    categories_data = [
        {"name": "Rent", "description": "Monthly salon rent"},
        {"name": "Utilities", "description": "Electricity, water, internet"},
        {"name": "Salaries", "description": "Staff salaries"},
        {"name": "Product Purchase", "description": "Inventory purchases"},
        {"name": "Marketing", "description": "Advertising and promotions"},
        {"name": "Maintenance", "description": "Equipment and facility maintenance"},
    ]

    categories = []
    for data in categories_data:
        category = ExpenseCategory(**data)
        categories.append(category)
        db.session.add(category)

    db.session.commit()

    # Expenses
    expenses = []
    for i in range(120):
        days_ago = random.randint(0, 90)
        expense_date = date.today() - timedelta(days=days_ago)

        category = random.choice(categories)

        # Amount based on category
        if category.name == "Rent":
            amount = 50000
        elif category.name == "Salaries":
            amount = random.randint(20000, 30000)
        elif category.name == "Product Purchase":
            amount = random.randint(5000, 15000)
        else:
            amount = random.randint(500, 5000)

        expense = Expense(
            category_id=category.id,
            name=f"{category.name} - {expense_date.strftime('%B %Y')}",
            amount=amount,
            payment_mode=random.choice(['cash', 'card', 'upi']),
            expense_date=expense_date,
            description=f"Payment for {category.name.lower()}"
        )
        expenses.append(expense)
        db.session.add(expense)

    db.session.commit()
    print(f"Added {len(categories)} expense categories and {len(expenses)} expenses")
    return categories, expenses

def seed_inventory(products):
    """Add suppliers and orders"""
    print("Seeding inventory...")

    # Suppliers
    suppliers_data = [
        {"name": "Beauty Products Co.", "contact_no": "9988776655", "email": "contact@beautyproducts.com", "address": "Mumbai, Maharashtra", "status": "active"},
        {"name": "Hair Care Suppliers", "contact_no": "9988776656", "email": "sales@haircare.com", "address": "Delhi, NCR", "status": "active"},
        {"name": "Professional Tools Ltd.", "contact_no": "9988776657", "email": "info@protools.com", "address": "Bangalore, Karnataka", "status": "active"},
    ]

    suppliers = []
    for data in suppliers_data:
        supplier = Supplier(**data)
        suppliers.append(supplier)
        db.session.add(supplier)

    db.session.commit()

    # Orders
    orders = []
    for i in range(10):
        days_ago = random.randint(5, 60)
        order_date = date.today() - timedelta(days=days_ago)

        supplier = random.choice(suppliers)

        order = Order(
            supplier_id=supplier.id,
            order_date=order_date,
            total_amount=0,
            status=random.choice(['received', 'received', 'pending']),
            notes="Regular stock order"
        )

        db.session.add(order)
        db.session.flush()

        # Add order items
        num_items = random.randint(2, 5)
        total_amount = 0

        for _ in range(num_items):
            product = random.choice(products)
            quantity = random.randint(5, 20)
            unit_price = product.cost
            total = quantity * unit_price

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                total=total
            )
            db.session.add(order_item)
            total_amount += total

        order.total_amount = total_amount
        orders.append(order)

    db.session.commit()
    print(f"Added {len(suppliers)} suppliers and {len(orders)} orders")
    return suppliers, orders

def seed_leads():
    """Add leads"""
    print("Seeding leads...")

    leads_data = [
        {"name": "Ravi Shankar", "mobile": "9123456780", "email": "ravi@email.com", "source": "Instagram", "status": "new", "notes": "Interested in bridal package", "converted_to_customer": False},
        {"name": "Simran Kaur", "mobile": "9123456781", "email": "simran@email.com", "source": "Facebook", "status": "contacted", "notes": "Called and interested", "follow_up_date": datetime.now() + timedelta(days=3), "converted_to_customer": False},
        {"name": "Manish Tiwari", "mobile": "9123456782", "email": "manish@email.com", "source": "Walk-in", "status": "follow-up", "notes": "Visited salon, needs pricing", "follow_up_date": datetime.now() + timedelta(days=5), "converted_to_customer": False},
        {"name": "Anita Roy", "mobile": "9123456783", "email": "anita@email.com", "source": "Referral", "status": "completed", "notes": "Converted to customer", "converted_to_customer": True},
        {"name": "Deepak Malhotra", "mobile": "9123456784", "email": "deepak@email.com", "source": "Instagram", "status": "lost", "notes": "Not interested anymore", "converted_to_customer": False},
    ]

    leads = []
    for data in leads_data:
        lead = Lead(**data)
        leads.append(lead)
        db.session.add(lead)

    db.session.commit()
    print(f"Added {len(leads)} leads")
    return leads

def seed_feedback(customers, bills):
    """Add customer feedback"""
    print("Seeding feedback...")

    feedbacks = []
    for i in range(50):
        customer = random.choice(customers)
        bill = random.choice([b for b in bills if b.customer_id == customer.id]) if any(b.customer_id == customer.id for b in bills) else None

        rating = random.randint(3, 5)  # Most feedback is positive

        comments = {
            5: ["Excellent service!", "Loved it!", "Best salon experience", "Highly recommend", "Amazing staff"],
            4: ["Good service", "Happy with the results", "Will come again", "Nice experience"],
            3: ["Average service", "Could be better", "Decent experience"]
        }

        feedback = Feedback(
            customer_id=customer.id,
            bill_id=bill.id if bill else None,
            rating=rating,
            comment=random.choice(comments[rating])
        )
        feedbacks.append(feedback)
        db.session.add(feedback)

    db.session.commit()
    print(f"Added {len(feedbacks)} feedback entries")
    return feedbacks

def seed_attendance(staff):
    """Add staff attendance"""
    print("Seeding attendance...")

    attendances = []

    # Last 90 days attendance
    for days_ago in range(90):
        attendance_date = date.today() - timedelta(days=days_ago)

        for staff_member in staff:
            # 90% attendance rate
            if random.random() < 0.9:
                check_in = time(random.randint(8, 10), random.randint(0, 59))
                check_out = time(random.randint(18, 20), random.randint(0, 59))
                status = 'present' if check_in.hour < 10 else 'late'

                attendance = StaffAttendance(
                    staff_id=staff_member.id,
                    attendance_date=attendance_date,
                    check_in_time=check_in,
                    check_out_time=check_out,
                    status=status
                )
                attendances.append(attendance)
                db.session.add(attendance)

    db.session.commit()
    print(f"Added {len(attendances)} attendance records")
    return attendances

def seed_assets():
    """Add salon assets"""
    print("Seeding assets...")

    assets_data = [
        {"name": "Salon Chairs (Set of 6)", "category": "Furniture", "purchase_date": date(2023, 1, 15), "purchase_price": 60000, "current_value": 50000, "depreciation_rate": 10, "status": "active", "location": "Main Floor"},
        {"name": "Hair Dryers (Professional)", "category": "Equipment", "purchase_date": date(2023, 3, 20), "purchase_price": 35000, "current_value": 30000, "depreciation_rate": 15, "status": "active", "location": "Styling Area"},
        {"name": "Facial Steamers", "category": "Equipment", "purchase_date": date(2023, 5, 10), "purchase_price": 25000, "current_value": 22000, "depreciation_rate": 12, "status": "active", "location": "Facial Room"},
        {"name": "Massage Tables", "category": "Furniture", "purchase_date": date(2022, 11, 1), "purchase_price": 40000, "current_value": 32000, "depreciation_rate": 10, "status": "active", "location": "Spa Area"},
        {"name": "Reception Desk", "category": "Furniture", "purchase_date": date(2022, 12, 15), "purchase_price": 30000, "current_value": 27000, "depreciation_rate": 5, "status": "active", "location": "Reception"},
        {"name": "Air Conditioners (3 Units)", "category": "Equipment", "purchase_date": date(2023, 4, 1), "purchase_price": 90000, "current_value": 75000, "depreciation_rate": 15, "status": "active", "location": "Throughout"},
    ]

    assets = []
    for data in assets_data:
        asset = Asset(**data, description=f"{data['name']} for salon operations")
        assets.append(asset)
        db.session.add(asset)

    db.session.commit()
    print(f"Added {len(assets)} assets")
    return assets

def seed_cash_transactions():
    """Add cash transactions"""
    print("Seeding cash transactions...")

    transactions = []

    # Last 90 days transactions
    for i in range(150):
        days_ago = random.randint(0, 90)
        transaction_date = date.today() - timedelta(days=days_ago)
        transaction_time = time(random.randint(9, 19), random.randint(0, 59))

        transaction_type = random.choice(['in', 'in', 'in', 'out'])  # More cash in than out

        if transaction_type == 'in':
            amount = random.randint(500, 5000)
            reasons = ["Customer payment", "Product sale", "Service payment", "Package purchase"]
        else:
            amount = random.randint(100, 2000)
            reasons = ["Petty cash", "Emergency purchase", "Staff advance", "Miscellaneous"]

        transaction = CashTransaction(
            transaction_type=transaction_type,
            amount=amount,
            reason=random.choice(reasons),
            notes=f"Transaction on {transaction_date}",
            transaction_date=transaction_date,
            transaction_time=transaction_time
        )
        transactions.append(transaction)
        db.session.add(transaction)

    db.session.commit()
    print(f"Added {len(transactions)} cash transactions")
    return transactions

def main():
    """Main function to seed all data"""
    print("=" * 50)
    print("SALON DATABASE SEEDING")
    print("=" * 50)

    with app.app_context():
        # Clear existing data
        clear_database()

        # Seed data in order (respecting foreign key constraints)
        customers = seed_customers()
        staff = seed_staff()
        service_groups, services = seed_service_groups_and_services()
        product_categories, products = seed_product_categories_and_products()
        packages = seed_packages()
        prepaid_groups, prepaids = seed_prepaid_packages(customers)
        memberships = seed_memberships(customers)
        bills = seed_bills(customers, staff, services, products, packages, prepaids, memberships)
        appointments = seed_appointments(customers, staff, services)
        expense_categories, expenses = seed_expenses()
        suppliers, orders = seed_inventory(products)
        leads = seed_leads()
        feedbacks = seed_feedback(customers, bills)
        attendances = seed_attendance(staff)
        assets = seed_assets()
        cash_transactions = seed_cash_transactions()

        print("\n" + "=" * 50)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print(f"\nDatabase populated with:")
        print(f"  ✓ {len(customers)} Customers")
        print(f"  ✓ {len(staff)} Staff Members")
        print(f"  ✓ {len(services)} Services in {len(service_groups)} Groups")
        print(f"  ✓ {len(products)} Products in {len(product_categories)} Categories")
        print(f"  ✓ {len(packages)} Packages")
        print(f"  ✓ {len(prepaids)} Prepaid Packages")
        print(f"  ✓ {len(memberships)} Memberships")
        print(f"  ✓ {len(bills)} Bills (with mixed item types)")
        print(f"  ✓ {len(appointments)} Appointments")
        print(f"  ✓ {len(expenses)} Expenses")
        print(f"  ✓ {len(orders)} Inventory Orders")
        print(f"  ✓ {len(leads)} Leads")
        print(f"  ✓ {len(feedbacks)} Feedback Entries")
        print(f"  ✓ {len(attendances)} Attendance Records")
        print(f"  ✓ {len(assets)} Assets")
        print(f"  ✓ {len(cash_transactions)} Cash Transactions")
        print("\nYou can now start the Flask server and test the API!")
        print("Run: python app.py")
        print("=" * 50)

if __name__ == "__main__":
    main()
