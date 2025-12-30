"""
Populate sample Missed Enquiries data for testing
"""
import os
import sys
from datetime import datetime, timedelta
import random
from mongoengine import connect

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import MissedEnquiry, Branch, Staff

# MongoDB connection
MONGO_URI = 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon'

def populate_missed_enquiries():
    """Populate missed enquiries data for all branches"""
    
    # Connect to MongoDB
    connect(host=MONGO_URI, db='Saloon')
    print("Connected to MongoDB")
    
    # Get all branches
    branches = list(Branch.objects())
    if not branches:
        print("No branches found. Please create branches first.")
        return
    
    print(f"Found {len(branches)} branches")
    
    # Sample data
    first_names = [
        "Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Karthik", "Divya",
        "Rahul", "Meera", "Sanjay", "Kavya", "Arun", "Nisha", "Suresh", "Pooja",
        "Ravi", "Lakshmi", "Mohan", "Deepa", "Kumar", "Swathi", "Ganesh", "Rani"
    ]
    
    last_names = [
        "Kumar", "Sharma", "Patel", "Reddy", "Nair", "Singh", "Rao", "Menon",
        "Verma", "Desai", "Iyer", "Gupta", "Mehta", "Joshi", "Pillai", "Krishnan"
    ]
    
    services = [
        "Haircut", "Hair Color", "Hair Spa", "Facial", "Manicure", "Pedicure",
        "Bridal Makeup", "Party Makeup", "Hair Straightening", "Hair Curling",
        "Beard Trimming", "Threading", "Waxing", "Massage", "Hair Treatment"
    ]
    
    reasons = [
        "Price too high",
        "Preferred time slot not available",
        "Changed mind",
        "Went to competitor",
        "Staff not available",
        "Wanted specific stylist who was busy",
        "Emergency came up",
        "Will book later",
        "Did not like the ambiance",
        "Waiting time too long",
        "Service not available at this branch",
        "Budget constraints"
    ]
    
    enquiry_types = ['call', 'walk-in', 'whatsapp', 'other']
    enquiry_weights = [0.60, 0.20, 0.15, 0.05]  # 60% call, 20% walk-in, 15% whatsapp, 5% other
    
    statuses = ['open', 'converted', 'lost']
    status_weights = [0.50, 0.30, 0.20]  # 50% open, 30% converted, 20% lost
    
    total_created = 0
    
    # Create enquiries for each branch
    for branch in branches:
        print(f"\nPopulating data for branch: {branch.name}")
        
        # Get staff for this branch
        staff_members = list(Staff.objects(branch=branch))
        
        # Create 25 enquiries per branch
        for i in range(25):
            # Generate random customer name and phone
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            customer_name = f"{first_name} {last_name}"
            customer_phone = f"9{random.randint(100000000, 999999999)}"
            
            # Random enquiry type
            enquiry_type = random.choices(enquiry_types, weights=enquiry_weights)[0]
            
            # Random requested service
            requested_service = random.choice(services)
            
            # Random status
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Random reason
            reason = random.choice(reasons) if status in ['lost', 'open'] else None
            
            # Random follow-up date (spread across past, present, future)
            days_offset = random.randint(-30, 30)  # -30 to +30 days from today
            follow_up_date = (datetime.utcnow() + timedelta(days=days_offset)).date()
            
            # Only set follow-up for open enquiries
            if status != 'open':
                follow_up_date = None
            
            # Random notes
            notes_options = [
                "Customer seemed interested",
                "Will call back later",
                "Needs to check schedule",
                "Price sensitive customer",
                "Regular customer referral",
                "First time enquiry",
                None,
                None,  # More likely to have no notes
                None
            ]
            notes = random.choice(notes_options)
            
            # Random created date (within last 60 days)
            created_days_ago = random.randint(0, 60)
            created_at = datetime.utcnow() - timedelta(days=created_days_ago)
            
            # Create enquiry
            enquiry = MissedEnquiry(
                customer_name=customer_name,
                customer_phone=customer_phone,
                branch=branch,
                enquiry_type=enquiry_type,
                requested_service=requested_service,
                reason_not_delivered=reason,
                follow_up_date=follow_up_date,
                status=status,
                notes=notes,
                created_at=created_at,
                updated_at=created_at
            )
            
            # Assign created_by if staff available
            if staff_members:
                enquiry.created_by = random.choice(staff_members)
            
            enquiry.save()
            total_created += 1
        
        print(f"Created 25 missed enquiries for {branch.name}")
    
    print(f"\n=== SUCCESS ===")
    print(f"Total missed enquiries created: {total_created}")
    print(f"Enquiries per branch: 25")
    print(f"\nData distribution:")
    print(f"- Call: ~60%")
    print(f"- Walk-in: ~20%")
    print(f"- WhatsApp: ~15%")
    print(f"- Other: ~5%")
    print(f"\nStatus distribution:")
    print(f"- Open: ~50%")
    print(f"- Converted: ~30%")
    print(f"- Lost: ~20%")
    print(f"\nFollow-up dates spread across -30 to +30 days from today")
    
if __name__ == '__main__':
    populate_missed_enquiries()

