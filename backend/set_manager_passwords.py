"""
Script to set passwords for all managers in MongoDB
This script will set secure passwords for each manager and store them hashed in MongoDB
"""

import os
import sys
from datetime import datetime, timezone
from mongoengine import connect, disconnect
from models import Manager
from utils.auth import hash_password, verify_password

def connect_to_mongodb():
    """Connect to MongoDB using the same logic as app.py"""
    try:
        # Get MongoDB URI from environment or use default (same as app.py)
        MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
        MONGODB_DB = 'Saloon'
        
        # Build connection URI with database name (same logic as app.py)
        base_uri = MONGODB_URI
        
        # If URI contains a database path, remove it (we'll add our own)
        if '@' in base_uri:
            parts = base_uri.split('@')
            if len(parts) == 2:
                credentials = parts[0]
                host_and_params = parts[1]
                
                # Remove database name from host part if present
                if '/' in host_and_params:
                    host = host_and_params.split('/')[0]
                    # Keep query parameters if they exist
                    if '?' in host_and_params:
                        params = '?' + host_and_params.split('?', 1)[1]
                    else:
                        params = ''
                    base_uri = f"{credentials}@{host}{params}"
        
        # Add database name to URI if not present
        if f'/{MONGODB_DB}' not in base_uri:
            if '?' in base_uri:
                base_uri = base_uri.replace('?', f'/{MONGODB_DB}?')
            else:
                base_uri = f"{base_uri}/{MONGODB_DB}"
        
        # Add retry parameters if not present
        if 'retryWrites' not in base_uri:
            separator = '&' if '?' in base_uri else '?'
            base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
        
        # Connect with increased timeouts to handle SSL handshake
        connect(host=base_uri, alias='default', db=MONGODB_DB,
                connectTimeoutMS=30000,
                serverSelectionTimeoutMS=30000)
        
        print(f"[OK] Connected to MongoDB: {MONGODB_DB}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        return False

def set_manager_passwords():
    """Set passwords for all managers"""
    try:
        # Get all managers (role='manager', not owners)
        managers = Manager.objects(role='manager').order_by('first_name', 'last_name')
        manager_count = managers.count()
        
        if manager_count == 0:
            print("\n[WARNING] No managers found in the database!")
            print("Make sure managers exist before running this script.")
            return False
        
        print("\n" + "=" * 80)
        print(f"SETTING PASSWORDS FOR {manager_count} MANAGERS")
        print("=" * 80)
        
        # Default password pattern: manager1, manager2, etc.
        # Or use a common password for all: manager123
        use_common_password = True  # Set to False to use manager1, manager2, etc.
        common_password = "manager123"
        
        updated_count = 0
        skipped_count = 0
        
        for i, manager in enumerate(managers, 1):
            # Determine password
            if use_common_password:
                password = common_password
            else:
                password = f"manager{i}"
            
            # Check if manager already has a password
            has_existing_password = bool(manager.password_hash)
            
            # Hash the password
            password_hash = hash_password(password)
            
            # Update manager
            manager.password_hash = password_hash
            manager.updated_at = datetime.now(timezone.utc)
            manager.save()
            
            # Verify the password was set correctly
            if verify_password(password, password_hash):
                updated_count += 1
                status = "[OK]"
                existing_msg = " (updated existing)" if has_existing_password else " (new)"
            else:
                status = "[ERROR]"
                existing_msg = ""
            
            # Display manager info
            branch_name = manager.branch.name if manager.branch else "No Branch"
            print(f"\n{status} Manager #{i}: {manager.first_name} {manager.last_name}{existing_msg}")
            print(f"   Email: {manager.email}")
            print(f"   Mobile: {manager.mobile}")
            print(f"   Branch: {branch_name}")
            print(f"   Password: {password}")
            
            if not verify_password(password, password_hash):
                print(f"   [WARNING] Password verification failed!")
                skipped_count += 1
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Managers: {manager_count}")
        print(f"Passwords Set: {updated_count}")
        if skipped_count > 0:
            print(f"Failed: {skipped_count}")
        
        if use_common_password:
            print(f"\nAll managers can log in with password: {common_password}")
        else:
            print(f"\nManagers can log in with passwords: manager1, manager2, ..., manager{manager_count}")
        
        print("\n" + "=" * 80)
        print("LOGIN CREDENTIALS")
        print("=" * 80)
        print("\nManager Login Credentials:")
        print("-" * 80)
        for i, manager in enumerate(managers, 1):
            password = common_password if use_common_password else f"manager{i}"
            branch_name = manager.branch.name if manager.branch else "No Branch"
            print(f"{i}. {manager.first_name} {manager.last_name}")
            print(f"   Email: {manager.email}")
            print(f"   Password: {password}")
            print(f"   Branch: {branch_name}")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to set manager passwords: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("SET MANAGER PASSWORDS")
    print("=" * 80)
    
    # Connect to MongoDB
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        # Set passwords
        success = set_manager_passwords()
        
        if success:
            print("\n[SUCCESS] Manager passwords have been set successfully!")
        else:
            print("\n[FAILED] Some errors occurred while setting passwords.")
            sys.exit(1)
            
    finally:
        # Disconnect from MongoDB
        disconnect()
        print("\n[OK] Disconnected from MongoDB")

if __name__ == '__main__':
    main()

