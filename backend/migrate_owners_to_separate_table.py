"""
Migration script to move owners from managers collection to owners collection
This script will:
1. Find all managers with role='owner'
2. Create corresponding Owner documents
3. Optionally delete the owner records from managers collection
"""
import os
import sys
from mongoengine import connect
from models import Manager, Owner
from utils.auth import hash_password
from datetime import datetime

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

def migrate_owners():
    """Migrate owners from managers collection to owners collection"""
    try:
        # Find all managers with role='owner'
        owner_managers = Manager.objects(role='owner')
        count = owner_managers.count()
        
        print(f"\n[INFO] Found {count} owner(s) in managers collection")
        
        if count == 0:
            print("[INFO] No owners to migrate")
            return True
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for manager in owner_managers:
            try:
                # Check if owner already exists in owners collection
                existing_owner = Owner.objects(email=manager.email).first()
                if existing_owner:
                    print(f"[SKIP] Owner with email {manager.email} already exists in owners collection")
                    skipped += 1
                    continue
                
                # Create new Owner document
                owner = Owner(
                    first_name=manager.first_name,
                    last_name=manager.last_name,
                    email=manager.email,
                    mobile=manager.mobile,
                    salon=manager.salon,
                    password_hash=manager.password_hash,
                    is_active=manager.is_active,
                    status=manager.status,
                    permissions=manager.permissions if hasattr(manager, 'permissions') else [],
                    created_at=manager.created_at if manager.created_at else datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                owner.save()
                
                print(f"[OK] Migrated owner: {owner.first_name} {owner.last_name} ({owner.email})")
                migrated += 1
                
            except Exception as e:
                print(f"[ERROR] Failed to migrate owner {manager.email}: {e}")
                errors += 1
                import traceback
                traceback.print_exc()
        
        print(f"\n[SUMMARY]")
        print(f"  - Migrated: {migrated}")
        print(f"  - Skipped: {skipped}")
        print(f"  - Errors: {errors}")
        
        if migrated > 0:
            print(f"\n[INFO] {migrated} owner(s) successfully migrated to owners collection")
            print("[INFO] You can now delete owner records from managers collection if desired")
            print("[INFO] To delete, run this script with --delete flag (not implemented for safety)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 80)
    print("Migrating Owners from managers collection to owners collection")
    print("=" * 80)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    success = migrate_owners()
    
    if success:
        print("\n[OK] Migration completed!")
    else:
        print("\n[ERROR] Migration failed")
        sys.exit(1)

