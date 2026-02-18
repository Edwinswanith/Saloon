"""
Script to clean Main Road branch customers by keeping only those in the Excel file
and deleting dummy data that's not in the original dataset.
"""
import os
import sys
import re
from mongoengine import connect
from datetime import datetime

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Customer, Branch

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon_prod'

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

def extract_mobiles_from_excel(file_path):
    """
    Extract mobile numbers from Excel file.
    Expected format: Customer, Mobilenumber, MembershipType, Membership.No
    Returns set of normalized mobile numbers
    """
    original_mobiles = set()
    stats = {
        'total_rows': 0,
        'valid_mobiles': 0,
        'skipped_empty': 0,
        'skipped_invalid': 0,
        'duplicates': 0
    }
    
    try:
        # Try using pandas first (if available)
        try:
            import pandas as pd
            
            # Try reading as Excel first
            try:
                df = pd.read_excel(file_path, header=0, dtype=str, keep_default_na=False)
            except:
                # If that fails, try as TSV/CSV
                df = pd.read_csv(file_path, sep='\t', header=0, dtype=str, keep_default_na=False)
            
            stats['total_rows'] = len(df)
            
            for idx, row in df.iterrows():
                # Column 1 is Mobilenumber (index 1)
                mobile_raw = str(row.iloc[1]).strip() if len(row) > 1 else ""
                
                # Normalize mobile number
                mobile = normalize_mobile(mobile_raw)
                
                # Skip rows with empty/invalid mobile numbers
                if not mobile:
                    if not mobile_raw or mobile_raw == "" or mobile_raw == "nan":
                        stats['skipped_empty'] += 1
                    else:
                        stats['skipped_invalid'] += 1
                    continue
                
                # Check for duplicates
                if mobile in original_mobiles:
                    stats['duplicates'] += 1
                    continue
                
                original_mobiles.add(mobile)
                stats['valid_mobiles'] += 1
        
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
                        stats['skipped_empty'] += 1
                        continue
                    
                    mobile_raw = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Normalize mobile number
                    mobile = normalize_mobile(mobile_raw)
                    
                    # Skip rows with empty/invalid mobile numbers
                    if not mobile:
                        if not mobile_raw or mobile_raw == "":
                            stats['skipped_empty'] += 1
                        else:
                            stats['skipped_invalid'] += 1
                        continue
                    
                    # Check for duplicates
                    if mobile in original_mobiles:
                        stats['duplicates'] += 1
                        continue
                    
                    original_mobiles.add(mobile)
                    stats['valid_mobiles'] += 1
        
        print("\n" + "="*80)
        print("EXCEL FILE ANALYSIS")
        print("="*80)
        print(f"Total rows in file: {stats['total_rows']}")
        print(f"Valid mobile numbers extracted: {stats['valid_mobiles']}")
        print(f"Skipped (empty mobile): {stats['skipped_empty']}")
        print(f"Skipped (invalid mobile): {stats['skipped_invalid']}")
        print(f"Duplicates skipped: {stats['duplicates']}")
        print("="*80)
        
        return original_mobiles, stats
        
    except Exception as e:
        print(f"ERROR reading Excel file: {str(e)}")
        raise

def connect_db():
    """Connect to MongoDB"""
    try:
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
                maxPoolSize=10,
                minPoolSize=2,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
                maxIdleTimeMS=60000)
        print(f"[OK] Connected to MongoDB: {MONGODB_DB}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {str(e)}")
        return False

def clean_main_road_customers(excel_file_path, dry_run=False):
    """
    Clean Main Road branch customers:
    1. Extract original mobile numbers from Excel file
    2. Get all Main Road customers from MongoDB
    3. Delete customers NOT in Excel file (dummy data)
    """
    print("\n" + "="*80)
    print("CLEANING MAIN ROAD BRANCH CUSTOMERS")
    print("="*80)
    
    if not os.path.exists(excel_file_path):
        print(f"ERROR: File not found: {excel_file_path}")
        return False
    
    # Connect to database
    if not connect_db():
        return False
    
    # Get Main Road branch
    main_road_branch = Branch.objects(name='Main Road').first()
    if not main_road_branch:
        print("ERROR: Main Road branch not found in database")
        return False
    
    print(f"\nMain Road branch ID: {main_road_branch.id}")
    
    # Extract original mobile numbers from Excel
    print("\nExtracting mobile numbers from Excel file...")
    original_mobiles, excel_stats = extract_mobiles_from_excel(excel_file_path)
    
    if not original_mobiles:
        print("ERROR: No valid mobile numbers found in Excel file")
        return False
    
    # Get all Main Road customers from MongoDB
    print("\nFetching Main Road customers from MongoDB...")
    all_customers = Customer.objects(branch=main_road_branch)
    total_customers = all_customers.count()
    
    print(f"Total customers in Main Road branch: {total_customers}")
    
    # Identify customers to delete (not in Excel file)
    customers_to_delete = []
    customers_to_keep = []
    
    for customer in all_customers:
        normalized_mobile = normalize_mobile(customer.mobile)
        if normalized_mobile and normalized_mobile in original_mobiles:
            customers_to_keep.append(customer)
        else:
            customers_to_delete.append(customer)
    
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)
    print(f"Customers in Excel file (to keep): {len(original_mobiles)}")
    print(f"Customers in MongoDB Main Road branch: {total_customers}")
    print(f"Customers to KEEP (match Excel): {len(customers_to_keep)}")
    print(f"Customers to DELETE (dummy data): {len(customers_to_delete)}")
    print("="*80)
    
    if dry_run:
        print("\n[DRY RUN MODE] - No deletions will be performed")
        if customers_to_delete:
            print("\nSample customers that would be deleted:")
            for i, customer in enumerate(customers_to_delete[:10]):
                print(f"  {i+1}. Mobile: {customer.mobile}, Name: {customer.first_name} {customer.last_name}")
            if len(customers_to_delete) > 10:
                print(f"  ... and {len(customers_to_delete) - 10} more")
        return True
    
    # Confirm deletion
    if customers_to_delete:
        print(f"\nWARNING: About to delete {len(customers_to_delete)} customers from Main Road branch")
        print("These customers are NOT in the Excel file and will be permanently deleted.")
        response = input("\nProceed with deletion? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("Deletion cancelled.")
            return False
        
        # Delete dummy customers
        print("\nDeleting dummy customers...")
        deleted_count = 0
        errors = []
        
        for customer in customers_to_delete:
            try:
                customer.delete()
                deleted_count += 1
                if deleted_count % 100 == 0:
                    print(f"  Deleted {deleted_count}/{len(customers_to_delete)} customers...")
            except Exception as e:
                error_msg = f"Error deleting customer {customer.mobile}: {str(e)}"
                errors.append(error_msg)
                if len(errors) <= 10:
                    print(f"  ERROR: {error_msg}")
        
        print("\n" + "="*80)
        print("DELETION COMPLETE")
        print("="*80)
        print(f"Successfully deleted: {deleted_count} customers")
        if errors:
            print(f"Errors: {len(errors)}")
        print("="*80)
        
        # Verify final count
        remaining = Customer.objects(branch=main_road_branch).count()
        print(f"\nRemaining customers in Main Road branch: {remaining}")
        
        return True
    else:
        print("\nNo dummy customers found. All customers match the Excel file.")
        return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python clean_main_road_customers.py <excel_file_path> [--dry-run]")
        print("Example: python clean_main_road_customers.py 'c:\\Users\\bizzz\\Documents\\CustomerList.xls'")
        sys.exit(1)
    
    excel_file_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    try:
        clean_main_road_customers(excel_file_path, dry_run=dry_run)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

