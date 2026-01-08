"""
Script to list all owners in MongoDB
Note: Owners are stored in the 'managers' collection with role='owner'
"""
import os
import sys
from mongoengine import connect
from models import Owner

# MongoDB connection - using the same connection string as app.py
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon')

def connect_to_mongodb():
    """Connect to MongoDB using the same logic as app.py"""
    try:
        # Parse the connection string
        base_uri = MONGO_URI
        parts = base_uri.split('@')
        if len(parts) == 2:
            credentials = parts[0]
            host_and_params = parts[1]
            host = host_and_params.split('/')[0]
            params = '?' + host_and_params.split('?', 1)[1] if '?' in host_and_params else ''
            base_uri = f'{credentials}@{host}{params}'
            base_uri = base_uri.replace('?', f'/{MONGODB_DB}?') if '?' in base_uri else f'{base_uri}/{MONGODB_DB}'
            separator = '&' if '?' in base_uri else '?'
            base_uri = f'{base_uri}{separator}retryWrites=true&w=majority'
        else:
            # If format is different, just append the database name
            if '/' not in base_uri or base_uri.endswith('/'):
                base_uri = f'{base_uri}{MONGODB_DB}'
            else:
                base_uri = f'{base_uri}/{MONGODB_DB}'
        
        connect(host=base_uri, alias='default', db=MONGODB_DB)
        print(f"[OK] Connected to MongoDB: {MONGODB_DB}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        return False

def list_all_owners():
    """List all owners in the managers collection"""
    try:
        # Get all owners from owners collection
        owners = Owner.objects()
        count = owners.count()
        
        print("\n" + "=" * 80)
        print(f"OWNERS IN MONGODB (Collection: 'owners')")
        print("=" * 80)
        print(f"Total Owners Found: {count}")
        print("=" * 80)
        
        if count == 0:
            print("\n[WARNING] No owners found in the database!")
            print("Run: python create_dummy_owner.py to create an owner")
        else:
            for i, owner in enumerate(owners, 1):
                print(f"\nOwner #{i}:")
                print(f"  ID: {owner.id}")
                print(f"  Name: {owner.first_name} {owner.last_name or ''}")
                print(f"  Email: {owner.email}")
                print(f"  Mobile: {owner.mobile}")
                print(f"  Saloon: {owner.salon}")
                print(f"  Is Active: {owner.is_active}")
                print(f"  Status: {owner.status}")
                print(f"  Has Password: {'Yes' if owner.password_hash else 'No'}")
                print(f"  Created At: {owner.created_at}")
                print(f"  Updated At: {owner.updated_at}")
        
        print("\n" + "=" * 80)
        print("NOTE: Owners are now stored in the separate 'owners' collection")
        print("=" * 80)
        
        return owners
        
    except Exception as e:
        print(f"[ERROR] Failed to list owners: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("=" * 80)
    print("Listing All Owners in MongoDB")
    print("=" * 80)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    owners = list_all_owners()
    
    if owners is not None:
        print("\n[OK] Script completed successfully!")
    else:
        print("\n[ERROR] Script failed")
        sys.exit(1)

