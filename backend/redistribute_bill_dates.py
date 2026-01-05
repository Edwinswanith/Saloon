"""
Script to redistribute bill dates to recent past dates
This ensures dashboard shows data in current time period
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Bill

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

def redistribute_bill_dates():
    """Redistribute bills across the past 90 days"""

    try:
        print("\n" + "="*60)
        print("Redistributing Bill Dates to Past 90 Days")
        print("="*60)

        # Get all bills
        all_bills = list(Bill.objects())
        total_bills = len(all_bills)

        print(f"\nFound {total_bills} bills to redistribute")

        if total_bills == 0:
            print("No bills to update!")
            return

        updated_count = 0
        now = datetime.now()

        # Distribute bills across past 90 days
        for bill in all_bills:
            # Generate a random date in the past 90 days
            days_ago = random.randint(0, 90)
            hours = random.randint(8, 20)  # Business hours
            minutes = random.randint(0, 59)

            new_date = now - timedelta(days=days_ago)
            new_date = new_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)

            # Update the bill
            bill.bill_date = new_date
            bill.save()

            updated_count += 1

            if updated_count % 100 == 0:
                print(f"Updated {updated_count}/{total_bills} bills...")

        print(f"\n[SUCCESS] Redistributed {updated_count} bills across past 90 days!")

        # Verify the update - show bills by time period
        print("\nBills by time period:")

        # Today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_bills = Bill.objects(
            is_deleted=False,
            bill_date__gte=today_start,
            bill_date__lte=now
        ).count()
        print(f"  Today: {today_bills} bills")

        # This week
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_bills = Bill.objects(
            is_deleted=False,
            bill_date__gte=week_start,
            bill_date__lte=now
        ).count()
        print(f"  This week: {week_bills} bills")

        # This month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_bills = Bill.objects(
            is_deleted=False,
            bill_date__gte=month_start,
            bill_date__lte=now
        ).count()
        print(f"  This month: {month_bills} bills")

        # This year
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        year_bills = Bill.objects(
            is_deleted=False,
            bill_date__gte=year_start,
            bill_date__lte=now
        ).count()
        print(f"  This year: {year_bills} bills")

        # Calculate revenue
        bills = Bill.objects(is_deleted=False, bill_date__gte=month_start, bill_date__lte=now)
        total_revenue = sum([float(b.final_amount) for b in bills])
        print(f"\nRevenue this month: Rs.{total_revenue:,.2f}")

        # Show some sample bills
        recent_bills = Bill.objects().order_by('-bill_date').limit(5)
        print("\nRecent bills:")
        for bill in recent_bills:
            print(f"  - Bill #{bill.bill_number}: {bill.bill_date.strftime('%Y-%m-%d %H:%M')} - Rs.{bill.final_amount:.2f}")

    except Exception as e:
        print(f"\n[ERROR] Error redistributing bills: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Bill Date Redistribution Script")
    print("="*60)

    # Ask for confirmation
    confirm = input("\nThis will redistribute ALL bills to past 90 days. Continue? (yes/no): ")

    if confirm.lower() == 'yes':
        redistribute_bill_dates()
    else:
        print("Update cancelled.")

    print("\n" + "="*60)
    print("Script completed!")
    print("="*60 + "\n")
