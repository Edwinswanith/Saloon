"""
Initialize MongoDB Collections
This script creates all collections by inserting a temporary document into each collection.
"""
from mongoengine import connect, disconnect
from pymongo import MongoClient
import os
from datetime import datetime

# MongoDB Configuration (same as app.py)
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

# Parse connection string
if MONGODB_DB not in MONGODB_URI:
    if '?' in MONGODB_URI:
        MONGODB_URI = MONGODB_URI.replace('?', f'/{MONGODB_DB}?')
    else:
        MONGODB_URI = f"{MONGODB_URI}/{MONGODB_DB}"

# Connect using pymongo directly for collection creation
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

print(f"Connected to MongoDB: {MONGODB_DB}\n")
print("=" * 60)
print("MongoDB Collections Initialization")
print("=" * 60)

# List of all collections to create
collections = [
    'customers',
    'staffs',
    'service_groups',
    'services',
    'product_categories',
    'products',
    'packages',
    'prepaid_groups',
    'prepaid_packages',
    'membership_plans',
    'memberships',
    'bills',
    'appointments',
    'expense_categories',
    'expenses',
    'suppliers',
    'orders',
    'leads',
    'feedbacks',
    'staff_attendance',
    'assets',
    'cash_transactions',
    'loyalty_program_settings',
    'referral_program_settings',
    'tax_settings',
    'tax_slabs',
    'managers',
]

created = []
existing = []
errors = []

for collection_name in collections:
    try:
        collection = db[collection_name]
        
        # Check if collection exists and has documents
        count = collection.count_documents({})
        if count > 0:
            existing.append(f"[EXISTS] {collection_name} ({count} documents)")
            continue
        
        # Create collection by inserting and immediately deleting a dummy document
        # This ensures the collection exists in MongoDB
        try:
            result = collection.insert_one({
                '_temp_init': True,
                'created_at': datetime.utcnow()
            })
            
            # Delete the temporary document
            collection.delete_one({'_id': result.inserted_id})
            
            created.append(f"[CREATED] {collection_name}")
        except Exception as e:
            # Even if insert fails, try to verify collection exists
            try:
                # Force collection creation by listing collections
                if collection_name in db.list_collection_names():
                    created.append(f"[CREATED] {collection_name} (verified)")
                else:
                    errors.append(f"[ERROR] {collection_name}: {str(e)[:80]}")
            except:
                errors.append(f"[ERROR] {collection_name}: {str(e)[:80]}")
    except Exception as e:
        errors.append(f"[ERROR] {collection_name}: {str(e)[:80]}")

print(f"\nCreated Collections ({len(created)}):")
for item in created:
    print(f"  {item}")

if existing:
    print(f"\nExisting Collections ({len(existing)}):")
    for item in existing:
        print(f"  {item}")

if errors:
    print(f"\nErrors ({len(errors)}):")
    for item in errors:
        print(f"  {item}")

print("\n" + "=" * 60)
print("Initialization complete!")
print("=" * 60)

# Now initialize using MongoEngine for settings
print("\nInitializing settings using MongoEngine...")
try:
    # Connect using MongoEngine
    connect(host=MONGODB_URI, alias='default')
    
    from models import (
        LoyaltyProgramSettings, 
        ReferralProgramSettings, 
        TaxSettings
    )
    
    try:
        LoyaltyProgramSettings.get_settings()
        print("  [OK] loyalty_program_settings initialized")
    except Exception as e:
        print(f"  [ERROR] loyalty_program_settings: {e}")
    
    try:
        ReferralProgramSettings.get_settings()
        print("  [OK] referral_program_settings initialized")
    except Exception as e:
        print(f"  [ERROR] referral_program_settings: {e}")
    
    try:
        TaxSettings.get_settings()
        print("  [OK] tax_settings initialized")
    except Exception as e:
        print(f"  [ERROR] tax_settings: {e}")
    
    disconnect()
except Exception as e:
    print(f"  [WARNING] Settings initialization failed: {e}")

# List all collections in database
print(f"\nAll collections in database '{MONGODB_DB}':")
try:
    all_collections = db.list_collection_names()
    if all_collections:
        for coll in sorted(all_collections):
            count = db[coll].count_documents({})
            print(f"  - {coll}: {count} document(s)")
    else:
        print("  (no collections found)")
except Exception as e:
    print(f"  [ERROR] Could not list collections: {e}")

client.close()
print("\nDisconnected from MongoDB.")
