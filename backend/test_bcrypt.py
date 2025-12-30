"""
BCrypt Password Testing Utility

This script helps you:
1. Test if a password matches a bcrypt hash
2. Generate new bcrypt hashes
3. Verify existing hashes
"""

from utils.auth import hash_password, verify_password

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
    "test123"
]

print("\n🔍 Testing common passwords against the hash:")
print("-" * 70)

found = False
for password in test_passwords:
    if verify_password(password, provided_hash):
        print(f"✅ MATCH FOUND!")
        print(f"   Password: {password}")
        print(f"   Hash: {provided_hash}")
        found = True
        break
    else:
        print(f"   ❌ {password} - No match")

if not found:
    print("\n⚠️  None of the common passwords matched.")
    print("   The password might be different or custom.")

print("\n" + "=" * 70)
print("GENERATE NEW HASH")
print("=" * 70)

# Option to generate new hash
print("\nTo generate a new bcrypt hash for a password, use:")
print("  from utils.auth import hash_password")
print("  hash = hash_password('your_password')")
print("  print(hash)")

# Example: Generate hash for a new password
print("\n📝 Example - Generate hash for 'newpassword123':")
example_hash = hash_password('newpassword123')
print(f"   Hash: {example_hash}")

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
            print(f"Cost factor: {cost}")
    except:
        pass
else:
    print("❌ Invalid bcrypt hash format")

print("\n" + "=" * 70)
print("USAGE IN YOUR CODE")
print("=" * 70)

print("""
To use this hash in your database:

1. For Staff:
   staff.password_hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
   staff.save()

2. For Manager:
   manager.password_hash = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
   manager.save()

3. To test login:
   from utils.auth import verify_password
   if verify_password("your_password", hash):
       print("Password matches!")
""")

print("\n✅ Done!\n")

