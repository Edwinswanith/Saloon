"""
Simple MongoDB Collections Creator
Creates collections quickly using direct MongoDB commands
"""
from pymongo import MongoClient
import os

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

# Parse connection string
if MONGODB_DB not in MONGODB_URI:
    if '?' in MONGODB_URI:
        db_uri = MONGODB_URI.replace('?', f'/{MONGODB_DB}?')
    else:
        db_uri = f"{MONGODB_URI}/{MONGODB_DB}"
else:
    db_uri = MONGODB_URI

print(f"Connecting to MongoDB: {MONGODB_DB}...")

try:
    # Connect with shorter timeout for faster failure detection
    client = MongoClient(
        db_uri,
        serverSelectionTimeoutMS=5000,  # 5 second timeout
        connectTimeoutMS=5000
    )
    
    # Test connection
    client.admin.command('ping')
    print("Connected successfully!\n")
    
    db = client[MONGODB_DB]
    
    # Collections to create
    collections = [
        'customers', 'staffs', 'service_groups', 'services',
        'product_categories', 'products', 'packages',
        'prepaid_groups', 'prepaid_packages', 'membership_plans',
        'memberships', 'bills', 'appointments', 'expense_categories',
        'expenses', 'suppliers', 'orders', 'leads', 'feedbacks',
        'staff_attendance', 'assets', 'cash_transactions',
        'loyalty_program_settings', 'referral_program_settings',
        'tax_settings', 'tax_slabs', 'managers'
    ]
    
    print("=" * 60)
    print("Creating Collections")
    print("=" * 60)
    
    created = []
    existing = []
    
    for collection_name in collections:
        try:
            collection = db[collection_name]
            
            # Check if collection exists
            if collection_name in db.list_collection_names():
                count = collection.count_documents({})
                existing.append(f"{collection_name} ({count} docs)")
            else:
                # Create collection by inserting and deleting a dummy document
                result = collection.insert_one({'_init': True})
                collection.delete_one({'_id': result.inserted_id})
                created.append(collection_name)
                
        except Exception as e:
            print(f"Error with {collection_name}: {str(e)[:50]}")
    
    print(f"\nCreated ({len(created)}):")
    for name in created:
        print(f"  - {name}")
    
    if existing:
        print(f"\nAlready Exist ({len(existing)}):")
        for item in existing[:5]:  # Show first 5
            print(f"  - {item}")
        if len(existing) > 5:
            print(f"  ... and {len(existing) - 5} more")
    
    print("\n" + "=" * 60)
    print("Done! Check MongoDB Atlas Data Explorer to see collections.")
    print("=" * 60)
    
    client.close()
    
except Exception as e:
    print(f"\nError: {e}")
    print("\nTip: Collections will be created automatically when you")
    print("use the app to create customers, bills, etc.")
    print("\nYou can also create them manually in MongoDB Atlas Data Explorer.")

