# Dummy Authentication Data - Setup Guide

## Overview

This guide explains how to insert dummy authentication data into MongoDB and how login/signup data is stored dynamically.

## Collections Created

When you run the script, the following MongoDB collections are automatically created:

1. **`staffs`** - Stores all staff members
2. **`managers`** - Stores all managers and owners
3. **`login_history`** - Stores all login/signup events (created automatically on first login)

## How to Insert Dummy Data

### Method 1: Python Script (Recommended)

```bash
cd backend
python insert_dummy_auth_data.py
```

The script will:
- Connect to MongoDB
- Ask if you want to clear existing data
- Insert 5 staff members and 3 managers
- Show verification summary

### Method 2: MongoDB Shell Script

If you prefer using the JavaScript file:

1. Open MongoDB Compass
2. Connect to your database
3. Click "MONGOSH" tab
4. Copy contents of `insert_dummy_data.js`
5. Paste and run

## Dummy Accounts Created

### Staff Members (No Password - Role Selection)

1. **Rajesh Kumar**
   - Mobile: `9876543210`
   - Role: `staff`
   - Login: Select from dropdown, choose role

2. **Priya Sharma**
   - Mobile: `9876543211`
   - Role: `staff`
   - Login: Select from dropdown, choose role

3. **Sneha Reddy**
   - Mobile: `9876543213`
   - Role: `staff`
   - Login: Select from dropdown, choose role

4. **Vikram Singh**
   - Mobile: `9876543214`
   - Role: `staff`
   - Login: Select from dropdown, choose role

### Staff with Password (Manager Role)

5. **Amit Patel**
   - Mobile: `9876543212`
   - Password: `manager123`
   - Role: `manager`

### Managers

1. **Arun Mehta**
   - Email: `arun@salon.com`
   - Mobile: `9876543220`
   - Password: `manager123`
   - Role: `manager`

2. **Kavita Desai**
   - Email: `kavita@salon.com`
   - Mobile: `9876543221`
   - Password: `manager456`
   - Role: `manager`

### Owner

3. **Rahul Chopra**
   - Email: `owner@salon.com`
   - Mobile: `9876543230`
   - Password: `owner123`
   - Role: `owner`

## How Dynamic Storage Works

### 1. Login Data Storage

When a user logs in, the system automatically:

1. **Retrieves user data** from MongoDB (`staffs` or `managers` collection)
2. **Validates credentials** (password if required)
3. **Generates JWT token** with user info
4. **Logs login event** to `login_history` collection

**Example Login Flow:**
```
User Login Request
    ↓
Backend checks MongoDB (staffs/managers collection)
    ↓
Validates password (if required)
    ↓
Generates JWT token
    ↓
Logs to login_history collection
    ↓
Returns token to frontend
```

### 2. Signup Data Storage

When a new user signs up (via staff/manager creation):

1. **Creates new document** in MongoDB
2. **Hashes password** (if provided)
3. **Stores in appropriate collection** (`staffs` or `managers`)
4. **Collections are auto-created** on first insert

**Example Signup Flow:**
```
New User Signup
    ↓
Backend creates Staff/Manager document
    ↓
Hashes password (bcrypt)
    ↓
Saves to MongoDB (staffs/managers collection)
    ↓
Collection auto-created if doesn't exist
    ↓
Returns success response
```

### 3. Login History Tracking

Every login attempt is logged to `login_history` collection with:

- `user_id` - Staff/Manager ID
- `user_type` - staff or manager
- `role` - staff, manager, or owner
- `login_method` - password or role_selection
- `ip_address` - User's IP address
- `user_agent` - Browser/client info
- `login_status` - success or failed
- `failure_reason` - Why login failed (if applicable)
- `created_at` - Timestamp

## Collections Structure

### staffs Collection

```javascript
{
  _id: ObjectId,
  mobile: "9876543210",
  first_name: "Rajesh",
  last_name: "Kumar",
  email: "rajesh@salon.com",
  salary: 25000,
  commission_rate: 10.0,
  status: "active",
  role: "staff",  // staff, manager, owner
  password_hash: null,  // null or bcrypt hash
  is_active: true,
  created_at: ISODate,
  updated_at: ISODate
}
```

