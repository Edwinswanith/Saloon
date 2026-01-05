"""
Script to redistribute MongoDB data: 50% to 2025, 50% to 2026
This ensures proper distribution across both years for testing and analysis
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import (
    Bill, Expense, Appointment, Customer, Lead, Feedback,
    StaffAttendance, CashTransaction, PrepaidPackage, MembershipPlan,
    Order, Asset
)

# Connect to MongoDB
try:
    connect(
        db='Saloon',
        host='mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon',
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit(1)


def redistribute_bills():
    """Redistribute bills: 50% to 2025, 50% to 2026"""
    try:
        print("\n" + "="*60)
        print("Redistributing Bills: 50% to 2025, 50% to 2026")
        print("="*60)
        
        all_bills = list(Bill.objects(is_deleted=False))
        total_bills = len(all_bills)
        
        if total_bills == 0:
            print("No bills to redistribute!")
            return
        
        print(f"\nFound {total_bills} bills to redistribute")
        
        # Shuffle bills randomly
        random.shuffle(all_bills)
        
        # Split 50/50
        midpoint = total_bills // 2
        bills_2025 = all_bills[:midpoint]
        bills_2026 = all_bills[midpoint:]
        
        updated_2025 = 0
        updated_2026 = 0
        
        # Update bills to 2025 (distribute across all months)
        for bill in bills_2025:
            # Random month in 2025
            month = random.randint(1, 12)
            # Random day in that month
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = random.randint(1, 31)
            elif month in [4, 6, 9, 11]:
                day = random.randint(1, 30)
            else:  # February
                day = random.randint(1, 28)
            
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            
            new_date = datetime(2025, month, day, hour, minute, 0)
            bill.bill_date = new_date
            bill.save()
            updated_2025 += 1
            
            if updated_2025 % 50 == 0:
                print(f"Updated {updated_2025}/{len(bills_2025)} bills to 2025...")
        
        # Update bills to 2026 (distribute across all months up to current)
        current_month = datetime.now().month
        for bill in bills_2026:
            # Random month in 2026 (up to current month)
            month = random.randint(1, current_month)
            # Random day in that month
            if month in [1, 3, 5, 7, 8, 10, 12]:
                max_day = 31
            elif month in [4, 6, 9, 11]:
                max_day = 30
            else:  # February
                max_day = 29  # 2026 is a leap year
            
            # If current month, don't go beyond today
            if month == current_month:
                max_day = min(max_day, datetime.now().day)
            
            day = random.randint(1, max_day)
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            
            new_date = datetime(2026, month, day, hour, minute, 0)
            bill.bill_date = new_date
            bill.save()
            updated_2026 += 1
            
            if updated_2026 % 50 == 0:
                print(f"Updated {updated_2026}/{len(bills_2026)} bills to 2026...")
        
        print(f"\n[SUCCESS] Redistributed {updated_2025} bills to 2025 and {updated_2026} bills to 2026!")
        
        # Verify distribution
        bills_2025_count = Bill.objects(
            bill_date__gte=datetime(2025, 1, 1),
            bill_date__lte=datetime(2025, 12, 31, 23, 59, 59),
            is_deleted=False
        ).count()
        
        bills_2026_count = Bill.objects(
            bill_date__gte=datetime(2026, 1, 1),
            bill_date__lte=datetime(2026, 12, 31, 23, 59, 59),
            is_deleted=False
        ).count()
        
        print(f"\nVerification:")
        print(f"  Bills in 2025: {bills_2025_count}")
        print(f"  Bills in 2026: {bills_2026_count}")
        print(f"  Total: {bills_2025_count + bills_2026_count}")
        
    except Exception as e:
        print(f"\n[ERROR] Error redistributing bills: {str(e)}")
        import traceback
        traceback.print_exc()


def redistribute_expenses():
    """Redistribute expenses: 50% to 2025, 50% to 2026"""
    try:
        print("\n" + "="*60)
        print("Redistributing Expenses: 50% to 2025, 50% to 2026")
        print("="*60)
        
        all_expenses = list(Expense.objects())
        total_expenses = len(all_expenses)
        
        if total_expenses == 0:
            print("No expenses to redistribute!")
            return
        
        print(f"\nFound {total_expenses} expenses to redistribute")
        
        random.shuffle(all_expenses)
        midpoint = total_expenses // 2
        expenses_2025 = all_expenses[:midpoint]
        expenses_2026 = all_expenses[midpoint:]
        
        updated_2025 = 0
        updated_2026 = 0
        
        # Update expenses to 2025
        for expense in expenses_2025:
            month = random.randint(1, 12)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = random.randint(1, 31)
            elif month in [4, 6, 9, 11]:
                day = random.randint(1, 30)
            else:
                day = random.randint(1, 28)
            
            new_date = datetime(2025, month, day).date()
            expense.expense_date = new_date
            expense.save()
            updated_2025 += 1
        
        # Update expenses to 2026
        current_month = datetime.now().month
        for expense in expenses_2026:
            month = random.randint(1, current_month)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                max_day = 31
            elif month in [4, 6, 9, 11]:
                max_day = 30
            else:
                max_day = 29
            
            if month == current_month:
                max_day = min(max_day, datetime.now().day)
            
            day = random.randint(1, max_day)
            new_date = datetime(2026, month, day).date()
            expense.expense_date = new_date
            expense.save()
            updated_2026 += 1
        
        print(f"\n[SUCCESS] Redistributed {updated_2025} expenses to 2025 and {updated_2026} expenses to 2026!")
        
    except Exception as e:
        print(f"\n[ERROR] Error redistributing expenses: {str(e)}")
        import traceback
        traceback.print_exc()


def redistribute_appointments():
    """Redistribute appointments: 50% to 2025, 50% to 2026"""
    try:
        print("\n" + "="*60)
        print("Redistributing Appointments: 50% to 2025, 50% to 2026")
        print("="*60)
        
        all_appointments = list(Appointment.objects())
        total_appointments = len(all_appointments)
        
        if total_appointments == 0:
            print("No appointments to redistribute!")
            return
        
        print(f"\nFound {total_appointments} appointments to redistribute")
        
        random.shuffle(all_appointments)
        midpoint = total_appointments // 2
        appointments_2025 = all_appointments[:midpoint]
        appointments_2026 = all_appointments[midpoint:]
        
        updated_2025 = 0
        updated_2026 = 0
        
        # Update appointments to 2025
        for appointment in appointments_2025:
            month = random.randint(1, 12)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = random.randint(1, 31)
            elif month in [4, 6, 9, 11]:
                day = random.randint(1, 30)
            else:
                day = random.randint(1, 28)
            
            new_date = datetime(2025, month, day).date()
            appointment.appointment_date = new_date
            appointment.save()
            updated_2025 += 1
        
        # Update appointments to 2026
        current_month = datetime.now().month
        for appointment in appointments_2026:
            month = random.randint(1, current_month)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                max_day = 31
            elif month in [4, 6, 9, 11]:
                max_day = 30
            else:
                max_day = 29
            
            if month == current_month:
                max_day = min(max_day, datetime.now().day)
            
            day = random.randint(1, max_day)
            new_date = datetime(2026, month, day).date()
            appointment.appointment_date = new_date
            appointment.save()
            updated_2026 += 1
        
        print(f"\n[SUCCESS] Redistributed {updated_2025} appointments to 2025 and {updated_2026} appointments to 2026!")
        
    except Exception as e:
        print(f"\n[ERROR] Error redistributing appointments: {str(e)}")
        import traceback
        traceback.print_exc()


def redistribute_customers():
    """Redistribute customer created_at: 50% to 2025, 50% to 2026"""
    try:
        print("\n" + "="*60)
        print("Redistributing Customers: 50% to 2025, 50% to 2026")
        print("="*60)
        
        all_customers = list(Customer.objects())
        total_customers = len(all_customers)
        
        if total_customers == 0:
            print("No customers to redistribute!")
            return
        
        print(f"\nFound {total_customers} customers to redistribute")
        
        random.shuffle(all_customers)
        midpoint = total_customers // 2
        customers_2025 = all_customers[:midpoint]
        customers_2026 = all_customers[midpoint:]
        
        updated_2025 = 0
        updated_2026 = 0
        
        # Update customers to 2025
        for customer in customers_2025:
            month = random.randint(1, 12)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = random.randint(1, 31)
            elif month in [4, 6, 9, 11]:
                day = random.randint(1, 30)
            else:
                day = random.randint(1, 28)
            
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            new_date = datetime(2025, month, day, hour, minute, 0)
            customer.created_at = new_date
            customer.updated_at = new_date
            customer.save()
            updated_2025 += 1
        
        # Update customers to 2026
        current_month = datetime.now().month
        for customer in customers_2026:
            month = random.randint(1, current_month)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                max_day = 31
            elif month in [4, 6, 9, 11]:
                max_day = 30
            else:
                max_day = 29
            
            if month == current_month:
                max_day = min(max_day, datetime.now().day)
            
            day = random.randint(1, max_day)
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            new_date = datetime(2026, month, day, hour, minute, 0)
            customer.created_at = new_date
            customer.updated_at = new_date
            customer.save()
            updated_2026 += 1
        
        print(f"\n[SUCCESS] Redistributed {updated_2025} customers to 2025 and {updated_2026} customers to 2026!")
        
    except Exception as e:
        print(f"\n[ERROR] Error redistributing customers: {str(e)}")
        import traceback
        traceback.print_exc()


def redistribute_leads():
    """Redistribute leads: 50% to 2025, 50% to 2026"""
    try:
        print("\n" + "="*60)
        print("Redistributing Leads: 50% to 2025, 50% to 2026")
        print("="*60)
        
        all_leads = list(Lead.objects())
        total_leads = len(all_leads)
        
        if total_leads == 0:
            print("No leads to redistribute!")
            return
        
        print(f"\nFound {total_leads} leads to redistribute")
        
        random.shuffle(all_leads)
        midpoint = total_leads // 2
        leads_2025 = all_leads[:midpoint]
        leads_2026 = all_leads[midpoint:]
        
        updated_2025 = 0
        updated_2026 = 0
        
        # Update leads to 2025
        for lead in leads_2025:
            month = random.randint(1, 12)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = random.randint(1, 31)
            elif month in [4, 6, 9, 11]:
                day = random.randint(1, 30)
            else:
                day = random.randint(1, 28)
            
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            new_date = datetime(2025, month, day, hour, minute, 0)
            lead.created_at = new_date
            lead.updated_at = new_date
            if lead.follow_up_date:
                follow_up_month = min(12, month + 1)
                follow_up_day = min(28, day)
                lead.follow_up_date = datetime(2025, follow_up_month, follow_up_day, hour, minute, 0)
            lead.save()
            updated_2025 += 1
        
        # Update leads to 2026
        current_month = datetime.now().month
        for lead in leads_2026:
            month = random.randint(1, current_month)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                max_day = 31
            elif month in [4, 6, 9, 11]:
                max_day = 30
            else:
                max_day = 29
            
            if month == current_month:
                max_day = min(max_day, datetime.now().day)
            
            day = random.randint(1, max_day)
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            new_date = datetime(2026, month, day, hour, minute, 0)
            lead.created_at = new_date
            lead.updated_at = new_date
            if lead.follow_up_date:
                follow_up_month = min(current_month, month + 1)
                follow_up_day = min(max_day, day)
                lead.follow_up_date = datetime(2026, follow_up_month, follow_up_day, hour, minute, 0)
            lead.save()
            updated_2026 += 1
        
        print(f"\n[SUCCESS] Redistributed {updated_2025} leads to 2025 and {updated_2026} leads to 2026!")
        
    except Exception as e:
        print(f"\n[ERROR] Error redistributing leads: {str(e)}")
        import traceback
        traceback.print_exc()


def redistribute_feedback():
    """Redistribute feedback: 50% to 2025, 50% to 2026"""
    try:
        print("\n" + "="*60)
        print("Redistributing Feedback: 50% to 2025, 50% to 2026")
        print("="*60)
        
        all_feedback = list(Feedback.objects())
        total_feedback = len(all_feedback)
        
        if total_feedback == 0:
            print("No feedback to redistribute!")
            return
        
        print(f"\nFound {total_feedback} feedback records to redistribute")
        
        random.shuffle(all_feedback)
        midpoint = total_feedback // 2
        feedback_2025 = all_feedback[:midpoint]
        feedback_2026 = all_feedback[midpoint:]
        
        updated_2025 = 0
        updated_2026 = 0
        
        # Update feedback to 2025
        for feedback in feedback_2025:
            month = random.randint(1, 12)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = random.randint(1, 31)
            elif month in [4, 6, 9, 11]:
                day = random.randint(1, 30)
            else:
                day = random.randint(1, 28)
            
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            new_date = datetime(2025, month, day, hour, minute, 0)
            feedback.created_at = new_date
            feedback.save()
            updated_2025 += 1
        
        # Update feedback to 2026
        current_month = datetime.now().month
        for feedback in feedback_2026:
            month = random.randint(1, current_month)
            if month in [1, 3, 5, 7, 8, 10, 12]:
                max_day = 31
            elif month in [4, 6, 9, 11]:
                max_day = 30
            else:
                max_day = 29
            
            if month == current_month:
                max_day = min(max_day, datetime.now().day)
            
            day = random.randint(1, max_day)
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            new_date = datetime(2026, month, day, hour, minute, 0)
            feedback.created_at = new_date
            feedback.save()
            updated_2026 += 1
        
        print(f"\n[SUCCESS] Redistributed {updated_2025} feedback to 2025 and {updated_2026} feedback to 2026!")
        
    except Exception as e:
        print(f"\n[ERROR] Error redistributing feedback: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to redistribute all data"""
    print("\n" + "="*60)
    print("MongoDB Data Redistribution: 50% to 2025, 50% to 2026")
    print("="*60)
    print("\nThis script will redistribute data across 2025 and 2026.")
    print("Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        import time
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        return
    
    # Redistribute all data types
    redistribute_bills()
    redistribute_expenses()
    redistribute_appointments()
    redistribute_customers()
    redistribute_leads()
    redistribute_feedback()
    
    print("\n" + "="*60)
    print("Data Redistribution Complete!")
    print("="*60)
    print("\nSummary:")
    print("  - Bills: 50% in 2025, 50% in 2026")
    print("  - Expenses: 50% in 2025, 50% in 2026")
    print("  - Appointments: 50% in 2025, 50% in 2026")
    print("  - Customers: 50% in 2025, 50% in 2026")
    print("  - Leads: 50% in 2025, 50% in 2026")
    print("  - Feedback: 50% in 2025, 50% in 2026")
    print("\nYou can now test date-based analysis with data from both years.")


if __name__ == '__main__':
    main()

