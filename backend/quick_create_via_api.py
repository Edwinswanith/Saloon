"""
Quick Collection Creation via Flask API
Start your Flask app first, then run this script
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

print("=" * 60)
print("Creating Collections via API")
print("=" * 60)
print("\nMake sure your Flask app is running: python app.py")
print("Then this script will create collections by making API calls.\n")

# Create a customer - this will create the 'customers' collection
try:
    print("1. Creating customer...")
    response = requests.post(f"{BASE_URL}/customers", json={
        "mobile": "9999999999",
        "firstName": "Test",
        "lastName": "User",
        "source": "Walk-in"
    })
    if response.status_code == 201:
        print("   [OK] Created customer - 'customers' collection now exists")
        customer_id = response.json().get('id')
        
        # Delete test customer
        requests.delete(f"{BASE_URL}/customers/{customer_id}")
        print("   [OK] Deleted test customer")
    else:
        print(f"   [ERROR] {response.status_code}: {response.text[:100]}")
except Exception as e:
    print(f"   [ERROR] {str(e)[:80]}")
    print("   Make sure Flask app is running on http://localhost:5000")

print("\n" + "=" * 60)
print("To create all collections:")
print("1. Start Flask app: python app.py")
print("2. Use the app features - collections will be created automatically")
print("3. OR create collections manually in MongoDB Atlas UI")
print("=" * 60)

