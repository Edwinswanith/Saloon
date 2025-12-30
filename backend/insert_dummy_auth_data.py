"""
Insert Dummy Authentication Data into MongoDB
Based on insert_dummy_data.js

This script:
1. Creates Staff and Manager collections (if they don't exist)
2. Inserts dummy data for testing login/signup
3. All login/signup data is automatically stored in MongoDB via models

Run: python backend/insert_dummy_auth_data.py
"""

from mongoengine import connect, disconnect
from models import Staff, Manager
from utils.auth import hash_password
from datetime import datetime
import os

# MongoDB connection - Use the actual connection string from app.py
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = 'Saloon'

print("=" * 70)
print("INSERTING DUMMY AUTHENTICATION DATA INTO MONGODB")
print("=" * 70)
print("\nConnecting to MongoDB...")

# Build connection URI with database name
base_uri = MONGODB_URI
if '@' in base_uri:
    parts = base_uri.split('@')
    if len(parts) == 2:
        credentials = parts[0]
        host_and_params = parts[1]
        
        # Remove database name from host part if present
        if '/' in host_and_params:
            host = host_and_params.split('/')[0]
            # Keep query parameters if they exist
            if '?' in host_and_params:
                params = '?' + host_and_params.split('?', 1)[1]
            else:
                params = ''
            base_uri = f"{credentials}@{host}{params}"

# Add database name to URI if not present
if f'/{MONGODB_DB}' not in base_uri:
    if '?' in base_uri:
        base_uri = base_uri.replace('?', f'/{MONGODB_DB}?')
    else:
        base_uri = f"{base_uri}/{MONGODB_DB}"

# Add retry parameters if not present
if 'retryWrites' not in base_uri:
    separator = '&' if '?' in base_uri else '?'
    base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"

try:
    connect(host=base_uri, alias='default', db=MONGODB_DB,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000)
    print("✓ Connected to MongoDB successfully\n")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# ============================================
# CLEAR EXISTING DATA (Optional)
# ============================================
print("WARNING: This will DELETE all existing staff and managers!")
response = input("Do you want to clear existing data? (yes/no): ")

if response.lower() == 'yes':
    print("\nClearing existing staff and managers...")
    try:
        staff_count = Staff.objects.count()
        manager_count = Manager.objects.count()
        
        Staff.objects.delete()
        Manager.objects.delete()
        
        print(f"✓ Deleted {staff_count} staff members")
        print(f"✓ Deleted {manager_count} managers\n")
    except Exception as e:
        print(f"✗ Error clearing data: {e}\n")
else:
    print("Keeping existing data. New records will be added.\n")

