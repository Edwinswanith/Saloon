from mongoengine import connect
from models import Branch, Staff, Customer, Service, ServiceGroup, Bill, BillItemEmbedded, Appointment, Feedback
from datetime import datetime, timedelta
import random
import os

# Connect to MongoDB
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
connect(host=MONGODB_URI, db='Saloon')

def generate_sample_data():
    print("Starting sample data generation...")
    
    # 1. Fetch existing data
    branches = list(Branch.objects())
    staff_list = list(Staff.objects(status='active'))
    
    print(f"Found {len(branches)} branches and {len(staff_list)} staff")
    
    if len(staff_list) == 0:
        print("ERROR: No staff found! Please create staff members first.")
        return
    
    # 2. Create or get services
    service_group = ServiceGroup.objects.first()
    if not service_group:
        service_group = ServiceGroup(name="General Services").save()
        print("Created service group: General Services")
    
    services = []
    service_names = [
        ("Haircut", 500),
        ("Hair Coloring", 2500),
        ("Facial", 1500),
        ("Manicure", 800),
        ("Pedicure", 900),
        ("Hair Spa", 2000),
        ("Blow Dry", 600),
        ("Keratin Treatment", 5000)
    ]
    
    for name, price in service_names:
        service = Service.objects(name=name).first()
        if not service:
            service = Service(
                name=name,
                group=service_group,
                price=price,
                duration=60
            ).save()
        services.append(service)
    
    print(f"Created/found {len(services)} services")
    
    # 3. Create sample customers
    customers = []
    for i in range(1, 51):
        mobile = f"90000000{i:02d}"
        customer = Customer.objects(mobile=mobile).first()
        if not customer:
            customer = Customer(
                mobile=mobile,
                first_name=f"Customer{i}",
                last_name=f"Test{i}",
                gender="Female" if i % 2 == 0 else "Male",
                source="Walk-in"
            ).save()
        customers.append(customer)
    
    print(f"Created {len(customers)} customers")
    
    # 4. Generate varied performance data for each staff
    performance_multipliers = [1.5, 1.3, 1.2, 1.0, 0.9, 0.7, 0.5]  # Top to bottom
    
    # Ensure we have enough multipliers for all staff
    while len(performance_multipliers) < len(staff_list):
        performance_multipliers.append(0.5)
    
    random.shuffle(performance_multipliers)
    
    date_range_start = datetime.now() - timedelta(days=30)
    date_range_end = datetime.now()
    
    total_bills_created = 0
    total_appointments_created = 0
    total_feedback_created = 0
    
    for idx, staff in enumerate(staff_list):
        multiplier = performance_multipliers[idx]
        branch = staff.branch
        
        print(f"\nProcessing staff: {staff.first_name} {staff.last_name} (multiplier: {multiplier})")
        
        # Bills for this staff (8-20 bills)
        num_bills = int(random.randint(8, 20) * multiplier)
        
        for bill_num in range(num_bills):
            # Random customer
            customer = random.choice(customers)
            
            # Random date in last 30 days
            random_days = random.randint(0, 29)
            bill_date = date_range_start + timedelta(days=random_days)
            
            # Random services (1-3)
            num_services = random.randint(1, 3)
            selected_services = random.sample(services, min(num_services, len(services)))
            
            # Create bill items
            items = []
            subtotal = 0
            for service in selected_services:
                quantity = 1
                price = service.price
                total = price * quantity
                subtotal += total
                
                item = BillItemEmbedded(
                    item_type='service',
                    service=service,
                    staff=staff,
                    price=price,
                    quantity=quantity,
                    total=total,
                    discount=0.0
                )
                items.append(item)
            
            # Create bill with unique bill number
            timestamp = int(datetime.now().timestamp() * 1000)
            bill_number = f"BILL-{timestamp}-{random.randint(1000, 9999)}"
            
            tax_rate = 18.0
            tax_amount = subtotal * (tax_rate / 100)
            final_amount = subtotal + tax_amount
            
            try:
                Bill(
                    bill_number=bill_number,
                    customer=customer,
                    branch=branch,
                    bill_date=bill_date,
                    subtotal=subtotal,
                    tax_rate=tax_rate,
                    tax_amount=tax_amount,
                    final_amount=final_amount,
                    payment_mode=random.choice(['cash', 'upi', 'card']),
                    booking_status='service-completed',
                    items=items
                ).save()
                total_bills_created += 1
            except Exception as e:
                print(f"  Warning: Could not create bill {bill_number}: {e}")
        
        print(f"  Created {num_bills} bills")
        
        # 5. Appointments (10-30 completed)
        num_appointments = int(random.randint(10, 30) * multiplier)
        
        for _ in range(num_appointments):
            customer = random.choice(customers)
            service = random.choice(services)
            random_days = random.randint(0, 29)
            appt_date = (date_range_start + timedelta(days=random_days)).date()
            
            try:
                Appointment(
                    customer=customer,
                    staff=staff,
                    branch=branch,
                    service=service,
                    appointment_date=appt_date,
                    start_time="10:00:00",
                    end_time="11:00:00",
                    status='completed'
                ).save()
                total_appointments_created += 1
            except Exception as e:
                print(f"  Warning: Could not create appointment: {e}")
        
        print(f"  Created {num_appointments} appointments")
        
        # 6. Feedback (5-15 with ratings)
        num_feedback = int(random.randint(5, 15) * multiplier)
        
        for _ in range(num_feedback):
            customer = random.choice(customers)
            random_days = random.randint(0, 29)
            feedback_date = date_range_start + timedelta(days=random_days)
            
            # Vary ratings: top performers get 4-5, others 3-5
            if multiplier >= 1.2:
                rating = random.randint(4, 5)
            else:
                rating = random.randint(3, 5)
            
            try:
                Feedback(
                    customer=customer,
                    staff=staff,
                    branch=branch,
                    rating=rating,
                    comment=f"Great service by {staff.first_name}!",
                    created_at=feedback_date
                ).save()
                total_feedback_created += 1
            except Exception as e:
                print(f"  Warning: Could not create feedback: {e}")
        
        print(f"  Created {num_feedback} feedback entries")
    
    print("\n" + "="*60)
    print("Sample data generation complete!")
    print("="*60)
    print(f"\nTotal created:")
    print(f"  - Bills: {total_bills_created}")
    print(f"  - Appointments: {total_appointments_created}")
    print(f"  - Feedback: {total_feedback_created}")
    print(f"  - Customers: {len(customers)}")
    print(f"  - Services: {len(services)}")
    print("\nExpected results:")
    print("  - Top performer will have highest revenue, services, and ratings")
    print("  - Other staff will have varied performance")
    print("  - All data is in the last 30 days")
    print("\nNext steps:")
    print("  1. Restart the backend server")
    print("  2. Hard refresh your browser (Ctrl+Shift+R)")
    print("  3. View the Dashboard to see performance metrics")

if __name__ == "__main__":
    generate_sample_data()

