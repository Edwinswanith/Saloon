"""
MongoDB Index Creation Script for Dashboard Performance Optimization

Run this script to create indexes specifically for dashboard queries:
    python backend/migrations/create_dashboard_indexes.py

These indexes are critical for:
- Top Moving Items queries
- Top Customers queries  
- Top Offerings queries
- All dashboard aggregation pipelines

Performance target: <200ms per query
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING

# MongoDB Configuration (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')


def create_dashboard_indexes():
    """Create all performance-critical indexes for dashboard queries"""

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    print(f"Connected to database: {MONGODB_DB}")
    print("=" * 60)
    print("Creating Dashboard Performance Indexes")
    print("=" * 60)

    created = []
    skipped = []

    # ===========================================
    # BILLS COLLECTION - Dashboard Queries
    # ===========================================
    print("\n[1] Bills Collection - Dashboard Indexes:")

    # Index for items.item_type queries (for top offerings)
    try:
        db.bills.create_index(
            [("items.item_type", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_type_date_deleted",
            background=True
        )
        created.append("bills: idx_bills_items_type_date_deleted")
        print("  + Created: items.item_type + bill_date + is_deleted")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("bills: idx_bills_items_type_date_deleted")
            print("  ~ Skipped: items.item_type + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for items.service queries (for top moving items - services)
    try:
        db.bills.create_index(
            [("items.service", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_service_date_deleted",
            background=True,
            sparse=True
        )
        created.append("bills: idx_bills_items_service_date_deleted")
        print("  + Created: items.service + bill_date + is_deleted (sparse)")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("bills: idx_bills_items_service_date_deleted")
            print("  ~ Skipped: items.service + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for items.package queries (for top moving items - packages)
    try:
        db.bills.create_index(
            [("items.package", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_package_date_deleted",
            background=True,
            sparse=True
        )
        created.append("bills: idx_bills_items_package_date_deleted")
        print("  + Created: items.package + bill_date + is_deleted (sparse)")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("bills: idx_bills_items_package_date_deleted")
            print("  ~ Skipped: items.package + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # Index for items.product queries (for top moving items - products)
    try:
        db.bills.create_index(
            [("items.product", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)],
            name="idx_bills_items_product_date_deleted",
            background=True,
            sparse=True
        )
        created.append("bills: idx_bills_items_product_date_deleted")
        print("  + Created: items.product + bill_date + is_deleted (sparse)")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("bills: idx_bills_items_product_date_deleted")
            print("  ~ Skipped: items.product + bill_date + is_deleted (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # SERVICES COLLECTION
    # ===========================================
    print("\n[2] Services Collection Indexes:")

    # Index for name lookups
    try:
        db.services.create_index(
            [("_id", ASCENDING), ("name", ASCENDING)],
            name="idx_services_id_name",
            background=True
        )
        created.append("services: idx_services_id_name")
        print("  + Created: _id + name")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("services: idx_services_id_name")
            print("  ~ Skipped: _id + name (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # PACKAGES COLLECTION
    # ===========================================
    print("\n[3] Packages Collection Indexes:")

    # Index for name lookups
    try:
        db.packages.create_index(
            [("_id", ASCENDING), ("name", ASCENDING)],
            name="idx_packages_id_name",
            background=True
        )
        created.append("packages: idx_packages_id_name")
        print("  + Created: _id + name")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("packages: idx_packages_id_name")
            print("  ~ Skipped: _id + name (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # PRODUCTS COLLECTION
    # ===========================================
    print("\n[4] Products Collection Indexes:")

    # Index for name and stock lookups
    try:
        db.products.create_index(
            [("_id", ASCENDING), ("name", ASCENDING), ("stock_quantity", ASCENDING), ("min_stock_level", ASCENDING)],
            name="idx_products_id_name_stock",
            background=True
        )
        created.append("products: idx_products_id_name_stock")
        print("  + Created: _id + name + stock_quantity + min_stock_level")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("products: idx_products_id_name_stock")
            print("  ~ Skipped: _id + name + stock_quantity + min_stock_level (exists)")
        else:
            print(f"  ! Error: {e}")

    # ===========================================
    # CUSTOMERS COLLECTION
    # ===========================================
    print("\n[5] Customers Collection Indexes:")

    # Index for customer lookups in top customers query
    try:
        db.customers.create_index(
            [("_id", ASCENDING), ("first_name", ASCENDING), ("last_name", ASCENDING), ("mobile", ASCENDING)],
            name="idx_customers_id_name_mobile",
            background=True
        )
        created.append("customers: idx_customers_id_name_mobile")
        print("  + Created: _id + first_name + last_name + mobile")
    except Exception as e:
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            skipped.append("customers: idx_customers_id_name_mobile")
            print("  ~ Skipped: _id + first_name + last_name + mobile (exists)")
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
            print(f"  ✓ {idx}")
    
    if skipped:
        print("\nExisting indexes (skipped):")
        for idx in skipped:
            print(f"  ~ {idx}")

    print("\n" + "=" * 60)
    print("Dashboard indexes setup complete!")
    print("=" * 60)
    print("\nNote: Indexes are created in the background.")
    print("Large collections may take a few minutes to index.")
    print("Monitor index creation progress in MongoDB Atlas.")

    client.close()


if __name__ == '__main__':
    try:
        create_dashboard_indexes()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

