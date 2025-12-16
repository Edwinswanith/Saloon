"""
Simple script to create one customer via API
This will automatically create the 'customers' collection in MongoDB
Run this AFTER starting your Flask app: python app.py
"""
import requests
import json

print("=" * 60)
print("Creating Collections via API")
print("=" * 60)
print("\nMake sure Flask app is running on http://localhost:5000")
print("Start it with: python app.py\n")

BASE_URL = "http://localhost:5000/api"

try:
    # Create a test customer - this creates the 'customers' collection
    print("Creating test customer...")
    response = requests.post(
        f"{BASE_URL}/customers",
        json={
            "mobile": "9999999999",
            "firstName": "Test",
            "lastName": "User",
            "source": "Walk-in"
        },
        timeout=10
    )
    
    if response.status_code == 201:
        customer_id = response.json().get('id')
        print(f"[OK] Created customer - 'customers' collection now exists!")
        print(f"Customer ID: {customer_id}")
        
        # Delete test customer
        print("\nDeleting test customer...")
        delete_response = requests.delete(f"{BASE_URL}/customers/{customer_id}", timeout=10)
        if delete_response.status_code == 200:
            print("[OK] Test customer deleted")
        
        print("\n" + "=" * 60)
        print("SUCCESS! The 'customers' collection was created.")
        print("\nTo create other collections:")
        print("  - Use the app features (create bills, staff, etc.)")
        print("  - Collections are created automatically when needed")
        print("=" * 60)
    else:
        print(f"[ERROR] Failed to create customer: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except requests.exceptions.ConnectionError:
    print("[ERROR] Could not connect to Flask app.")
    print("\nPlease start your Flask app first:")
    print("  1. Open a new terminal")
    print("  2. Run: cd D:\\Salon\\backend")
    print("  3. Run: python app.py")
    print("  4. Then run this script again")
    
except Exception as e:
    print(f"[ERROR] {str(e)}")


