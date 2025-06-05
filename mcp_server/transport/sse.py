"""
Server-Sent Events (SSE) transport implementation for MCP server.

Provides SSE-based communication for cloud MCP server deployment
with proper connection management and error handling.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from starlette.responses import StreamingResponse as StarletteStreamingResponse
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False


@dataclass
class SSEMessage:
    """SSE message structure."""
    id: str
    event: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_sse_format(self) -> str:
        """Convert message to SSE format with JSON-RPC 2.0 compliance."""
        lines = []
        lines.append(f"id: {self.id}")
        lines.append(f"event: {self.event}")
        
        # Handle data conversion to JSON-RPC 2.0 format
        if isinstance(self.data, dict):
            # Check if data is already JSON-RPC 2.0 format
            if "jsonrpc" in self.data:
                # Already JSON-RPC 2.0 format, use as-is
                jsonrpc_data = self.data
            else:
                # Convert to JSON-RPC 2.0 format
                jsonrpc_data = {"jsonrpc": "2.0"}
                
                # Handle type-based conversion
                if "type" in self.data:
                    message_type = self.data["type"]
                    data_copy = {k: v for k, v in self.data.items() if k != "type"}
                    
                    # Convert type to method for notifications
                    if message_type in ["welcome", "ping", "error", "connection"]:
                        jsonrpc_data["method"] = f"notifications/{message_type}"
                        jsonrpc_data["params"] = data_copy
                    
                    # Handle result messages
                    elif "result" in self.data:
                        jsonrpc_data["id"] = self.data.get("id")
                        jsonrpc_data["result"] = self.data["result"]
                    
                    # Handle error messages
                    elif "error" in self.data:
                        jsonrpc_data["id"] = self.data.get("id")
                        if isinstance(self.data["error"], dict):
                            jsonrpc_data["error"] = self.data["error"]
                        else:
                            jsonrpc_data["error"] = {
                                "code": -32000,
                                "message": str(self.data["error"])
                            }
                    
                    # Default: treat as notification
                    else:
                        jsonrpc_data["method"] = f"notifications/{message_type}"
                        jsonrpc_data["params"] = data_copy
                
                # Handle arguments -> params conversion
                elif "arguments" in self.data:
                    data_copy = dict(self.data)
                    data_copy["params"] = data_copy.pop("arguments")
                    jsonrpc_data.update(data_copy)
                
                # Handle direct method calls
                elif "method" in self.data:
                    jsonrpc_data.update(self.data)
                
                # Handle direct result messages
                elif "result" in self.data:
                    jsonrpc_data["id"] = self.data.get("id")
                    jsonrpc_data["result"] = self.data["result"]
                
                # Handle direct error messages
                elif "error" in self.data:
                    jsonrpc_data["id"] = self.data.get("id")
                    if isinstance(self.data["error"], dict):
                        jsonrpc_data["error"] = self.data["error"]
                    else:
                        jsonrpc_data["error"] = {
                            "code": -32000,
                            "message": str(self.data["error"])
                        }
                
                # Fallback: treat as generic notification
                else:
                    jsonrpc_data["method"] = "notifications/message"
                    jsonrpc_data["params"] = self.data
            
            lines.append(f"data: {json.dumps(jsonrpc_data)}")
        
        else:
            # Handle non-dict data (strings, etc.)
            if isinstance(self.data, str):
                lines.append(f"data: {self.data}")
            else:
                lines.append(f"data: {json.dumps(self.data)}")
        
        lines.append("")  # Empty line to end the message
        return "\n".join(lines)


@dataclass
class SSEConnection:
    """SSE connection information."""
    connection_id: str
    client_ip: str
    connected_at: datetime
    last_ping: datetime
    credentials: Dict[str, Any]
    is_active: bool = True
    
    def is_expired(self, timeout_seconds: int = 840) -> bool:
        """Check if connection has expired (Cloud Run 14-minute limit)."""
        elapsed = datetime.now() - self.connected_at
        return elapsed.total_seconds() > timeout_seconds


class SSEConnectionManager:
    """Manages SSE connections and message routing."""
    
    def __init__(self, connection_timeout: int = 840):
        """
        Initialize SSE connection manager.
        
        Args:
            connection_timeout: Connection timeout in seconds (default 14 minutes)
        """
        self.connections: Dict[str, SSEConnection] = {}
        self.connection_timeout = connection_timeout
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start_cleanup_task(self):
        """Start background task to clean up expired connections."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_connections())
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_expired_connections(self):
        """Background task to clean up expired connections."""
        while True:
            try:
                current_time = datetime.now()
                expired_connections = [
                    conn_id for conn_id, conn in self.connections.items()
                    if conn.is_expired(self.connection_timeout) or not conn.is_active
                ]
                
                for conn_id in expired_connections:
                    await self.disconnect(conn_id)
                
                # Run cleanup every 60 seconds
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in connection cleanup: {e}")
                await asyncio.sleep(60)
    
    async def connect(self, client_ip: str, credentials: Dict[str, Any]) -> str:
        """
        Register a new SSE connection.
        
        Args:
            client_ip: Client IP address
            credentials: Authentication credentials
            
        Returns:
            Connection ID
        """
        connection_id = str(uuid.uuid4())
        
        connection = SSEConnection(
            connection_id=connection_id,
            client_ip=client_ip,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
            credentials=credentials
        )
        
        self.connections[connection_id] = connection
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect and remove SSE connection.
        
        Args:
            connection_id: Connection ID to disconnect
        """
        if connection_id in self.connections:
            self.connections[connection_id].is_active = False
            del self.connections[connection_id]
    
    async def ping_connection(self, connection_id: str) -> bool:
        """
        Update last ping time for connection.
        
        Args:
            connection_id: Connection ID to ping
            
        Returns:
            True if connection exists and is active
        """
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            if conn.is_active and not conn.is_expired(self.connection_timeout):
                conn.last_ping = datetime.now()
                return True
            else:
                await self.disconnect(connection_id)
        return False
    
    def get_connection(self, connection_id: str) -> Optional[SSEConnection]:
        """Get connection information."""
        return self.connections.get(connection_id)
    
    def get_active_connections_count(self) -> int:
        """Get count of active connections."""
        return len([conn for conn in self.connections.values() if conn.is_active])


class SSETransport:
    """
    SSE transport implementation for MCP server.
    
    Handles SSE communication with proper message formatting,
    connection management, and error handling.
    """
    
    def __init__(self, connection_manager: Optional[SSEConnectionManager] = None):
        """
        Initialize SSE transport.
        
        Args:
            connection_manager: Optional connection manager (creates one if None)
        """
        self.connection_manager = connection_manager or SSEConnectionManager()
        self.message_handlers: Dict[str, Callable] = {}
        self.error_handler: Optional[Callable] = None
    
    def register_message_handler(self, event_type: str, handler: Callable):
        """
        Register handler for specific message type.
        
        Args:
            event_type: Type of message to handle
            handler: Async function to handle the message
        """
        self.message_handlers[event_type] = handler
    
    def register_error_handler(self, handler: Callable):
        """
        Register error handler.
        
        Args:
            handler: Function to handle errors
        """
        self.error_handler = handler
    
    async def start(self):
        """Start the SSE transport (cleanup tasks, etc.)."""
        await self.connection_manager.start_cleanup_task()
    
    async def stop(self):
        """Stop the SSE transport."""
        await self.connection_manager.stop_cleanup_task()
    
    async def create_sse_stream(
        self, 
        connection_id: str, 
        request: Optional[Any] = None
    ) -> AsyncGenerator[str, None]:
        """
        Create SSE stream for a connection.
        
        Args:
            connection_id: Connection ID
            request: Optional request object for additional context
            
        Yields:
            SSE formatted messages
        """
        try:
            # Send initial endpoint event (MCP standard requirement)
            endpoint_msg = SSEMessage(
                id=str(uuid.uuid4()),
                event="endpoint",  # エンドポイントイベント
                data="/message"  # メッセージ送信用エンドポイント（MCP Inspectorは単数形を期待）
            )
            yield endpoint_msg.to_sse_format()
            
            # Send initial connection message
            welcome_msg = SSEMessage(
                id=str(uuid.uuid4()),
                event="connection",
                data={
                    "type": "welcome",
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "server": "MCP-SSE-Server/1.0"
                }
            )
            yield welcome_msg.to_sse_format()
            
            # Send periodic ping messages and handle incoming messages
            while True:
                # Check if connection is still active
                if not await self.connection_manager.ping_connection(connection_id):
                    break
                
                # Send ping message
                ping_msg = SSEMessage(
                    id=str(uuid.uuid4()),
                    event="ping",
                    data={
                        "timestamp": datetime.now().isoformat(),
                        "connection_id": connection_id
                    }
                )
                yield ping_msg.to_sse_format()
                
                # Wait before next ping (30 seconds)
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            # Client disconnected
            await self.connection_manager.disconnect(connection_id)
        except Exception as e:
            # Handle errors
            if self.error_handler:
                await self.error_handler(connection_id, e)
            
            error_msg = SSEMessage(
                id=str(uuid.uuid4()),
                event="error",
                data={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            yield error_msg.to_sse_format()
            
            await self.connection_manager.disconnect(connection_id)
    
    async def send_message(
        self, 
        connection_id: str, 
        event: str, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Send message to specific connection.
        
        Args:
            connection_id: Target connection ID
            event: Event type
            data: Message data
            
        Returns:
            True if message was sent successfully
        """
        connection = self.connection_manager.get_connection(connection_id)
        if not connection or not connection.is_active:
            return False
        
        try:
            message = SSEMessage(
                id=str(uuid.uuid4()),
                event=event,
                data=data
            )
            
            # In a real implementation, this would queue the message
            # for delivery through the SSE stream
            # For now, we'll just log it
            print(f"Sending SSE message to {connection_id}: {message.to_sse_format()}")
            return True
            
        except Exception as e:
            if self.error_handler:
                await self.error_handler(connection_id, e)
            return False
    
    async def broadcast_message(self, event: str, data: Dict[str, Any]) -> int:
        """
        Broadcast message to all active connections.
        
        Args:
            event: Event type
            data: Message data
            
        Returns:
            Number of connections that received the message
        """
        sent_count = 0
        active_connections = [
            conn_id for conn_id, conn in self.connection_manager.connections.items()
            if conn.is_active
        ]
        
        for connection_id in active_connections:
            if await self.send_message(connection_id, event, data):
                sent_count += 1
        
        return sent_count
    
    async def handle_incoming_message(
        self, 
        connection_id: str, 
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle incoming message from client.
        
        Args:
            connection_id: Source connection ID
            message: Incoming message data
            
        Returns:
            Response message
        """
        try:
            message_type = message.get("type")
            
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                response = await handler(connection_id, message)
                return response
            else:
                return {
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            if self.error_handler:
                await self.error_handler(connection_id, e)
            
            return {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def create_sse_response(
    transport: Optional[SSETransport] = None,
    connection_id: Optional[str] = None, 
    request: Optional[Any] = None,
    stream_generator: Optional[Any] = None,
    custom_headers: Optional[Dict[str, str]] = None
):
    """
    Create FastAPI StreamingResponse for SSE with enhanced header support.
    
    Args:
        transport: SSE transport instance (optional if stream_generator provided)
        connection_id: Connection ID (optional if stream_generator provided)
        request: Optional request object
        stream_generator: Optional custom stream generator
        custom_headers: Optional custom headers to include
        
    Returns:
        FastAPI StreamingResponse
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not available for SSE response creation")
    
    from fastapi.responses import StreamingResponse
    
    # Default headers
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id, Authorization",
        "X-Accel-Buffering": "no"  # Disable nginx buffering
    }
    
    # Add custom headers
    if custom_headers:
        headers.update(custom_headers)
    
    # Determine stream generator
    if stream_generator:
        generator = stream_generator
    elif transport and connection_id:
        generator = transport.create_sse_stream(connection_id, request)
    else:
        raise ValueError("Either stream_generator or (transport + connection_id) must be provided")
    
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=headers
    )