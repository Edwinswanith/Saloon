# Salon Management System - Backend Setup Guide

## Prerequisites

Make sure you have Python installed and the required packages:

```bash
pip install flask flask-cors flask-sqlalchemy
```

## Database Setup with Dummy Data

### Option 1: Quick Start (Recommended)

Run the seed script to populate the database with comprehensive dummy data:

```bash
cd backend
python seed_data.py
```

This will:
- ✅ Clear any existing data
- ✅ Create all database tables
- ✅ Populate with realistic sample data

### Option 2: Manual Start

If you want to start with an empty database:

```bash
cd backend
python app.py
```

The database will be created automatically on first run.

## What Gets Seeded

The seed script populates your database with:

| Entity | Count | Details |
|--------|-------|---------|
| **Customers** | 10 | With varying loyalty points and wallet balances |
| **Staff** | 5 | Different commission rates and salaries |
| **Service Groups** | 5 | Hair Care, Skin Care, Nail Care, Spa, Bridal |
| **Services** | 17 | Various services with prices and durations |
| **Product Categories** | 4 | Hair, Skin, Nail, Styling Tools |
| **Products** | 11 | With stock levels (some low stock for testing) |
| **Packages** | 4 | Combo service packages |
| **Prepaid Packages** | 3 | Active prepaid balances for customers |
| **Memberships** | 2 | Gold and Platinum memberships |
| **Bills** | 50 | Last 30 days with items and payments |
| **Appointments** | 50 | Past (30) + Future (20) appointments |
| **Expenses** | 40 | Various expense types over 30 days |
| **Suppliers** | 3 | Beauty and hair care suppliers |
| **Orders** | 10 | Inventory purchase orders |
| **Leads** | 5 | Different lead statuses |
| **Feedback** | 15 | Customer reviews with ratings |
| **Attendance** | 150+ | Last 30 days for all staff |
| **Assets** | 6 | Salon furniture and equipment |
| **Cash Transactions** | 50 | Cash in/out transactions |

## Sample Credentials

### Sample Customer Mobile Numbers
- 9876543210 (Priya Sharma)
- 9876543211 (Rahul Kumar)
- 9876543212 (Anjali Patel)
- 9876543213 (Vikram Singh)
- 9876543214 (Neha Gupta)

### Sample Staff Mobile Numbers
- 9999888877 (Meera Shah)
- 9999888878 (Rohan Mehta)
- 9999888879 (Kavita Rao)
- 9999888880 (Suresh Joshi)
- 9999888881 (Divya Pillai)

## Starting the Server

After seeding the database, start the Flask server:

```bash
python app.py
```

Server will run on: **http://localhost:5000**

## Testing the API

### Quick Test Endpoints

1. **Get All Customers**
   ```
   GET http://localhost:5000/api/customers
   ```

2. **Get Dashboard Stats**
   ```
   GET http://localhost:5000/api/dashboard/stats
   ```

3. **Get Services**
   ```
   GET http://localhost:5000/api/services/groups
   ```

4. **Get Today's Appointments**
   ```
   GET http://localhost:5000/api/appointments?start_date=2025-12-11&end_date=2025-12-11
   ```

5. **Get Bills (Last 7 Days)**
   ```
   GET http://localhost:5000/api/bills?start_date=2025-12-04&end_date=2025-12-11
   ```

## API Documentation

### Base URL
```
http://localhost:5000
```

### Available Endpoints

#### Customers
- `GET /api/customers` - List all customers
- `POST /api/customers` - Create customer
- `GET /api/customers/{id}` - Get customer details
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Delete customer

#### Staff
- `GET /api/staffs` - List all staff
- `POST /api/staffs` - Create staff
- `GET /api/staffs/{id}` - Get staff details
- `PUT /api/staffs/{id}` - Update staff
- `DELETE /api/staffs/{id}` - Delete staff

#### Services
- `GET /api/services/groups` - Get service groups
- `GET /api/services` - List all services
- `POST /api/services` - Create service
- `GET /api/services/{id}` - Get service details
- `PUT /api/services/{id}` - Update service
- `DELETE /api/services/{id}` - Delete service

#### Bills & Checkout
- `GET /api/bills` - List all bills
- `POST /api/bills` - Create bill
- `GET /api/bills/{id}` - Get bill with items
- `POST /api/bills/{id}/items` - Add item to bill
- `POST /api/bills/{id}/checkout` - Complete checkout
- `DELETE /api/bills/{id}` - Soft delete bill

#### Appointments
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Create appointment
- `GET /api/appointments/calendar` - Calendar view
- `GET /api/appointments/available-slots` - Check availability

#### Products
- `GET /api/products` - List products
- `GET /api/products/low-stock` - Low stock items
- `POST /api/products` - Create product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

#### Dashboard & Analytics
- `GET /api/dashboard/stats` - Overall statistics
- `GET /api/dashboard/staff-performance` - Staff metrics
- `GET /api/dashboard/top-customers` - Top customers
- `GET /api/dashboard/top-offerings` - Best selling services/products
- `GET /api/dashboard/alerts` - Operational alerts

#### Reports
- `GET /api/reports/service-sales-analysis` - Service performance
- `GET /api/reports/list-of-bills` - Bills report
- `GET /api/reports/staff-incentive` - Commission report
- `GET /api/reports/expense-report` - Expenses
- `GET /api/reports/inventory-report` - Stock report
- `GET /api/reports/business-growth` - Growth trends
- `GET /api/reports/period-summary` - Period analysis

#### Other Modules
- **Expenses**: `/api/expenses`
- **Inventory**: `/api/inventory/suppliers`, `/api/inventory/orders`
- **Leads**: `/api/leads`
- **Feedback**: `/api/feedback`
- **Attendance**: `/api/attendance`
- **Assets**: `/api/assets`
- **Cash**: `/api/cash/transactions`
- **Prepaid**: `/api/prepaid/packages`
- **Packages**: `/api/packages`

## Database Location

SQLite database file: `backend/salon.db`

To reset and reseed:
```bash
python seed_data.py
```

## Troubleshooting

### Import Errors
If you get import errors, make sure you're in the backend directory:
```bash
cd backend
python seed_data.py
```

### Port Already in Use
If port 5000 is in use, change it in `app.py`:
```python
app.run(debug=True, port=5001)  # Change to any available port
```

### CORS Issues
CORS is already configured for all origins. If you need to restrict:
```python
CORS(app, origins=['http://localhost:3000'])
```

## Next Steps

1. ✅ Run `python seed_data.py` to populate the database
2. ✅ Start the server with `python app.py`
3. ✅ Test endpoints using Postman or curl
4. ✅ Connect your React frontend to these endpoints

## Support

For issues or questions:
- Check the seed script output for any errors
- Verify all required packages are installed
- Ensure Python 3.7+ is being used
- Check that the `backend` directory structure is correct

---

**Happy Testing! 🚀**
