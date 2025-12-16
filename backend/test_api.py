"""
Quick API test script to verify all endpoints are working
Run this after seeding the database and starting the server
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)

        status = "✓" if response.status_code in [200, 201] else "✗"
        print(f"{status} {method} {endpoint} - {response.status_code} - {description}")

        if response.status_code not in [200, 201]:
            print(f"   Error: {response.text[:100]}")

        return response
    except Exception as e:
        print(f"✗ {method} {endpoint} - ERROR - {str(e)}")
        return None

def main():
    print("=" * 70)
    print("SALON MANAGEMENT SYSTEM - API TESTING")
    print("=" * 70)
    print(f"Testing server at: {BASE_URL}")
    print("Make sure the Flask server is running (python app.py)")
    print("=" * 70)

    # Check if server is running
    try:
        requests.get(BASE_URL)
    except:
        print("\n❌ ERROR: Server is not running!")
        print("Please start the server first: python app.py")
        return

    print("\n1. CUSTOMER ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/customers", description="Get all customers")
    test_endpoint("GET", "/api/customers/1", description="Get customer by ID")

    print("\n2. STAFF ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/staffs", description="Get all staff")
    test_endpoint("GET", "/api/staffs/1", description="Get staff by ID")

    print("\n3. SERVICE ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/services/groups", description="Get service groups")
    test_endpoint("GET", "/api/services", description="Get all services")
    test_endpoint("GET", "/api/services?status=active", description="Get active services")

    print("\n4. PRODUCT ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/products", description="Get all products")
    test_endpoint("GET", "/api/products/categories", description="Get product categories")
    test_endpoint("GET", "/api/products/low-stock", description="Get low stock products")

    print("\n5. PACKAGE ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/packages", description="Get all packages")
    test_endpoint("GET", "/api/packages/active", description="Get active packages")

    print("\n6. PREPAID ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/prepaid/groups", description="Get prepaid groups")
    test_endpoint("GET", "/api/prepaid/packages", description="Get prepaid packages")
    test_endpoint("GET", "/api/prepaid/clients", description="Get prepaid clients")

    print("\n7. BILL ENDPOINTS")
    print("-" * 70)
    today = date.today()
    week_ago = today - timedelta(days=7)
    test_endpoint("GET", "/api/bills", description="Get all bills")
    test_endpoint("GET", "/api/bills", {"start_date": str(week_ago), "end_date": str(today)}, "Get bills last 7 days")
    test_endpoint("GET", "/api/bills/stats", {"start_date": str(week_ago), "end_date": str(today)}, "Get bill statistics")

    print("\n8. APPOINTMENT ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/appointments", description="Get all appointments")
    test_endpoint("GET", "/api/appointments/calendar", {"view": "week"}, "Get calendar view")
    test_endpoint("GET", "/api/appointments/stats", description="Get appointment stats")

    print("\n9. EXPENSE ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/expenses/categories", description="Get expense categories")
    test_endpoint("GET", "/api/expenses", description="Get all expenses")
    test_endpoint("GET", "/api/expenses/summary", description="Get expense summary")

    print("\n10. INVENTORY ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/inventory/suppliers", description="Get all suppliers")
    test_endpoint("GET", "/api/inventory/orders", description="Get all orders")
    test_endpoint("GET", "/api/inventory/low-stock", description="Get low stock items")
    test_endpoint("GET", "/api/inventory/summary", description="Get inventory summary")

    print("\n11. LEAD ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/leads", description="Get all leads")
    test_endpoint("GET", "/api/leads/stats", description="Get lead statistics")

    print("\n12. FEEDBACK ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/feedback", description="Get all feedback")
    test_endpoint("GET", "/api/feedback/stats", description="Get feedback statistics")
    test_endpoint("GET", "/api/feedback/recent", description="Get recent feedback")

    print("\n13. ATTENDANCE ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/attendance", description="Get all attendance")
    test_endpoint("GET", "/api/attendance/summary", description="Get attendance summary")

    print("\n14. ASSET ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/assets", description="Get all assets")
    test_endpoint("GET", "/api/assets/summary", description="Get asset summary")
    test_endpoint("GET", "/api/assets/categories", description="Get asset categories")

    print("\n15. CASH TRANSACTION ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/cash/transactions", description="Get cash transactions")
    test_endpoint("GET", "/api/cash/summary", description="Get cash summary")
    test_endpoint("GET", "/api/cash/balance", description="Get cash balance")

    print("\n16. DASHBOARD ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/dashboard/stats", description="Get dashboard statistics")
    test_endpoint("GET", "/api/dashboard/staff-performance", description="Get staff performance")
    test_endpoint("GET", "/api/dashboard/top-customers", description="Get top customers")
    test_endpoint("GET", "/api/dashboard/top-offerings", description="Get top offerings")
    test_endpoint("GET", "/api/dashboard/revenue-breakdown", description="Get revenue breakdown")
    test_endpoint("GET", "/api/dashboard/payment-distribution", description="Get payment distribution")
    test_endpoint("GET", "/api/dashboard/client-funnel", description="Get client funnel")
    test_endpoint("GET", "/api/dashboard/alerts", description="Get operational alerts")

    print("\n17. REPORT ENDPOINTS")
    print("-" * 70)
    test_endpoint("GET", "/api/reports/service-sales-analysis", description="Service sales analysis")
    test_endpoint("GET", "/api/reports/list-of-bills", description="List of bills")
    test_endpoint("GET", "/api/reports/sales-by-service-group", description="Sales by service group")
    test_endpoint("GET", "/api/reports/prepaid-clients", description="Prepaid clients report")
    test_endpoint("GET", "/api/reports/membership-clients", description="Membership clients report")
    test_endpoint("GET", "/api/reports/staff-incentive", description="Staff incentive report")
    test_endpoint("GET", "/api/reports/expense-report", description="Expense report")
    test_endpoint("GET", "/api/reports/inventory-report", description="Inventory report")
    test_endpoint("GET", "/api/reports/business-growth", description="Business growth report")
    test_endpoint("GET", "/api/reports/period-summary", {"start_date": str(week_ago), "end_date": str(today)}, "Period summary")

    print("\n" + "=" * 70)
    print("API TESTING COMPLETED!")
    print("=" * 70)
    print("\nIf all endpoints show ✓, your backend is working correctly!")
    print("Any ✗ indicates an issue that needs to be fixed.")
    print("\nNext steps:")
    print("1. Review any failed endpoints")
    print("2. Test POST/PUT/DELETE operations with Postman")
    print("3. Connect your React frontend")
    print("=" * 70)

if __name__ == "__main__":
    main()
