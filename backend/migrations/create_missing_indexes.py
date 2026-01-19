"""
MongoDB Index Creation Script for Missing Performance Indexes

Run this script to create indexes for:
- Bills items (service, package, product) queries
- Customer history queries
- Memberships and prepaid packages queries

Run: python backend/migrations/create_missing_indexes.py
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING

# MongoDB Configuration (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')


def create_missing_indexes():
    """Create all missing performance-critical indexes"""

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    print(f"Connected to database: {MONGODB_DB}")
    print("=" * 60)
    print("Creating Missing Performance Indexes")
    print("=" * 60)

    created = []
    skipped = []

    # ===========================================
    # BILLS COLLECTION - Items Queries
    # ===========================================
    print("\n[1] Bills Collection - Items Indexes:")

    # Index for items.service queries (top-moving-items)
    try:
        db.bills.create_index(
            [("items.service", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_service_date",
            sparse=True,
            background=True
        )
        created.append("bills: idx_bills_items_service_date")
        print("  + Created: items.service + bill_date + is_deleted")
    except Exception as e:
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            skipped.append("bills: idx_bills_items_service_date")
            print("  ~ Skipped: items.service + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for items.package queries
    try:
        db.bills.create_index(
            [("items.package", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_package_date",
            sparse=True,
            background=True
        )
        created.append("bills: idx_bills_items_package_date")
        print("  + Created: items.package + bill_date + is_deleted")
    except Exception as e:
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            skipped.append("bills: idx_bills_items_package_date")
            print("  ~ Skipped: items.package + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for items.product queries
    try:
        db.bills.create_index(
            [("items.product", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_product_date",
            sparse=True,
            background=True
        )
        created.append("bills: idx_bills_items_product_date")
        print("  + Created: items.product + bill_date + is_deleted")
    except Exception as e:
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            skipped.append("bills: idx_bills_items_product_date")
            print("  ~ Skipped: items.product + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for customer history queries
    try:
        db.bills.create_index(
            [("customer", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_customer_date_deleted",
            background=True
        )
        created.append("bills: idx_bills_customer_date_deleted")
        print("  + Created: customer + bill_date + is_deleted")
    except Exception as e:
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            skipped.append("bills: idx_bills_customer_date_deleted")
            print("  ~ Skipped: customer + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # MEMBERSHIPS COLLECTION
    # ===========================================
    print("\n[2] Memberships Collection:")

    try:
        db.memberships.create_index(
            [("customer", ASCENDING), ("status", ASCENDING), ("expiry_date", DESCENDING)],
            name="idx_memberships_customer_status_expiry",
            background=True
        )
        created.append("memberships: idx_memberships_customer_status_expiry")
        print("  + Created: customer + status + expiry_date")
    except Exception as e:
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            skipped.append("memberships: idx_memberships_customer_status_expiry")
            print("  ~ Skipped: customer + status + expiry_date (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # PREPAID_PACKAGES COLLECTION
    # ===========================================
    print("\n[3] PrepaidPackages Collection:")

    try:
        db.prepaid_packages.create_index(
            [("customer", ASCENDING), ("status", ASCENDING)],
            name="idx_prepaid_customer_status",
            background=True
        )
        created.append("prepaid_packages: idx_prepaid_customer_status")
        print("  + Created: customer + status")
    except Exception as e:
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            skipped.append("prepaid_packages: idx_prepaid_customer_status")
            print("  ~ Skipped: customer + status (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # SUMMARY
    # ===========================================
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if created:
        print(f"\nNew indexes created: {len(created)}")
        for idx in created:
            print(f"  + {idx}")

    if skipped:
        print(f"\nExisting indexes (skipped): {len(skipped)}")
        for idx in skipped:
            print(f"  ~ {idx}")

    if not created and not skipped:
        print("\nNo indexes to create or skip.")

    print("\n" + "=" * 60)
    print("Index creation complete!")
    print("=" * 60)

    client.close()


if __name__ == '__main__':
    try:
        create_missing_indexes()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

