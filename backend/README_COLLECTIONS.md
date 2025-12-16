# How to Create MongoDB Collections

## Current Issue
SSL handshake errors are preventing direct MongoDB connections from Python scripts.

## ✅ SOLUTION: Collections Created Automatically

**Good news:** MongoDB collections are created automatically when you insert data!

### Option 1: Use Your Flask App (Recommended)
1. Start your Flask app:
   ```bash
   cd backend
   python app.py
   ```

2. Use any feature in your app:
   - Create a customer → creates `customers` collection
   - Create a bill → creates `bills` collection
   - Create staff → creates `staffs` collection
   - etc.

**Collections appear in MongoDB Atlas as you use the app!**

### Option 2: Create via MongoDB Atlas UI (Fastest - 2 minutes)
1. Go to MongoDB Atlas → Data Explorer
2. Click **"CREATE COLLECTION"** button (green button)
3. Database: `Saloon`
4. Collection name: Enter one of the 27 collection names below
5. Click "Create"
6. Repeat for all collections

**All 27 Collections:**
- customers
- staffs
- bills
- appointments
- services
- products
- packages
- prepaid_packages
- memberships
- membership_plans
- expenses
- expense_categories
- leads
- feedbacks
- staff_attendance
- assets
- cash_transactions
- suppliers
- orders
- service_groups
- product_categories
- prepaid_groups
- tax_settings
- tax_slabs
- loyalty_program_settings
- referral_program_settings
- managers

### Option 3: Use API Endpoint
Once Flask app is running, you can use:
```bash
python create_one_customer.py
```

This will create the `customers` collection via API call.

## Note
The SSL connection issues don't affect your Flask app - it connects successfully. The errors only happen with direct pymongo scripts. Your app will work fine and create collections automatically as you use it!


