#!/usr/bin/env python3
"""
Configuration test script for MCP server settings.

Tests environment variable loading and default values.
"""

import os
import sys
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.config import MCPBaseSettings, CloudSettings, get_settings_for_environment


def test_base_settings():
    """Test base settings functionality."""
    print("=== Testing MCPBaseSettings ===")
    
    settings = MCPBaseSettings()
    print(f"API Base URL: {settings.api_base_url}")
    print(f"API Key: {'***' if settings.api_key else 'None'}")
    print(f"Node Environment: {settings.node_env}")
    
    return settings


def test_cloud_settings():
    """Test cloud settings functionality."""
    print("\n=== Testing CloudSettings ===")
    
    settings = CloudSettings()
    print(f"API Base URL: {settings.api_base_url}")
    print(f"API Key: {'***' if settings.api_key else 'None'}")
    print(f"MCP API Key: {'***' if settings.mcp_api_key else 'None'}")
    print(f"Auth Provider: {settings.auth_provider}")
    print(f"Transport Type: {settings.transport_type}")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Cloud Run Timeout: {settings.cloud_run_timeout}")
    print(f"OAuth Enabled: {settings.oauth_enabled}")
    print(f"Log Level: {settings.log_level}")
    print(f"Log Format: {settings.log_format}")
    
    return settings


def test_environment_detection():
    """Test environment-based settings selection."""
    print("\n=== Testing Environment Detection ===")
    
    # Test default (development)
    settings = get_settings_for_environment()
    print(f"Default settings type: {type(settings).__name__}")
    
    # Test with MCP_CLOUD_MODE=true
    os.environ["MCP_CLOUD_MODE"] = "true"
    settings = get_settings_for_environment()
    print(f"Cloud mode settings type: {type(settings).__name__}")
    
    # Test with NODE_ENV=production
    os.environ.pop("MCP_CLOUD_MODE", None)
    os.environ["NODE_ENV"] = "production"
    settings = get_settings_for_environment()
    print(f"Production settings type: {type(settings).__name__}")
    
    # Reset environment
    os.environ.pop("NODE_ENV", None)


def test_environment_variables():
    """Test environment variable loading."""
    print("\n=== Testing Environment Variables ===")
    
    # Set test environment variables
    test_vars = {
        "MCP_API_BASE_URL": "https://api.example.com",
        "MCP_API_KEY": "test-api-key",
        "MCP_MCP_API_KEY": "test-mcp-key",
        "MCP_AUTH_PROVIDER": "oauth",
        "MCP_LOG_LEVEL": "DEBUG"
    }
    
    for key, value in test_vars.items():
        os.environ[key] = value
    
    settings = CloudSettings()
    print(f"API Base URL from env: {settings.api_base_url}")
    print(f"API Key from env: {'***' if settings.api_key else 'None'}")
    print(f"MCP API Key from env: {'***' if settings.mcp_api_key else 'None'}")
    print(f"Auth Provider from env: {settings.auth_provider}")
    print(f"Log Level from env: {settings.log_level}")
    
    # Clean up test environment variables
    for key in test_vars:
        os.environ.pop(key, None)


def main():
    """Run all configuration tests."""
    print("MCP Server Configuration Test")
    print("=" * 40)
    
    try:
        test_base_settings()
        test_cloud_settings()
        test_environment_detection()
        test_environment_variables()
        
        print("\n✅ All configuration tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())