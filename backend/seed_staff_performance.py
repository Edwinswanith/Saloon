"""
Script to seed staff performance data for Staff Leaderboard
Creates bills with bill items assigned to staff members
"""
from app import app
from models import db, Staff, Bill, BillItem, Service, Product, Package, Customer
from datetime import datetime, timedelta
import random
from sqlalchemy import func

def seed_staff_performance_data():
    """Create sample bills with bill items for staff performance"""
    with app.app_context():
        try:
            # Check if staff exist
            staff_list = Staff.query.filter_by(status='active').all()
            if not staff_list:
                print("No active staff found. Please seed staff first.")
                return

            # Check if services exist
            services = Service.query.filter_by(status='active').all()
            if not services:
                print("No services found. Please seed services first.")
                return

            # Check if products exist
            products = Product.query.filter_by(status='active').all()
            if not products:
                print("No products found. Please seed products first.")
                return

            # Check if packages exist
            packages = Package.query.filter_by(status='active').all()
            if not packages:
                print("No packages found. Please seed packages first.")
                return

            # Check if customers exist
            customers = Customer.query.all()
            if not customers:
                print("No customers found. Please seed customers first.")
                return

            # Check existing bills with staff items in last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            existing_recent_bills = db.session.query(Bill).join(BillItem).filter(
                BillItem.staff_id.isnot(None),
                Bill.is_deleted == False,
                Bill.bill_date >= thirty_days_ago
            ).distinct().count()

            if existing_recent_bills > 10:
                print(f"Found {existing_recent_bills} existing bills with staff assignments in last 30 days.")
                print("Recent sample data already exists. Skipping seed.")
                return
            
            print(f"Found {existing_recent_bills} recent bills. Creating additional sample data...")

            print("Creating sample bills with staff assignments...")
            
            # Create bills for the last 30 days
            bills_created = 0
            items_created = 0

            for day in range(30):
                bill_date = datetime.now() - timedelta(days=day)
                
                # Create 5-10 bills per day
                bills_per_day = random.randint(5, 10)
                
                for bill_num in range(bills_per_day):
                    # Random customer
                    customer = random.choice(customers) if customers else None
                    
                    # Create bill
                    bill = Bill(
                        bill_number=f"BILL-{bill_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                        customer_id=customer.id if customer else None,
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

                    subtotal = 0
                    num_items = random.randint(1, 4)
                    
                    for item_num in range(num_items):
                        # Assign random staff
                        staff_member = random.choice(staff_list)
                        item_type_choice = random.random()
                        
                        if item_type_choice > 0.5:  # 50% services
                            service = random.choice(services)
                            item = BillItem(
                                bill_id=bill.id,
                                item_type='service',
                                service_id=service.id,
                                staff_id=staff_member.id,
                                price=service.price,
                                discount=0,
                                quantity=1,
                                total=service.price
                            )
                            subtotal += service.price
                        elif item_type_choice > 0.3:  # 20% products
                            product = random.choice(products)
                            quantity = random.randint(1, 2)
                            item = BillItem(
                                bill_id=bill.id,
                                item_type='product',
                                product_id=product.id,
                                staff_id=staff_member.id,  # Staff can sell products too
                                price=product.price,
                                discount=0,
                                quantity=quantity,
                                total=product.price * quantity
                            )
                            subtotal += product.price * quantity
                        elif item_type_choice > 0.2:  # 10% packages
                            package = random.choice(packages)
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
                            subtotal += package.price
                        else:  # 20% prepaid (but we'll use service as fallback)
                            service = random.choice(services)
                            item = BillItem(
                                bill_id=bill.id,
                                item_type='service',
                                service_id=service.id,
                                staff_id=staff_member.id,
                                price=service.price,
                                discount=0,
                                quantity=1,
                                total=service.price
                            )
                            subtotal += service.price

                        db.session.add(item)
                        items_created += 1

                    # Calculate totals
                    discount = random.choice([0, 0, 0, 100, 200])
                    tax_amount = (subtotal - discount) * 0.18
                    final_amount = subtotal - discount + tax_amount

                    bill.subtotal = subtotal
                    bill.discount_amount = discount
                    bill.tax_amount = tax_amount
                    bill.final_amount = final_amount

                    bills_created += 1

            db.session.commit()
            print(f"✅ Successfully created {bills_created} bills with {items_created} bill items")
            print(f"✅ All items assigned to {len(staff_list)} staff members")
            print("✅ Staff performance data is now available!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding staff performance data: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    seed_staff_performance_data()

