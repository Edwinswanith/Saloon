"""
Migrate SQLite database to MongoDB
Preserves exact schema and data from SQLite to MongoDB
"""
import sqlite3
import sys
import os
from datetime import datetime, date, time
from decimal import Decimal
from mongoengine.errors import ValidationError

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app for MongoDB connection
print("Loading Flask app and MongoDB connection...")
from app import app

# Import MongoDB models
from models import (
    Customer, Staff, ServiceGroup, Service, ProductCategory, Product,
    Package, PrepaidGroup, PrepaidPackage, MembershipPlan, Membership,
    Bill, Appointment, ExpenseCategory, Expense, Supplier, Order,
    Lead, Feedback, StaffAttendance, Asset, CashTransaction,
    LoyaltyProgramSettings, ReferralProgramSettings, TaxSettings, TaxSlab, Manager
)

# SQLite database path
SQLITE_DB_PATH = 'instance/salon.db'

# ID mapping: SQLite ID -> MongoDB ObjectId
id_mappings = {
    'customers': {},
    'staffs': {},
    'service_groups': {},
    'product_categories': {},
    'services': {},
    'products': {},
    'packages': {},
    'prepaid_groups': {},
    'prepaid_packages': {},
    'membership_plans': {},
    'memberships': {},
    'bills': {},
    'appointments': {},
    'expense_categories': {},
    'expenses': {},
    'suppliers': {},
    'orders': {},
    'leads': {},
    'feedbacks': {},
    'staff_attendance': {},
    'assets': {},
    'cash_transactions': {},
    'loyalty_program_settings': {},
    'referral_program_settings': {},
    'tax_settings': {},
    'tax_slabs': {},
    'managers': {}
}

def convert_value(value, sqlite_type):
    """Convert SQLite value to appropriate Python type"""
    if value is None:
        return None
    
    if sqlite_type == 'INTEGER':
        return int(value)
    elif sqlite_type == 'FLOAT' or sqlite_type == 'REAL':
        return float(value)
    elif sqlite_type == 'BOOLEAN':
        return bool(value)
    elif sqlite_type == 'DATE':
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        return value
    elif sqlite_type == 'DATETIME':
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except:
                    return value
        return value
    elif sqlite_type == 'TIME':
        # MongoDB models expect time as string in HH:MM:SS format
        # Keep as string, don't convert to time object
        if isinstance(value, str):
            # Clean up the time string - remove microseconds if present
            if '.' in value:
                value = value.split('.')[0]
            # Ensure it's in HH:MM:SS format
            parts = value.split(':')
            if len(parts) == 3:
                return value  # Already in correct format
            elif len(parts) == 2:
                return f"{value}:00"  # Add seconds
            else:
                return value
        elif isinstance(value, time):
            # Convert time object to string
            return value.strftime('%H:%M:%S')
        elif value is not None:
            return str(value)
        return None
    else:
        return str(value) if value is not None else None

