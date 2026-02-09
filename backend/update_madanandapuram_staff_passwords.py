"""
Script to update Madanandapuram branch staff passwords
"""
import os
import sys
from datetime import datetime, timezone
from mongoengine import connect, disconnect
from models import Staff, Branch
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
    sanitized = ''.join(c for c in branch_name if c.isalnum())
    return sanitized if sanitized else 'Unknown'

def update_staff_passwords():
    """Update Madanandapuram branch staff passwords"""
    try:
        # Find Madanandapuram branch
        branch = Branch.objects(name='Madanandapuram').first()
        if not branch:
            print("[ERROR] Madanandapuram branch not found!")
            return False
        
        print(f"[OK] Found branch: {branch.name}")
        
        # Find all staff for this branch
        staff_list = Staff.objects(branch=branch).order_by('first_name')
        staff_count = staff_list.count()
        
        if staff_count == 0:
            print("[WARNING] No staff members found for Madanandapuram branch!")
            return False
        
        print(f"\n[OK] Found {staff_count} staff member(s)")
        print("=" * 80)
        
        # Sanitize branch name
        branch_name_sanitized = sanitize_branch_name(branch.name)
        
        print("\nUPDATING PASSWORDS:")
        print("=" * 80)
        
        for idx, staff in enumerate(staff_list, 1):
            full_name = f"{staff.first_name} {staff.last_name or ''}".strip()
            password = f"staff{branch_name_sanitized}{idx}"
            
            # Hash and update password
            staff.password_hash = hash_password(password)
            staff.updated_at = datetime.now(timezone.utc)
            staff.save()
            
            # Verify password
            if verify_password(password, staff.password_hash):
                print(f"\n[OK] {full_name}")
                print(f"     Mobile: {staff.mobile}")
                print(f"     Password: {password}")
                print(f"     Verification: PASSED")
            else:
                print(f"\n[ERROR] {full_name}")
                print(f"     Password verification failed!")
        
        print("\n" + "=" * 80)
        print("LOGIN CREDENTIALS:")
        print("=" * 80)
        
        for idx, staff in enumerate(staff_list, 1):
            full_name = f"{staff.first_name} {staff.last_name or ''}".strip()
            password = f"staff{branch_name_sanitized}{idx}"
            print(f"\nStaff #{idx}: {full_name}")
            print(f"  Mobile: {staff.mobile}")
            print(f"  Password: {password}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to update passwords: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("UPDATE MADANANDAPURAM BRANCH STAFF PASSWORDS")
    print("=" * 80)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        success = update_staff_passwords()
        if success:
            print("\n[SUCCESS] Staff passwords have been updated!")
        else:
            print("\n[FAILED] Password update failed.")
            sys.exit(1)
    finally:
        disconnect()
        print("\n[OK] Disconnected from MongoDB")

if __name__ == '__main__':
    main()

