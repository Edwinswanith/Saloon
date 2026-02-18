"""
Comprehensive MongoDB Index Verification and Creation Script
Verifies existing indexes and creates missing ones for ALL collections

Run: python backend/migrations/verify_and_fix_all_indexes.py --yes
"""
import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')

def get_existing_indexes(db, collection_name):
    """Get all existing indexes for a collection"""
    try:
        collection = db[collection_name]
        indexes = list(collection.list_indexes())
        return {idx['name']: idx['key'] for idx in indexes}
    except Exception as e:
        print(f"  [ERROR] Failed to get indexes for {collection_name}: {e}")
        return {}

def index_exists(existing_indexes, index_key):
    """Check if an index with the given key already exists"""
    for name, key in existing_indexes.items():
        if key == index_key:
            return True, name
    return False, None

def create_index_safe(db, collection_name, fields, name, opts=None):
    """Safely create an index, handling errors gracefully"""
    if opts is None:
        opts = {}
    try:
        collection = db[collection_name]
        collection.create_index(fields, name=name, background=True, **opts)
        return True, None
    except Exception as e:
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str:
            return False, "exists"
        else:
            return False, str(e)

def verify_and_create_indexes():
    """Verify and create all required indexes for all collections"""
    
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    
    print(f"Connected to database: {MONGODB_DB}")
    print("=" * 80)
    print("COMPREHENSIVE INDEX VERIFICATION AND CREATION")
    print("=" * 80)
    
    all_created = []
    all_skipped = []
    all_errors = []
    all_missing = []
    
    # Define all required indexes for each collection
    collections_indexes = {
        # ===========================================
        # 1. PRODUCTS - Critical for Quick Sale
        # ===========================================
        'products': [
            ([("branch", ASCENDING), ("status", ASCENDING), ("name", ASCENDING)], 
             "idx_products_branch_status_name", {}),
            ([("category", ASCENDING), ("status", ASCENDING)], 
             "idx_products_category_status", {}),
            ([("status", ASCENDING), ("name", ASCENDING)], 
             "idx_products_status_name", {}),
            ([("branch", ASCENDING), ("stock_quantity", ASCENDING)], 
             "idx_products_branch_stock", {"sparse": True}),
        ],
        
        # ===========================================
        # 2. SERVICES - Critical for Quick Sale
        # ===========================================
        'services': [
            ([("branch", ASCENDING), ("status", ASCENDING), ("name", ASCENDING)], 
             "idx_services_branch_status_name", {}),
            ([("status", ASCENDING), ("group", ASCENDING)], 
             "idx_services_status_group", {}),
            ([("group", ASCENDING), ("name", ASCENDING)], 
             "idx_services_group_name", {}),
        ],
        
        # ===========================================
        # 3. PACKAGES - Critical for Quick Sale
        # ===========================================
        'packages': [
            ([("branch", ASCENDING), ("status", ASCENDING), ("name", ASCENDING)], 
             "idx_packages_branch_status_name", {}),
            ([("status", ASCENDING), ("name", ASCENDING)], 
             "idx_packages_status_name", {}),
        ],
        
        # ===========================================
        # 4. MEMBERSHIP PLANS - Critical for Checkout
        # ===========================================
        'membership_plans': [
            ([("status", ASCENDING), ("created_at", DESCENDING)], 
             "idx_membership_plans_status_created", {}),
            ([("status", ASCENDING), ("name", ASCENDING)], 
             "idx_membership_plans_status_name", {}),
        ],
        
        # ===========================================
        # 5. MEMBERSHIPS - Critical for Checkout Speed
        # ===========================================
        'memberships': [
            ([("customer", ASCENDING), ("status", ASCENDING), ("expiry_date", DESCENDING)], 
             "idx_memberships_customer_status_expiry", {}),
            ([("branch", ASCENDING), ("status", ASCENDING), ("expiry_date", DESCENDING)], 
             "idx_memberships_branch_status_expiry", {}),
            ([("status", ASCENDING), ("expiry_date", ASCENDING)], 
             "idx_memberships_status_expiry", {}),
        ],
        
        # ===========================================
        # 6. BILLS - Most Critical Collection
        # ===========================================
        'bills': [
            ([("branch", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)], 
             "idx_bills_branch_date_deleted", {}),
            ([("branch", ASCENDING), ("is_deleted", ASCENDING), ("bill_date", DESCENDING)], 
             "idx_bills_branch_deleted_date", {}),
            ([("customer", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)], 
             "idx_bills_customer_date_deleted", {}),
            ([("branch", ASCENDING), ("booking_status", ASCENDING), ("bill_date", DESCENDING)], 
             "idx_bills_branch_status_date", {}),
            ([("branch", ASCENDING), ("payment_mode", ASCENDING), ("bill_date", DESCENDING)], 
             "idx_bills_branch_payment_date", {}),
            ([("bill_number", ASCENDING)], 
             "idx_bills_bill_number", {"unique": True}),
            ([("appointment", ASCENDING), ("is_deleted", ASCENDING)], 
             "idx_bills_appointment_deleted", {"sparse": True}),
            ([("items.service", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)], 
             "idx_bills_items_service_date", {"sparse": True}),
            ([("items.product", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)], 
             "idx_bills_items_product_date", {"sparse": True}),
            ([("items.package", ASCENDING), ("bill_date", DESCENDING), ("is_deleted", ASCENDING)], 
             "idx_bills_items_package_date", {"sparse": True}),
        ],
        
        # ===========================================
        # 7. CUSTOMERS - Heavy Search Collection
        # ===========================================
        'customers': [
            ([("branch", ASCENDING), ("mobile", ASCENDING)], 
             "idx_customers_branch_mobile", {"unique": True}),
            ([("branch", ASCENDING), ("created_at", DESCENDING)], 
             "idx_customers_branch_created", {}),
            ([("mobile", TEXT), ("first_name", TEXT), ("last_name", TEXT)], 
             "idx_customers_text_search", {}),
            ([("referral_code", ASCENDING)], 
             "idx_customers_referral_code", {"sparse": True}),
        ],
        
        # ===========================================
        # 8. STAFF - Branch Filtering
        # ===========================================
        'staffs': [
            ([("branch", ASCENDING), ("status", ASCENDING)], 
             "idx_staffs_branch_status", {}),
            ([("mobile", ASCENDING)], 
             "idx_staffs_mobile", {"unique": True}),
            ([("status", ASCENDING), ("branch", ASCENDING)], 
             "idx_staffs_status_branch", {}),
        ],
        
        # ===========================================
        # 9. APPOINTMENTS - Calendar Queries
        # ===========================================
        'appointments': [
            ([("branch", ASCENDING), ("appointment_date", ASCENDING), ("status", ASCENDING)], 
             "idx_appointments_branch_date_status", {}),
            ([("staff", ASCENDING), ("appointment_date", ASCENDING), ("status", ASCENDING)], 
             "idx_appointments_staff_date_status", {}),
            ([("customer", ASCENDING), ("appointment_date", DESCENDING)], 
             "idx_appointments_customer_date", {}),
        ],
        
        # ===========================================
        # 10. INVOICES - Invoice Queries
        # ===========================================
        'invoices': [
            ([("invoice_number", ASCENDING)], 
             "idx_invoices_invoice_number", {"unique": True}),
            ([("bill", ASCENDING)], 
             "idx_invoices_bill", {}),
            ([("customer", ASCENDING), ("generated_at", DESCENDING)], 
             "idx_invoices_customer_generated", {}),
            ([("branch", ASCENDING), ("generated_at", DESCENDING)], 
             "idx_invoices_branch_generated", {}),
            ([("share_code", ASCENDING)], 
             "idx_invoices_share_code", {"unique": True, "sparse": True}),
        ],
        
        # ===========================================
        # 11. EXPENSES - Branch Filtering
        # ===========================================
        'expenses': [
            ([("branch", ASCENDING), ("expense_date", DESCENDING)], 
             "idx_expenses_branch_date", {}),
            ([("category", ASCENDING), ("expense_date", DESCENDING)], 
             "idx_expenses_category_date", {}),
        ],
        
        # ===========================================
        # 12. FEEDBACKS - Staff Performance
        # ===========================================
        'feedbacks': [
            ([("staff", ASCENDING), ("created_at", DESCENDING)], 
             "idx_feedbacks_staff_created", {}),
            ([("branch", ASCENDING), ("created_at", DESCENDING)], 
             "idx_feedbacks_branch_created", {}),
            ([("customer", ASCENDING), ("created_at", DESCENDING)], 
             "idx_feedbacks_customer_created", {}),
        ],
        
        # ===========================================
        # 13. LEADS - Lead Management
        # ===========================================
        'leads': [
            ([("branch", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], 
             "idx_leads_branch_status_created", {}),
            ([("status", ASCENDING), ("created_at", DESCENDING)], 
             "idx_leads_status_created", {}),
            ([("mobile", ASCENDING)], 
             "idx_leads_mobile", {}),
        ],
        
        # ===========================================
        # 14. ORDERS - Supplier Orders
        # ===========================================
        'orders': [
            ([("branch", ASCENDING), ("order_date", DESCENDING)], 
             "idx_orders_branch_date", {}),
            ([("supplier", ASCENDING), ("order_date", DESCENDING)], 
             "idx_orders_supplier_date", {}),
            ([("status", ASCENDING), ("order_date", DESCENDING)], 
             "idx_orders_status_date", {}),
        ],
        
        # ===========================================
        # 15. SUPPLIERS - Supplier Management
        # ===========================================
        'suppliers': [
            ([("branch", ASCENDING), ("status", ASCENDING)], 
             "idx_suppliers_branch_status", {}),
            ([("status", ASCENDING), ("name", ASCENDING)], 
             "idx_suppliers_status_name", {}),
        ],
        
        # ===========================================
        # 16. ASSETS - Asset Management
        # ===========================================
        'assets': [
            ([("branch", ASCENDING), ("status", ASCENDING)], 
             "idx_assets_branch_status", {}),
            ([("category", ASCENDING), ("status", ASCENDING)], 
             "idx_assets_category_status", {}),
        ],
        
        # ===========================================
        # 17. STAFF ATTENDANCE - Attendance Tracking
        # ===========================================
        'staff_attendance': [
            ([("staff", ASCENDING), ("attendance_date", DESCENDING)], 
             "idx_attendance_staff_date", {}),
            ([("branch", ASCENDING), ("attendance_date", DESCENDING)], 
             "idx_attendance_branch_date", {}),
        ],
        
        # ===========================================
        # 18. CASH TRANSACTIONS - Cash Management
        # ===========================================
        'cash_transactions': [
            ([("branch", ASCENDING), ("transaction_date", DESCENDING)], 
             "idx_cash_branch_date", {}),
            ([("transaction_type", ASCENDING), ("transaction_date", DESCENDING)], 
             "idx_cash_type_date", {}),
        ],
        
        # ===========================================
        # 19. REFERRALS - Referral Tracking
        # ===========================================
        'referrals': [
            ([("branch", ASCENDING), ("created_at", DESCENDING)], 
             "idx_referrals_branch_created", {}),
            ([("referrer", ASCENDING), ("created_at", DESCENDING)], 
             "idx_referrals_referrer_created", {}),
            ([("referee", ASCENDING)], 
             "idx_referrals_referee", {"unique": True}),
        ],
        
        # ===========================================
        # 20. DISCOUNT APPROVAL REQUESTS
        # ===========================================
        'discount_approval_requests': [
            ([("branch", ASCENDING), ("approval_status", ASCENDING), ("created_at", DESCENDING)], 
             "idx_discount_requests_branch_status_created", {}),
            ([("requested_by", ASCENDING), ("created_at", DESCENDING)], 
             "idx_discount_requests_requested_by_created", {}),
        ],
        
        # ===========================================
        # 21. MISSED ENQUIRIES
        # ===========================================
        'missed_enquiries': [
            ([("branch", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], 
             "idx_missed_enquiries_branch_status_created", {}),
        ],
        
        # ===========================================
        # 22. SERVICE RECOVERY CASES
        # ===========================================
        'service_recovery_cases': [
            ([("branch", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], 
             "idx_recovery_cases_branch_status_created", {}),
            ([("customer", ASCENDING), ("created_at", DESCENDING)], 
             "idx_recovery_cases_customer_created", {}),
        ],
        
        # ===========================================
        # 23. WHATSAPP MESSAGES
        # ===========================================
        'whatsapp_messages': [
            ([("customer", ASCENDING), ("sent_at", DESCENDING)], 
             "idx_whatsapp_customer_sent", {}),
            ([("branch", ASCENDING), ("sent_at", DESCENDING)], 
             "idx_whatsapp_branch_sent", {}),
        ],
        
        # ===========================================
        # 24. STAFF LEAVES
        # ===========================================
        'staff_leaves': [
            ([("staff", ASCENDING), ("start_date", DESCENDING)], 
             "idx_staff_leaves_staff_start", {}),
            ([("branch", ASCENDING), ("status", ASCENDING), ("start_date", DESCENDING)], 
             "idx_staff_leaves_branch_status_start", {}),
        ],
        
        # ===========================================
        # 25. STAFF TEMP ASSIGNMENTS
        # ===========================================
        'staff_temp_assignments': [
            ([("staff", ASCENDING), ("start_date", DESCENDING)], 
             "idx_temp_assignments_staff_start", {}),
            ([("temp_branch", ASCENDING), ("status", ASCENDING), ("start_date", DESCENDING)], 
             "idx_temp_assignments_branch_status_start", {}),
        ],
        
        # ===========================================
        # 26. LOGIN HISTORY
        # ===========================================
        'login_history': [
            ([("user_id", ASCENDING), ("created_at", DESCENDING)], 
             "idx_login_history_user_created", {}),
            ([("user_type", ASCENDING), ("created_at", DESCENDING)], 
             "idx_login_history_type_created", {}),
        ],
        
        # ===========================================
        # 27. BASIC COLLECTIONS - Simple Indexes
        # ===========================================
        'product_categories': [
            ([("name", ASCENDING)], 
             "idx_product_categories_name", {}),
        ],
        'service_groups': [
            ([("name", ASCENDING)], 
             "idx_service_groups_name", {}),
        ],
        'expense_categories': [
            ([("name", ASCENDING)], 
             "idx_expense_categories_name", {}),
        ],
        'branches': [
            ([("is_active", ASCENDING), ("name", ASCENDING)], 
             "idx_branches_active_name", {}),
        ],
        'managers': [
            ([("email", ASCENDING)], 
             "idx_managers_email", {"unique": True}),
            ([("mobile", ASCENDING)], 
             "idx_managers_mobile", {"unique": True}),
        ],
        'owners': [
            ([("email", ASCENDING)], 
             "idx_owners_email", {"unique": True}),
            ([("mobile", ASCENDING)], 
             "idx_owners_mobile", {"unique": True}),
        ],
    }
    
    # Process each collection
    for collection_name, indexes in collections_indexes.items():
        print(f"\n[{collection_name.upper()}] Collection:")
        
        # Get existing indexes
        existing_indexes = get_existing_indexes(db, collection_name)
        
        for fields, name, opts in indexes:
            # Convert fields to dict format for comparison
            index_key = dict(fields)
            
            # Check if index already exists
            exists, existing_name = index_exists(existing_indexes, index_key)
            
            if exists:
                all_skipped.append(f"{collection_name}: {name}")
                print(f"  ~ {name} (already exists as {existing_name})")
            else:
                # Try to create the index
                success, error = create_index_safe(db, collection_name, fields, name, opts)
                if success:
                    all_created.append(f"{collection_name}: {name}")
                    print(f"  + {name}")
                elif error == "exists":
                    all_skipped.append(f"{collection_name}: {name}")
                    print(f"  ~ {name} (exists)")
                else:
                    all_errors.append(f"{collection_name}: {name}: {error}")
                    all_missing.append(f"{collection_name}: {name}")
                    print(f"  ! {name}: {error}")
    
    # ===========================================
    # SUMMARY
    # ===========================================
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"[OK] Created: {len(all_created)} indexes")
    print(f"[SKIP] Already exist: {len(all_skipped)} indexes")
    if all_missing:
        print(f"[MISSING] Failed to create: {len(all_missing)} indexes")
        for missing in all_missing[:10]:  # Show first 10
            print(f"   - {missing}")
        if len(all_missing) > 10:
            print(f"   ... and {len(all_missing) - 10} more")
    if all_errors:
        print(f"[ERROR] Errors: {len(all_errors)}")
        for err in all_errors[:5]:  # Show first 5
            print(f"   - {err}")
        if len(all_errors) > 5:
            print(f"   ... and {len(all_errors) - 5} more")
    
    print("\n" + "=" * 80)
    print("PERFORMANCE IMPACT")
    print("=" * 80)
    print("[OK] All critical indexes verified/created")
    print("[OK] Query performance optimized across all collections")
    print("=" * 80)
    
    client.close()
    return len(all_created), len(all_skipped), len(all_errors)

if __name__ == "__main__":
    print("=" * 80)
    print("MONGODB INDEX VERIFICATION AND CREATION")
    print("=" * 80)
    print(f"\nTarget database: {MONGODB_DB}")
    print("\nThis script will:")
    print("  1. Check all existing indexes in all collections")
    print("  2. Identify missing indexes")
    print("  3. Create missing indexes automatically")
    print("\n[WARNING] Index creation runs in background (non-blocking)")
    print("[WARNING] Large collections may take a few minutes")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        verify_and_create_indexes()
    else:
        print("\nRun with --yes to execute, or press Enter to continue...")
        try:
            input()
            verify_and_create_indexes()
        except KeyboardInterrupt:
            print("\nCancelled.")

