#!/usr/bin/env python3
"""
Basic test for cloud MCP server functionality.

Tests server initialization, configuration, and component integration.
"""

import sys
import asyncio
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.config import CloudSettings
from cloud_mcp_server import CloudMCPServer


async def test_server_initialization():
    """Test cloud MCP server initialization."""
    print("=== Testing Server Initialization ===")
    
    # Create test settings
    settings = CloudSettings(
        api_base_url="http://localhost:8080",
        api_key="test-key",
        auth_provider="api_key",
        host="127.0.0.1",
        port=8081
    )
    
    # Initialize server
    server = CloudMCPServer(settings)
    
    # Test basic properties
    assert server.settings.api_base_url == "http://localhost:8080"
    assert server.settings.auth_provider == "api_key"
    assert server.settings.host == "127.0.0.1"
    assert server.settings.port == 8081
    print("✓ Server settings configured correctly")
    
    # Test initialization
    await server.initialize()
    
    # Verify components are initialized
    assert server.api_client is not None
    assert server.ticket_tools is not None
    assert server.auth_manager is not None
    assert server.sse_transport is not None
    print("✓ Server components initialized")
    
    # Test cleanup
    await server.cleanup()
    print("✓ Server cleanup completed")


async def test_tool_execution():
    """Test tool execution functionality."""
    print("\n=== Testing Tool Execution ===")
    
    settings = CloudSettings(
        api_base_url="http://localhost:8080",
        api_key="test-key",
        auth_provider="none"  # Use no auth for testing
    )
    
    server = CloudMCPServer(settings)
    await server.initialize()
    
    # Test tool method mapping
    try:
        # This will fail because we don't have a real API, but we can test the method exists
        await server._execute_tool("get_accounts", {})
    except Exception as e:
        # Expected to fail due to no real API connection
        assert "Error" in str(e) or "failed" in str(e).lower()
        print("✓ Tool execution method works (expected API error)")
    
    # Test invalid tool
    try:
        await server._execute_tool("invalid_tool", {})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown tool" in str(e)
        print("✓ Invalid tool properly rejected")
    
    await server.cleanup()


async def test_message_handling():
    """Test message handling functionality."""
    print("\n=== Testing Message Handling ===")
    
    settings = CloudSettings(
        api_base_url="http://localhost:8080",
        auth_provider="none"
    )
    
    server = CloudMCPServer(settings)
    await server.initialize()
    
    # Test that message handlers are registered
    assert "tool_call" in server.sse_transport.message_handlers
    assert "ping" in server.sse_transport.message_handlers
    assert "list_tools" in server.sse_transport.message_handlers
    print("✓ Message handlers registered")
    
    # Test ping handler
    connection_id = await server.sse_transport.connection_manager.connect("127.0.0.1", {})
    
    ping_response = await server.sse_transport.handle_incoming_message(
        connection_id,
        {"type": "ping", "id": "test-ping"}
    )
    
    assert ping_response["type"] == "pong"
    assert "timestamp" in ping_response
    assert ping_response["connection_id"] == connection_id
    print("✓ Ping message handler works")
    
    # Test list tools handler
    tools_response = await server.sse_transport.handle_incoming_message(
        connection_id,
        {"type": "list_tools", "id": "test-tools"}
    )
    
    assert tools_response["type"] == "tools_list"
    assert "tools" in tools_response
    assert len(tools_response["tools"]) > 0
    
    # Check for expected tools
    tool_names = [tool["name"] for tool in tools_response["tools"]]
    assert "get_ticket_list" in tool_names
    assert "create_ticket" in tool_names
    assert "get_users" in tool_names
    print("✓ List tools handler works")
    
    await server.cleanup()


def test_settings_validation():
    """Test configuration settings validation."""
    print("\n=== Testing Settings Validation ===")
    
    # Test default settings
    settings = CloudSettings()
    assert settings.auth_provider == "api_key"
    assert settings.transport_type == "sse"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    print("✓ Default settings work")
    
    # Test custom settings
    settings = CloudSettings(
        api_base_url="https://api.example.com",
        auth_provider="oauth",
        host="127.0.0.1",
        port=9000,
        log_level="DEBUG"
    )
    assert settings.api_base_url == "https://api.example.com"
    assert settings.auth_provider == "oauth"
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"
    print("✓ Custom settings work")


async def main():
    """Run all cloud server tests."""
    print("Cloud MCP Server Test")
    print("=" * 40)
    
    try:
        await test_server_initialization()
        await test_tool_execution()
        await test_message_handling()
        test_settings_validation()
        
        print("\n✅ All cloud server tests passed!")
        print("\nNote: To fully test the server, run:")
        print("  python cloud_mcp_server.py")
        print("  # Then test endpoints with curl or similar")
        return 0
        
    except Exception as e:
        print(f"\n❌ Cloud server test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))