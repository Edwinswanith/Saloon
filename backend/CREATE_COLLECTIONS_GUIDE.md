# How to Create MongoDB Collections

## Option 1: Create via MongoDB Atlas UI (FASTEST - 2 minutes)

1. Open MongoDB Atlas Data Explorer (you're already there!)
2. Click the **"CREATE COLLECTION"** button (green button on the right)
3. Database: `Saloon` (select from dropdown)
4. Collection name: Enter one of these:
   - `customers`
   - `staffs`
   - `bills`
   - `appointments`
   - `services`
   - `products`
   - `packages`
   - `prepaid_packages`
   - `memberships`
   - `membership_plans`
   - `expenses`
   - `expense_categories`
   - `leads`
   - `feedbacks`
   - `staff_attendance`
   - `assets`
   - `cash_transactions`
   - `suppliers`
   - `orders`
   - `service_groups`
   - `product_categories`
   - `prepaid_groups`
   - `tax_settings`
   - `tax_slabs`
   - `loyalty_program_settings`
   - `referral_program_settings`
   - `managers`

5. Repeat for all 27 collections

## Option 2: Collections Created Automatically When You Use the App

Start your Flask app and use it - collections will be created automatically:

```bash
python app.py
```

Then:
- Create a customer via API → creates `customers` collection
- Create a bill → creates `bills` collection
- Use any feature → creates needed collections

## Option 3: Use This Python Script (When SSL Issue is Fixed)

Run: `python create_all_collections.py`

Note: Currently there's an SSL handshake issue preventing script execution, but collections will work fine when you use the app normally.


