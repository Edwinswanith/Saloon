"""
Migration Script: Duplicate Legacy Products/Services/Packages to All Branches

This script finds all items (products, services, packages) without a branch assigned
and creates a copy for each active branch with the same stock/data.

Run this BEFORE updating the route files to remove Q(branch=None).

Usage:
    python migrate_legacy_data.py

The script will:
1. Find all legacy items (branch=None)
2. For each legacy item, create a copy for each active branch
3. Mark the original legacy item as inactive (or delete)
4. Log all changes
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import Product, Service, Package, Branch, ProductCategory, ServiceGroup
from mongoengine import connect

def get_all_branches():
    """Get all active branches"""
    branches = list(Branch.objects())
    print(f"Found {len(branches)} branches:")
    for b in branches:
        print(f"  - {b.name} (ID: {b.id})")
    return branches

def migrate_legacy_products(branches):
    """Migrate products without branch to all branches"""
    legacy_products = list(Product.objects(branch=None))
    print(f"\n=== PRODUCTS ===")
    print(f"Found {len(legacy_products)} legacy products (no branch assigned)")

    if not legacy_products:
        print("No legacy products to migrate.")
        return 0

    migrated_count = 0

    for product in legacy_products:
        print(f"\nMigrating product: {product.name} (ID: {product.id})")
        print(f"  Current stock: {product.stock_quantity}")

        for branch in branches:
            # Check if this product already exists for this branch
            existing = Product.objects(name=product.name, branch=branch).first()
            if existing:
                print(f"  - Branch '{branch.name}': Already exists (ID: {existing.id}, stock: {existing.stock_quantity})")
                continue

            # Create a copy for this branch
            new_product = Product(
                name=product.name,
                category=product.category,
                price=product.price,
                cost=product.cost,
                stock_quantity=product.stock_quantity,  # Copy current stock
                min_stock_level=product.min_stock_level,
                sku=product.sku,
                description=product.description,
                branch=branch,
                status=product.status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            new_product.save()
            print(f"  - Branch '{branch.name}': Created (ID: {new_product.id}, stock: {new_product.stock_quantity})")
            migrated_count += 1

        # Mark original as inactive (soft delete)
        product.status = 'migrated'
        product.updated_at = datetime.utcnow()
        product.save()
        print(f"  - Original marked as 'migrated'")

    return migrated_count

def migrate_legacy_services(branches):
    """Migrate services without branch to all branches"""
    legacy_services = list(Service.objects(branch=None))
    print(f"\n=== SERVICES ===")
    print(f"Found {len(legacy_services)} legacy services (no branch assigned)")

    if not legacy_services:
        print("No legacy services to migrate.")
        return 0

    migrated_count = 0

    for service in legacy_services:
        print(f"\nMigrating service: {service.name} (ID: {service.id})")

        for branch in branches:
            # Check if this service already exists for this branch
            existing = Service.objects(name=service.name, branch=branch).first()
            if existing:
                print(f"  - Branch '{branch.name}': Already exists (ID: {existing.id})")
                continue

            # Create a copy for this branch
            new_service = Service(
                name=service.name,
                group=service.group,
                price=service.price,
                duration=service.duration,
                description=service.description,
                branch=branch,
                status=service.status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            new_service.save()
            print(f"  - Branch '{branch.name}': Created (ID: {new_service.id})")
            migrated_count += 1

        # Mark original as inactive
        service.status = 'migrated'
        service.updated_at = datetime.utcnow()
        service.save()
        print(f"  - Original marked as 'migrated'")

    return migrated_count

def migrate_legacy_packages(branches):
    """Migrate packages without branch to all branches"""
    legacy_packages = list(Package.objects(branch=None))
    print(f"\n=== PACKAGES ===")
    print(f"Found {len(legacy_packages)} legacy packages (no branch assigned)")

    if not legacy_packages:
        print("No legacy packages to migrate.")
        return 0

    migrated_count = 0

    for package in legacy_packages:
        print(f"\nMigrating package: {package.name} (ID: {package.id})")

        for branch in branches:
            # Check if this package already exists for this branch
            existing = Package.objects(name=package.name, branch=branch).first()
            if existing:
                print(f"  - Branch '{branch.name}': Already exists (ID: {existing.id})")
                continue

            # Create a copy for this branch
            new_package = Package(
                name=package.name,
                price=package.price,
                description=package.description,
                services=package.services,
                branch=branch,
                status=package.status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            new_package.save()
            print(f"  - Branch '{branch.name}': Created (ID: {new_package.id})")
            migrated_count += 1

        # Mark original as inactive
        package.status = 'migrated'
        package.updated_at = datetime.utcnow()
        package.save()
        print(f"  - Original marked as 'migrated'")

    return migrated_count

def main():
    print("=" * 60)
    print("LEGACY DATA MIGRATION SCRIPT")
    print("Duplicating items without branch to all branches")
    print("=" * 60)

    # Get all branches
    branches = get_all_branches()

    if not branches:
        print("\nERROR: No branches found in database!")
        print("Please create at least one branch before running this migration.")
        return

    # Confirm before proceeding
    print(f"\nThis will duplicate legacy items to {len(branches)} branches.")
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Migration cancelled.")
        return

    # Run migrations
    product_count = migrate_legacy_products(branches)
    service_count = migrate_legacy_services(branches)
    package_count = migrate_legacy_packages(branches)

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"Products migrated: {product_count}")
    print(f"Services migrated: {service_count}")
    print(f"Packages migrated: {package_count}")
    print(f"Total new items created: {product_count + service_count + package_count}")
    print("\nOriginal legacy items have been marked as 'migrated'.")
    print("They will not appear in queries once Q(branch=None) is removed.")

if __name__ == '__main__':
    with app.app_context():
        main()
