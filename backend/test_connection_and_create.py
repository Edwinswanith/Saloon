"""
Test MongoDB connection and create collections by using the app
This uses MongoEngine (like the app does) instead of pymongo directly
"""
from app import app
from models import Customer, LoyaltyProgramSettings, ReferralProgramSettings, TaxSettings

print("Testing MongoDB connection using app configuration...")
print("=" * 60)

with app.app_context():
    try:
        # Test connection by creating a test customer
        print("\n1. Testing connection by creating test customer...")
        test_customer = Customer(
            mobile='9999999999',
            first_name='Test',
            last_name='User'
        )
        test_customer.save()
        print(f"   ✓ Connected! Created test customer with ID: {test_customer.id}")
        
        # Delete test customer
        test_customer.delete()
        print("   ✓ Deleted test customer")
        
        # Initialize settings collections
        print("\n2. Initializing settings collections...")
        try:
            LoyaltyProgramSettings.get_settings()
            print("   ✓ loyalty_program_settings")
        except Exception as e:
            print(f"   ✗ loyalty_program_settings: {e}")
        
        try:
            ReferralProgramSettings.get_settings()
            print("   ✓ referral_program_settings")
        except Exception as e:
            print(f"   ✗ referral_program_settings: {e}")
        
        try:
            TaxSettings.get_settings()
            print("   ✓ tax_settings")
        except Exception as e:
            print(f"   ✗ tax_settings: {e}")
        
        print("\n" + "=" * 60)
        print("SUCCESS! MongoDB connection works.")
        print("\nCollections will be created automatically when you:")
        print("  - Create a customer (creates 'customers' collection)")
        print("  - Create a bill (creates 'bills' collection)")
        print("  - Use any feature in your app")
        print("\nCheck MongoDB Atlas Data Explorer to see collections as they're created.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nPlease check:")
        print("  1. MongoDB Atlas connection string is correct")
        print("  2. IP address is whitelisted in MongoDB Atlas")
        print("  3. Database user has proper permissions")