### managers Collection

```javascript
{
  _id: ObjectId,
  first_name: "Arun",
  last_name: "Mehta",
  email: "arun@salon.com",
  mobile: "9876543220",
  salon: "Glamour Saloon - Main Branch",
  password_hash: "$2b$12$...",  // bcrypt hash
  role: "manager",  // manager or owner
  permissions: [],
  is_active: true,
  status: "active",
  created_at: ISODate,
  updated_at: ISODate
}
```

### login_history Collection

```javascript
{
  _id: ObjectId,
  user_id: "507f1f77bcf86cd799439011",
  user_type: "staff",  // staff or manager
  role: "manager",
  login_method: "password",  // password or role_selection
  ip_address: "192.168.1.1",
  user_agent: "Mozilla/5.0...",
  login_status: "success",  // success or failed
  failure_reason: null,  // null or error message
  created_at: ISODate
}
```

## Testing Login

### Test 1: Staff Login (No Password)

1. Open app → `http://localhost:5173`
2. Select "Staff" toggle
3. Choose "Rajesh Kumar" from dropdown
4. Select role: "staff"
5. Click "Sign In"
6. ✓ Should redirect to dashboard

**What happens:**
- Backend retrieves Rajesh from `staffs` collection
- No password check (password_hash is null)
- Role updated if changed
- JWT token generated
- Login logged to `login_history`

### Test 2: Manager Login (With Password)

1. Open app → `http://localhost:5173`
2. Select "Manager / Owner" toggle
3. Email: `arun@salon.com`
4. Password: `manager123`
5. Click "Sign In"
6. ✓ Should redirect to dashboard as Manager

**What happens:**
- Backend retrieves Arun from `managers` collection
- Password verified (bcrypt)
- JWT token generated
- Login logged to `login_history`

### Test 3: Owner Login (Full Access)

1. Open app → `http://localhost:5173`
2. Select "Manager / Owner" toggle
3. Email: `owner@salon.com`
4. Password: `owner123`
5. Click "Sign In"
6. ✓ Should redirect to dashboard as Owner

**What happens:**
- Backend retrieves Rahul from `managers` collection
- Password verified
- JWT token generated with owner role
- Login logged to `login_history`

## Viewing Data in MongoDB

### Using MongoDB Compass

1. Connect to your MongoDB cluster
2. Select `Saloon` database
3. View collections:
   - `staffs` - All staff members
   - `managers` - All managers/owners
   - `login_history` - All login events

### Using MongoDB Shell

```javascript
use('Saloon');

// View all staff
db.staffs.find().pretty();

// View all managers
db.managers.find().pretty();

// View login history
db.login_history.find().sort({created_at: -1}).limit(10).pretty();

// Count documents
db.staffs.countDocuments();
db.managers.countDocuments();
db.login_history.countDocuments();
```

## Security Notes

1. **Passwords are hashed** using bcrypt (12 rounds)
2. **JWT tokens expire** after 24 hours
3. **Login history** tracks all attempts (success and failed)
4. **IP addresses logged** for security auditing
5. **Collections auto-created** - no manual setup needed

## Troubleshooting

### Issue: "Staff member not found"

**Solution:** Run the insert script to create dummy data:
```bash
python backend/insert_dummy_auth_data.py
```

### Issue: "Invalid password"

**Solution:** Use the correct password:
- Manager: `manager123` or `manager456`
- Owner: `owner123`
- Staff with password: `manager123`

### Issue: "Collection doesn't exist"

**Solution:** Collections are auto-created on first insert. If you see this error, check MongoDB connection.

### Issue: "Connection failed"

**Solution:** Check your MongoDB URI in the script matches your actual connection string.

## Summary

✅ **Collections**: `staffs`, `managers`, `login_history`  
✅ **Auto-created**: Collections created automatically  
✅ **Dynamic storage**: All login/signup data stored in MongoDB  
✅ **Login tracking**: Every login logged to `login_history`  
✅ **Password security**: All passwords hashed with bcrypt  
✅ **Ready to test**: 5 staff + 3 managers/owners created

