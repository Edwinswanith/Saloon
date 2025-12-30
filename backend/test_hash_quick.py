"""
Quick script to test the bcrypt hash against common passwords
Run this from the backend directory: python test_hash_quick.py
"""

import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.auth import verify_password
    
    # The hash you provided
    hash_to_test = "$2b$12$XGOSaiWjJMdbVkS9RzD/gOXFkFVomffY3.dEOsD8/7NZ6W.x.uDfK"
    
    # Common passwords to test
    passwords_to_test = [
        "manager123",
        "owner123", 
        "manager456",
        "password",
        "admin",
        "123456",
        "salon123",
        "test123",
        "admin123",
        "salon",
        "password123"
    ]
    
    print("=" * 70)
    print("TESTING BCRYPT HASH")
    print("=" * 70)
    print(f"\nHash: {hash_to_test}\n")
    print("Testing passwords...\n")
    
    found = False
    for password in passwords_to_test:
        try:
            if verify_password(password, hash_to_test):
                print(f"✅ ✅ ✅ MATCH FOUND! ✅ ✅ ✅")
                print(f"\n   Password: '{password}'")
                print(f"   Hash: {hash_to_test}\n")
                found = True
                break
            else:
                print(f"   ❌ '{password}' - No match")
        except Exception as e:
            print(f"   ⚠️  '{password}' - Error: {e}")
    
    if not found:
        print("\n⚠️  None of the tested passwords matched.")
        print("   The password might be custom or different.")
        print("   You can add more passwords to test in the 'passwords_to_test' list.")
    
    print("\n" + "=" * 70)
    print("✅ Testing complete!\n")
    
except ImportError as e:
    print("Error: Could not import utils.auth")
    print("Make sure you're running this from the backend directory")
    print(f"Error details: {e}")
    print("\nAlternative: Install bcrypt and use the standalone script")
    print("  pip install bcrypt")
    print("  python test_bcrypt_standalone.py")

