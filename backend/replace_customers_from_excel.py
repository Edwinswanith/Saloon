"""
Replace all customers from Excel file
Uses Mobile Number as the unique identifier (already configured in Customer model)

CRITICAL WARNING: This will DELETE ALL existing customers and break references in:
- Bills (1,352+ records)
- Appointments (821+ records)  
- Memberships (21+ records)
- Prepaid packages, feedbacks, leads, WhatsApp messages

Usage:
    python replace_customers_from_excel.py --file ../customer_list/CustomerList.xls --confirm
"""

import os
import sys
from mongoengine import connect
from datetime import datetime, timezone
import argparse
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Customer, Branch

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

def normalize_mobile(mobile):
    """Normalize mobile number: remove spaces, keep only digits"""
    if not mobile:
        return None
    # Remove all non-digit characters
    normalized = re.sub(r'\D', '', str(mobile))
    # Return None if empty or too short (less than 10 digits)
    if len(normalized) < 10:
        return None
    return normalized

def parse_excel_file(file_path):
    """
    Parse Excel/TSV file and extract customer data.
    Expected format: Customer Name, Mobile Number, Membership Type, Membership Number
    Returns list of customer dictionaries and statistics
    """
    customers_data = []
    stats = {
        'total_rows': 0,
        'skipped_empty_mobile': 0,
        'skipped_invalid_mobile': 0,
        'duplicate_mobiles': 0,
        'empty_names': 0
    }
    seen_mobiles = set()
    
    try:
        # Try using pandas first (if available)
        try:
            import pandas as pd
            df = pd.read_csv(file_path, sep='\t', header=0, dtype=str, keep_default_na=False)
            
            stats['total_rows'] = len(df)
            
            for idx, row in df.iterrows():
                customer_name = str(row.iloc[0]).strip() if len(row) > 0 else ""
                mobile_raw = str(row.iloc[1]).strip() if len(row) > 1 else ""
                membership_type = str(row.iloc[2]).strip().lower() if len(row) > 2 else "no"
                membership_no = str(row.iloc[3]).strip() if len(row) > 3 else ""
                
                # Normalize mobile number
                mobile = normalize_mobile(mobile_raw)
                
                # Skip rows with empty/invalid mobile numbers
                if not mobile:
                    if not mobile_raw or mobile_raw == "" or mobile_raw == "nan":
                        stats['skipped_empty_mobile'] += 1
                    else:
                        stats['skipped_invalid_mobile'] += 1
                    continue
                
                # Check for duplicates
                if mobile in seen_mobiles:
                    stats['duplicate_mobiles'] += 1
                    continue
                seen_mobiles.add(mobile)
                
                # Parse customer name
                if not customer_name or customer_name == "" or customer_name == "nan":
                    customer_name = "Customer"
                    stats['empty_names'] += 1
                
                name_parts = customer_name.split()
                first_name = name_parts[0] if name_parts else "Customer"
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                
                customers_data.append({
                    'mobile': mobile,
                    'first_name': first_name,
                    'last_name': last_name,
                    'has_membership': membership_type == 'yes',
                    'membership_number': membership_no
                })
        
        except ImportError:
            # Fallback: Read as plain text file (TSV format)
            print("Pandas not available. Reading file as TSV...")
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                stats['total_rows'] = len(lines) - 1  # Exclude header
                
                # Skip header line
                for line in lines[1:]:
                    parts = line.strip().split('\t')
                    if len(parts) < 2:
                        stats['skipped_empty_mobile'] += 1
                        continue
                    
                    customer_name = parts[0].strip() if len(parts) > 0 else ""
                    mobile_raw = parts[1].strip() if len(parts) > 1 else ""
                    membership_type = parts[2].strip().lower() if len(parts) > 2 else "no"
                    membership_no = parts[3].strip() if len(parts) > 3 else ""
                    
                    # Normalize mobile number
                    mobile = normalize_mobile(mobile_raw)
                    
                    # Skip rows with empty/invalid mobile numbers
                    if not mobile:
                        if not mobile_raw or mobile_raw == "":
                            stats['skipped_empty_mobile'] += 1
                        else:
                            stats['skipped_invalid_mobile'] += 1
                        continue
                    
                    # Check for duplicates
                    if mobile in seen_mobiles:
                        stats['duplicate_mobiles'] += 1
                        continue
                    seen_mobiles.add(mobile)
                    
                    # Parse customer name
                    if not customer_name or customer_name == "":
                        customer_name = "Customer"
                        stats['empty_names'] += 1
                    
                    name_parts = customer_name.split()
                    first_name = name_parts[0] if name_parts else "Customer"
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                    
                    customers_data.append({
                        'mobile': mobile,
                        'first_name': first_name,
                        'last_name': last_name,
                        'has_membership': membership_type == 'yes',
                        'membership_number': membership_no
                    })
    
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
    return customers_data, stats

