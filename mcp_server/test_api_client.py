#!/usr/bin/env python3
"""
Unit tests for API client functionality.

Tests both sync and async methods with error handling.
"""

import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.api_client import APIClient, APIClientError


def test_api_client_initialization():
    """Test API client initialization."""
    print("=== Testing API Client Initialization ===")
    
    # Test basic initialization
    client = APIClient("http://localhost:8080")
    assert client.base_url == "http://localhost:8080"
    assert client.api_key is None
    assert client.timeout == 30
    print("✓ Basic initialization works")
    
    # Test initialization with API key
    client = APIClient("http://localhost:8080", api_key="test-key", timeout=60)
    assert client.api_key == "test-key"
    assert client.timeout == 60
    print("✓ Initialization with API key works")
    
    # Test URL normalization
    client = APIClient("http://localhost:8080/")
    assert client.base_url == "http://localhost:8080"
    print("✓ URL normalization works")


def test_headers():
    """Test header generation."""
    print("\n=== Testing Headers ===")
    
    # Test headers without API key
    client = APIClient("http://localhost:8080")
    headers = client.get_headers()
    expected = {
        'Content-Type': 'application/json',
        'User-Agent': 'MCP-Server/1.0'
    }
    assert headers == expected
    print("✓ Headers without API key work")
    
    # Test headers with API key
    client = APIClient("http://localhost:8080", api_key="test-key")
    headers = client.get_headers()
    expected = {
        'Content-Type': 'application/json',
        'User-Agent': 'MCP-Server/1.0',
        'x-api-key': 'test-key'
    }
    assert headers == expected
    print("✓ Headers with API key work")


def test_url_building():
    """Test URL building functionality."""
    print("\n=== Testing URL Building ===")
    
    client = APIClient("http://localhost:8080")
    
    # Test relative endpoint
    url = client._build_url("tickets")
    assert url == "http://localhost:8080/tickets"
    print("✓ Relative endpoint URL building works")
    
    # Test endpoint with leading slash
    url = client._build_url("/tickets")
    assert url == "http://localhost:8080/tickets"
    print("✓ Leading slash endpoint URL building works")
    
    # Test absolute URL (should pass through)
    url = client._build_url("https://api.example.com/tickets")
    assert url == "https://api.example.com/tickets"
    print("✓ Absolute URL pass-through works")


def test_sync_methods_without_requests():
    """Test sync methods when requests is not available."""
    print("\n=== Testing Sync Methods (Mock) ===")
    
    client = APIClient("http://localhost:8080")
    
    # Mock successful response
    mock_response_data = {"status": "success", "data": []}
    
    with patch('shared.api_client.REQUESTS_AVAILABLE', False):
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = mock_response_data
            
            result = client.get_sync("tickets")
            assert result == mock_response_data
            mock_run.assert_called_once()
            print("✓ Sync GET fallback to async works")


async def test_async_methods_mock():
    """Test async methods with mocked responses."""
    print("\n=== Testing Async Methods (Mock) ===")
    
    client = APIClient("http://localhost:8080", api_key="test-key")
    
    # Test that methods can be called (actual HTTP testing would require a real server)
    try:
        # This will fail due to connection, but we can test the method exists
        await client.get("tickets")
    except APIClientError:
        print("✓ Async GET method exists and handles errors")
    
    try:
        await client.post("tickets", {"title": "test"})
    except APIClientError:
        print("✓ Async POST method exists and handles errors")
    
    try:
        await client.put("tickets/1", {"title": "updated"})
    except APIClientError:
        print("✓ Async PUT method exists and handles errors")


def test_error_handling():
    """Test error handling."""
    print("\n=== Testing Error Handling ===")
    
    client = APIClient("http://invalid-url-that-should-not-exist:9999")
    
    # Test sync error handling
    try:
        client.get_sync("test")
        assert False, "Should have raised APIClientError"
    except APIClientError as e:
        assert "failed" in str(e).lower()
        print("✓ Sync error handling works")


async def main():
    """Run all API client tests."""
    print("MCP Server API Client Test")
    print("=" * 40)
    
    try:
        test_api_client_initialization()
        test_headers()
        test_url_building()
        test_sync_methods_without_requests()
        await test_async_methods_mock()
        test_error_handling()
        
        print("\n✅ All API client tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ API client test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))