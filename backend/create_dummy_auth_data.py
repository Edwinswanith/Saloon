"""
Create dummy authentication data for testing the Saloon Management System

This script creates:
1. Staff members (with and without passwords)
2. Managers (with passwords)
3. Owner account (with password)

Run this script ONCE to populate the database for testing.
"""

from mongoengine import connect
from models import Staff, Manager
from utils.auth import hash_password
from datetime import datetime
import os
from utils.env_config import load_env, get_mongodb_uri, get_mongodb_db

# MongoDB connection - Use the actual connection string from app.py
load_env()
MONGODB_URI = get_mongodb_uri()
MONGODB_DB = 'Saloon'

print("Connecting to MongoDB...")
# Build connection URI with database name
base_uri = MONGODB_URI
if f'/{MONGODB_DB}' not in base_uri:
    if '?' in base_uri:
        base_uri = base_uri.replace('?', f'/{MONGODB_DB}?')
    else:
        base_uri = f"{base_uri}/{MONGODB_DB}"

if 'retryWrites' not in base_uri:
    separator = '&' if '?' in base_uri else '?'
    base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"

connect(host=base_uri, alias='default', db=MONGODB_DB)
print("✓ Connected successfully\n")

# Clear existing data (CAUTION: This will delete existing staff and managers)
print("WARNING: This will delete existing staff and managers!")
response = input("Continue? (yes/no): ")

if response.lower() != 'yes':
    print("Aborted.")
    exit()

print("\nClearing existing data...")
Staff.objects.delete()
Manager.objects.delete()
print("✓ Cleared existing staff and managers\n")

# ============================================
# CREATE STAFF MEMBERS
# ============================================
print("Creating staff members...")

staff_data = [
    {
        'mobile': '9876543210',
        'first_name': 'Rajesh',
        'last_name': 'Kumar',
        'email': 'rajesh@salon.com',
        'salary': 25000,
        'commission_rate': 10.0,
        'status': 'active',
        'role': 'staff',
        'password_hash': None,  # No password - role selection at login
        'is_active': True
    },
    {
        'mobile': '9876543211',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'email': 'priya@salon.com',
        'salary': 28000,
        'commission_rate': 12.0,
        'status': 'active',
        'role': 'staff',
        'password_hash': None,
        'is_active': True
    },
    {
        'mobile': '9876543212',
        'first_name': 'Amit',
        'last_name': 'Patel',
        'email': 'amit@salon.com',
        'salary': 30000,
        'commission_rate': 15.0,
        'status': 'active',
        'role': 'manager',  # Staff member with manager role
        'password_hash': hash_password('manager123'),  # Password: manager123
        'is_active': True
    },
    {
        'mobile': '9876543213',
        'first_name': 'Sneha',
        'last_name': 'Reddy',
        'email': 'sneha@salon.com',
        'salary': 22000,
        'commission_rate': 8.0,
        'status': 'active',
        'role': 'staff',
        'password_hash': None,
        'is_active': True
    },
    {
        'mobile': '9876543214',
        'first_name': 'Vikram',
        'last_name': 'Singh',
        'email': 'vikram@salon.com',
        'salary': 26000,
        'commission_rate': 10.0,
        'status': 'active',
        'role': 'staff',
        'password_hash': None,
        'is_active': True
    }
]