# ============================================
# INSERT STAFF MEMBERS
# ============================================
print("Inserting staff members...")
print("-" * 70)

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
    try:
        # Check if staff already exists
        existing = Staff.objects(mobile=data['mobile']).first()
        if existing:
            print(f"  ⚠ Staff {data['first_name']} {data['last_name']} ({data['mobile']}) already exists - skipping")
            continue
        
        staff = Staff(
            mobile=data['mobile'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            salary=data['salary'],
            commission_rate=data['commission_rate'],
            status=data['status'],
            role=data['role'],
            password_hash=data['password_hash'],
            is_active=data['is_active'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        staff.save()
        created_staff.append(staff)
        
        password_info = "No password (role selection)" if not data['password_hash'] else "Password: manager123"
        print(f"  ✓ Created: {data['first_name']} {data['last_name']} ({data['mobile']}) - {password_info}")
    except Exception as e:
        print(f"  ✗ Error creating {data['first_name']} {data['last_name']}: {e}")

print(f"\n✓ Created {len(created_staff)} staff members\n")

# ============================================
# INSERT MANAGERS
# ============================================
print("Inserting managers...")
print("-" * 70)

manager_data = [
    {
        'first_name': 'Arun',
        'last_name': 'Mehta',
        'email': 'arun@salon.com',
        'mobile': '9876543220',
        'salon': 'Glamour Salon - Main Branch',
        'password_hash': hash_password('manager123'),  # Password: manager123
        'role': 'manager',
        'permissions': [],
        'is_active': True,
        'status': 'active'
    },
    {
        'first_name': 'Kavita',
        'last_name': 'Desai',
        'email': 'kavita@salon.com',
        'mobile': '9876543221',
        'salon': 'Glamour Salon - Main Branch',
        'password_hash': hash_password('manager456'),  # Password: manager456
        'role': 'manager',
        'permissions': [],
        'is_active': True,
        'status': 'active'
    },
    {
        'first_name': 'Rahul',
        'last_name': 'Chopra',
        'email': 'owner@salon.com',
        'mobile': '9876543230',
        'salon': 'Glamour Salon - All Branches',
        'password_hash': hash_password('owner123'),  # Password: owner123
        'role': 'owner',
        'permissions': [],
        'is_active': True,
        'status': 'active'
    }
]

created_managers = []
for data in manager_data:
    try:
        # Check if manager already exists
        existing = Manager.objects(
            (Manager.email == data['email']) | (Manager.mobile == data['mobile'])
        ).first()
        if existing:
            print(f"  ⚠ Manager {data['first_name']} {data['last_name']} ({data['email']}) already exists - skipping")
            continue
        
        manager = Manager(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            mobile=data['mobile'],
            salon=data['salon'],
            password_hash=data['password_hash'],
            role=data['role'],
            permissions=data['permissions'],
            is_active=data['is_active'],
            status=data['status'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        manager.save()
        created_managers.append(manager)
        
        password_map = {
            'arun@salon.com': 'manager123',
            'kavita@salon.com': 'manager456',
            'owner@salon.com': 'owner123'
        }
        password = password_map.get(data['email'], 'Set')
        print(f"  ✓ Created {data['role']}: {data['first_name']} {data['last_name']} ({data['email']}) - Password: {password}")
    except Exception as e:
        print(f"  ✗ Error creating {data['first_name']} {data['last_name']}: {e}")

print(f"\n✓ Created {len(created_managers)} managers/owners\n")

# ============================================
# VERIFICATION
# ============================================
print("=" * 70)
print("VERIFICATION")
print("=" * 70)

total_staff = Staff.objects.count()
total_managers = Manager.objects.count()

print(f"Total Staff in database: {total_staff}")
print(f"Total Managers in database: {total_managers}\n")

# ============================================
# SUMMARY
# ============================================
print("=" * 70)
print("TEST ACCOUNTS CREATED")
print("=" * 70)

print("\n📋 STAFF (No Password - Role Selection):")
print("-" * 70)
staff_without_password = Staff.objects(password_hash=None, role='staff')
for staff in staff_without_password:
    print(f"  • {staff.first_name} {staff.last_name}")
    print(f"    Mobile: {staff.mobile}")
    print(f"    Role: {staff.role}")
    print(f"    Login: Select from dropdown, choose role\n")

print("\n📋 STAFF WITH PASSWORD (Manager Role):")
print("-" * 70)
staff_with_password = Staff.objects(password_hash__ne=None)
for staff in staff_with_password:
    print(f"  • {staff.first_name} {staff.last_name}")
    print(f"    Mobile: {staff.mobile}")
    print(f"    Password: manager123")
    print(f"    Role: {staff.role}\n")

print("\n📋 MANAGERS:")
print("-" * 70)
managers = Manager.objects(role='manager')
for manager in managers:
    print(f"  • {manager.first_name} {manager.last_name}")
    print(f"    Email: {manager.email}")
    print(f"    Mobile: {manager.mobile}")
    if manager.email == 'arun@salon.com':
        print(f"    Password: manager123")
    elif manager.email == 'kavita@salon.com':
        print(f"    Password: manager456")
    print(f"    Salon: {manager.salon}\n")

print("\n📋 OWNER:")
print("-" * 70)
owners = Manager.objects(role='owner')
for owner in owners:
    print(f"  • {owner.first_name} {owner.last_name}")
    print(f"    Email: {owner.email}")
    print(f"    Mobile: {owner.mobile}")
    print(f"    Password: owner123")
    print(f"    Salon: {owner.salon}\n")

print("=" * 70)
print("✅ DUMMY DATA INSERTED SUCCESSFULLY!")
print("=" * 70)

print("\n📝 HOW TO TEST LOGIN:")
print("-" * 70)
print("\n1️⃣  STAFF LOGIN (No Password):")
print("   • Select 'Staff' toggle")
print("   • Choose 'Rajesh Kumar' from dropdown")
print("   • Select role: staff")
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

print("\n" + "=" * 70)
print("📊 DATA STORAGE INFORMATION")
print("=" * 70)
print("\n✅ Collections Created:")
print("   • 'staffs' collection - Stores all staff members")
print("   • 'managers' collection - Stores all managers/owners")
print("\n✅ Dynamic Storage:")
print("   • When users login → Data retrieved from MongoDB")
print("   • When users signup → New records saved to MongoDB")
print("   • All authentication data stored in MongoDB automatically")
print("\n✅ Collections are automatically created when first document is inserted")

# Disconnect
disconnect()
print("\n✓ Disconnected from MongoDB")
print("\n✅ Database is ready for testing!\n")

