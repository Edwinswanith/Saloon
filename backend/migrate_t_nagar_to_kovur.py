"""
Migration script to replace T. Nagar branch with Kovur branch
This script will:
1. Find all documents referencing T. Nagar branch
2. Update them to reference Kovur branch
3. Delete the T. Nagar branch
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import (
    Branch, Customer, Staff, Manager, Bill, Appointment, Expense, Lead,
    Feedback, MissedEnquiry, ServiceRecoveryCase, WhatsAppMessage,
    DiscountApprovalRequest, StaffAttendance, Asset, CashTransaction,
    Order, Membership, PrepaidPackage, Product, Package, Service,
    Supplier, StaffLeave, StaffTempAssignment
)
from datetime import datetime, timezone

# MongoDB connection - use same as app.py
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')

def build_connection_uri(base_uri, db_name):
    """Build connection URI with database name"""
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
    
    if f'/{db_name}' not in base_uri:
        if '?' in base_uri:
            base_uri = base_uri.replace('?', f'/{db_name}?')
        else:
            base_uri = f"{base_uri}/{db_name}"
    
    if 'retryWrites' not in base_uri:
        separator = '&' if '?' in base_uri else '?'
        base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
    
    return base_uri

def migrate_t_nagar_to_kovur():
    """Migrate all T. Nagar references to Kovur"""
    try:
        print("Connecting to MongoDB...")
        base_uri = build_connection_uri(MONGO_URI, MONGODB_DB)
        connect(host=base_uri, alias='default', db=MONGODB_DB)
        print("Connected successfully!")
        
        # Find T. Nagar and Kovur branches
        t_nagar_branch = Branch.objects(name="T. Nagar").first()
        kovur_branch = Branch.objects(name="Kovur").first()
        
        if not t_nagar_branch:
            print("ERROR: T. Nagar branch not found!")
            return False
        
        if not kovur_branch:
            print("ERROR: Kovur branch not found!")
            return False
        
        print(f"\nT. Nagar branch ID: {t_nagar_branch.id}")
        print(f"Kovur branch ID: {kovur_branch.id}")
        print("\nStarting migration...")
        
        # Collections to update (based on models.py)
        collections_to_update = [
            ('Customer', Customer, 'customers'),
            ('Staff', Staff, 'staffs'),
            ('Manager', Manager, 'managers'),
            ('Product', Product, 'products'),
            ('Package', Package, 'packages'),
            ('Service', Service, 'services'),
            ('PrepaidPackage', PrepaidPackage, 'prepaid_packages'),
            ('Membership', Membership, 'memberships'),
            ('Bill', Bill, 'bills'),
            ('Appointment', Appointment, 'appointments'),
            ('Expense', Expense, 'expenses'),
            ('Supplier', Supplier, 'suppliers'),
            ('Order', Order, 'orders'),
            ('Lead', Lead, 'leads'),
            ('Feedback', Feedback, 'feedbacks'),
            ('MissedEnquiry', MissedEnquiry, 'missed_enquiries'),
            ('ServiceRecoveryCase', ServiceRecoveryCase, 'service_recovery_cases'),
            ('WhatsAppMessage', WhatsAppMessage, 'whatsapp_messages'),
            ('DiscountApprovalRequest', DiscountApprovalRequest, 'discount_approval_requests'),
            ('StaffAttendance', StaffAttendance, 'staff_attendance'),
            ('Asset', Asset, 'assets'),
            ('CashTransaction', CashTransaction, 'cash_transactions'),
            ('StaffLeave', StaffLeave, 'staff_leaves'),
        ]
        
        # Special handling for StaffTempAssignment (has original_branch and temp_branch)
        print("\nUpdating StaffTempAssignment (special handling for original_branch and temp_branch)...")
        try:
            # Update original_branch
            count_original = StaffTempAssignment.objects(original_branch=t_nagar_branch.id).count()
            if count_original > 0:
                updated = StaffTempAssignment.objects(original_branch=t_nagar_branch.id).update(
                    set__original_branch=kovur_branch.id,
                    set__updated_at=datetime.now(timezone.utc)
                )
                print(f"  [OK] Updated {updated} documents (original_branch)")
                total_updated += updated
            
            # Update temp_branch
            count_temp = StaffTempAssignment.objects(temp_branch=t_nagar_branch.id).count()
            if count_temp > 0:
                updated = StaffTempAssignment.objects(temp_branch=t_nagar_branch.id).update(
                    set__temp_branch=kovur_branch.id,
                    set__updated_at=datetime.now(timezone.utc)
                )
                print(f"  [OK] Updated {updated} documents (temp_branch)")
                total_updated += updated
            
            if count_original == 0 and count_temp == 0:
                print("  No documents to update")
        except Exception as e:
            print(f"  [ERROR] Error updating StaffTempAssignment: {e}")
        
        total_updated = 0
        
        for model_name, model_class, collection_name in collections_to_update:
            try:
                # Count documents with T. Nagar branch
                count = model_class.objects(branch=t_nagar_branch.id).count()
                
                if count > 0:
                    print(f"\nUpdating {model_name} ({collection_name}): {count} documents")
                    # Update all documents
                    updated = model_class.objects(branch=t_nagar_branch.id).update(
                        set__branch=kovur_branch.id,
                        set__updated_at=datetime.now(timezone.utc)
                    )
                    print(f"  [OK] Updated {updated} documents")
                    total_updated += updated
                else:
                    print(f"\n{model_name} ({collection_name}): No documents to update")
            except Exception as e:
                print(f"  [ERROR] Error updating {model_name}: {e}")
        
        # Delete T. Nagar branch
        print(f"\n\nDeleting T. Nagar branch...")
        t_nagar_branch.delete()
        print("[OK] T. Nagar branch deleted")
        
        print("\n" + "="*50)
        print(f"Migration completed successfully!")
        print(f"Total documents updated: {total_updated}")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    
    print("="*50)
    print("T. Nagar to Kovur Migration Script")
    print("="*50)
    print("\nThis script will:")
    print("1. Update all references from T. Nagar to Kovur")
    print("2. Delete the T. Nagar branch")
    print("\nDatabase:", MONGODB_DB)
    print("\nWARNING: This operation cannot be undone!")
    print("Make sure you have a backup of your database before running this script!")
    
    # Skip interactive prompt if --yes flag is provided
    if '--yes' not in sys.argv:
        print("\nPress Ctrl+C to cancel, or Enter to continue...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\nMigration cancelled.")
            sys.exit(0)
    
    success = migrate_t_nagar_to_kovur()
    if success:
        print("\nMigration completed successfully!")
    else:
        print("\nMigration failed. Please check the errors above.")
        sys.exit(1)

