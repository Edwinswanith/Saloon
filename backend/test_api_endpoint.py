"""
Test the Customer Lifecycle API endpoint directly
"""
import requests

# Test with different branch IDs
branches = {
    "Anna Nagar": "694523e1e7624aff7c44993a",
    "Adyar": "694523e1e7624aff7c44993c",
}

# You'll need to get your auth token from localStorage
# For now, let's just test if the endpoint responds

for branch_name, branch_id in branches.items():
    print(f"\n=== Testing {branch_name} (ID: {branch_id}) ===")
    
    # Make request with branch ID header
    response = requests.get(
        'http://127.0.0.1:5000/api/customer-lifecycle/report',
        headers={
            'X-Branch-Id': branch_id,
            'Authorization': 'Bearer YOUR_TOKEN_HERE'  # You'll need to add this
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Customers returned: {len(data.get('customers', []))}")
        if data.get('customers'):
            sample = data['customers'][:3]
            print(f"Sample customers:")
            for c in sample:
                print(f"  - {c.get('first_name')} {c.get('last_name')} (Mobile: {c.get('mobile')})")
    else:
        print(f"Error: {response.text}")