created_staff = []
for data in staff_data:
    staff = Staff(**data, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    staff.save()
    created_staff.append(staff)
    password_info = "No password (role selection)" if not data['password_hash'] else f"Password: {data.get('_temp_password', 'Set')}"
    print(f"  ✓ Created staff: {data['first_name']} {data['last_name']} ({data['mobile']}) - {password_info}")

print(f"\n✓ Created {len(created_staff)} staff members\n")

# ============================================
# CREATE MANAGERS
# ============================================
print("Creating managers...")

manager_data = [
    {
        'first_name': 'Arun',
        'last_name': 'Mehta',
        'email': 'arun@salon.com',
        'mobile': '9876543220',
        'salon': 'Glamour Saloon - Main Branch',
        'password_hash': hash_password('manager123'),  # Password: manager123
        'role': 'manager',
        'permissions': [],
        'is_active': True,
        'status': 'active',
        '_temp_password': 'manager123'
    },
    {
        'first_name': 'Kavita',
        'last_name': 'Desai',
        'email': 'kavita@salon.com',
        'mobile': '9876543221',
        'salon': 'Glamour Saloon - Main Branch',
        'password_hash': hash_password('manager456'),  # Password: manager456
        'role': 'manager',
        'permissions': [],
        'is_active': True,
        'status': 'active',
        '_temp_password': 'manager456'
    },
    {
        'first_name': 'Rahul',
        'last_name': 'Chopra',
        'email': 'owner@salon.com',
        'mobile': '9876543230',
        'salon': 'Glamour Saloon - All Branches',
        'password_hash': hash_password('owner123'),  # Password: owner123
        'role': 'owner',
        'permissions': [],
        'is_active': True,
        'status': 'active',
        '_temp_password': 'owner123'
    }
]

created_managers = []
for data in manager_data:
    temp_password = data.pop('_temp_password', None)
    manager = Manager(**data, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    manager.save()
    created_managers.append(manager)
    print(f"  ✓ Created {data['role']}: {data['first_name']} {data['last_name']} ({data['email']}) - Password: {temp_password}")

print(f"\n✓ Created {len(created_managers)} managers/owners\n")

# ============================================
# SUMMARY
# ============================================
print("=" * 60)
print("DUMMY DATA CREATED SUCCESSFULLY!")
print("=" * 60)

print("\n📋 STAFF MEMBERS (Login without password - role selection):")
print("-" * 60)
for staff in created_staff:
    if not staff.password_hash:
        print(f"  • {staff.first_name} {staff.last_name}")
        print(f"    Mobile: {staff.mobile}")
        print(f"    Default Role: {staff.role}")
        print(f"    Login: Select from dropdown, choose role\n")

print("\n📋 STAFF WITH PASSWORD (Manager role):")
print("-" * 60)
for staff in created_staff:
    if staff.password_hash:
        print(f"  • {staff.first_name} {staff.last_name}")
        print(f"    Mobile: {staff.mobile}")
        print(f"    Password: manager123")
        print(f"    Role: {staff.role}\n")

print("\n📋 MANAGERS:")
print("-" * 60)
for manager in created_managers:
    if manager.role == 'manager':
        print(f"  • {manager.first_name} {manager.last_name}")
        print(f"    Email: {manager.email}")
        print(f"    Mobile: {manager.mobile}")
        if manager.email == 'arun@salon.com':
            print(f"    Password: manager123")
        elif manager.email == 'kavita@salon.com':
            print(f"    Password: manager456")
        print(f"    Saloon: {manager.salon}\n")

print("\n📋 OWNER:")
print("-" * 60)
for manager in created_managers:
    if manager.role == 'owner':
        print(f"  • {manager.first_name} {manager.last_name}")
        print(f"    Email: {manager.email}")
        print(f"    Mobile: {manager.mobile}")
        print(f"    Password: owner123")
        print(f"    Saloon: {manager.salon}\n")

print("\n" + "=" * 60)
print("HOW TO TEST LOGIN:")
print("=" * 60)

print("\n1️⃣  STAFF LOGIN (No Password):")
print("   • Select 'Staff' toggle")
print("   • Choose any staff from dropdown")
print("   • Select role: staff/manager/owner")
print("   • Click 'Sign In'")

print("\n2️⃣  MANAGER LOGIN (With Password):")
print("   • Select 'Manager / Owner' toggle")
print("   • Email: arun@salon.com")
print("   • Password: manager123")
print("   • Click 'Sign In'")

print("\n3️⃣  OWNER LOGIN (With Password):")
print("   • Select 'Manager / Owner' toggle")
print("   • Email: owner@salon.com")
print("   • Password: owner123")
print("   • Click 'Sign In'")

print("\n" + "=" * 60)
print("DISCOUNT LIMITS BY ROLE:")
print("=" * 60)
print("  • Staff: 15% max (without approval)")
print("  • Manager: 25% max (without approval)")
print("  • Owner: Unlimited")

print("\n✅ Database is ready for testing!\n")
