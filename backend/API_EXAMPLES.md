# Saloon Management API - Request Examples

Complete examples for testing all API endpoints using curl or Postman.

## Base URL
```
http://localhost:5000
```

---

## 1. CUSTOMERS

### Get All Customers
```bash
curl -X GET http://localhost:5000/api/customers
```

### Get Customer by ID
```bash
curl -X GET http://localhost:5000/api/customers/1
```

### Create Customer
```bash
curl -X POST http://localhost:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "mobile": "9876543299",
    "first_name": "Test",
    "last_name": "Customer",
    "email": "test@email.com",
    "source": "Walk-in",
    "gender": "Male"
  }'
```

### Update Customer
```bash
curl -X PUT http://localhost:5000/api/customers/1 \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Updated",
    "email": "updated@email.com"
  }'
```

---

## 2. STAFF

### Get All Staff
```bash
curl -X GET http://localhost:5000/api/staffs
```

### Create Staff
```bash
curl -X POST http://localhost:5000/api/staffs \
  -H "Content-Type: application/json" \
  -d '{
    "mobile": "9999888899",
    "first_name": "New",
    "last_name": "Staff",
    "email": "newstaff@salon.com",
    "salary": 22000,
    "commission_rate": 10,
    "status": "active"
  }'
```

---

## 3. SERVICES

### Get Service Groups
```bash
curl -X GET http://localhost:5000/api/services/groups
```

### Get All Services
```bash
curl -X GET http://localhost:5000/api/services
```

### Get Services by Group
```bash
curl -X GET "http://localhost:5000/api/services?group_id=1"
```

### Create Service
```bash
curl -X POST http://localhost:5000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Beard Trim",
    "group_id": 1,
    "price": 150,
    "duration": 20,
    "status": "active"
  }'
```

---

## 4. PRODUCTS

### Get All Products
```bash
curl -X GET http://localhost:5000/api/products
```

### Get Low Stock Products
```bash
curl -X GET http://localhost:5000/api/products/low-stock
```

### Get Product Categories
```bash
curl -X GET http://localhost:5000/api/products/categories
```

### Create Product
```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Shampoo",
    "category_id": 1,
    "price": 500,
    "cost": 350,
    "stock_quantity": 20,
    "min_stock_level": 10,
    "sku": "SHMP002",
    "status": "active"
  }'
```

---

## 5. BILLS & CHECKOUT

### Create New Bill (Draft)
```bash
curl -X POST http://localhost:5000/api/bills \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "booking_status": "service-completed"
  }'
```

### Add Item to Bill
```bash
curl -X POST http://localhost:5000/api/bills/1/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "service",
    "service_id": 1,
    "staff_id": 1,
    "start_time": "10:00:00",
    "price": 300,
    "quantity": 1,
    "total": 300
  }'
```

### Checkout Bill
```bash
curl -X POST http://localhost:5000/api/bills/1/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "discount_amount": 0,
    "discount_type": "fix",
    "tax_rate": 18,
    "payment_mode": "cash"
  }'
```

### Get Bill with Items
```bash
curl -X GET http://localhost:5000/api/bills/1
```

### Get Bills in Date Range
```bash
curl -X GET "http://localhost:5000/api/bills?start_date=2025-12-01&end_date=2025-12-11"
```

---

## 6. APPOINTMENTS

### Create Appointment
```bash
curl -X POST http://localhost:5000/api/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "staff_id": 1,
    "service_id": 1,
    "appointment_date": "2025-12-15",
    "start_time": "14:00:00",
    "status": "confirmed",
    "notes": "Regular haircut"
  }'
```

### Get Calendar View
```bash
curl -X GET "http://localhost:5000/api/appointments/calendar?view=week&date=2025-12-11"
```

### Check Available Slots
```bash
curl -X GET "http://localhost:5000/api/appointments/available-slots?staff_id=1&date=2025-12-15&service_id=1"
```

### Update Appointment Status
```bash
curl -X PUT http://localhost:5000/api/appointments/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

---

## 7. EXPENSES

### Get All Expenses
```bash
curl -X GET http://localhost:5000/api/expenses
```

### Create Expense
```bash
curl -X POST http://localhost:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Office Supplies",
    "category_id": 1,
    "amount": 1500,
    "payment_mode": "cash",
    "expense_date": "2025-12-11",
    "description": "Stationery and cleaning supplies"
  }'
```

### Get Expense Summary
```bash
curl -X GET "http://localhost:5000/api/expenses/summary?start_date=2025-12-01&end_date=2025-12-11"
```

---

## 8. INVENTORY

### Get All Suppliers
```bash
curl -X GET http://localhost:5000/api/inventory/suppliers
```

### Create Supplier
```bash
curl -X POST http://localhost:5000/api/inventory/suppliers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Supplier Co.",
    "contact_no": "9988776699",
    "email": "contact@newsupplier.com",
    "address": "Mumbai, India",
    "status": "active"
  }'
