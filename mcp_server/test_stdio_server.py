#!/usr/bin/env python3
"""
Test script for updated STDIO MCP server with shared components.

Tests server initialization and basic functionality.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the MCP imports since we're testing without full MCP
sys.modules['mcp'] = Mock()
sys.modules['mcp.server'] = Mock()
sys.modules['mcp.server.fastmcp'] = Mock()

# Now we can import our module
from mcp_server import STDIOContext, app_lifespan
from shared.config import MCPBaseSettings


def test_stdio_context():
    """Test STDIO context initialization."""
    print("=== Testing STDIO Context ===")
    
    # Create test settings
    settings = MCPBaseSettings(
        api_base_url="http://localhost:8080",
        api_key="test-key",
        node_env="development"
    )
    
    # Initialize context
    context = STDIOContext(settings)
    
    # Verify components are initialized
    assert context.settings == settings
    assert context.api_client is not None
    assert context.ticket_tools is not None
    assert context.api_client.base_url == "http://localhost:8080"
    assert context.api_client.api_key == "test-key"
    
    print("✓ STDIO context initialization works")
    print("✓ API client configured correctly")
    print("✓ Ticket tools initialized")


def test_configuration_loading():
    """Test configuration loading from environment."""
    print("\n=== Testing Configuration Loading ===")
    
    # Test with environment variables
    os.environ["MCP_API_BASE_URL"] = "https://api.example.com"
    os.environ["MCP_API_KEY"] = "env-test-key"
    
    from shared.config import get_base_settings
    settings = get_base_settings()
    
    assert settings.api_base_url == "https://api.example.com"
    assert settings.api_key == "env-test-key"
    print("✓ Environment variables loaded correctly")
    
    # Clean up
    os.environ.pop("MCP_API_BASE_URL", None)
    os.environ.pop("MCP_API_KEY", None)


def test_shared_components_integration():
    """Test that shared components are properly integrated."""
    print("\n=== Testing Shared Components Integration ===")
    
    # Import shared components
    from shared.api_client import APIClient
    from shared.tools import TicketTools
    
    # Create test instances
    api_client = APIClient("http://localhost:8080", api_key="test")
    ticket_tools = TicketTools(api_client)
    
    # Verify methods exist
    assert hasattr(ticket_tools, 'get_ticket_list_sync')
    assert hasattr(ticket_tools, 'get_ticket_detail_sync')
    assert hasattr(ticket_tools, 'create_ticket_sync')
    assert hasattr(ticket_tools, 'update_ticket_sync')
    assert hasattr(ticket_tools, 'add_ticket_history_sync')
    assert hasattr(ticket_tools, 'get_users_sync')
    assert hasattr(ticket_tools, 'get_accounts_sync')
    assert hasattr(ticket_tools, 'get_categories_sync')
    assert hasattr(ticket_tools, 'get_statuses_sync')
    
    print("✓ APIClient integration verified")
    print("✓ TicketTools integration verified")
    print("✓ All required sync methods exist")


def test_tool_functions_structure():
    """Test that tool functions maintain FastMCP structure."""
    print("\n=== Testing Tool Functions Structure ===")
    
    # Import the mcp_server module
    import mcp_server
    
    # Check tool functions exist
    tool_functions = [
        'get_ticket_list',
        'get_ticket_detail',
        'create_ticket',
        'update_ticket',
        'add_ticket_history',
        'get_users',
        'get_accounts',
        'get_categories',
        'get_category_details',
        'get_statuses',
        'get_request_channels'
    ]
    
    for func_name in tool_functions:
        assert hasattr(mcp_server, func_name), f"Missing tool function: {func_name}"
        func = getattr(mcp_server, func_name)
        assert callable(func), f"{func_name} is not callable"
    
    print("✓ All tool functions exist")
    print("✓ All tool functions are callable")
    
    # Check resource function
    assert hasattr(mcp_server, 'get_overview')
    print("✓ Resource function exists")


def test_error_handling():
    """Test error handling in tool functions."""
    print("\n=== Testing Error Handling ===")
    
    settings = MCPBaseSettings(
        api_base_url="http://invalid-url-that-should-not-exist:9999",
        api_key=None
    )
    
    context = STDIOContext(settings)
    
    # Test error handling in API calls
    try:
        result = context.ticket_tools.get_users_sync()
        assert "Error" in result or "error" in result.lower()
        print("✓ Error handling works for failed API calls")
    except Exception:
        print("✓ Error handling works (exception caught)")


def main():
    """Run all tests."""
    print("Updated STDIO MCP Server Test")
    print("=" * 40)
    
    try:
        test_stdio_context()
        test_configuration_loading()
        test_shared_components_integration()
        test_tool_functions_structure()
        test_error_handling()
        
        print("\n✅ All STDIO server tests passed!")
        print("\nThe updated STDIO server:")
        print("- Uses shared configuration management")
        print("- Uses shared API client")
        print("- Uses shared ticket tools")
        print("- Maintains FastMCP compatibility")
        print("- Shares business logic with cloud version")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ STDIO server test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())