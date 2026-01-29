"""
Migration script to populate denormalized 'name' field in bill items
This script will:
1. Find all bills with items that don't have a name field
2. Look up the referenced service/package/product/prepaid/membership
3. Store the name directly in the bill item for future lookups
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Bill, Service, Package, Product, PrepaidPackage, Membership
from datetime import datetime, timezone
from bson import ObjectId

# MongoDB connection - use same as app.py
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')

def build_connection_uri(base_uri, db_name):
    """Build connection URI with database name"""
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

    if f'/{db_name}' not in base_uri:
        if '?' in base_uri:
            base_uri = base_uri.replace('?', f'/{db_name}?')
        else:
            base_uri = f"{base_uri}/{db_name}"

    if 'retryWrites' not in base_uri:
        separator = '&' if '?' in base_uri else '?'
        base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"

    return base_uri

def get_ref_id(ref):
    """Extract ObjectId from a reference (handles both ObjectId and DBRef)"""
    if ref is None:
        return None
    if hasattr(ref, 'id'):
        return ref.id
    if isinstance(ref, dict) and '$id' in ref:
        return ref['$id']
    return ref

def migrate_bill_item_names():
    """Populate name field in bill items from referenced documents"""
    try:
        print("Connecting to MongoDB...")
        base_uri = build_connection_uri(MONGO_URI, MONGODB_DB)
        connect(host=base_uri, alias='default', db=MONGODB_DB)
        print("Connected successfully!")

        # First, build lookup maps for all services, packages, products, prepaids, memberships
        print("\nBuilding lookup maps...")

        service_names = {}
        for svc in Service.objects.only('id', 'name'):
            service_names[str(svc.id)] = svc.name
        print(f"  Loaded {len(service_names)} services")

        package_names = {}
        for pkg in Package.objects.only('id', 'name'):
            package_names[str(pkg.id)] = pkg.name
        print(f"  Loaded {len(package_names)} packages")

        product_names = {}
        for prod in Product.objects.only('id', 'name'):
            product_names[str(prod.id)] = prod.name
        print(f"  Loaded {len(product_names)} products")

        prepaid_names = {}
        for pp in PrepaidPackage.objects.only('id', 'name'):
            prepaid_names[str(pp.id)] = pp.name
        print(f"  Loaded {len(prepaid_names)} prepaid packages")

        membership_names = {}
        for mem in Membership.objects.only('id', 'name'):
            membership_names[str(mem.id)] = mem.name
        print(f"  Loaded {len(membership_names)} memberships")

        # Process bills using raw MongoDB to avoid dereferencing issues
        print("\nProcessing bills...")

        # Get raw MongoDB collection
        from mongoengine.connection import get_db
        db = get_db()
        bills_collection = db['bills']

        total_bills = bills_collection.count_documents({})
        print(f"Total bills to process: {total_bills}")

        updated_count = 0
        items_updated = 0
        skipped_count = 0
        not_found_count = 0

        # Process all bills using raw MongoDB
        cursor = bills_collection.find({})

        for bill_doc in cursor:
            bill_modified = False
            items = bill_doc.get('items', [])

            for i, item in enumerate(items):
                # Skip if name already exists
                if item.get('name'):
                    skipped_count += 1
                    continue

                item_name = None
                item_type = item.get('item_type')

                # Extract reference ID (handle both ObjectId and DBRef)
                if item_type == 'service':
                    ref = item.get('service')
                    ref_id = get_ref_id(ref)
                    if ref_id:
                        item_name = service_names.get(str(ref_id))
                elif item_type == 'package':
                    ref = item.get('package')
                    ref_id = get_ref_id(ref)
                    if ref_id:
                        item_name = package_names.get(str(ref_id))
                elif item_type == 'product':
                    ref = item.get('product')
                    ref_id = get_ref_id(ref)
                    if ref_id:
                        item_name = product_names.get(str(ref_id))
                elif item_type == 'prepaid':
                    ref = item.get('prepaid')
                    ref_id = get_ref_id(ref)
                    if ref_id:
                        item_name = prepaid_names.get(str(ref_id))
                elif item_type == 'membership':
                    ref = item.get('membership')
                    ref_id = get_ref_id(ref)
                    if ref_id:
                        item_name = membership_names.get(str(ref_id))

                if item_name:
                    items[i]['name'] = item_name
                    bill_modified = True
                    items_updated += 1
                else:
                    not_found_count += 1

            if bill_modified:
                # Update the bill document directly
                bills_collection.update_one(
                    {'_id': bill_doc['_id']},
                    {'$set': {'items': items}}
                )
                updated_count += 1

        print(f"  Processed {total_bills} bills...")

        print("\n" + "="*50)
        print("Migration completed!")
        print(f"  Bills updated: {updated_count}")
        print(f"  Items with names added: {items_updated}")
        print(f"  Items already had names (skipped): {skipped_count}")
        print(f"  Items with missing references (not found): {not_found_count}")
        print("="*50)

        return True

    except Exception as e:
        print(f"\nError during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys

    print("="*50)
    print("Bill Item Names Migration Script")
    print("="*50)
    print("\nThis script will:")
    print("1. Find all bill items without a 'name' field")
    print("2. Look up the referenced service/package/product")
    print("3. Store the name directly in the bill item")
    print("\nDatabase:", MONGODB_DB)

    # Skip interactive prompt if --yes flag is provided
    if '--yes' not in sys.argv:
        print("\nPress Ctrl+C to cancel, or Enter to continue...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\nMigration cancelled.")
            sys.exit(0)

    success = migrate_bill_item_names()
    if success:
        print("\nMigration completed successfully!")
    else:
        print("\nMigration failed. Please check the errors above.")
        sys.exit(1)
