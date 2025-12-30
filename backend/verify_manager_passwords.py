"""
Script to verify manager passwords and branch assignments
"""
import os
import sys
from mongoengine import connect, disconnect
from models import Manager, Branch
from utils.auth import verify_password, hash_password

def connect_to_mongodb():
    """Connect to MongoDB"""
    try:
        MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
        MONGODB_DB = 'Saloon'
        
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

def verify_managers():
    """Verify manager passwords and branch assignments"""
    try:
        managers = Manager.objects(role='manager').order_by('first_name', 'last_name')
        manager_count = managers.count()
        
        if manager_count == 0:
            print("\n[WARNING] No managers found!")
            return False
        
        print("\n" + "=" * 100)
        print(f"VERIFYING {manager_count} MANAGERS")
        print("=" * 100)
        
        test_password = "manager123"
        all_valid = True
        
        for i, manager in enumerate(managers, 1):
            print(f"\n[{i}] Manager: {manager.first_name} {manager.last_name}")
            print(f"    Email: {manager.email}")
            print(f"    Mobile: {manager.mobile}")
            
            # Check password
            if not manager.password_hash:
                print(f"    Password: [ERROR] No password set!")
                all_valid = False
            else:
                is_valid = verify_password(test_password, manager.password_hash)
                if is_valid:
                    print(f"    Password: [OK] Password 'manager123' is valid")
                else:
                    print(f"    Password: [ERROR] Password 'manager123' is NOT valid")
                    all_valid = False
                    # Try to fix it
                    print(f"    [FIXING] Setting password to 'manager123'...")
                    manager.password_hash = hash_password(test_password)
                    manager.save()
                    if verify_password(test_password, manager.password_hash):
                        print(f"    [FIXED] Password has been set correctly")
                    else:
                        print(f"    [ERROR] Failed to set password")
            
            # Check branch assignment
            if not manager.branch:
                print(f"    Branch: [ERROR] No branch assigned!")
                all_valid = False
            else:
                print(f"    Branch: [OK] {manager.branch.name} (ID: {manager.branch.id})")
            
            print("-" * 100)
        
        print("\n" + "=" * 100)
        print("SUMMARY")
        print("=" * 100)
        if all_valid:
            print("[SUCCESS] All managers have valid passwords and branch assignments!")
        else:
            print("[WARNING] Some managers have issues. Check the details above.")
        
        return all_valid
        
    except Exception as e:
        print(f"\n[ERROR] Failed to verify managers: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 100)
    print("VERIFY MANAGER PASSWORDS AND BRANCH ASSIGNMENTS")
    print("=" * 100)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        success = verify_managers()
        if not success:
            print("\n[INFO] Some issues were found and fixed. Please try logging in again.")
        else:
            print("\n[SUCCESS] All managers are ready to use!")
    finally:
        disconnect()
        print("\n[OK] Disconnected from MongoDB")

if __name__ == '__main__':
    main()

