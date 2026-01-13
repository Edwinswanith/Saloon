"""
MongoDB Index Creation Script for Saloon Performance Optimization

Run this script once to create all necessary indexes:
    python backend/migrations/create_indexes.py

These indexes are critical for query performance on:
- Bills (most queried collection)
- Customers (18k+ documents, heavy search)
- Appointments (calendar queries)
- Staff attendance
- Expenses
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT

# MongoDB Configuration (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon_prod'  # Use 'Saloon' for development


def create_indexes():
    """Create all performance-critical indexes"""

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    print(f"Connected to database: {MONGODB_DB}")
    print("-" * 50)

    # Track created indexes
    created = []
    skipped = []

    # ===========================================
    # 1. BILLS COLLECTION - MOST CRITICAL
    # ===========================================
    print("\n[1] Bills Collection Indexes:")

    # Index for dashboard queries: branch + date range + deleted status
    try:
        db.bills.create_index(
            [("branch", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_branch_date_deleted",
            background=True
        )
        created.append("bills: idx_bills_branch_date_deleted")
        print("  + Created: branch + bill_date + is_deleted")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("bills: idx_bills_branch_date_deleted")
            print("  ~ Skipped: branch + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for customer bill history
    try:
        db.bills.create_index(
            [("customer", ASCENDING), ("bill_date", DESCENDING)],
            name="idx_bills_customer_date",
            background=True
        )
        created.append("bills: idx_bills_customer_date")
        print("  + Created: customer + bill_date")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("bills: idx_bills_customer_date")
            print("  ~ Skipped: customer + bill_date (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for status-based queries
    try:
        db.bills.create_index(
            [("branch", ASCENDING), ("booking_status", ASCENDING), ("bill_date", DESCENDING)],
            name="idx_bills_branch_status_date",
            background=True
        )
        created.append("bills: idx_bills_branch_status_date")
        print("  + Created: branch + booking_status + bill_date")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("bills: idx_bills_branch_status_date")
            print("  ~ Skipped: branch + booking_status + bill_date (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for bill_number lookup (unique)
    try:
        db.bills.create_index(
            [("bill_number", ASCENDING)],
            name="idx_bills_bill_number",
            unique=True,
            background=True
        )
        created.append("bills: idx_bills_bill_number")
        print("  + Created: bill_number (unique)")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("bills: idx_bills_bill_number")
            print("  ~ Skipped: bill_number (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for payment distribution queries
    try:
        db.bills.create_index(
            [("branch", ASCENDING), ("payment_mode", ASCENDING), ("bill_date", DESCENDING)],
            name="idx_bills_branch_payment_date",
            background=True
        )
        created.append("bills: idx_bills_branch_payment_date")
        print("  + Created: branch + payment_mode + bill_date")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("bills: idx_bills_branch_payment_date")
            print("  ~ Skipped: branch + payment_mode + bill_date (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # 2. CUSTOMERS COLLECTION
    # ===========================================
    print("\n[2] Customers Collection Indexes:")

    # Index for branch + created_at (customer list sorting)
    try:
        db.customers.create_index(
            [("branch", ASCENDING), ("created_at", DESCENDING)],
            name="idx_customers_branch_created",
            background=True
        )
        created.append("customers: idx_customers_branch_created")
        print("  + Created: branch + created_at")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("customers: idx_customers_branch_created")
            print("  ~ Skipped: branch + created_at (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for branch + mobile (duplicate check)
    try:
        db.customers.create_index(
            [("branch", ASCENDING), ("mobile", ASCENDING)],
            name="idx_customers_branch_mobile",
            background=True
        )
        created.append("customers: idx_customers_branch_mobile")
        print("  + Created: branch + mobile")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("customers: idx_customers_branch_mobile")
            print("  ~ Skipped: branch + mobile (exists)")
        else:
            print(f"  ! Error: {e}")

    # Text index for search (mobile, first_name, last_name)
    try:
        db.customers.create_index(
            [("mobile", TEXT), ("first_name", TEXT), ("last_name", TEXT)],
            name="idx_customers_text_search",
            background=True
        )
        created.append("customers: idx_customers_text_search")
        print("  + Created: TEXT index on mobile, first_name, last_name")
    except Exception as e:
        if "already exists" in str(e) or "text index" in str(e).lower():
            skipped.append("customers: idx_customers_text_search")
            print("  ~ Skipped: TEXT index (exists or conflict)")
        else:
            print(f"  ! Error: {e}")

    # Index for referral_code lookup (sparse)
    try:
        db.customers.create_index(
            [("referral_code", ASCENDING)],
            name="idx_customers_referral_code",
            sparse=True,
            background=True
        )
        created.append("customers: idx_customers_referral_code")
        print("  + Created: referral_code (sparse)")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("customers: idx_customers_referral_code")
            print("  ~ Skipped: referral_code (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # 3. APPOINTMENTS COLLECTION
    # ===========================================
    print("\n[3] Appointments Collection Indexes:")

    # Index for calendar view (branch + date + status)
    try:
        db.appointments.create_index(
            [("branch", ASCENDING), ("appointment_date", ASCENDING), ("status", ASCENDING)],
            name="idx_appointments_branch_date_status",
            background=True
        )
        created.append("appointments: idx_appointments_branch_date_status")
        print("  + Created: branch + appointment_date + status")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("appointments: idx_appointments_branch_date_status")
            print("  ~ Skipped: branch + appointment_date + status (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for staff schedule
    try:
        db.appointments.create_index(
            [("staff", ASCENDING), ("appointment_date", ASCENDING), ("status", ASCENDING)],
            name="idx_appointments_staff_date_status",
            background=True
        )
        created.append("appointments: idx_appointments_staff_date_status")
        print("  + Created: staff + appointment_date + status")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("appointments: idx_appointments_staff_date_status")
            print("  ~ Skipped: staff + appointment_date + status (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for customer appointments
    try:
        db.appointments.create_index(
            [("customer", ASCENDING), ("appointment_date", DESCENDING)],
            name="idx_appointments_customer_date",
            background=True
        )
        created.append("appointments: idx_appointments_customer_date")
        print("  + Created: customer + appointment_date")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("appointments: idx_appointments_customer_date")
            print("  ~ Skipped: customer + appointment_date (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # 4. STAFF ATTENDANCE COLLECTION
    # ===========================================
    print("\n[4] Staff Attendance Collection Indexes:")

    try:
        db.staff_attendance.create_index(
            [("staff", ASCENDING), ("attendance_date", DESCENDING)],
            name="idx_attendance_staff_date",
            background=True
        )
        created.append("staff_attendance: idx_attendance_staff_date")
        print("  + Created: staff + attendance_date")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("staff_attendance: idx_attendance_staff_date")
            print("  ~ Skipped: staff + attendance_date (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # 5. EXPENSES COLLECTION
    # ===========================================
    print("\n[5] Expenses Collection Indexes:")

    try:
        db.expenses.create_index(
            [("branch", ASCENDING), ("expense_date", DESCENDING)],
            name="idx_expenses_branch_date",
            background=True
        )
        created.append("expenses: idx_expenses_branch_date")
        print("  + Created: branch + expense_date")
    except Exception as e:
        if "already exists" in str(e):
            skipped.append("expenses: idx_expenses_branch_date")
            print("  ~ Skipped: branch + expense_date (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # SUMMARY
    # ===========================================
    print("\n" + "=" * 50)
    print("INDEX CREATION SUMMARY")
    print("=" * 50)
    print(f"Created: {len(created)}")
    for idx in created:
        print(f"  + {idx}")
    print(f"\nSkipped (already exist): {len(skipped)}")
    for idx in skipped:
        print(f"  ~ {idx}")

    # Close connection
    client.close()
    print("\nDone! Connection closed.")

    return len(created), len(skipped)


if __name__ == "__main__":
    print("=" * 50)
    print("SALOON MONGODB INDEX CREATION")
    print("=" * 50)

    # Confirm before running
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        create_indexes()
    else:
        print(f"\nTarget database: {MONGODB_DB}")
        print("\nThis will create performance indexes on:")
        print("  - bills (3 indexes)")
        print("  - customers (3 indexes)")
        print("  - appointments (2 indexes)")
        print("  - staff_attendance (1 index)")
        print("  - expenses (1 index)")
        print("\nRun with --yes to execute, or press Enter to continue...")

        try:
            input()
            create_indexes()
        except KeyboardInterrupt:
            print("\nCancelled.")