def migrate_table(table_name, model_class, sqlite_conn, order=0):
    """Migrate a single table from SQLite to MongoDB"""
    print(f"\n[{order}] Migrating {table_name}...")
    
    cursor = sqlite_conn.cursor()
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    column_types = {col[1]: col[2] for col in columns}
    
    # Get all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for row in rows:
        try:
            # Convert row to dictionary
            row_dict = {}
            for i, col_name in enumerate(column_names):
                value = row[i]
                sqlite_type = column_types.get(col_name, 'TEXT')
                row_dict[col_name] = convert_value(value, sqlite_type)
            
            # Store original SQLite ID
            sqlite_id = row_dict.get('id')
            
            # Remove 'id' from dict (MongoDB will create _id)
            if 'id' in row_dict:
                del row_dict['id']
            
            # Handle foreign key references - convert to MongoDB ObjectId
            # Map based on table name
            if table_name == 'services' and 'group_id' in row_dict:
                group_id = row_dict.pop('group_id')
                if group_id and group_id in id_mappings['service_groups']:
                    row_dict['group'] = id_mappings['service_groups'][group_id]
                else:
                    print(f"  Warning: Service {sqlite_id} has invalid group_id {group_id}")
                    continue
            
            elif table_name == 'products' and 'category_id' in row_dict:
                category_id = row_dict.pop('category_id')
                if category_id and category_id in id_mappings['product_categories']:
                    row_dict['category'] = id_mappings['product_categories'][category_id]
                else:
                    print(f"  Warning: Product {sqlite_id} has invalid category_id {category_id}")
                    continue
            
            elif table_name == 'prepaid_packages' and 'group_id' in row_dict:
                group_id = row_dict.pop('group_id')
                if group_id and group_id in id_mappings['prepaid_groups']:
                    row_dict['group'] = id_mappings['prepaid_groups'][group_id]
                else:
                    row_dict['group'] = None  # Optional field
            
            elif table_name == 'prepaid_packages' and 'customer_id' in row_dict:
                customer_id = row_dict.pop('customer_id')
                if customer_id and customer_id in id_mappings['customers']:
                    row_dict['customer'] = id_mappings['customers'][customer_id]
                else:
                    row_dict['customer'] = None  # Optional field
            
            elif table_name == 'memberships' and 'customer_id' in row_dict:
                customer_id = row_dict.pop('customer_id')
                if customer_id and customer_id in id_mappings['customers']:
                    row_dict['customer'] = id_mappings['customers'][customer_id]
                else:
                    print(f"  Warning: Membership {sqlite_id} has invalid customer_id {customer_id}")
                    continue
            
            elif table_name == 'memberships' and 'plan_id' in row_dict:
                plan_id = row_dict.pop('plan_id')
                if plan_id and plan_id in id_mappings['membership_plans']:
                    row_dict['plan'] = id_mappings['membership_plans'][plan_id]
                else:
                    print(f"  Warning: Membership {sqlite_id} has invalid plan_id {plan_id}")
                    continue
            
            # Handle appointments - both customer and staff are required
            if table_name == 'appointments':
                # Check customer_id
                if 'customer_id' in row_dict:
                    customer_id = row_dict.pop('customer_id')
                    if customer_id and customer_id in id_mappings['customers']:
                        row_dict['customer'] = id_mappings['customers'][customer_id]
                    else:
                        if not customer_id:
                            print(f"  Warning: Appointment {sqlite_id} has no customer_id, skipping")
                        else:
                            available_ids = list(id_mappings['customers'].keys())[:5]
                            print(f"  Warning: Appointment {sqlite_id} customer_id {customer_id} not in mappings (have {len(id_mappings['customers'])} customers, sample IDs: {available_ids}), skipping")
                        skipped_count += 1
                        continue
                
                # Check staff_id
                if 'staff_id' in row_dict:
                    staff_id = row_dict.pop('staff_id')
                    if staff_id and staff_id in id_mappings['staffs']:
                        row_dict['staff'] = id_mappings['staffs'][staff_id]
                    else:
                        # Skip appointments without valid staff
                        if not staff_id:
                            print(f"  Warning: Appointment {sqlite_id} has no staff_id, skipping")
                        else:
                            available_ids = list(id_mappings['staffs'].keys())[:5]
                            print(f"  Warning: Appointment {sqlite_id} staff_id {staff_id} not in mappings (have {len(id_mappings['staffs'])} staff, sample IDs: {available_ids}), skipping")
                        skipped_count += 1
                        continue
            
            elif table_name == 'appointments' and 'service_id' in row_dict:
                service_id = row_dict.pop('service_id')
                if service_id and service_id in id_mappings['services']:
                    row_dict['service'] = id_mappings['services'][service_id]
                else:
                    row_dict['service'] = None  # Optional field
            
            # Convert time fields to strings for appointments
            if table_name == 'appointments' and 'start_time' in row_dict:
                if isinstance(row_dict['start_time'], time):
                    row_dict['start_time'] = row_dict['start_time'].strftime('%H:%M:%S')
                elif row_dict['start_time'] and not isinstance(row_dict['start_time'], str):
                    row_dict['start_time'] = str(row_dict['start_time'])
            
            # Convert time fields to strings for cash_transactions
            if table_name == 'cash_transactions' and 'transaction_time' in row_dict:
                if isinstance(row_dict['transaction_time'], time):
                    row_dict['transaction_time'] = row_dict['transaction_time'].strftime('%H:%M:%S')
                elif row_dict['transaction_time'] and not isinstance(row_dict['transaction_time'], str):
                    row_dict['transaction_time'] = str(row_dict['transaction_time'])
            
            # Convert time fields to strings for staff_attendance
            if table_name == 'staff_attendance':
                if 'check_in_time' in row_dict and row_dict['check_in_time']:
                    if isinstance(row_dict['check_in_time'], time):
                        row_dict['check_in_time'] = row_dict['check_in_time'].strftime('%H:%M:%S')
                    elif not isinstance(row_dict['check_in_time'], str):
                        row_dict['check_in_time'] = str(row_dict['check_in_time'])
                if 'check_out_time' in row_dict and row_dict['check_out_time']:
                    if isinstance(row_dict['check_out_time'], time):
                        row_dict['check_out_time'] = row_dict['check_out_time'].strftime('%H:%M:%S')
                    elif not isinstance(row_dict['check_out_time'], str):
                        row_dict['check_out_time'] = str(row_dict['check_out_time'])
            
            elif table_name == 'expenses' and 'category_id' in row_dict:
                category_id = row_dict.pop('category_id')
                if category_id and category_id in id_mappings['expense_categories']:
                    row_dict['category'] = id_mappings['expense_categories'][category_id]
                else:
                    print(f"  Warning: Expense {sqlite_id} has invalid category_id {category_id}")
                    continue
            
            elif table_name == 'orders' and 'supplier_id' in row_dict:
                supplier_id = row_dict.pop('supplier_id')
                if supplier_id and supplier_id in id_mappings['suppliers']:
                    row_dict['supplier'] = id_mappings['suppliers'][supplier_id]
                else:
                    print(f"  Warning: Order {sqlite_id} has invalid supplier_id {supplier_id}")
                    continue
            
            # Handle order_items (embedded documents)
            if table_name == 'orders' and 'order_items' in row_dict:
                order_items = row_dict.get('order_items')
                if order_items:
                    try:
                        import json
                        from models import OrderItemEmbedded
                        items_list = json.loads(order_items) if isinstance(order_items, str) else order_items
                        # Convert items to embedded documents
                        embedded_items = []
                        for item in items_list:
                            item_dict = {}
                            if 'product_id' in item and item['product_id'] in id_mappings['products']:
                                item_dict['product'] = id_mappings['products'][item['product_id']]
                            item_dict['quantity'] = item.get('quantity', 1)
                            item_dict['unit_price'] = item.get('unit_price', 0.0)
                            item_dict['total'] = item.get('total', 0.0)
                            embedded_items.append(OrderItemEmbedded(**item_dict))
                        row_dict['order_items'] = embedded_items
                    except Exception as e:
                        print(f"  Warning: Could not parse order_items for order {sqlite_id}: {e}")
                        row_dict['order_items'] = []
                else:
                    row_dict['order_items'] = []
            
            elif table_name == 'staff_attendance' and 'staff_id' in row_dict:
                staff_id = row_dict.pop('staff_id')
                if staff_id and staff_id in id_mappings['staffs']:
                    row_dict['staff'] = id_mappings['staffs'][staff_id]
                else:
                    if not staff_id:
                        print(f"  Warning: StaffAttendance {sqlite_id} has no staff_id, skipping")
                    else:
                        available_ids = list(id_mappings['staffs'].keys())[:5]
                        print(f"  Warning: StaffAttendance {sqlite_id} staff_id {staff_id} not in mappings (have {len(id_mappings['staffs'])} staff, sample IDs: {available_ids}), skipping")
                    skipped_count += 1
                    continue
            
            elif table_name == 'bills' and 'customer_id' in row_dict:
                customer_id = row_dict.pop('customer_id')
                if customer_id and customer_id in id_mappings['customers']:
                    row_dict['customer'] = id_mappings['customers'][customer_id]
                else:
                    row_dict['customer'] = None  # Optional field
            
            elif table_name == 'leads' and 'customer_id' in row_dict:
                customer_id = row_dict.pop('customer_id')
                if customer_id and customer_id in id_mappings['customers']:
                    row_dict['customer'] = id_mappings['customers'][customer_id]
                else:
                    row_dict['customer'] = None  # Optional field
            
            elif table_name == 'feedbacks' and 'customer_id' in row_dict:
                customer_id = row_dict.pop('customer_id')
                if customer_id and customer_id in id_mappings['customers']:
                    row_dict['customer'] = id_mappings['customers'][customer_id]
                else:
                    row_dict['customer'] = None  # Optional field
            
            elif table_name == 'feedbacks' and 'bill_id' in row_dict:
                bill_id = row_dict.pop('bill_id')
                if bill_id and bill_id in id_mappings['bills']:
                    row_dict['bill'] = id_mappings['bills'][bill_id]
                else:
                    row_dict['bill'] = None  # Optional field
            
            # Handle packages services field (keep as JSON string, but update IDs)
            if table_name == 'packages' and 'services' in row_dict and row_dict['services']:
                try:
                    import json
                    services_list = json.loads(row_dict['services'])
                    # Convert service IDs from SQLite integers to MongoDB ObjectId strings
                    mongodb_service_ids = []
                    for svc_id in services_list:
                        if svc_id in id_mappings['services']:
                            # Convert ObjectId to string
                            mongodb_service_ids.append(str(id_mappings['services'][svc_id]))
                    # Store as JSON string (as expected by StringField)
                    row_dict['services'] = json.dumps(mongodb_service_ids)
                except:
                    row_dict['services'] = '[]'
            
            # Handle bills items - items are embedded, so they might not exist in SQLite
            # If they do exist as JSON, we'll handle them, otherwise leave as empty list
            if table_name == 'bills' and 'items' in row_dict:
                # Bills items might be stored as JSON, handle if needed
                items = row_dict.get('items')
                if items:
                    try:
                        import json
                        items_list = json.loads(items) if isinstance(items, str) else items
                        # Convert items to embedded documents (simplified - may need more processing)
                        row_dict['items'] = items_list
                    except:
                        row_dict['items'] = []
                else:
                    row_dict['items'] = []
            
            # Remove fields that don't exist in the MongoDB model
            # MongoEngine will raise errors for unknown fields, so we filter them
            model_fields = set(model_class._fields.keys())
            filtered_dict = {k: v for k, v in row_dict.items() if k in model_fields}
            
            # Create MongoDB document
            doc = model_class(**filtered_dict)
            doc.save()
            
            # Store ID mapping
            if sqlite_id:
                id_mappings[table_name][sqlite_id] = doc.id
            
            migrated_count += 1
            
        except ValidationError as e:
            error_count += 1
            print(f"  ValidationError migrating row {sqlite_id if 'sqlite_id' in locals() else 'unknown'}: {str(e)[:200]}")
        except Exception as e:
            error_count += 1
            print(f"  Error migrating row {sqlite_id if 'sqlite_id' in locals() else 'unknown'}: {str(e)[:200]}")
            continue
    
    print(f"  [OK] Migrated: {migrated_count}, Skipped: {skipped_count}, Errors: {error_count}")
    
    # Debug: Show ID mappings count for this table
    if table_name in id_mappings:
        print(f"  [DEBUG] ID mappings for {table_name}: {len(id_mappings[table_name])} entries")
        if len(id_mappings[table_name]) > 0:
            sample_ids = list(id_mappings[table_name].keys())[:3]
            print(f"  [DEBUG] Sample SQLite IDs: {sample_ids}")
    
    return migrated_count, error_count

