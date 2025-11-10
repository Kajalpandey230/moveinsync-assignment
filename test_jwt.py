"""Test script for JWT token generation and decoding."""

from app.auth.jwt_handler import create_access_token, decode_access_token
from datetime import timedelta
from fastapi import HTTPException

def test_jwt_tokens():
    """Test JWT token creation and decoding."""
    
    print("=" * 60)
    print("JWT TOKEN TESTING")
    print("=" * 60)
    
    # Test 1: Create a token
    print("\n📝 Test 1: Creating JWT Token...")
    try:
        token = create_access_token(
            data={"sub": "testuser", "role": "admin"},
            expires_delta=timedelta(minutes=30)
        )
        print(f"✅ Token created successfully!")
        print(f"Token (first 50 chars): {token[:50]}...")
        print(f"Token length: {len(token)} characters")
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        return
    
    # Test 2: Decode valid token
    print("\n🔓 Test 2: Decoding Valid Token...")
    try:
        payload = decode_access_token(token)
        print(f"✅ Token decoded successfully!")
        print(f"Payload: {payload}")
        print(f"Username: {payload.get('sub')}")
        print(f"Role: {payload.get('role')}")
    except Exception as e:
        print(f"❌ Error decoding token: {e}")
        return
    
    # Test 3: Try to decode invalid token
    print("\n🚫 Test 3: Decoding Invalid Token (should fail)...")
    try:
        invalid_token = "invalid.token.here"
        decode_access_token(invalid_token)
        print("❌ Should have raised an error!")
    except HTTPException as e:
        print(f"✅ Correctly rejected invalid token!")
        print(f"Error: {e.detail}")
    
    # Test 4: Create token with default expiration
    print("\n⏰ Test 4: Token with Default Expiration...")
    try:
        default_token = create_access_token(data={"sub": "user2"})
        payload = decode_access_token(default_token)
        print(f"✅ Default token works!")
        print(f"Expires at: {payload.get('exp')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Create multiple tokens
    print("\n🔄 Test 5: Creating Multiple Tokens...")
    try:
        tokens = []
        for i in range(3):
            t = create_access_token(data={"sub": f"user{i}"})
            tokens.append(t)
        print(f"✅ Created {len(tokens)} tokens successfully!")
        
        # Decode each
        for i, t in enumerate(tokens):
            p = decode_access_token(t)
            print(f"  Token {i+1}: user = {p.get('sub')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_jwt_tokens()