"""
Script to update bill dates from 2025 to 2026
This will make the dashboard show data for the current year
"""

import sys
import os
from datetime import datetime, timedelta

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

def update_bill_dates():
    """Update all 2025 bills to 2026"""

    try:
        print("\n" + "="*60)
        print("Updating Bill Dates from 2025 to 2026")
        print("="*60)

        # Get all bills from 2025
        bills_2025 = Bill.objects(
            bill_date__gte=datetime(2025, 1, 1),
            bill_date__lte=datetime(2025, 12, 31, 23, 59, 59)
        )

        total_bills = bills_2025.count()
        print(f"\nFound {total_bills} bills from 2025")

        if total_bills == 0:
            print("No bills to update!")
            return

        updated_count = 0

        for bill in bills_2025:
            # Add one year to the bill date
            old_date = bill.bill_date
            new_date = old_date.replace(year=2026)

            # Update the bill
            bill.bill_date = new_date
            bill.save()

            updated_count += 1

            if updated_count % 100 == 0:
                print(f"Updated {updated_count}/{total_bills} bills...")

        print(f"\n[SUCCESS] Updated {updated_count} bills from 2025 to 2026!")

        # Verify the update
        bills_2026 = Bill.objects(
            bill_date__gte=datetime(2026, 1, 1),
            bill_date__lte=datetime(2026, 12, 31, 23, 59, 59)
        ).count()

        print(f"Bills now in 2026: {bills_2026}")

        # Show some sample updated bills
        recent_bills = Bill.objects().order_by('-bill_date').limit(5)
        print("\nSample updated bills:")
        for bill in recent_bills:
            print(f"  - Bill #{bill.bill_number}: {bill.bill_date.strftime('%Y-%m-%d')} - Rs.{bill.final_amount:.2f}")

    except Exception as e:
        print(f"\n[ERROR] Error updating bills: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Bill Date Update Script")
    print("="*60)

    # Ask for confirmation
    confirm = input("\nThis will update ALL 2025 bills to 2026. Continue? (yes/no): ")

    if confirm.lower() == 'yes':
        update_bill_dates()
    else:
        print("Update cancelled.")

    print("\n" + "="*60)
    print("Script completed!")
    print("="*60 + "\n")
