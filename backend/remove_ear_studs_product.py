"""
Script to remove 'Ear studs' product from MongoDB
This script will find and delete all products with 'Ear studs' in the name
"""
import os
import sys
from mongoengine import connect, disconnect
from models import Product

def connect_to_mongodb():
    """Connect to MongoDB using the same logic as app.py"""
    try:
        # Get MongoDB connection details
        mongo_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
        mongodb_db = os.environ.get('MONGODB_DB', 'Saloon_prod')
        
        # Parse connection string - same logic as app.py
        base_uri = mongo_uri
        
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
        if f'/{mongodb_db}' not in base_uri:
            if '?' in base_uri:
                base_uri = base_uri.replace('?', f'/{mongodb_db}?')
            else:
                base_uri = f"{base_uri}/{mongodb_db}"
        
        # Add retry parameters if not present
        if 'retryWrites' not in base_uri:
            separator = '&' if '?' in base_uri else '?'
            base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
        
        connect(host=base_uri, alias='default', db=mongodb_db,
                connectTimeoutMS=30000,
                serverSelectionTimeoutMS=30000)
        print(f"[OK] Connected to MongoDB: {mongodb_db}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {str(e)}")
        return False

def remove_ear_studs_products():
    """Find and remove all 'Ear studs' products"""
    try:
        # Search for products with 'Ear studs' in the name (case insensitive)
        products = Product.objects(name__icontains='Ear studs')
        count = products.count()
        
        if count == 0:
            print("[INFO] No products with 'Ear studs' found in the database")
            return 0
        
        print(f"[INFO] Found {count} product(s) with 'Ear studs' in the name")
        
        # List the products before deletion
        for product in products:
            print(f"  - {product.name} (ID: {product.id}, Branch: {product.branch})")
        
        # Delete all matching products
        deleted_count = products.delete()
        
        print(f"[SUCCESS] Deleted {deleted_count} product(s) with 'Ear studs'")
        return deleted_count
        
    except Exception as e:
        print(f"[ERROR] Error removing products: {str(e)}")
        return 0

def main():
    """Main function"""
    print("=" * 60)
    print("REMOVE EAR STUDS PRODUCT FROM MONGODB")
    print("=" * 60)
    
    if not connect_to_mongodb():
        sys.exit(1)
    
    try:
        deleted_count = remove_ear_studs_products()
        print("\n" + "=" * 60)
        if deleted_count > 0:
            print(f"SUCCESS: Removed {deleted_count} product(s)")
        else:
            print("INFO: No products to remove")
        print("=" * 60)
    finally:
        disconnect()

if __name__ == "__main__":
    main()

