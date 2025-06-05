"""
Streamable HTTP transport implementation for MCP server.

Provides MCP-compliant Streamable HTTP transport with session management,
JSON-RPC 2.0 support, and backward compatibility.
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse, StreamingResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .session import SessionManager, SessionData
from .sse import SSEConnectionManager, SSEMessage

# Configure logging
logger = logging.getLogger('streamable_http_transport')


class StreamableHTTPTransport:
    """
    Streamable HTTP transport implementation for MCP server.
    
    Handles both GET (stream establishment) and POST (message processing)
    requests with proper session management and JSON-RPC 2.0 compliance.
    """
    
    def __init__(self, endpoint_path: str = "/mcp", tools_instance = None):
        """
        Initialize Streamable HTTP transport.
        
        Args:
            endpoint_path: Base endpoint path
            tools_instance: Tool execution instance (e.g., TicketTools)
        """
        self.endpoint_path = endpoint_path
        self.session_manager = SessionManager()
        self.tools_instance = tools_instance
        
        logger.info(f"Streamable HTTP transport initialized with endpoint: {endpoint_path}")
    
    async def handle_request(self, request: Request) -> Union[JSONResponse, StreamingResponse]:
        """
        Handle incoming request and route to appropriate handler.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Appropriate response (JSON or Streaming)
        """
        try:
            if request.method == "GET":
                return await self._handle_get_request(request)
            elif request.method == "POST":
                return await self._handle_post_request(request)
            else:
                return JSONResponse(
                    status_code=405,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Method not allowed"
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
            )
    
    async def _handle_get_request(self, request: Request) -> Union[JSONResponse, StreamingResponse]:
        """
        Handle GET request for SSE stream establishment.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            StreamingResponse for SSE or JSONResponse for errors
        """
        # Validate Accept header (MUST include text/event-stream)
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" not in accept_header:
            logger.warning(f"GET request missing text/event-stream in Accept header: {accept_header}")
            return JSONResponse(
                status_code=405,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Method Not Allowed. Accept header must include text/event-stream"
                    }
                }
            )
        
        # Extract session ID from header
        session_id = request.headers.get("Mcp-Session-Id")
        
        if not session_id:
            logger.warning("GET request missing Mcp-Session-Id header")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Missing Mcp-Session-Id header"
                    }
                }
            )
        
        # Validate session
        if not self.session_manager.validate_session(session_id):
            logger.warning(f"Invalid session ID: {session_id}")
            return JSONResponse(
                status_code=404,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Invalid session ID"
                    }
                }
            )
        
        logger.info(f"Establishing SSE stream for session: {session_id}")
        return await self._establish_sse_stream(request, session_id)
    
    async def _handle_post_request(self, request: Request) -> Union[JSONResponse, StreamingResponse]:
        """
        Handle POST request for message processing.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            JSONResponse or StreamingResponse with processing result
        """
        # Validate Accept header (MUST include both application/json and text/event-stream)
        accept_header = request.headers.get("accept", "")
        if not ("application/json" in accept_header and "text/event-stream" in accept_header):
            logger.warning(f"Invalid Accept header: {accept_header}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32600,
                        "message": "Invalid Accept header. Must include both application/json and text/event-stream"
                    }
                }
            )
        
        try:
            # Parse JSON body (MUST be single JSON-RPC message)
            body = await request.json()
            
            # Validate it's a single JSON-RPC message (not batch)
            if isinstance(body, list):
                logger.error("Batch requests not supported in Streamable HTTP")
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32600,
                            "message": "Batch requests not supported. Body must be single JSON-RPC message."
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"Error parsing JSON body: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error",
                        "data": str(e)
                    }
                }
            )
        
        # Determine message type
        message_type = self._get_message_type(body)
        
        # Handle initialize request (no session required)
        if message_type == "request" and self._is_initialize_request(body):
            return await self._handle_initialize_request(request, body)
        
        # Handle notifications and responses (return 202 Accepted)
        if message_type in ["notification", "response"]:
            session_id = request.headers.get("Mcp-Session-Id")
            
            if not session_id:
                logger.warning("POST notification/response missing Mcp-Session-Id header")
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Missing Mcp-Session-Id header for notification/response"
                        }
                    }
                )
            
            # Validate session
            if not self.session_manager.validate_session(session_id):
                logger.warning(f"Invalid session ID for notification/response: {session_id}")
                return JSONResponse(
                    status_code=404,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Invalid session ID"
                        }
                    }
                )
            
            # Process notification/response
            await self._process_notification_or_response(body, session_id)
            
            # Update session activity
            self.session_manager.update_session_activity(session_id)
            
            # Return 202 Accepted (as per spec)
            return JSONResponse(
                status_code=202,
                content=None,
                headers={"Mcp-Session-Id": session_id}
            )
        
        # Handle requests (require session ID)
        if message_type == "request":
            session_id = request.headers.get("Mcp-Session-Id")
            
            if not session_id:
                logger.warning("POST request missing Mcp-Session-Id header")
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {
                            "code": -32000,
                            "message": "Missing Mcp-Session-Id header"
                        }
                    }
                )
            
            # Validate session
            if not self.session_manager.validate_session(session_id):
                logger.warning(f"Invalid session ID: {session_id}")
                return JSONResponse(
                    status_code=404,
                    content={
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {
                            "code": -32000,
                            "message": "Invalid session ID"
                        }
                    }
                )
            
            # Process request - server can return JSON or SSE
            result = await self._process_message(body, session_id)
            
            # Update session activity
            self.session_manager.update_session_activity(session_id)
            
            # Return JSON response (could be extended to support SSE streaming)
            return JSONResponse(
                content=result,
                headers={"Mcp-Session-Id": session_id}
            )
        
        # Unknown message type
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid JSON-RPC message format"
                }
            }
        )
    
    async def _handle_initialize_request(self, request: Request, body: Dict[str, Any]) -> JSONResponse:
        """
        Handle initialize request by creating new session.
        
        Args:
            request: FastAPI Request object
            body: Request body
            
        Returns:
            JSONResponse with initialize result and session ID
        """
        # Extract authentication info if available
        auth_info = {}
        if "Authorization" in request.headers:
            auth_info["authorization"] = request.headers["Authorization"]
        
        # Create new session
        session_id = self.session_manager.create_session(auth_info)
        
        logger.info(f"Created new session: {session_id}")
        
        # Process initialize message
        result = await self._process_message(body, session_id)
        
        # Return result with session ID in header
        return JSONResponse(
            content=result,
            headers={"Mcp-Session-Id": session_id}
        )
    
    async def _establish_sse_stream(self, request: Request, session_id: str) -> StreamingResponse:
        """
        Establish SSE stream for session.
        
        Args:
            request: FastAPI Request object
            session_id: Session ID
            
        Returns:
            StreamingResponse for SSE
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Create SSE generator
        async def sse_generator():
            try:
                # Send initial endpoint event
                endpoint_msg = SSEMessage(
                    id=str(uuid.uuid4()),
                    event="endpoint",
                    data={
                        "jsonrpc": "2.0",
                        "method": "notifications/endpoint",
                        "params": {
                            "endpoint": self.endpoint_path
                        }
                    }
                )
                yield endpoint_msg.to_sse_format()
                
                logger.info(f"SSE stream started for session: {session_id}")
                
                # Keep connection alive with periodic messages
                while self.session_manager.validate_session(session_id):
                    # Update activity
                    self.session_manager.update_session_activity(session_id)
                    
                    # Send keep-alive ping
                    ping_msg = SSEMessage(
                        id=str(uuid.uuid4()),
                        event="ping",
                        data={
                            "jsonrpc": "2.0",
                            "method": "notifications/ping",
                            "params": {
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    )
                    yield ping_msg.to_sse_format()
                    
                    # Wait before next ping
                    await asyncio.sleep(30)
                
                logger.info(f"SSE stream ended for session: {session_id}")
                
            except asyncio.CancelledError:
                logger.info(f"SSE stream cancelled for session: {session_id}")
            except Exception as e:
                logger.error(f"SSE stream error for session {session_id}: {e}")
                # Send error message
                error_msg = SSEMessage(
                    id=str(uuid.uuid4()),
                    event="error",
                    data={
                        "jsonrpc": "2.0",
                        "method": "notifications/error",
                        "params": {
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                yield error_msg.to_sse_format()
        
        # Return streaming response
        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id, Authorization",
                "Mcp-Session-Id": session_id
            }
        )
    
    async def _process_message(self, body: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Process MCP message and return response.
        
        Args:
            body: Message body
            session_id: Session ID
            
        Returns:
            JSON-RPC 2.0 response
        """
        method = body.get("method")
        params = body.get("params", {})
        message_id = body.get("id")
        
        logger.info(f"Processing message for session {session_id}: {method}")
        
        try:
            if method == "initialize":
                return await self._handle_method_initialize(message_id, params)
            elif method == "tools/list":
                return await self._handle_method_tools_list(message_id, params)
            elif method == "tools/call":
                return await self._handle_method_tools_call(message_id, params)
            elif method == "ping":
                return await self._handle_method_ping(message_id, params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            logger.error(f"Error processing method {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def _handle_method_initialize(self, message_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize method."""
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "serverName": "MCP Ticket Server",
                "serverVersion": "1.0.0",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                    "logging": {}
                }
            }
        }
    
    async def _handle_method_tools_list(self, message_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list method."""
        tools = [
            {
                "name": "search",
                "description": "Searches for resources using the provided query string and returns matching results.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch",
                "description": "Retrieves detailed content for a specific resource identified by the given ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "ID of the resource to fetch."}
                    },
                    "required": ["id"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {"tools": tools}
        }
    
    async def _handle_method_tools_call(self, message_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call method."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not self.tools_instance:
            raise RuntimeError("Tools instance not available")
        
        # Execute tool
        if tool_name == "search":
            result = await self._execute_search_tool(arguments)
        elif tool_name == "fetch":
            result = await self._execute_fetch_tool(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result)}]
            }
        }
    
    async def _handle_method_ping(self, message_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping method."""
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "status": "pong",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _execute_search_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search tool with OpenAI Deep Research format."""
        query = arguments.get("query", "")
        
        if not self.tools_instance:
            raise RuntimeError("Tools instance not available")
        
        try:
            # Call the existing get_ticket_list with search_term
            raw_result = await self.tools_instance.get_ticket_list(
                search_term=query,
                limit=20
            )
            
            # Handle empty or invalid results
            if not raw_result:
                logger.warning("Empty result from get_ticket_list")
                return {"results": []}
            
            # Parse the JSON result
            if isinstance(raw_result, str):
                if raw_result.strip():
                    try:
                        ticket_data = json.loads(raw_result)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}, raw_result: {raw_result}")
                        return {"results": []}
                else:
                    logger.warning("Empty string result from get_ticket_list")
                    return {"results": []}
            else:
                ticket_data = raw_result
            
            # Convert to OpenAI Deep Research format
            results = []
            if isinstance(ticket_data, dict) and "tickets" in ticket_data:
                for ticket in ticket_data["tickets"]:
                    # Create summary text
                    text_parts = []
                    if ticket.get("description"):
                        text_parts.append(ticket["description"])
                    if ticket.get("status_name"):
                        text_parts.append(f"Status: {ticket['status_name']}")
                    if ticket.get("category_name"):
                        text_parts.append(f"Category: {ticket['category_name']}")
                    if ticket.get("account_name"):
                        text_parts.append(f"Account: {ticket['account_name']}")
                    
                    summary_text = " | ".join(text_parts) if text_parts else ticket.get("title", "")
                    
                    results.append({
                        "id": str(ticket.get("id", "")),
                        "title": ticket.get("title", ""),
                        "text": summary_text,
                        "url": None
                    })
            elif isinstance(ticket_data, list):
                # Handle direct list of tickets
                for ticket in ticket_data:
                    if isinstance(ticket, dict):
                        text_parts = []
                        if ticket.get("description"):
                            text_parts.append(ticket["description"])
                        if ticket.get("status_name"):
                            text_parts.append(f"Status: {ticket['status_name']}")
                        
                        summary_text = " | ".join(text_parts) if text_parts else ticket.get("title", "")
                        
                        results.append({
                            "id": str(ticket.get("id", "")),
                            "title": ticket.get("title", ""),
                            "text": summary_text,
                            "url": None
                        })
            
            logger.info(f"Search tool returning {len(results)} results")
            return {"results": results}
            
        except Exception as e:
            logger.error(f"Error in search tool execution: {e}")
            # Return empty results instead of raising exception
            return {"results": []}
    
    async def _execute_fetch_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fetch tool with OpenAI Deep Research format."""
        ticket_id = arguments.get("id", "")
        
        if not self.tools_instance:
            raise RuntimeError("Tools instance not available")
        
        try:
            # Call the existing get_ticket_detail
            raw_result = await self.tools_instance.get_ticket_detail(ticketId=ticket_id)
            
            # Handle empty or invalid results
            if not raw_result:
                logger.warning(f"Empty result from get_ticket_detail for ID: {ticket_id}")
                raise ValueError(f"Ticket not found: {ticket_id}")
            
            # Parse the JSON result
            if isinstance(raw_result, str):
                if raw_result.strip():
                    try:
                        ticket_data = json.loads(raw_result)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}, raw_result: {raw_result}")
                        raise ValueError(f"Invalid ticket data for ID: {ticket_id}")
                else:
                    logger.warning(f"Empty string result from get_ticket_detail for ID: {ticket_id}")
                    raise ValueError(f"Ticket not found: {ticket_id}")
            else:
                ticket_data = raw_result
            
            # Convert to OpenAI Deep Research format
            if isinstance(ticket_data, dict):
                # Build complete text content
                text_parts = []
                if ticket_data.get("description"):
                    text_parts.append(f"Description: {ticket_data['description']}")
                
                # Add history if available
                if ticket_data.get("history"):
                    text_parts.append("\nHistory:")
                    for history_item in ticket_data["history"]:
                        if isinstance(history_item, dict):
                            created_at = history_item.get("created_at", "")
                            content = history_item.get("content", "")
                            user_name = history_item.get("user_name", "")
                            text_parts.append(f"- {created_at}: {content} (by {user_name})")
                
                complete_text = "\n".join(text_parts) if text_parts else "No description available"
                
                # Prepare metadata
                metadata = {}
                for key in ["status_name", "category_name", "account_name", "person_in_charge_name", "priority", "created_at", "updated_at"]:
                    if ticket_data.get(key):
                        metadata[key] = str(ticket_data[key])
                
                logger.info(f"Fetch tool returning ticket data for ID: {ticket_id}")
                return {
                    "id": str(ticket_data.get("id", ticket_id)),
                    "title": ticket_data.get("title", "No title"),
                    "text": complete_text,
                    "url": None,
                    "metadata": metadata if metadata else None
                }
            
            raise ValueError(f"Invalid ticket data format for ID: {ticket_id}")
            
        except Exception as e:
            logger.error(f"Error in fetch tool execution: {e}")
            raise ValueError(f"Failed to fetch ticket: {ticket_id}")
    
    def _get_message_type(self, body: Dict[str, Any]) -> str:
        """
        Determine JSON-RPC message type.
        
        Args:
            body: Message body
            
        Returns:
            Message type: "request", "response", "notification", or "invalid"
        """
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
            return "invalid"
        
        has_id = "id" in body
        has_method = "method" in body
        has_result_or_error = "result" in body or "error" in body
        
        if has_method and has_id:
            return "request"
        elif has_method and not has_id:
            return "notification"
        elif has_result_or_error and has_id:
            return "response"
        else:
            return "invalid"
    
    async def _process_notification_or_response(self, body: Dict[str, Any], session_id: str):
        """
        Process notification or response message.
        
        Args:
            body: Message body
            session_id: Session ID
        """
        message_type = self._get_message_type(body)
        
        if message_type == "notification":
            logger.info(f"Processing notification for session {session_id}: {body.get('method')}")
            # Handle notification (e.g., cancellation, progress updates)
            if body.get("method") == "notifications/cancelled":
                # Handle cancellation notification
                request_id = body.get("params", {}).get("requestId")
                reason = body.get("params", {}).get("reason", "Client cancelled")
                logger.info(f"Cancellation request for ID {request_id}: {reason}")
            
        elif message_type == "response":
            logger.info(f"Processing response for session {session_id}: ID {body.get('id')}")
            # Handle response (if server sent requests to client)
            # This would be used for sampling or other client->server responses
        
        # Update session activity
        self.session_manager.update_session_activity(session_id)
    
    def _is_initialize_request(self, body: Dict[str, Any]) -> bool:
        """
        Check if request is an initialize request.
        
        Args:
            body: Request body
            
        Returns:
            True if initialize request
        """
        return body.get("method") == "initialize"
    
    def _should_use_sse_response(self, request: Dict[str, Any], result: Any) -> bool:
        """
        Determine if SSE response should be used.
        
        Args:
            request: Request data
            result: Processing result
            
        Returns:
            True if SSE response should be used
        """
        # For now, use standard HTTP responses
        # Future: implement logic for long-running tasks
        return False
    
    async def cleanup(self):
        """Cleanup transport resources."""
        # Cleanup expired sessions
        cleaned = self.session_manager.cleanup_expired_sessions()
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired sessions")
    
    def get_session_count(self) -> int:
        """Get active session count."""
        return self.session_manager.get_active_session_count()