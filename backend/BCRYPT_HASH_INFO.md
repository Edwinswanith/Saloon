# BCrypt Hash Information

## Your Hash
```
$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK
```

## Hash Details
- **Format**: `$2b$` (bcrypt variant)
- **Cost Factor**: `12` (2^12 = 4,096 iterations)
- **Length**: 60 characters (standard bcrypt hash length)
- **Valid**: ✅ This is a valid bcrypt hash format

## Important Note
**BCrypt is a one-way hashing function** - you **cannot** convert it back to the original password. You can only:
1. Test if a password matches the hash
2. Generate a new hash from a password

## How to Test Passwords

### Method 1: Using Python (if bcrypt is installed)
```python
import bcrypt

hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
password = "your_password_here"

if bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8')):
    print("✅ Password matches!")
else:
    print("❌ Password does not match")
```

### Method 2: Using Your Auth Utils
```python
from utils.auth import verify_password

hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
password = "your_password_here"

if verify_password(password, hash):
    print("✅ Password matches!")
else:
    print("❌ Password does not match")
```

## Common Passwords to Test
Try these common passwords:
- `manager123`
- `owner123`
- `manager456`
- `password`
- `admin`
- `123456`
- `salon123`
- `test123`

## How to Use This Hash in Your Database

### For Staff Member
```python
from models import Staff

staff = Staff.objects(mobile="9876543210").first()
staff.password_hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
staff.save()
```

### For Manager
```python
from models import Manager

manager = Manager.objects(email="manager@salon.com").first()
manager.password_hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
manager.save()
```

## Generate a New Hash

If you want to create a new hash for a password:

```python
from utils.auth import hash_password

new_hash = hash_password("your_new_password")
print(new_hash)
```

Or using bcrypt directly:
```python
import bcrypt

password = "your_new_password"
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hash)
```

## Quick Test Script

Create a file `test_hash.py`:
```python
from utils.auth import verify_password

hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"

# Test passwords
passwords = ["manager123", "owner123", "manager456", "password", "admin"]

for pwd in passwords:
    if verify_password(pwd, hash):
        print(f"✅ FOUND: Password is '{pwd}'")
        break
    else:
        print(f"❌ '{pwd}' - No match")
```

Run it:
```bash
cd backend
python test_hash.py
```

## Security Note
- Never share the original password if you find it
- BCrypt hashes are safe to store in databases
- The cost factor 12 means it takes significant time to compute (good for security)
- Each password should have a unique hash (different salt)