# Migration order: independent tables first, then dependent ones
MIGRATION_ORDER = [
    # Independent tables (no foreign keys)
    ('service_groups', ServiceGroup, 1),
    ('product_categories', ProductCategory, 2),
    ('customers', Customer, 3),
    ('staffs', Staff, 4),
    ('prepaid_groups', PrepaidGroup, 5),
    ('membership_plans', MembershipPlan, 6),
    ('expense_categories', ExpenseCategory, 7),
    ('suppliers', Supplier, 8),
    ('packages', Package, 9),
    ('assets', Asset, 10),
    ('cash_transactions', CashTransaction, 11),
    ('loyalty_program_settings', LoyaltyProgramSettings, 12),
    ('referral_program_settings', ReferralProgramSettings, 13),
    ('tax_settings', TaxSettings, 14),
    ('tax_slabs', TaxSlab, 15),
    ('managers', Manager, 16),
    
    # Dependent tables (have foreign keys)
    ('services', Service, 17),  # depends on service_groups
    ('products', Product, 18),  # depends on product_categories
    ('prepaid_packages', PrepaidPackage, 19),  # depends on prepaid_groups, customers
    ('memberships', Membership, 20),  # depends on customers, membership_plans
    ('appointments', Appointment, 21),  # depends on customers, staffs
    ('expenses', Expense, 22),  # depends on expense_categories
    ('orders', Order, 23),  # depends on suppliers, products
    ('staff_attendance', StaffAttendance, 24),  # depends on staffs
    ('bills', Bill, 25),  # depends on customers, services, products, etc.
    ('leads', Lead, 26),  # depends on customers (optional)
    ('feedbacks', Feedback, 27),  # depends on customers, bills (optional)
]

