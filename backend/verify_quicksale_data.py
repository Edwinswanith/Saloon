#!/usr/bin/env python3
"""
Verification script to check QuickSale data availability in MongoDB
"""
import sys
from mongoengine import connect
from models import Customer, Staff, Service, Package, Product, PrepaidPackage, Membership, Branch

# MongoDB connection - Use Saloon database
MONGODB_URI = "mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/Saloon?appName=Saloon"

def verify_quicksale_data():
    """Verify all data required for QuickSale is available"""
    
    print("\n" + "="*60)
    print("QUICKSALE DATA VERIFICATION")
    print("="*60)
    
    try:
        # Connect to MongoDB
        connect(host=MONGODB_URI)
        print("\n[SUCCESS] Connected to MongoDB")
        
        # Check Branches
        branches = Branch.objects()
        print(f"\n[BRANCHES] Found {len(branches)} branches:")
        for branch in branches[:3]:
            print(f"  - {branch.name} ({branch.city})")
        
        # Check Customers
        customers = Customer.objects()
        print(f"\n[CUSTOMERS] Found {len(customers)} customers:")
        for customer in customers[:3]:
            name = f"{customer.first_name} {customer.last_name}"
            print(f"  - {name} | Mobile: {customer.mobile} | Branch: {customer.branch.name if customer.branch else 'N/A'}")
        
        # Check Staff
        staff_members = Staff.objects()
        print(f"\n[STAFF] Found {len(staff_members)} staff members:")
        for staff in staff_members[:3]:
            name = f"{staff.first_name} {staff.last_name}"
            print(f"  - {name} | Role: {staff.role} | Branch: {staff.branch.name if staff.branch else 'N/A'}")
        
        # Check Services
        services = Service.objects()
        print(f"\n[SERVICES] Found {len(services)} services:")
        for service in services[:5]:
            print(f"  - {service.name} | Price: Rs.{service.price} | Duration: {service.duration}min")
        
        # Check Packages
        packages = Package.objects()
        print(f"\n[PACKAGES] Found {len(packages)} packages:")
        for package in packages[:3]:
            validity = getattr(package, 'validity_days', 'N/A')
            print(f"  - {package.name} | Price: Rs.{package.price} | Validity: {validity} days")
        
        # Check Products
        products = Product.objects()
        print(f"\n[PRODUCTS] Found {len(products)} products:")
        for product in products[:5]:
            stock = product.stock_quantity if hasattr(product, 'stock_quantity') else 'N/A'
            print(f"  - {product.name} | Price: Rs.{product.price} | Stock: {stock}")
        
        # Check Products with Stock
        products_with_stock = Product.objects(stock_quantity__gt=0)
        products_low_stock = Product.objects(stock_quantity__lte=5, stock_quantity__gt=0)
        products_out_of_stock = Product.objects(stock_quantity=0)
        
        print(f"\n[PRODUCT INVENTORY]")
        print(f"  - In Stock: {len(products_with_stock)} products")
        print(f"  - Low Stock (<=5): {len(products_low_stock)} products")
        print(f"  - Out of Stock: {len(products_out_of_stock)} products")
        
        if products_low_stock:
            print(f"\n  Low Stock Items:")
            for product in products_low_stock[:3]:
                print(f"    - {product.name}: {product.stock_quantity} units")
        
        # Check Prepaid Packages
        prepaid_packages = PrepaidPackage.objects()
        print(f"\n[PREPAID PACKAGES] Found {len(prepaid_packages)} prepaid packages:")
        active_prepaid = PrepaidPackage.objects(remaining_balance__gt=0)
        print(f"  - Active (with balance): {len(active_prepaid)} packages")
        for prepaid in active_prepaid[:3]:
            customer_name = f"{prepaid.customer.first_name} {prepaid.customer.last_name}" if prepaid.customer else "N/A"
            print(f"    - {customer_name} | Balance: Rs.{prepaid.remaining_balance}")
        
        # Check Memberships
        memberships = Membership.objects()
        print(f"\n[MEMBERSHIP PLANS] Found {len(memberships)} membership plans:")
        for membership in memberships[:3]:
            validity = getattr(membership, 'validity_days', getattr(membership, 'validity', 'N/A'))
            print(f"  - {membership.name} | Price: Rs.{membership.price} | Validity: {validity} days")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total Branches: {len(branches)}")
        print(f"Total Customers: {len(customers)}")
        print(f"Total Staff: {len(staff_members)}")
        print(f"Total Services: {len(services)}")
        print(f"Total Packages: {len(packages)}")
        print(f"Total Products: {len(products)} ({len(products_with_stock)} in stock)")
        print(f"Total Active Prepaid: {len(active_prepaid)}")
        print(f"Total Membership Plans: {len(memberships)}")
        
        # Warnings
        warnings = []
        if len(services) == 0:
            warnings.append("No services found! Add services to enable bookings.")
        if len(packages) == 0:
            warnings.append("No packages found! Add packages for package sales.")
        if len(products) == 0:
            warnings.append("No products found! Add products for retail sales.")
        if len(products_out_of_stock) > 10:
            warnings.append(f"{len(products_out_of_stock)} products are out of stock. Restock inventory!")
        
        if warnings:
            print("\n" + "="*60)
            print("WARNINGS")
            print("="*60)
            for warning in warnings:
                print(f"[WARNING] {warning}")
        
        print("\n" + "="*60)
        print("[SUCCESS] QuickSale data verification complete!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_quicksale_data()
    sys.exit(0 if success else 1)

