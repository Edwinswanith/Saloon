"""
Comprehensive script to verify all customer data and salon service details
are properly saved and stored in MongoDB.

This script checks:
1. Customer data integrity
2. Service details (services, service groups)
3. Products and categories
4. Packages
5. Relationships between entities
6. Data completeness
"""

import sys
import os
from datetime import datetime
from collections import defaultdict

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect, disconnect
from models import (
    Customer, Branch, Service, ServiceGroup, Product, ProductCategory,
    Package, Membership, MembershipPlan, Bill, Staff, Appointment
)

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon_prod'  # Production database

# Connect to MongoDB
try:
    base_uri = MONGODB_URI
    
    if '@' in base_uri:
        parts = base_uri.split('@')
        if len(parts) == 2:
            credentials = parts[0]
            host_and_params = parts[1]
            
            if '/' in host_and_params:
                host = host_and_params.split('/')[0]
                if '?' in host_and_params:
                    params = '?' + host_and_params.split('?', 1)[1]
                else:
                    params = ''
                base_uri = f"{credentials}@{host}{params}"
    
    if f'/{MONGODB_DB}' not in base_uri:
        if '?' in base_uri:
            base_uri = base_uri.replace('?', f'/{MONGODB_DB}?')
        else:
            base_uri = f"{base_uri}/{MONGODB_DB}"
    
    if 'retryWrites' not in base_uri:
        separator = '&' if '?' in base_uri else '?'
        base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
    
    connect(
        host=base_uri,
        alias='default',
        db=MONGODB_DB,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    print(f"[OK] Connected to MongoDB: {MONGODB_DB}")
except Exception as e:
    print(f"[ERROR] Error connecting to MongoDB: {e}")
    sys.exit(1)


def verify_customers():
    """Verify customer data integrity"""
    print("\n" + "="*70)
    print("VERIFYING CUSTOMER DATA")
    print("="*70)
    
    issues = []
    warnings = []
    
    # Count customers
    total_customers = Customer.objects().count()
    print(f"\n[INFO] Total Customers: {total_customers}")
    
    if total_customers == 0:
        issues.append("No customers found in database")
        return issues, warnings
    
    # Check customers with missing required fields
    customers_no_mobile = Customer.objects(mobile__exists=False).count()
    customers_no_branch = Customer.objects(branch__exists=False).count()
    customers_null_branch = Customer.objects(branch=None).count()
    
    if customers_no_mobile > 0:
        issues.append(f"{customers_no_mobile} customers missing mobile number")
    
    if customers_no_branch > 0 or customers_null_branch > 0:
        warnings.append(f"{customers_no_branch + customers_null_branch} customers without branch assignment")
    
    # Check for duplicate mobiles (should be unique per branch)
    print(f"\n[INFO] Checking for duplicate mobile numbers...")
    duplicate_count = 0
    mobile_map = defaultdict(list)
    
    for customer in Customer.objects().only('id', 'mobile', 'branch'):
        if customer.mobile:
            key = f"{customer.mobile}_{str(customer.branch.id) if customer.branch else 'no_branch'}"
            mobile_map[key].append(str(customer.id))
            if len(mobile_map[key]) > 1:
                duplicate_count += 1
    
    if duplicate_count > 0:
        issues.append(f"Found {duplicate_count} potential duplicate mobile numbers (same branch)")
    
    # Sample customer data
    sample_customers = list(Customer.objects().limit(5))
    print(f"\n[INFO] Sample Customer Records:")
    for i, c in enumerate(sample_customers, 1):
        name = f"{c.first_name or ''} {c.last_name or ''}".strip() or "No Name"
        branch_name = c.branch.name if c.branch else "No Branch"
        print(f"   {i}. {name} ({c.mobile}) - Branch: {branch_name}")
        if not c.mobile:
            issues.append(f"Customer {c.id} missing mobile number")
    
    # Customer statistics
    customers_with_branch = Customer.objects(branch__exists=True, branch__ne=None).count()
    customers_with_email = Customer.objects(email__exists=True, email__ne=None).exclude(email='').count()
    customers_with_source = Customer.objects(source__exists=True, source__ne=None).exclude(source='').count()
    
    print(f"\n[STATS] Customer Data Completeness:")
    print(f"   - With branch: {customers_with_branch}/{total_customers} ({customers_with_branch*100/total_customers:.1f}%)")
    print(f"   - With email: {customers_with_email}/{total_customers} ({customers_with_email*100/total_customers:.1f}%)")
    print(f"   - With source: {customers_with_source}/{total_customers} ({customers_with_source*100/total_customers:.1f}%)")
    
    return issues, warnings


def verify_services():
    """Verify service details"""
    print("\n" + "="*70)
    print("VERIFYING SERVICE DETAILS")
    print("="*70)
    
    issues = []
    warnings = []
    
    # Service Groups
    service_groups = list(ServiceGroup.objects())
    service_group_count = len(service_groups)
    print(f"\n[INFO] Service Groups: {service_group_count}")
    
    if service_group_count == 0:
        issues.append("No service groups found")
    else:
        print(f"\n[INFO] Service Groups List:")
        for sg in service_groups:
            print(f"   - {sg.name} (Order: {sg.display_order})")
    
    # Services
    total_services = Service.objects().count()
    active_services = Service.objects(status='active').count()
    inactive_services = Service.objects(status='inactive').count()
    
    print(f"\n[INFO] Services:")
    print(f"   Total: {total_services}")
    print(f"   Active: {active_services}")
    print(f"   Inactive: {inactive_services}")
    
    if total_services == 0:
        issues.append("No services found in database")
        return issues, warnings
    
    # Check services with missing fields
    services_no_group = Service.objects(group__exists=False).count()
    services_no_price = Service.objects(price__exists=False).count()
    services_no_branch = Service.objects(branch__exists=False).count()
    
    if services_no_group > 0:
        issues.append(f"{services_no_group} services missing service group")
    if services_no_price > 0:
        issues.append(f"{services_no_price} services missing price")
    if services_no_branch > 0:
        warnings.append(f"{services_no_branch} services without branch assignment")
    
    # Sample services
    sample_services = list(Service.objects(status='active').limit(10))
    print(f"\n[INFO] Sample Active Services:")
    for i, s in enumerate(sample_services, 1):
        group_name = s.group.name if s.group else "No Group"
        branch_name = s.branch.name if s.branch else "No Branch"
        duration = f"{s.duration} min" if s.duration else "N/A"
        print(f"   {i}. {s.name} - {group_name} - Rs.{s.price} ({duration}) - {branch_name}")
    
    # Services by group
    print(f"\n[INFO] Services by Group:")
    for sg in service_groups:
        count = Service.objects(group=sg, status='active').count()
        if count > 0:
            print(f"   - {sg.name}: {count} active services")
    
    # Services by branch
    branches = Branch.objects()
    print(f"\n[INFO] Services by Branch:")
    for branch in branches:
        count = Service.objects(branch=branch, status='active').count()
        if count > 0:
            print(f"   - {branch.name}: {count} active services")
    
    return issues, warnings


def verify_products():
    """Verify product data"""
    print("\n" + "="*70)
    print("VERIFYING PRODUCT DATA")
    print("="*70)
    
    issues = []
    warnings = []
    
    # Product Categories
    categories = list(ProductCategory.objects())
    category_count = len(categories)
    print(f"\n[INFO] Product Categories: {category_count}")
    
    if category_count == 0:
        warnings.append("No product categories found")
    else:
        print(f"\n[INFO] Product Categories List:")
        for cat in categories:
            print(f"   - {cat.name} (Order: {cat.display_order})")
    
    # Products
    total_products = Product.objects().count()
    active_products = Product.objects(status='active').count()
    
    print(f"\n[INFO] Products:")
    print(f"   Total: {total_products}")
    print(f"   Active: {active_products}")
    
    if total_products == 0:
        warnings.append("No products found in database")
        return issues, warnings
    
    # Check products with missing fields
    products_no_category = Product.objects(category__exists=False).count()
    products_no_price = Product.objects(price__exists=False).count()
    products_no_stock = Product.objects(stock_quantity__exists=False).count()
    
    if products_no_category > 0:
        issues.append(f"{products_no_category} products missing category")
    if products_no_price > 0:
        issues.append(f"{products_no_price} products missing price")
    if products_no_stock > 0:
        warnings.append(f"{products_no_stock} products missing stock quantity")
    
    # Stock analysis
    products_in_stock = Product.objects(stock_quantity__gt=0, status='active').count()
    products_low_stock = Product.objects(stock_quantity__lte=5, stock_quantity__gt=0, status='active').count()
    products_out_of_stock = Product.objects(stock_quantity__lte=0, status='active').count()
    
    print(f"\n[INFO] Stock Status:")
    print(f"   In Stock: {products_in_stock}")
    print(f"   Low Stock (<=5): {products_low_stock}")
    print(f"   Out of Stock: {products_out_of_stock}")
    
    # Sample products
    sample_products = list(Product.objects(status='active').limit(10))
    print(f"\n[INFO] Sample Active Products:")
    for i, p in enumerate(sample_products, 1):
        cat_name = p.category.name if p.category else "No Category"
        branch_name = p.branch.name if p.branch else "No Branch"
        stock = p.stock_quantity if p.stock_quantity is not None else 0
        stock_status = "OUT" if stock <= 0 else ("LOW" if stock <= 5 else "OK")
        print(f"   {i}. {p.name} - {cat_name} - Rs.{p.price} - Stock: {stock} ({stock_status}) - {branch_name}")
    
    return issues, warnings


def verify_packages():
    """Verify package data"""
    print("\n" + "="*70)
    print("VERIFYING PACKAGE DATA")
    print("="*70)
    
    issues = []
    warnings = []
    
    total_packages = Package.objects().count()
    active_packages = Package.objects(status='active').count()
    
    print(f"\n[INFO] Packages:")
    print(f"   Total: {total_packages}")
    print(f"   Active: {active_packages}")
    
    if total_packages == 0:
        warnings.append("No packages found in database")
        return issues, warnings
    
    # Check packages with missing fields
    packages_no_price = Package.objects(price__exists=False).count()
    packages_no_branch = Package.objects(branch__exists=False).count()
    
    if packages_no_price > 0:
        issues.append(f"{packages_no_price} packages missing price")
    if packages_no_branch > 0:
        warnings.append(f"{packages_no_branch} packages without branch assignment")
    
    # Sample packages
    sample_packages = list(Package.objects(status='active').limit(10))
    print(f"\n[INFO] Sample Active Packages:")
    for i, p in enumerate(sample_packages, 1):
        branch_name = p.branch.name if p.branch else "No Branch"
        services_count = len(p.services.split(',')) if p.services else 0
        print(f"   {i}. {p.name} - Rs.{p.price} - {services_count} services - {branch_name}")
    
    return issues, warnings


def verify_relationships():
    """Verify relationships between entities"""
    print("\n" + "="*70)
    print("VERIFYING DATA RELATIONSHIPS")
    print("="*70)
    
    issues = []
    warnings = []
    
    # Check branch references
    branches = list(Branch.objects())
    print(f"\n[INFO] Branches: {len(branches)}")
    for branch in branches:
        print(f"   - {branch.name} ({branch.city})")
    
    # Check customers with bills
    customers_with_bills = set()
    bills = Bill.objects().only('customer')
    for bill in bills:
        if bill.customer:
            customers_with_bills.add(str(bill.customer.id))
    
    total_customers = Customer.objects().count()
    customers_with_transactions = len(customers_with_bills)
    
    print(f"\n[INFO] Customer Transaction Statistics:")
    print(f"   Total Customers: {total_customers}")
    print(f"   Customers with Bills: {customers_with_transactions}")
    print(f"   Customers without Bills: {total_customers - customers_with_transactions}")
    
    # Check services used in bills
    services_used = set()
    bills_with_items = Bill.objects().only('items')
    for bill in bills_with_items:
        if bill.items:
            for item in bill.items:
                if item.item_type == 'service' and item.service_id:
                    services_used.add(str(item.service_id))
    
    total_services = Service.objects().count()
    services_used_count = len(services_used)
    
    print(f"\n[INFO] Service Usage Statistics:")
    print(f"   Total Services: {total_services}")
    print(f"   Services Used in Bills: {services_used_count}")
    print(f"   Services Never Used: {total_services - services_used_count}")
    
    # Check products used in bills
    products_used = set()
    for bill in bills_with_items:
        if bill.items:
            for item in bill.items:
                if item.item_type == 'product' and item.product_id:
                    products_used.add(str(item.product_id))
    
    total_products = Product.objects().count()
    products_used_count = len(products_used)
    
    print(f"\n[INFO] Product Usage Statistics:")
    print(f"   Total Products: {total_products}")
    print(f"   Products Sold: {products_used_count}")
    print(f"   Products Never Sold: {total_products - products_used_count}")
    
    return issues, warnings


def verify_data_completeness():
    """Overall data completeness check"""
    print("\n" + "="*70)
    print("OVERALL DATA COMPLETENESS CHECK")
    print("="*70)
    
    stats = {}
    
    # Count all entities
    stats['branches'] = Branch.objects().count()
    stats['customers'] = Customer.objects().count()
    stats['staff'] = Staff.objects().count()
    stats['service_groups'] = ServiceGroup.objects().count()
    stats['services'] = Service.objects(status='active').count()
    stats['product_categories'] = ProductCategory.objects().count()
    stats['products'] = Product.objects(status='active').count()
    stats['packages'] = Package.objects(status='active').count()
    stats['membership_plans'] = MembershipPlan.objects(status='active').count()
    stats['memberships'] = Membership.objects(status='active').count()
    stats['bills'] = Bill.objects().count()
    stats['appointments'] = Appointment.objects().count()
    
    print(f"\n[INFO] Database Statistics:")
    for key, value in sorted(stats.items()):
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Check minimum requirements
    print(f"\n[INFO] Minimum Requirements Check:")
    requirements = {
        'Branches': stats['branches'] >= 1,
        'Customers': stats['customers'] >= 1,
        'Services': stats['services'] >= 1,
        'Products': stats['products'] >= 1,
    }
    
    for req, met in requirements.items():
        status = "[OK]" if met else "[MISSING]"
        print(f"   {status} {req}")
    
    return stats


def main():
    """Main execution function"""
    try:
        print("\n" + "="*70)
        print("COMPREHENSIVE DATA INTEGRITY VERIFICATION")
        print("="*70)
        print(f"Database: {MONGODB_DB}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_issues = []
        all_warnings = []
        
        # Verify each data type
        issues, warnings = verify_customers()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        issues, warnings = verify_services()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        issues, warnings = verify_products()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        issues, warnings = verify_packages()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        issues, warnings = verify_relationships()
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        stats = verify_data_completeness()
        
        # Final summary
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)
        
        if all_issues:
            print(f"\n[ISSUES FOUND] {len(all_issues)} issues detected:")
            for i, issue in enumerate(all_issues, 1):
                print(f"   {i}. {issue}")
        else:
            print(f"\n[OK] No critical issues found")
        
        if all_warnings:
            print(f"\n[WARNINGS] {len(all_warnings)} warnings:")
            for i, warning in enumerate(all_warnings, 1):
                print(f"   {i}. {warning}")
        else:
            print(f"\n[OK] No warnings")
        
        # Overall status
        print("\n" + "="*70)
        if all_issues:
            print("[STATUS] VERIFICATION COMPLETED WITH ISSUES")
            print("="*70)
            print("Some data integrity issues were found. Please review and fix.")
        else:
            print("[STATUS] VERIFICATION PASSED")
            print("="*70)
            print("All customer data and salon service details are properly saved in MongoDB.")
        
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            disconnect()
        except:
            pass


if __name__ == '__main__':
    main()