def get_default_branch():
    """Get or create a default branch for customers"""
    # Try to get first active branch
    branch = Branch.objects(is_active=True).first()
    
    if not branch:
        # Try any branch
        branch = Branch.objects().first()
    
    if not branch:
        # Create default branch
        print("No branches found. Creating default branch...")
        branch = Branch(
            name="T. Nagar",
            address="123 Main Street, T. Nagar",
            city="Chennai",
            is_active=True
        )
        branch.save()
        print(f"Created default branch: {branch.name}")
    
    return branch

def backup_customers():
    """Export current customers to a backup file"""
    try:
        customers = Customer.objects()
        backup_file = f"customer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("mobile\tfirst_name\tlast_name\temail\tsource\tgender\ttotal_spent\ttotal_visits\tbranch_id\n")
            for customer in customers:
                branch_id = str(customer.branch.id) if customer.branch else ""
                f.write(f"{customer.mobile}\t{customer.first_name or ''}\t{customer.last_name or ''}\t")
                f.write(f"{customer.email or ''}\t{customer.source or ''}\t{customer.gender or ''}\t")
                f.write(f"{customer.total_spent or 0}\t{customer.total_visits or 0}\t{branch_id}\n")
        
        print(f"Backup saved to: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
        import traceback
        traceback.print_exc()
        return None

def replace_customers(excel_file_path, confirm=False, dry_run=False):
    """
    Replace all customers with data from Excel file
    
    Args:
        excel_file_path: Path to Excel/TSV file
        confirm: Must be True to proceed with deletion
        dry_run: If True, only parse and validate, don't import
    """
    if not confirm and not dry_run:
        print("\n" + "="*80)
        print("CRITICAL WARNING: This will DELETE ALL existing customers!")
        print("="*80)
        print("\nThis operation will:")
        print("  - Delete all existing customers")
        print("  - Break references in 1,352+ bills")
        print("  - Break references in 821+ appointments")
        print("  - Break references in 21+ memberships")
        print("  - Lose all customer history (spending, visits)")
        print("\nTo proceed, run with --confirm flag")
        print("="*80)
        return False
    
    # Connect to MongoDB
    print("\nConnecting to MongoDB...")
    try:
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
        
        connect(host=base_uri, alias='default', db=MONGODB_DB,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000)
        print("Connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Parse Excel file
    print(f"\nReading customer data from: {excel_file_path}")
    customers_data, stats = parse_excel_file(excel_file_path)
    
    if not customers_data:
        print("Failed to parse Excel file or no data found")
        return False
    
    # Display statistics
    print("\n" + "="*80)
    print("DATA VALIDATION SUMMARY")
    print("="*80)
    print(f"Total rows in file: {stats['total_rows']}")
    print(f"Valid customers to import: {len(customers_data)}")
    print(f"Skipped (empty mobile): {stats['skipped_empty_mobile']}")
    print(f"Skipped (invalid mobile): {stats['skipped_invalid_mobile']}")
    print(f"Skipped (duplicate mobile): {stats['duplicate_mobiles']}")
    print(f"Empty names (defaulted to 'Customer'): {stats['empty_names']}")
    print("="*80)
    
    # Show sample data
    print("\nSample data (first 5 customers):")
    for i, cust in enumerate(customers_data[:5]):
        membership_info = f"Membership: {cust['membership_number']}" if cust['has_membership'] else "No membership"
        print(f"  {i+1}. {cust['first_name']} {cust['last_name']} - {cust['mobile']} ({membership_info})")
    
    # Get existing customer count
    existing_count = Customer.objects().count()
    print(f"\nCurrent customers in database: {existing_count}")
    
    # Dry run mode - just validate, don't import
    if dry_run:
        print("\n" + "="*80)
        print("DRY RUN MODE - No changes will be made")
        print("="*80)
        print(f"This would:")
        print(f"  - DELETE {existing_count} existing customers")
        print(f"  - IMPORT {len(customers_data)} new customers")
        print(f"  - BREAK all references in bills, appointments, memberships")
        print("\nDry run complete. Use --confirm to actually perform the import.")
        return True
    
    # Final confirmation
    print("\n" + "="*80)
    print("FINAL CONFIRMATION REQUIRED")
    print("="*80)
    print(f"This will:")
    print(f"  - DELETE {existing_count} existing customers")
    print(f"  - IMPORT {len(customers_data)} new customers")
    print(f"  - BREAK all references in bills, appointments, memberships")
    print("="*80)
    response = input(f"\nType 'yes' to proceed: ")
    if response.lower() != 'yes':
        print("Operation cancelled")
        return False
    
    # Backup existing customers
    print("\nCreating backup of existing customers...")
    backup_file = backup_customers()
    
    # Get default branch
    print("\nGetting default branch...")
    default_branch = get_default_branch()
    print(f"Using branch: {default_branch.name} (ID: {default_branch.id})")
    
    # Delete all existing customers
    print("\n" + "="*80)
    print("DELETING ALL EXISTING CUSTOMERS...")
    print("="*80)
    print(f"Deleting {existing_count} existing customers...")
    
    try:
        deleted_count = Customer.objects().delete()
        print(f"Deleted {deleted_count} customers")
    except Exception as e:
        print(f"Error deleting customers: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Import new customers
    print("\n" + "="*80)
    print("IMPORTING NEW CUSTOMERS...")
    print("="*80)
    
    imported_count = 0
    skipped_count = 0
    errors = []
    seen_mobiles = set()
    
    for idx, cust_data in enumerate(customers_data):
        try:
            mobile = cust_data['mobile']
            
            # Double-check for duplicates (shouldn't happen after parsing, but safety check)
            if mobile in seen_mobiles:
                skipped_count += 1
                errors.append(f"Duplicate mobile in import list: {mobile}")
                continue
            seen_mobiles.add(mobile)
            
            # Check if already exists (shouldn't happen after delete, but safety check)
            if Customer.objects(mobile=mobile).first():
                skipped_count += 1
                errors.append(f"Customer with mobile {mobile} already exists in database")
                continue
            
            # Create customer - mobile is the unique identifier
            customer = Customer(
                mobile=mobile,  # Primary unique identifier
                first_name=cust_data['first_name'],
                last_name=cust_data['last_name'],
                branch=default_branch,
                source='Walk-in',  # Default source
                total_spent=0.0,
                total_visits=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            customer.save()
            imported_count += 1
            
            if (idx + 1) % 500 == 0:
                print(f"  Imported {idx + 1}/{len(customers_data)} customers...")
        
        except Exception as e:
            skipped_count += 1
            error_msg = f"Error importing {cust_data['mobile']}: {str(e)}"
            errors.append(error_msg)
            # Don't print every error to avoid spam, but log them
            if len(errors) <= 10:
                print(f"  ERROR: {error_msg}")
            continue
    
    # Summary
    print("\n" + "="*80)
    print("IMPORT COMPLETE")
    print("="*80)
    print(f"Total customers in Excel: {len(customers_data)}")
    print(f"Successfully imported: {imported_count}")
    print(f"Skipped/Failed: {skipped_count}")
    
    if errors:
        print(f"\nErrors encountered: {len(errors)}")
        if len(errors) <= 20:
            print("Error details:")
            for error in errors[:20]:
                print(f"  - {error}")
        else:
            print("First 20 errors:")
            for error in errors[:20]:
                print(f"  - {error}")
            print(f"  ... and {len(errors) - 20} more errors")
    
    if backup_file:
        print(f"\nBackup saved to: {backup_file}")
    
    print("\n" + "="*80)
    print("WARNING: All bills, appointments, and memberships now have broken customer references!")
    print("You will need to manually update or delete those records.")
    print("="*80)
    
    # Verify import
    final_count = Customer.objects().count()
    print(f"\nVerification: {final_count} customers now in database")
    
    if final_count == imported_count:
        print("✓ Import successful - count matches!")
    else:
        print(f"⚠ Warning: Expected {imported_count} customers, found {final_count}")
    
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replace all customers from Excel file')
    parser.add_argument('--file', type=str, default='../customer_list/CustomerList.xls',
                       help='Path to Excel file (default: ../customer_list/CustomerList.xls)')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirm that you understand the consequences')
    parser.add_argument('--dry-run', action='store_true',
                       help='Parse and validate data without importing (safe to test)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    
    replace_customers(args.file, confirm=args.confirm, dry_run=args.dry_run)

