"""
Script to set passwords for ALL staff and managers in production database
This will update passwords for all users across all branches
"""
import os
import sys
from datetime import datetime, timezone
from mongoengine import connect, disconnect
from models import Staff, Manager, Branch
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

def sanitize_branch_name(branch_name):
    """Sanitize branch name for password generation"""
    if not branch_name:
        return 'Unknown'
    # Remove spaces and special characters, keep alphanumeric
    sanitized = ''.join(c for c in branch_name if c.isalnum())
    return sanitized if sanitized else 'Unknown'

def set_all_passwords():
    """Set passwords for all staff and managers across all branches"""
    try:
        # Get all active branches
        branches = Branch.objects(is_active=True).order_by('name')
        branch_count = branches.count()
        
        if branch_count == 0:
            print("[ERROR] No active branches found!")
            return False
        
        print(f"\n[OK] Found {branch_count} active branch(es)")
        print("=" * 80)
        
        all_staff_credentials = []
        all_manager_credentials = []
        
        for branch in branches:
            branch_name_sanitized = sanitize_branch_name(branch.name)
            print(f"\n{'=' * 80}")
            print(f"BRANCH: {branch.name}")
            print(f"{'=' * 80}")
            
            # Process Staff
            staff_list = Staff.objects(branch=branch, status='active').order_by('first_name')
            staff_count = staff_list.count()
            
            if staff_count > 0:
                print(f"\n[STAFF] Found {staff_count} staff member(s)")
                print("-" * 80)
                
                for idx, staff in enumerate(staff_list, 1):
                    full_name = f"{staff.first_name} {staff.last_name or ''}".strip()
                    password = f"staff{branch_name_sanitized}{idx}"
                    
                    # Hash and update password
                    staff.password_hash = hash_password(password)
                    staff.updated_at = datetime.now(timezone.utc)
                    staff.save()
                    
                    # Verify password
                    if verify_password(password, staff.password_hash):
                        status = "[OK]"
                    else:
                        status = "[ERROR]"
                    
                    print(f"{status} {full_name}")
                    print(f"     Mobile: {staff.mobile}")
                    print(f"     Email: {staff.email or 'N/A'}")
                    print(f"     Password: {password}")
                    
                    all_staff_credentials.append({
                        'branch': branch.name,
                        'name': full_name,
                        'mobile': staff.mobile,
                        'email': staff.email or '',
                        'password': password,
                        'status': 'OK' if status == '[OK]' else 'ERROR'
                    })
            else:
                print(f"\n[STAFF] No active staff members found")
            
            # Process Managers
            manager_list = Manager.objects(branch=branch, role='manager', is_active=True).order_by('first_name')
            manager_count = manager_list.count()
            
            if manager_count > 0:
                print(f"\n[MANAGER] Found {manager_count} manager(s)")
                print("-" * 80)
                
                for idx, manager in enumerate(manager_list, 1):
                    full_name = f"{manager.first_name} {manager.last_name or ''}".strip()
                    # For managers, use pattern: manager{BranchName} or manager{BranchName}{Number} if multiple
                    if manager_count > 1:
                        password = f"manager{branch_name_sanitized}{idx}"
                    else:
                        password = f"manager{branch_name_sanitized}"
                    
                    # Hash and update password
                    manager.password_hash = hash_password(password)
                    manager.updated_at = datetime.now(timezone.utc)
                    manager.save()
                    
                    # Verify password
                    if verify_password(password, manager.password_hash):
                        status = "[OK]"
                    else:
                        status = "[ERROR]"
                    
                    print(f"{status} {full_name}")
                    print(f"     Email: {manager.email}")
                    print(f"     Mobile: {manager.mobile}")
                    print(f"     Password: {password}")
                    
                    all_manager_credentials.append({
                        'branch': branch.name,
                        'name': full_name,
                        'email': manager.email,
                        'mobile': manager.mobile,
                        'password': password,
                        'status': 'OK' if status == '[OK]' else 'ERROR'
                    })
            else:
                print(f"\n[MANAGER] No active managers found")
        
        # Print summary
        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Branches Processed: {branch_count}")
        print(f"Total Staff Passwords Set: {len(all_staff_credentials)}")
        print(f"Total Manager Passwords Set: {len(all_manager_credentials)}")
        
        # Print all credentials
        print(f"\n{'=' * 80}")
        print("ALL LOGIN CREDENTIALS")
        print(f"{'=' * 80}")
        
        # Staff credentials
        if all_staff_credentials:
            print("\nSTAFF LOGIN CREDENTIALS:")
            print("-" * 80)
            for cred in all_staff_credentials:
                print(f"\nBranch: {cred['branch']}")
                print(f"  Name: {cred['name']}")
                print(f"  Mobile: {cred['mobile']}")
                print(f"  Email: {cred['email']}")
                print(f"  Password: {cred['password']}")
        
        # Manager credentials
        if all_manager_credentials:
            print("\n\nMANAGER LOGIN CREDENTIALS:")
            print("-" * 80)
            for cred in all_manager_credentials:
                print(f"\nBranch: {cred['branch']}")
                print(f"  Name: {cred['name']}")
                print(f"  Email: {cred['email']}")
                print(f"  Mobile: {cred['mobile']}")
                print(f"  Password: {cred['password']}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to set passwords: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("SET PASSWORDS FOR ALL STAFF AND MANAGERS (PRODUCTION)")
    print("=" * 80)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        success = set_all_passwords()
        if success:
            print("\n[SUCCESS] All passwords have been set successfully!")
        else:
            print("\n[FAILED] Some errors occurred while setting passwords.")
            sys.exit(1)
    finally:
        disconnect()
        print("\n[OK] Disconnected from MongoDB")

if __name__ == '__main__':
    main()

