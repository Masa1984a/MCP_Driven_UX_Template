#!/usr/bin/env python3
"""
Unit tests for SSE transport implementation.

Tests SSE message formatting, connection management, and transport functionality.
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from transport.sse import (
    SSEMessage, SSEConnection, SSEConnectionManager, SSETransport
)


def test_sse_message():
    """Test SSE message formatting."""
    print("=== Testing SSE Message ===")
    
    # Test basic message
    message = SSEMessage(
        id="test-123",
        event="test-event",
        data={"key": "value", "number": 42}
    )
    
    sse_format = message.to_sse_format()
    lines = sse_format.split('\n')
    
    assert lines[0] == "id: test-123"
    assert lines[1] == "event: test-event"
    assert lines[2] == 'data: {"key": "value", "number": 42}'
    assert lines[3] == ""  # Empty line at end
    print("✓ SSE message formatting works")
    
    # Test data can be parsed back
    data_line = lines[2]
    json_data = data_line.replace("data: ", "")
    parsed_data = json.loads(json_data)
    assert parsed_data["key"] == "value"
    assert parsed_data["number"] == 42
    print("✓ SSE message data is valid JSON")


def test_sse_connection():
    """Test SSE connection management."""
    print("\n=== Testing SSE Connection ===")
    
    # Test connection creation
    connection = SSEConnection(
        connection_id="conn-123",
        client_ip="192.168.1.1",
        connected_at=datetime.now(),
        last_ping=datetime.now(),
        credentials={"api_key": "test-key"}
    )
    
    assert connection.connection_id == "conn-123"
    assert connection.client_ip == "192.168.1.1"
    assert connection.is_active == True
    print("✓ SSE connection creation works")
    
    # Test expiration (not expired)
    assert connection.is_expired(timeout_seconds=900) == False
    print("✓ Fresh connection not expired")
    
    # Test expiration (expired)
    old_connection = SSEConnection(
        connection_id="old-conn",
        client_ip="192.168.1.2",
        connected_at=datetime.now() - timedelta(seconds=1000),
        last_ping=datetime.now() - timedelta(seconds=1000),
        credentials={}
    )
    assert old_connection.is_expired(timeout_seconds=900) == True
    print("✓ Old connection properly expired")


async def test_connection_manager():
    """Test SSE connection manager."""
    print("\n=== Testing Connection Manager ===")
    
    manager = SSEConnectionManager(connection_timeout=60)  # Short timeout for testing
    
    # Test connection creation
    conn_id = await manager.connect("192.168.1.1", {"api_key": "test"})
    assert conn_id is not None
    assert len(conn_id) > 0
    print("✓ Connection creation works")
    
    # Test connection retrieval
    connection = manager.get_connection(conn_id)
    assert connection is not None
    assert connection.connection_id == conn_id
    assert connection.client_ip == "192.168.1.1"
    print("✓ Connection retrieval works")
    
    # Test active connections count
    assert manager.get_active_connections_count() == 1
    print("✓ Active connections count works")
    
    # Test ping
    ping_result = await manager.ping_connection(conn_id)
    assert ping_result == True
    print("✓ Connection ping works")
    
    # Test disconnection
    await manager.disconnect(conn_id)
    assert manager.get_connection(conn_id) is None
    assert manager.get_active_connections_count() == 0
    print("✓ Connection disconnection works")
    
    # Test ping non-existent connection
    ping_result = await manager.ping_connection("non-existent")
    assert ping_result == False
    print("✓ Ping non-existent connection handled")


async def test_sse_transport():
    """Test SSE transport functionality."""
    print("\n=== Testing SSE Transport ===")
    
    transport = SSETransport()
    
    # Test message handler registration
    async def test_handler(connection_id, message):
        return {"type": "response", "echo": message}
    
    transport.register_message_handler("test", test_handler)
    assert "test" in transport.message_handlers
    print("✓ Message handler registration works")
    
    # Test error handler registration
    async def error_handler(connection_id, error):
        print(f"Error in connection {connection_id}: {error}")
    
    transport.register_error_handler(error_handler)
    assert transport.error_handler is not None
    print("✓ Error handler registration works")
    
    # Test connection creation
    conn_id = await transport.connection_manager.connect("127.0.0.1", {})
    assert conn_id is not None
    print("✓ Transport connection creation works")
    
    # Test message sending
    success = await transport.send_message(conn_id, "test-event", {"data": "test"})
    assert success == True
    print("✓ Message sending works")
    
    # Test message sending to non-existent connection
    success = await transport.send_message("non-existent", "test", {})
    assert success == False
    print("✓ Message sending to invalid connection handled")
    
    # Test incoming message handling
    response = await transport.handle_incoming_message(conn_id, {
        "type": "test",
        "data": "test-data"
    })
    assert response["type"] == "response"
    assert response["echo"]["data"] == "test-data"
    print("✓ Incoming message handling works")
    
    # Test unknown message type handling
    response = await transport.handle_incoming_message(conn_id, {
        "type": "unknown"
    })
    assert response["type"] == "error"
    assert "Unknown message type" in response["error"]
    print("✓ Unknown message type handling works")
    
    # Test broadcast
    conn_id2 = await transport.connection_manager.connect("127.0.0.2", {})
    sent_count = await transport.broadcast_message("broadcast", {"msg": "hello"})
    assert sent_count == 2
    print("✓ Message broadcasting works")


async def test_sse_stream():
    """Test SSE stream generation."""
    print("\n=== Testing SSE Stream ===")
    
    transport = SSETransport()
    conn_id = await transport.connection_manager.connect("127.0.0.1", {})
    
    # Test stream generation (collect first few messages)
    message_count = 0
    async for message in transport.create_sse_stream(conn_id):
        assert message.startswith("id: ")
        assert "event: " in message
        assert "data: " in message
        
        message_count += 1
        if message_count >= 2:  # Get welcome + first ping
            break
    
    assert message_count >= 2
    print("✓ SSE stream generation works")
    
    # Cleanup
    await transport.connection_manager.disconnect(conn_id)


async def main():
    """Run all SSE transport tests."""
    print("MCP Server SSE Transport Test")
    print("=" * 40)
    
    try:
        test_sse_message()
        test_sse_connection()
        await test_connection_manager()
        await test_sse_transport()
        await test_sse_stream()
        
        print("\n✅ All SSE transport tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ SSE transport test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))