```

### Create Order with Items
```bash
curl -X POST http://localhost:5000/api/inventory/orders \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": 1,
    "order_date": "2025-12-11",
    "total_amount": 15000,
    "status": "pending",
    "items": [
      {
        "product_id": 1,
        "quantity": 10,
        "unit_price": 300,
        "total": 3000
      },
      {
        "product_id": 2,
        "quantity": 8,
        "unit_price": 350,
        "total": 2800
      }
    ]
  }'
```

### Mark Order as Received
```bash
curl -X POST http://localhost:5000/api/inventory/orders/1/receive \
  -H "Content-Type: application/json"
```

---

## 9. LEADS

### Create Lead
```bash
curl -X POST http://localhost:5000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Potential Customer",
    "mobile": "9123456789",
    "email": "potential@email.com",
    "source": "Instagram",
    "status": "new",
    "notes": "Interested in bridal package"
  }'
```

### Convert Lead to Customer
```bash
curl -X POST http://localhost:5000/api/leads/1/convert \
  -H "Content-Type: application/json"
```

### Get Lead Stats
```bash
curl -X GET http://localhost:5000/api/leads/stats
```

---

## 10. FEEDBACK

### Create Feedback
```bash
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "bill_id": 1,
    "rating": 5,
    "comment": "Excellent service! Very satisfied."
  }'
```

### Get Feedback Stats
```bash
curl -X GET http://localhost:5000/api/feedback/stats
```

---

## 11. ATTENDANCE

### Staff Check-In
```bash
curl -X POST http://localhost:5000/api/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "notes": "On time"
  }'
```

### Staff Check-Out
```bash
curl -X POST http://localhost:5000/api/attendance/check-out \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1
  }'
```

### Get Attendance Summary
```bash
curl -X GET "http://localhost:5000/api/attendance/summary?start_date=2025-12-01&end_date=2025-12-11"
```

---

## 12. CASH TRANSACTIONS

### Add Cash In
```bash
curl -X POST http://localhost:5000/api/cash/in \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "reason": "Customer payment",
    "transaction_date": "2025-12-11",
    "transaction_time": "14:30:00"
  }'
```

### Add Cash Out
```bash
curl -X POST http://localhost:5000/api/cash/out \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1500,
    "reason": "Petty cash",
    "transaction_date": "2025-12-11",
    "transaction_time": "15:00:00"
  }'
```

### Get Cash Balance
```bash
curl -X GET http://localhost:5000/api/cash/balance
```

---

## 13. DASHBOARD

### Get Overall Statistics
```bash
curl -X GET "http://localhost:5000/api/dashboard/stats?start_date=2025-11-11&end_date=2025-12-11"
```

### Get Staff Performance
```bash
curl -X GET http://localhost:5000/api/dashboard/staff-performance
```

### Get Top Customers
```bash
curl -X GET "http://localhost:5000/api/dashboard/top-customers?limit=10"
```

### Get Top Services/Products
```bash
curl -X GET http://localhost:5000/api/dashboard/top-offerings
```

### Get Revenue Breakdown
```bash
curl -X GET http://localhost:5000/api/dashboard/revenue-breakdown
```

### Get Operational Alerts
```bash
curl -X GET http://localhost:5000/api/dashboard/alerts
```

---

## 14. REPORTS

### Service Sales Analysis
```bash
curl -X GET "http://localhost:5000/api/reports/service-sales-analysis?start_date=2025-11-11&end_date=2025-12-11"
```

### Staff Incentive Report
```bash
curl -X GET "http://localhost:5000/api/reports/staff-incentive?start_date=2025-11-11&end_date=2025-12-11"
```

### Expense Report
```bash
curl -X GET "http://localhost:5000/api/reports/expense-report?start_date=2025-12-01&end_date=2025-12-11"
```

### Inventory Report
```bash
curl -X GET "http://localhost:5000/api/reports/inventory-report?low_stock_only=true"
```

### Business Growth Report
```bash
curl -X GET "http://localhost:5000/api/reports/business-growth?start_date=2025-09-01&end_date=2025-12-11"
```

### Period Summary
```bash
curl -X GET "http://localhost:5000/api/reports/period-summary?start_date=2025-12-01&end_date=2025-12-11"
```

---

## Common Query Parameters

### Date Filtering
Most endpoints support date range filtering:
```
?start_date=2025-12-01&end_date=2025-12-11
```

### Pagination (if needed in future)
```
?page=1&limit=20
```

### Search
```
?search=keyword
```

### Status Filtering
```
?status=active
```

---

## Response Format

All endpoints return JSON in this format:

**Success (GET):**
```json
[
  {
    "id": 1,
    "name": "Example",
    ...
  }
]
```

**Success (POST/PUT):**
```json
{
  "id": 1,
  "message": "Operation successful",
  "data": {...}
}
```

**Error:**
```json
{
  "error": "Error message description"
}
```

---

## Testing Tips

1. **Use Postman**: Import these examples into Postman for easier testing
2. **Check Server**: Make sure Flask server is running on port 5000
3. **Test Order**: Test GET endpoints first, then POST/PUT/DELETE
4. **Date Format**: Always use YYYY-MM-DD for dates
5. **Time Format**: Always use HH:MM:SS for times
6. **Foreign Keys**: Ensure referenced IDs exist before creating related records

---

**Happy Testing! 🚀**
