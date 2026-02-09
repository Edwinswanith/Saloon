"""
Script to update DLF branch manager password to managerDLF
"""
import os
import sys
from datetime import datetime, timezone
from mongoengine import connect, disconnect
from models import Manager, Branch
from utils.auth import hash_password, verify_password

def connect_to_mongodb():
    """Connect to MongoDB using the same logic as app.py"""
    try:
        MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
        MONGODB_DB = 'Saloon_prod'
        
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
        
        connect(host=base_uri, alias='default', db=MONGODB_DB,
                connectTimeoutMS=30000,
                serverSelectionTimeoutMS=30000)
        
        print(f"[OK] Connected to MongoDB: {MONGODB_DB}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        return False

def update_dlf_password():
    """Update DLF branch manager password to managerDLF"""
    try:
        # Find DLF branch
        dlf_branch = Branch.objects(name='DLF').first()
        if not dlf_branch:
            print("[ERROR] DLF branch not found!")
            return False
        
        print(f"[OK] Found DLF branch: {dlf_branch.id}")
        
        # Find manager for DLF branch
        manager = Manager.objects(branch=dlf_branch).first()
        if not manager:
            print("[ERROR] No manager found for DLF branch!")
            return False
        
        print(f"[OK] Found manager: {manager.first_name} {manager.last_name}")
        print(f"     Email: {manager.email}")
        print(f"     Current password hash: {manager.password_hash[:20]}...")
        
        # Set new password
        new_password = "managerDLF"
        new_hash = hash_password(new_password)
        
        # Update manager
        manager.password_hash = new_hash
        manager.updated_at = datetime.now(timezone.utc)
        manager.save()
        
        # Verify password
        if verify_password(new_password, manager.password_hash):
            print(f"[SUCCESS] Password updated successfully!")
            print(f"     New password: {new_password}")
            print(f"     Verification: PASSED")
            return True
        else:
            print(f"[ERROR] Password verification failed!")
            return False
        
    except Exception as e:
        print(f"\n[ERROR] Failed to update password: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("UPDATE DLF MANAGER PASSWORD")
    print("=" * 80)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        success = update_dlf_password()
        if success:
            print("\n[SUCCESS] DLF manager password has been updated to 'managerDLF'!")
        else:
            print("\n[FAILED] Password update failed.")
            sys.exit(1)
    finally:
        disconnect()
        print("\n[OK] Disconnected from MongoDB")

if __name__ == '__main__':
    main()

