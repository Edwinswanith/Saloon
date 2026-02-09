"""
Script to generate a comprehensive login credentials table
"""
import os
import sys
from datetime import datetime, timezone
from mongoengine import connect, disconnect
from models import Staff, Manager, Branch
from utils.auth import verify_password

def connect_to_mongodb():
    """Connect to MongoDB"""
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
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        return False

def sanitize_branch_name(branch_name):
    """Sanitize branch name for password generation"""
    if not branch_name:
        return 'Unknown'
    sanitized = ''.join(c for c in branch_name if c.isalnum())
    return sanitized if sanitized else 'Unknown'

def find_password(user, branch_name_sanitized, user_type, index):
    """Find the password by testing common patterns"""
    if not user.password_hash:
        return "NOT SET"
    
    # Generate possible passwords
    test_passwords = []
    
    if user_type == 'staff':
        test_passwords.append(f"staff{branch_name_sanitized}{index}")
        test_passwords.extend([
            "staff123",
            "staff1",
            "password"
        ])
    else:  # manager
        test_passwords.append(f"manager{branch_name_sanitized}")
        test_passwords.append(f"manager{branch_name_sanitized}{index}")
        test_passwords.extend([
            "manager123",
            "manager1",
            "password"
        ])
    
    # Test each password
    for pwd in test_passwords:
        if verify_password(pwd, user.password_hash):
            return pwd
    
    return "UNKNOWN"

def generate_table():
    """Generate login credentials table"""
    try:
        # Get all branches
        branches = Branch.objects(is_active=True).order_by('name')
        branch_map = {str(branch.id): branch.name for branch in branches}
        
        all_credentials = []
        
        # Process Staff
        staff_list = Staff.objects(status='active').order_by('branch', 'first_name')
        for staff in staff_list:
            branch_id = str(staff.branch.id) if staff.branch else None
            branch_name = branch_map.get(branch_id, "No Branch")
            branch_sanitized = sanitize_branch_name(branch_name)
            
            # Count staff in same branch to get index
            same_branch_staff = Staff.objects(branch=staff.branch, status='active').order_by('first_name')
            index = list(same_branch_staff).index(staff) + 1
            
            password = find_password(staff, branch_sanitized, 'staff', index)
            
            all_credentials.append({
                'user_type': 'Staff',
                'name': f"{staff.first_name} {staff.last_name or ''}".strip(),
                'username': staff.mobile,
                'branch': branch_name,
                'password': password
            })
        
        # Process Managers
        manager_list = Manager.objects(is_active=True, role='manager').order_by('branch', 'first_name')
        for manager in manager_list:
            branch_id = str(manager.branch.id) if manager.branch else None
            branch_name = branch_map.get(branch_id, "No Branch")
            branch_sanitized = sanitize_branch_name(branch_name)
            
            # Count managers in same branch to get index
            same_branch_managers = Manager.objects(branch=manager.branch, is_active=True, role='manager').order_by('first_name')
            index = list(same_branch_managers).index(manager) + 1
            
            password = find_password(manager, branch_sanitized, 'manager', index)
            
            all_credentials.append({
                'user_type': 'Manager',
                'name': f"{manager.first_name} {manager.last_name or ''}".strip(),
                'username': manager.email,
                'branch': branch_name,
                'password': password
            })
        
        # Sort by branch, then user type, then name
        all_credentials.sort(key=lambda x: (x['branch'], x['user_type'], x['name']))
        
        # Print table
        print("\n" + "=" * 120)
        print("LOGIN AUTHENTICATION CREDENTIALS TABLE")
        print("=" * 120)
        print(f"{'User Type':<12} {'Name':<25} {'Username':<30} {'Branch':<20} {'Password':<25}")
        print("-" * 120)
        
        for cred in all_credentials:
            print(f"{cred['user_type']:<12} {cred['name']:<25} {cred['username']:<30} {cred['branch']:<20} {cred['password']:<25}")
        
        print("=" * 120)
        print(f"\nTotal Users: {len(all_credentials)}")
        print(f"  - Staff: {sum(1 for c in all_credentials if c['user_type'] == 'Staff')}")
        print(f"  - Managers: {sum(1 for c in all_credentials if c['user_type'] == 'Manager')}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to generate table: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        generate_table()
    finally:
        disconnect()

if __name__ == '__main__':
    main()

