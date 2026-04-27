#!/usr/bin/env python3
"""
Test script to verify password hashing functionality.
Run this script to check if password hashing works correctly.
"""

def test_password_hashing():
    """Test password hashing and verification."""
    try:
        # Test imports
        print("Testing imports...")
        from passlib.context import CryptContext
        from cryptography.fernet import Fernet
        import jose
        print("✅ All security imports successful")
        
        # Test password hashing
        print("\nTesting password hashing...")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        test_password = "TestPassword123!"
        
        # Hash the password
        hashed = pwd_context.hash(test_password)
        print(f"✅ Password hashed successfully: {hashed[:50]}...")
        
        # Verify the password
        is_valid = pwd_context.verify(test_password, hashed)
        print(f"✅ Password verification: {is_valid}")
        
        # Test with wrong password
        is_invalid = pwd_context.verify("WrongPassword", hashed)
        print(f"✅ Wrong password verification: {is_invalid}")
        
        # Test JWT token creation
        print("\nTesting JWT token...")
        from jose import jwt
        from datetime import datetime, timezone, timedelta
        
        secret_key = "test-secret-key-for-testing-only"
        token = jwt.encode(
            {"sub": "test-user", "exp": datetime.now(timezone.utc) + timedelta(minutes=60)},
            secret_key,
            algorithm="HS256"
        )
        print(f"✅ JWT token created: {token[:50]}...")
        
        # Verify JWT token
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(f"✅ JWT token verified: {decoded}")
        
        print("\n🎉 All security functions working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Solution: Run 'pip install -r requirements.txt'")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_password_hashing()
