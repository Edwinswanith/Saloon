"""
Script to create a dummy owner with email and password in MongoDB
"""
import os
import sys
from mongoengine import connect
from models import Owner, Branch
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

def create_dummy_owner():
    """Create a dummy owner with email and password"""
    try:
        # Check if owner already exists
        existing_owner = Owner.objects(email='owner@salon.com').first()
        if existing_owner:
            print(f"[OK] Owner already exists with email: owner@salon.com")
            print(f"  - Name: {existing_owner.first_name} {existing_owner.last_name}")
            print(f"  - Mobile: {existing_owner.mobile}")
            print(f"  - ID: {existing_owner.id}")
            
            # Update password if it doesn't exist
            if not existing_owner.password_hash:
                password = 'owner123'
                existing_owner.password_hash = hash_password(password)
                existing_owner.updated_at = datetime.utcnow()
                existing_owner.save()
                print(f"[OK] Password set for existing owner: {password}")
            else:
                print(f"  - Password already set")
            return existing_owner
        
        # Get first branch (or create a default one if none exists)
        branch = Branch.objects().first()
        if not branch:
            print("[WARNING] No branches found. Creating a default branch...")
            branch = Branch(
                name='T. Nagar',
                city='Chennai',
                address='123 Main Street',
                phone='9876543210',
                email='info@salon.com',
                is_active=True
            )
            branch.save()
            print(f"[OK] Created default branch: {branch.name}")
        
        # Create new owner
        password = 'owner123'
        owner = Owner(
            first_name='Saloon',
            last_name='Owner',
            email='owner@salon.com',
            mobile='9999999999',
            salon='Hair Studio',
            password_hash=hash_password(password),
            is_active=True,
            status='active'
        )
        owner.save()
        
        print(f"[OK] Created dummy owner successfully!")
        print(f"  - Name: {owner.first_name} {owner.last_name}")
        print(f"  - Email: {owner.email}")
        print(f"  - Mobile: {owner.mobile}")
        print(f"  - Password: {password}")
        print(f"  - ID: {owner.id}")
        
        return owner
        
    except Exception as e:
        print(f"[ERROR] Failed to create owner: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("=" * 60)
    print("Creating Dummy Owner with Email and Password")
    print("=" * 60)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    owner = create_dummy_owner()
    
    if owner:
        print("\n" + "=" * 60)
        print("SUCCESS! Owner credentials:")
        print("=" * 60)
        print(f"Email: owner@salon.com")
        print(f"Password: owner123")
        print("=" * 60)
    else:
        print("\n[ERROR] Failed to create owner")
        sys.exit(1)

