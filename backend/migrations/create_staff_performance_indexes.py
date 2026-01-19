"""
MongoDB Index Creation Script for Staff Performance Optimization

Run this script to create indexes specifically for staff performance queries:
    python backend/migrations/create_staff_performance_indexes.py

These indexes are critical for:
- Staff performance dashboard queries
- Top performer calculations
- Staff leaderboard queries

Performance target: <200ms per query
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING

# MongoDB Configuration (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')


def create_staff_performance_indexes():
    """Create all performance-critical indexes for staff performance queries"""

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    print(f"Connected to database: {MONGODB_DB}")
    print("=" * 60)
    print("Creating Staff Performance Indexes")
    print("=" * 60)

    created = []
    skipped = []

    # ===========================================
    # BILLS COLLECTION - Staff Performance Queries
    # ===========================================
    print("\n[1] Bills Collection - Staff Performance Indexes:")

    # Index for items.staff queries (CRITICAL for staff performance)
    try:
        db.bills.create_index(
            [("items.staff", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_staff_date_deleted",
            background=True,
            sparse=True
        )
        created.append("bills: idx_bills_items_staff_date_deleted")
        print("  + Created: items.staff + bill_date + is_deleted (sparse)")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("bills: idx_bills_items_staff_date_deleted")
            print("  ~ Skipped: items.staff + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Compound index for staff + item_type queries
    try:
        db.bills.create_index(
            [("items.staff", ASCENDING), ("items.item_type", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_staff_type_date_deleted",
            background=True,
            sparse=True
        )
        created.append("bills: idx_bills_items_staff_type_date_deleted")
        print("  + Created: items.staff + items.item_type + bill_date + is_deleted (sparse)")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("bills: idx_bills_items_staff_type_date_deleted")
            print("  ~ Skipped: items.staff + items.item_type + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for customer retention queries (staff + customer)
    try:
        db.bills.create_index(
            [("items.staff", ASCENDING), ("customer", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_staff_customer_date_deleted",
            background=True,
            sparse=True
        )
        created.append("bills: idx_bills_items_staff_customer_date_deleted")
        print("  + Created: items.staff + customer + bill_date + is_deleted (sparse)")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("bills: idx_bills_items_staff_customer_date_deleted")
            print("  ~ Skipped: items.staff + customer + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # FEEDBACKS COLLECTION
    # ===========================================
    print("\n[2] Feedbacks Collection Indexes:")

    # Index for staff feedback queries (CRITICAL for top performer)
    try:
        db.feedbacks.create_index(
            [("staff", ASCENDING), ("created_at", DESCENDING)],
            name="idx_feedbacks_staff_created",
            background=True
        )
        created.append("feedbacks: idx_feedbacks_staff_created")
        print("  + Created: staff + created_at")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("feedbacks: idx_feedbacks_staff_created")
            print("  ~ Skipped: staff + created_at (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # APPOINTMENTS COLLECTION
    # ===========================================
    print("\n[3] Appointments Collection - Staff Performance Indexes:")

    # Index already exists (idx_appointments_staff_date_status) but verify
    # This is for staff performance appointment counts
    try:
        # Check if index exists by trying to create it
        db.appointments.create_index(
            [("staff", ASCENDING), ("appointment_date", ASCENDING), ("status", ASCENDING)],
            name="idx_appointments_staff_date_status_perf",
            background=True
        )
        created.append("appointments: idx_appointments_staff_date_status_perf")
        print("  + Created: staff + appointment_date + status (performance)")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("appointments: idx_appointments_staff_date_status_perf")
            print("  ~ Skipped: staff + appointment_date + status (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # SUMMARY
    # ===========================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created: {len(created)} indexes")
    print(f"Skipped: {len(skipped)} indexes (already exist)")
    
    if created:
        print("\nNew indexes created:")
        for idx in created:
            print(f"  + {idx}")
    
    if skipped:
        print("\nExisting indexes (skipped):")
        for idx in skipped:
            print(f"  ~ {idx}")

    print("\n" + "=" * 60)
    print("Staff performance indexes setup complete!")
    print("=" * 60)
    print("\nNote: Indexes are created in the background.")
    print("Large collections may take a few minutes to index.")
    print("Monitor index creation progress in MongoDB Atlas.")

    client.close()


if __name__ == '__main__':
    try:
        create_staff_performance_indexes()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

