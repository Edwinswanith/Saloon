"""
Script to update product stock quantities in the database.
Run this script from the backend directory.
"""

import os
import sys
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect, disconnect
from models import Product

# MongoDB connection settings
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon_prod'

def update_product_stock():
    """Update stock quantities for all products"""
    try:
        # Connect to MongoDB using the URI directly with db parameter
        connect(host=MONGODB_URI, db=MONGODB_DB)
        print(f"Connected to MongoDB: {MONGODB_DB}")

        # Get all products
        products = Product.objects.all()
        print(f"Found {len(products)} products")

        # Update each product with a reasonable stock quantity
        updated_count = 0
        for product in products:
            # Set stock quantity based on product type/name
            # Give each product a reasonable stock value between 10 and 100
            if product.stock_quantity == 0 or product.stock_quantity is None:
                # Generate a reasonable stock quantity
                stock_qty = random.randint(15, 75)
                min_stock = random.randint(5, 15)

                product.stock_quantity = stock_qty
                product.min_stock_level = min_stock
                product.save()

                print(f"  Updated: {product.name} -> stock: {stock_qty}, min_stock: {min_stock}")
                updated_count += 1
            else:
                print(f"  Skipped: {product.name} (already has stock: {product.stock_quantity})")

        print(f"\nUpdated {updated_count} products with stock quantities")

        # Disconnect
        disconnect()
        print("Disconnected from MongoDB")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    update_product_stock()