def main():
    """Main migration function"""
    print("=" * 60)
    print("SQLite to MongoDB Migration")
    print("=" * 60)
    print(f"Source: {SQLITE_DB_PATH}")
    print(f"Target: MongoDB (Saloon database)")
    print()
    
    # Connect to SQLite
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"ERROR: SQLite database not found at {SQLITE_DB_PATH}")
        return
    
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Use Flask app context for MongoDB connection
    with app.app_context():
        # Check MongoDB connection
        try:
            from mongoengine import get_db
            db = get_db()
            db.list_collection_names()
            print("[OK] MongoDB connection verified")
        except Exception as e:
            print(f"ERROR: MongoDB connection failed: {e}")
            return
        
        total_migrated = 0
        total_errors = 0
        
        # Check which tables exist in SQLite
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Migrate tables in order
        for table_name, model_class, order in MIGRATION_ORDER:
            if table_name not in existing_tables:
                print(f"\n[{order}] Skipping {table_name} (table not found in SQLite)")
                continue
            try:
                migrated, errors = migrate_table(table_name, model_class, sqlite_conn, order)
                total_migrated += migrated
                total_errors += errors
            except Exception as e:
                print(f"  ✗ Failed to migrate {table_name}: {e}")
                total_errors += 1
        
        sqlite_conn.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total records migrated: {total_migrated}")
        print(f"Total errors: {total_errors}")
        print("\nMigration completed!")
        print("=" * 60)

if __name__ == '__main__':
    main()

