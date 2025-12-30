"""
Script to reduce staff count per branch to 1 staff member
This will keep only 1 staff member per branch and delete the rest
"""
import os
import sys
from datetime import datetime
from mongoengine import connect, disconnect
from models import Staff, Branch

def connect_to_mongodb():
    """Connect to MongoDB using the same logic as app.py"""
    try:
        # Get MongoDB URI from environment or use default
        MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
        MONGODB_DB = 'Saloon'
        
        # Build connection URI with database name
        base_uri = MONGODB_URI
        
        # If URI contains a database path, remove it
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
        
        # Connect with increased timeouts
        connect(host=base_uri, alias='default', db=MONGODB_DB,
                connectTimeoutMS=30000,
                serverSelectionTimeoutMS=30000)
        
        print(f"[OK] Connected to MongoDB: {MONGODB_DB}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        return False

def reduce_staff_per_branch():
    """Reduce staff count to 1 per branch"""
    try:
        branches = Branch.objects().order_by('name')
        total_branches = branches.count()
        
        if total_branches == 0:
            print("\n[WARNING] No branches found in the database!")
            return False
        
        print("\n" + "=" * 80)
        print(f"REDUCING STAFF COUNT PER BRANCH")
        print("=" * 80)
        print(f"Total Branches: {total_branches}\n")
        
        total_deleted = 0
        total_kept = 0
        
        for branch in branches:
            print(f"\nProcessing Branch: {branch.name}")
            print("-" * 80)
            
            # Get all staff for this branch
            staff_members = Staff.objects(branch=branch).order_by('created_at')
            staff_count = staff_members.count()
            
            print(f"  Current staff count: {staff_count}")
            
            if staff_count == 0:
                print(f"  [WARNING] No staff found for this branch")
                continue
            
            if staff_count <= 1:
                print(f"  [OK] Already has 1 or fewer staff, skipping")
                total_kept += staff_count
                continue
            
            # Keep the first staff member (oldest by creation date)
            staff_to_keep = staff_members.first()
            print(f"  [KEEP] Keeping: {staff_to_keep.first_name} {staff_to_keep.last_name} ({staff_to_keep.mobile})")
            total_kept += 1
            
            # Delete the rest
            staff_to_delete = staff_members[1:]
            deleted_count = 0
            
            for staff in staff_to_delete:
                try:
                    staff_name = f"{staff.first_name} {staff.last_name} ({staff.mobile})"
                    staff.delete()
                    deleted_count += 1
                    print(f"  [DELETE] Deleted: {staff_name}")
                except Exception as e:
                    print(f"  [ERROR] Error deleting {staff.first_name} {staff.last_name}: {e}")
            
            total_deleted += deleted_count
            print(f"  Summary: Kept 1, Deleted {deleted_count}")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Branches Processed: {total_branches}")
        print(f"Total Staff Kept: {total_kept}")
        print(f"Total Staff Deleted: {total_deleted}")
        print(f"Final Staff Count: {total_kept} (1 per branch)")
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to reduce staff count: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("REDUCE STAFF COUNT PER BRANCH")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Keep only 1 staff member per branch (the oldest one)")
    print("  2. Delete all other staff members from each branch")
    print("\nWARNING: This action cannot be undone!")
    
    # Check for --yes flag to skip confirmation
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv
    
    if not skip_confirmation:
        try:
            response = input("\nDo you want to continue? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Operation cancelled.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled (no input available).")
            print("Use --yes flag to run without confirmation: python reduce_staff_count.py --yes")
            sys.exit(0)
    
    # Connect to MongoDB
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        # Reduce staff count
        success = reduce_staff_per_branch()
        
        if success:
            print("\n[SUCCESS] Staff count has been reduced successfully!")
        else:
            print("\n[FAILED] Some errors occurred while reducing staff count.")
            sys.exit(1)
            
    finally:
        # Disconnect from MongoDB
        disconnect()
        print("\n[OK] Disconnected from MongoDB")

if __name__ == '__main__':
    main()

