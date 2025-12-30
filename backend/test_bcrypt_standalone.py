"""
BCrypt Password Testing Utility (Standalone)

This script helps you test bcrypt hashes without requiring the full app setup.
"""

import bcrypt

# The bcrypt hash you provided
provided_hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"

print("=" * 70)
print("BCRYPT PASSWORD UTILITY")
print("=" * 70)

# Test common passwords
test_passwords = [
    "manager123",
    "owner123",
    "manager456",
    "password",
    "admin",
    "123456",
    "salon123",
    "test123",
    "admin123",
    "salon"
]

print("\n🔍 Testing common passwords against the hash:")
print("-" * 70)
print(f"Hash: {provided_hash}\n")

found = False
for password in test_passwords:
    try:
        # Verify password against hash
        if bcrypt.checkpw(password.encode('utf-8'), provided_hash.encode('utf-8')):
            print(f"✅ MATCH FOUND!")
            print(f"   Password: {password}")
            print(f"   Hash: {provided_hash}")
            found = True
            break
        else:
            print(f"   ❌ {password} - No match")
    except Exception as e:
        print(f"   ⚠️  {password} - Error: {e}")

if not found:
    print("\n⚠️  None of the common passwords matched.")
    print("   The password might be different or custom.")
    print("   You can test your own password by modifying this script.")

print("\n" + "=" * 70)
print("GENERATE NEW HASH")
print("=" * 70)

# Example: Generate hash for a new password
print("\n📝 Example - Generate hash for 'newpassword123':")
example_hash = bcrypt.hashpw('newpassword123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"   Hash: {example_hash}")

print("\n📝 To generate a hash in Python:")
print("   import bcrypt")
print("   password = 'your_password'")
print("   hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')")
print("   print(hash)")

print("\n" + "=" * 70)
print("VERIFY HASH FORMAT")
print("=" * 70)

# Verify the hash format
print(f"\nProvided hash: {provided_hash}")
print(f"Hash length: {len(provided_hash)} characters")
print(f"Hash prefix: {provided_hash[:7]}")

if provided_hash.startswith("$2b$") or provided_hash.startswith("$2a$") or provided_hash.startswith("$2y$"):
    print("✅ Valid bcrypt hash format")
    
    # Extract cost factor
    try:
        parts = provided_hash.split('$')
        if len(parts) >= 3:
            cost = parts[2]
            print(f"Cost factor: {cost} (12 rounds = 2^12 = 4096 iterations)")
    except:
        pass
else:
    print("❌ Invalid bcrypt hash format")

print("\n" + "=" * 70)
print("USAGE IN YOUR CODE")
print("=" * 70)

print("""
To use this hash in your database:

1. For Staff (in MongoDB):
   staff.password_hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
   staff.save()

2. For Manager (in MongoDB):
   manager.password_hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
   manager.save()

3. To test login programmatically:
   from utils.auth import verify_password
   if verify_password("your_password", hash):
       print("Password matches!")
""")

print("\n" + "=" * 70)
print("TEST YOUR OWN PASSWORD")
print("=" * 70)
print("\nTo test a custom password, modify the 'test_passwords' list in this script")
print("or use this code:")
print("""
import bcrypt
hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
password = "your_password_here"
if bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8')):
    print("Password matches!")
else:
    print("Password does not match!")
""")

print("\n✅ Done!\n")

