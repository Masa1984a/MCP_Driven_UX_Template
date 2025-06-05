#!/usr/bin/env python3
"""
Unit tests for authentication providers.

Tests different authentication methods and the auth manager.
"""

import sys
import asyncio
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from auth.providers import (
    APIKeyAuthProvider, NoAuthProvider, AuthManager, 
    create_auth_manager, AuthResult
)


async def test_api_key_auth():
    """Test API key authentication provider."""
    print("=== Testing API Key Auth Provider ===")
    
    provider = APIKeyAuthProvider()
    
    # Test valid API key
    credentials = {"api_key": "test-api-key-123"}
    result = await provider.authenticate(credentials)
    assert result.success == True
    assert result.user_id == "api_key_user"
    assert result.user_info["auth_method"] == "api_key"
    print("✓ Valid API key authentication works")
    
    # Test missing API key
    credentials = {}
    result = await provider.authenticate(credentials)
    assert result.success == False
    assert "not provided" in result.error_message
    print("✓ Missing API key properly rejected")
    
    # Test headers
    credentials = {"api_key": "test-key"}
    headers = provider.get_auth_headers(credentials)
    assert headers["x-api-key"] == "test-key"
    assert headers["Content-Type"] == "application/json"
    print("✓ Auth headers generated correctly")
    
    # Test credential validation
    assert provider.validate_credentials({"api_key": "valid-key"}) == True
    assert provider.validate_credentials({"api_key": ""}) == False
    assert provider.validate_credentials({}) == False
    print("✓ Credential validation works")


async def test_no_auth():
    """Test no authentication provider."""
    print("\n=== Testing No Auth Provider ===")
    
    provider = NoAuthProvider()
    
    # Test authentication (should always succeed)
    result = await provider.authenticate({})
    assert result.success == True
    assert result.user_id == "anonymous"
    assert result.user_info["auth_method"] == "none"
    print("✓ No-auth always succeeds")
    
    # Test headers
    headers = provider.get_auth_headers({})
    assert headers["Content-Type"] == "application/json"
    assert "x-api-key" not in headers
    print("✓ No-auth headers don't include API key")
    
    # Test validation (should always succeed)
    assert provider.validate_credentials({}) == True
    assert provider.validate_credentials({"anything": "goes"}) == True
    print("✓ No-auth validation always succeeds")


async def test_auth_manager():
    """Test authentication manager."""
    print("\n=== Testing Auth Manager ===")
    
    # Test with API key provider
    api_provider = APIKeyAuthProvider()
    manager = AuthManager(api_provider)
    
    credentials = {"api_key": "test-key"}
    result = await manager.authenticate(credentials)
    assert result.success == True
    print("✓ Auth manager delegates to provider correctly")
    
    headers = manager.get_auth_headers(credentials)
    assert headers["x-api-key"] == "test-key"
    print("✓ Auth manager headers delegation works")
    
    assert manager.validate_credentials(credentials) == True
    print("✓ Auth manager validation delegation works")


def test_auth_factory():
    """Test authentication factory function."""
    print("\n=== Testing Auth Factory ===")
    
    # Test API key auth creation
    manager = create_auth_manager("api_key")
    assert isinstance(manager.provider, APIKeyAuthProvider)
    print("✓ API key auth manager creation works")
    
    # Test no auth creation
    manager = create_auth_manager("none")
    assert isinstance(manager.provider, NoAuthProvider)
    print("✓ No auth manager creation works")
    
    # Test custom API key header
    manager = create_auth_manager("api_key", api_key_header="Authorization")
    assert manager.provider.api_key_header == "Authorization"
    print("✓ Custom API key header works")
    
    # Test invalid auth type
    try:
        create_auth_manager("invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported authentication type" in str(e)
        print("✓ Invalid auth type properly rejected")
    
    # Test OAuth (not implemented)
    try:
        create_auth_manager("oauth")
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        print("✓ OAuth not implemented error works")


async def test_auth_result():
    """Test AuthResult data structure."""
    print("\n=== Testing AuthResult ===")
    
    # Test successful result
    result = AuthResult(
        success=True,
        user_id="user123",
        user_info={"name": "Test User"}
    )
    assert result.success == True
    assert result.user_id == "user123"
    assert result.user_info["name"] == "Test User"
    assert result.error_message is None
    print("✓ Successful AuthResult works")
    
    # Test failure result
    result = AuthResult(
        success=False,
        error_message="Authentication failed"
    )
    assert result.success == False
    assert result.user_id is None
    assert result.error_message == "Authentication failed"
    print("✓ Failed AuthResult works")


async def main():
    """Run all authentication tests."""
    print("MCP Server Authentication Test")
    print("=" * 40)
    
    try:
        await test_api_key_auth()
        await test_no_auth()
        await test_auth_manager()
        test_auth_factory()
        await test_auth_result()
        
        print("\n✅ All authentication tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Authentication test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))