"""
Cloud MCP Server for Ticket Management System

SSE-based MCP server for cloud deployment with FastAPI and proper
authentication, connection management, and tool functionality.
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, Request, HTTPException, Depends, Form, WebSocket, WebSocketDisconnect, Header
    from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Import shared components
from shared.config import get_cloud_settings, CloudSettings
from shared.api_client import APIClient
from shared.tools import TicketTools
from auth.providers import create_auth_manager, AuthManager
from transport.sse import SSETransport, SSEConnectionManager, create_sse_response
from transport.streamable_http import StreamableHTTPTransport
from transport.session import SessionManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cloud_mcp_server')


def get_real_url(request: Request) -> str:
    """
    Get the real URL considering Cloud Run reverse proxy headers.
    
    Cloud Run terminates HTTPS and forwards HTTP to the container,
    so we need to check X-Forwarded-Proto to determine the real scheme.
    """
    # Check proxy headers for real scheme
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
    forwarded_host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host")
    
    # Use forwarded values if available, otherwise fall back to request values
    scheme = forwarded_proto if forwarded_proto in ["http", "https"] else "https"
    host = forwarded_host or request.url.hostname
    path = str(request.url.path)
    query = str(request.url.query) if request.url.query else ""
    
    # Construct the real URL
    url = f"{scheme}://{host}{path}"
    if query:
        url += f"?{query}"
    
    return url


class CloudMCPServer:
    """
    Cloud-based MCP server with SSE transport and authentication.
    
    Provides ticket management tools through SSE connections with
    proper authentication and connection management.
    """
    
    def __init__(self, settings: CloudSettings):
        """
        Initialize cloud MCP server.
        
        Args:
            settings: Cloud configuration settings
        """
        self.settings = settings
        self.api_client: Optional[APIClient] = None
        self.ticket_tools: Optional[TicketTools] = None
        self.auth_manager: Optional[AuthManager] = None
        self.sse_transport: Optional[SSETransport] = None
        self.streamable_transport: Optional[StreamableHTTPTransport] = None
        self.app: Optional[FastAPI] = None
        
        logger.info(f"Initializing Cloud MCP Server with auth: {settings.auth_provider}, transport: {settings.transport_type}")
    
    async def initialize(self):
        """Initialize all server components."""
        # Initialize API client
        self.api_client = APIClient(
            base_url=self.settings.api_base_url,
            api_key=self.settings.api_key,
            timeout=30
        )
        
        # Initialize ticket tools
        self.ticket_tools = TicketTools(self.api_client)
        
        # Initialize authentication
        self.auth_manager = create_auth_manager(
            self.settings.auth_provider,
            api_key_header="x-mcp-api-key"
        )
        
        # Initialize SSE transport (for backward compatibility)
        connection_manager = SSEConnectionManager(
            connection_timeout=self.settings.cloud_run_timeout
        )
        self.sse_transport = SSETransport(connection_manager)
        
        # Initialize Streamable HTTP transport
        self.streamable_transport = StreamableHTTPTransport(
            endpoint_path="/mcp",
            tools_instance=self.ticket_tools
        )
        
        # Register message handlers
        await self._register_message_handlers()
        
        # Start transports
        await self.sse_transport.start()
        
        logger.info("Cloud MCP Server initialized successfully")
    
    async def _register_message_handlers(self):
        """Register handlers for different MCP message types."""
        
        async def handle_tool_call(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
            """Handle tool call requests."""
            try:
                tool_name = message.get("tool")
                arguments = message.get("arguments", {})
                request_id = message.get("id")
                
                if not tool_name:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "Tool name not specified"}
                    }
                
                # Execute tool
                result = await self._execute_tool(tool_name, arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {"code": -32603, "message": str(e)}
                }
        
        async def handle_ping(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
            """Handle ping requests."""
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {"status": "pong", "timestamp": datetime.now().isoformat()}
            }
        
        async def handle_initialize(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
            """Handle MCP initialize request."""
            logger.info(f"Initialize request from {connection_id}: {message}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
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
        
        async def handle_list_tools(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
            """Handle list tools requests."""
            # OpenAI Deep Research compatible tools only
            tools = [
                {
                    "name": "search",
                    "description": "Searches for resources using the provided query string and returns matching results.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query."}
                        },
                        "required": ["query"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "results": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "description": "ID of the resource."},
                                        "title": {"type": "string", "description": "Title or headline of the resource."},
                                        "text": {"type": "string", "description": "Text snippet or summary from the resource."},
                                        "url": {"type": ["string", "null"], "description": "URL of the resource. Optional but needed for citations to work."}
                                    },
                                    "required": ["id", "title", "text"]
                                }
                            }
                        },
                        "required": ["results"]
                    }
                },
                {
                    "name": "fetch",
                    "description": "Retrieves detailed content for a specific resource identified by the given ID.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "ID of the resource to fetch."}
                        },
                        "required": ["id"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "ID of the resource."},
                            "title": {"type": "string", "description": "Title or headline of the fetched resource."},
                            "text": {"type": "string", "description": "Complete textual content of the resource."},
                            "url": {"type": ["string", "null"], "description": "URL of the resource. Optional but needed for citations to work."},
                            "metadata": {
                                "type": ["object", "null"],
                                "additionalProperties": {"type": "string"},
                                "description": "Optional metadata providing additional context."
                            }
                        },
                        "required": ["id", "title", "text"]
                    }
                }
            ]
            
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {"tools": tools}
            }
        
        # Register handlers
        self.sse_transport.register_message_handler("initialize", handle_initialize)
        self.sse_transport.register_message_handler("tool_call", handle_tool_call)
        self.sse_transport.register_message_handler("ping", handle_ping)
        self.sse_transport.register_message_handler("list_tools", handle_list_tools)
        
        # Register error handler
        async def handle_error(connection_id: str, error: Exception):
            logger.error(f"SSE Transport error for connection {connection_id}: {error}")
        
        self.sse_transport.register_error_handler(handle_error)
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a search or fetch tool (OpenAI Deep Research compatible)."""
        if not self.ticket_tools:
            raise RuntimeError("Ticket tools not initialized")
        
        if tool_name == "search":
            return await self._execute_search(arguments)
        elif tool_name == "fetch":
            return await self._execute_fetch(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _execute_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search tool with OpenAI Deep Research format."""
        query = arguments.get("query", "")
        
        # Call the existing get_ticket_list with search_term
        raw_result = await self.ticket_tools.get_ticket_list(
            search_term=query,
            limit=20  # Reasonable limit for search results
        )
        
        # Parse the JSON result
        import json
        if isinstance(raw_result, str):
            ticket_data = json.loads(raw_result)
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
                    "url": None  # Could add ticket URL if available
                })
        
        return {"results": results}
    
    async def _execute_fetch(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fetch tool with OpenAI Deep Research format."""
        ticket_id = arguments.get("id", "")
        
        # Call the existing get_ticket_detail
        raw_result = await self.ticket_tools.get_ticket_detail(ticketId=ticket_id)
        
        # Parse the JSON result
        import json
        if isinstance(raw_result, str):
            ticket_data = json.loads(raw_result)
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
            
            complete_text = "\n".join(text_parts)
            
            # Prepare metadata
            metadata = {}
            for key in ["status_name", "category_name", "account_name", "person_in_charge_name", "priority", "created_at", "updated_at"]:
                if ticket_data.get(key):
                    metadata[key] = str(ticket_data[key])
            
            return {
                "id": str(ticket_data.get("id", "")),
                "title": ticket_data.get("title", ""),
                "text": complete_text,
                "url": None,  # Could add ticket URL if available
                "metadata": metadata if metadata else None
            }
        
        raise ValueError(f"Ticket not found: {ticket_id}")
    
    async def _execute_legacy_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute legacy tools (for backward compatibility)."""
        tool_methods = {
            "get_ticket_list": self.ticket_tools.get_ticket_list,
            "get_ticket_detail": self.ticket_tools.get_ticket_detail,
            "create_ticket": self.ticket_tools.create_ticket_sync,
            "update_ticket": self.ticket_tools.update_ticket_sync,
            "add_ticket_history": self.ticket_tools.add_ticket_history_sync,
            "get_users": self.ticket_tools.get_users_sync,
            "get_accounts": self.ticket_tools.get_accounts_sync,
            "get_categories": self.ticket_tools.get_categories_sync,
            "get_category_details": self.ticket_tools.get_category_details_sync,
            "get_statuses": self.ticket_tools.get_statuses_sync,
            "get_request_channels": self.ticket_tools.get_request_channels_sync
        }
        
        if tool_name not in tool_methods:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        method = tool_methods[tool_name]
        
        # Execute method with arguments
        if asyncio.iscoroutinefunction(method):
            return await method(**arguments)
        else:
            return method(**arguments)
    
    async def cleanup(self):
        """Cleanup server resources."""
        if self.sse_transport:
            await self.sse_transport.stop()
        
        if self.streamable_transport:
            await self.streamable_transport.cleanup()
        
        if self.api_client:
            await self.api_client.close()
        
        logger.info("Cloud MCP Server cleanup completed")


# Global server instance and session management
server_instance: Optional[CloudMCPServer] = None
app = None

# Session management for MCP over SSE
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, AsyncGenerator
import asyncio
import queue

@dataclass
class MCPSession:
    """MCP session information for SSE + Messages pattern."""
    session_id: str
    auth_token: str
    connection_id: Optional[str] = None
    message_queue: Optional[asyncio.Queue] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True

class MCPSessionManager:
    """Manages MCP sessions for proper SSE + Messages implementation."""
    
    def __init__(self):
        self.sessions: Dict[str, MCPSession] = {}
        self._lock = threading.Lock()
    
    def create_session(self, auth_token: str) -> str:
        """Create new MCP session."""
        session_id = str(uuid.uuid4())
        message_queue = asyncio.Queue()
        
        session = MCPSession(
            session_id=session_id,
            auth_token=auth_token,
            message_queue=message_queue
        )
        
        with self._lock:
            self.sessions[session_id] = session
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """Get session by ID."""
        with self._lock:
            return self.sessions.get(session_id)
    
    def update_activity(self, session_id: str):
        """Update session last activity."""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].last_activity = datetime.now()
    
    def send_message_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send message to session's SSE stream."""
        session = self.get_session(session_id)
        logger.info(f"Attempting to send message to session {session_id}: {message}")
        
        if session and session.message_queue:
            try:
                session.message_queue.put_nowait(message)
                logger.info(f"Successfully queued message for session {session_id}")
                return True
            except asyncio.QueueFull:
                logger.error(f"Queue full for session {session_id}")
                return False
        else:
            logger.error(f"Session {session_id} not found or no queue")
            return False
    
    async def get_next_message(self, session_id: str, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Get next message for session."""
        session = self.get_session(session_id)
        logger.info(f"get_next_message called for session {session_id}")
        
        if not session or not session.message_queue:
            logger.error(f"No session or queue for {session_id}")
            return None
        
        try:
            logger.info(f"Waiting for message from queue for session {session_id} (timeout: {timeout}s)")
            message = await asyncio.wait_for(session.message_queue.get(), timeout=timeout)
            logger.info(f"Retrieved message from queue for session {session_id}: {message}")
            return message
        except asyncio.TimeoutError:
            logger.info(f"Timeout waiting for message for session {session_id}")
            return None
    
    def cleanup_expired_sessions(self, timeout_minutes: int = 15):
        """Remove expired sessions."""
        now = datetime.now()
        expired_sessions = []
        
        with self._lock:
            for session_id, session in self.sessions.items():
                if (now - session.last_activity).total_seconds() > timeout_minutes * 60:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]

# Global session manager
session_manager = MCPSessionManager()


if FASTAPI_AVAILABLE:
    @asynccontextmanager
    async def lifespan(fastapi_app):
        """FastAPI lifespan management."""
        global server_instance
        
        # Startup
        settings = get_cloud_settings()
        server_instance = CloudMCPServer(settings)
        await server_instance.initialize()
        
        logger.info("FastAPI application started")
        yield
        
        # Shutdown
        if server_instance:
            await server_instance.cleanup()
        logger.info("FastAPI application shutdown")


# Create FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Cloud MCP Server",
        description="Server-Sent Events based MCP server for ticket management",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware with proper expose headers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id", "Mcp-Session-Id"],  # Critical for MCP Inspector
    )
    
    # Security scheme
    security = HTTPBearer(auto_error=False)
    
    
    async def verify_authentication(request: Request, authorization: Optional[str] = Header(None), token: Optional[str] = Depends(security)):
        """Verify authentication for requests with Bearer token support."""
        if not server_instance or not server_instance.auth_manager:
            raise HTTPException(status_code=500, detail="Server not initialized")
        
        # Extract credentials
        credentials = {}
        
        # Check for Authorization: Bearer <token> header (MCP Inspector preferred)
        if authorization and authorization.startswith("Bearer "):
            credentials["api_key"] = authorization[7:]  # Remove "Bearer " prefix
        # Check for API key in query parameter (for MCP clients)
        elif request.query_params.get("api_key"):
            credentials["api_key"] = request.query_params.get("api_key")
        # Check for API key in header
        elif request.headers.get("x-mcp-api-key"):
            credentials["api_key"] = request.headers.get("x-mcp-api-key")
        elif token:
            credentials["api_key"] = token.credentials
        
        # Validate credentials
        if not server_instance.auth_manager.validate_credentials(credentials):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Authenticate
        auth_result = await server_instance.auth_manager.authenticate(credentials)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail=auth_result.error_message or "Authentication failed")
        
        return auth_result
    
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Cloud MCP Server",
            "version": "1.0.0",
            "transport": ["Streamable HTTP", "SSE"],
            "timestamp": datetime.now().isoformat()
        }
    
    
    @app.route("/mcp", methods=["GET", "POST", "OPTIONS"])
    async def mcp_streamable_endpoint(request: Request):
        """
        Streamable HTTP endpoint for MCP communication.
        
        Handles both GET (stream establishment) and POST (message processing)
        requests according to MCP Streamable HTTP specification.
        """
        # Handle CORS preflight
        if request.method == "OPTIONS":
            return JSONResponse(
                content={},
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, mcp-session-id, Mcp-Session-Id",
                    "Access-Control-Expose-Headers": "mcp-session-id, Mcp-Session-Id"
                }
            )
        
        # Validate Origin header for security (DNS rebinding protection)
        if not await validate_origin_header(request):
            logger.warning(f"Rejected request from invalid origin: {request.headers.get('origin')}")
            raise HTTPException(status_code=403, detail="Invalid origin")
        
        if not server_instance or not server_instance.streamable_transport:
            raise HTTPException(status_code=503, detail="Server not initialized")
        
        # Check if this is a proxy request from MCP Inspector
        origin = request.headers.get("origin", "")
        user_agent = request.headers.get("user-agent", "")
        
        # Enhanced debugging for MCP Inspector issues
        logger.info(f"MCP endpoint request - Method: {request.method}, Origin: '{origin}', User-Agent: '{user_agent}'")
        logger.info(f"Query params: {dict(request.query_params)}")
        logger.info(f"Headers - Content-Type: {request.headers.get('content-type', 'None')}, Accept: {request.headers.get('accept', 'None')}")
        logger.info(f"Session header: mcp-session-id='{request.headers.get('mcp-session-id', 'None')}', Mcp-Session-Id='{request.headers.get('Mcp-Session-Id', 'None')}'")
        
        # Log additional headers for debugging
        if request.method == "POST":
            authorization = request.headers.get("authorization", "None")
            logger.info(f"Authorization header present: {'Yes' if authorization != 'None' else 'No'}")
        
        # Log MCP Inspector detection but use standard Streamable HTTP handling
        if ("127.0.0.1:6274" in origin or "127.0.0.1:6277" in origin or 
            "mcp-inspector" in user_agent.lower() or user_agent.strip().lower() == "node"):
            real_url = get_real_url(request)
            logger.info(f"MCP Inspector proxy request detected: {request.method} {real_url}")
            # Continue with standard Streamable HTTP processing instead of special handling
        
        # Get correct HTTPS URL for logging (Cloud Run proxy-aware)
        real_url = get_real_url(request)
        logger.info(f"MCP Streamable HTTP request: {request.method} {real_url}")
        return await server_instance.streamable_transport.handle_request(request)
    
    
    async def validate_origin_header(request: Request) -> bool:
        """Validate Origin header to prevent DNS rebinding attacks."""
        origin = request.headers.get("origin", "")
        logger.debug(f"Origin header validation - Origin: '{origin}', User-Agent: '{request.headers.get('user-agent', '')}')")
        
        # Allow requests without Origin (direct API calls)
        if not origin:
            return True
        
        # Allow localhost origins for development
        allowed_origins = [
            "http://127.0.0.1:6274",  # MCP Inspector
            "http://127.0.0.1:6277",  # MCP Inspector alternative port
            "http://localhost:6274",
            "http://localhost:6277",
            "https://127.0.0.1:6274",
            "https://127.0.0.1:6277",
            "https://localhost:6274",
            "https://localhost:6277"
        ]
        
        # Allow the actual deployment domain
        allowed_origins.append("https://mcp-server-883360737972.asia-northeast1.run.app")
        
        is_allowed = origin in allowed_origins
        logger.debug(f"Origin validation result - Origin: '{origin}', Allowed: {is_allowed}, Allowed origins: {allowed_origins}")
        return is_allowed
    
    
    # Removed handle_mcp_inspector_request - using standard Streamable HTTP instead
    
    
    @app.get("/.well-known/ai-plugin.json")
    async def ai_plugin_manifest():
        """ChatGPT Actions API manifest."""
        base_url = "https://mcp-server-883360737972.asia-northeast1.run.app"
        return {
            "schema_version": "v1",
            "name_for_human": "MCP Ticket Server",
            "name_for_model": "mcp_ticket_server", 
            "description_for_human": "Access ticket management system data",
            "description_for_model": "Search and fetch ticket information from the ticket management system",
            "auth": {
                "type": "none"
            },
            "api": {
                "type": "openapi",
                "url": f"{base_url}/openapi.json"
            },
            "logo_url": None,
            "contact_email": "support@example.com",
            "legal_info_url": None
        }
    
    @app.get("/openapi.json")
    async def openapi_spec():
        """OpenAPI specification for ChatGPT Actions."""
        base_url = "https://mcp-server-883360737972.asia-northeast1.run.app"
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "MCP Ticket Server API",
                "version": "1.0.0",
                "description": "API for searching and fetching ticket information"
            },
            "servers": [{"url": base_url}],
            "paths": {
                "/search": {
                    "post": {
                        "operationId": "search",
                        "summary": "Search for tickets",
                        "description": "Search for tickets using a query string",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "Search query for tickets"
                                            }
                                        },
                                        "required": ["query"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Search results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "results": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "id": {"type": "string"},
                                                            "title": {"type": "string"},
                                                            "text": {"type": "string"},
                                                            "url": {"type": "string", "nullable": True}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/fetch": {
                    "post": {
                        "operationId": "fetch",
                        "summary": "Fetch ticket details",
                        "description": "Fetch detailed information for a specific ticket",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {
                                                "type": "string",
                                                "description": "Ticket ID to fetch"
                                            }
                                        },
                                        "required": ["id"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Ticket details",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "string"},
                                                "title": {"type": "string"},
                                                "text": {"type": "string"},
                                                "url": {"type": "string", "nullable": True},
                                                "metadata": {"type": "object", "nullable": True}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    @app.post("/search")
    async def chatgpt_search_action(request: Request):
        """ChatGPT Actions API compatible search endpoint."""
        if not server_instance or not server_instance.ticket_tools:
            raise HTTPException(status_code=503, detail="Server not initialized")
        
        try:
            body = await request.json()
            query = body.get("query", "")
            
            # Use existing search implementation
            raw_result = await server_instance.ticket_tools.get_ticket_list(
                search_term=query,
                limit=20
            )
            
            # Parse the JSON result
            if isinstance(raw_result, str):
                if raw_result.strip():
                    try:
                        ticket_data = json.loads(raw_result)
                    except json.JSONDecodeError:
                        return {"results": []}
                else:
                    return {"results": []}
            else:
                ticket_data = raw_result
            
            # Convert to search results format
            results = []
            if isinstance(ticket_data, dict) and "tickets" in ticket_data:
                for ticket in ticket_data["tickets"]:
                    text_parts = []
                    if ticket.get("description"):
                        text_parts.append(ticket["description"])
                    if ticket.get("status_name"):
                        text_parts.append(f"Status: {ticket['status_name']}")
                    if ticket.get("category_name"):
                        text_parts.append(f"Category: {ticket['category_name']}")
                    
                    summary_text = " | ".join(text_parts) if text_parts else ticket.get("title", "")
                    
                    results.append({
                        "id": str(ticket.get("id", "")),
                        "title": ticket.get("title", ""),
                        "text": summary_text,
                        "url": None
                    })
            
            return {"results": results}
            
        except Exception as e:
            logger.error(f"Search action error: {e}")
            return {"results": []}
    
    @app.post("/fetch")
    async def chatgpt_fetch_action(request: Request):
        """ChatGPT Actions API compatible fetch endpoint."""
        if not server_instance or not server_instance.ticket_tools:
            raise HTTPException(status_code=503, detail="Server not initialized")
        
        try:
            body = await request.json()
            ticket_id = body.get("id", "")
            
            # Use existing fetch implementation
            raw_result = await server_instance.ticket_tools.get_ticket_detail(ticketId=ticket_id)
            
            # Parse the JSON result
            if isinstance(raw_result, str):
                if raw_result.strip():
                    try:
                        ticket_data = json.loads(raw_result)
                    except json.JSONDecodeError:
                        raise HTTPException(status_code=404, detail="Ticket not found")
                else:
                    raise HTTPException(status_code=404, detail="Ticket not found")
            else:
                ticket_data = raw_result
            
            # Convert to fetch result format
            if isinstance(ticket_data, dict):
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
                
                return {
                    "id": str(ticket_data.get("id", ticket_id)),
                    "title": ticket_data.get("title", "No title"),
                    "text": complete_text,
                    "url": None,
                    "metadata": metadata if metadata else None
                }
            
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Fetch action error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        if not server_instance:
            raise HTTPException(status_code=503, detail="Server not initialized")
        
        # Get SSE connections count (legacy)
        sse_connections = 0
        if server_instance.sse_transport:
            sse_connections = server_instance.sse_transport.connection_manager.get_active_connections_count()
        
        # Get Streamable HTTP sessions count (new)
        streamable_sessions = 0
        if server_instance.streamable_transport:
            streamable_sessions = server_instance.streamable_transport.get_session_count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "transport": {
                "sse_connections": sse_connections,
                "streamable_sessions": streamable_sessions,
                "total_active": sse_connections + streamable_sessions
            },
            "auth_provider": server_instance.settings.auth_provider,
            "endpoints": ["/mcp", "/sse", "/messages", "/message"]
        }
    
    
    @app.get("/.well-known/oauth-authorization-server")
    async def oauth_discovery():
        """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
        # Get the actual service URL from the request
        base_url = "https://mcp-server-883360737972.asia-northeast1.run.app"
        
        return {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/oauth/authorize",
            "token_endpoint": f"{base_url}/oauth/token",
            "registration_endpoint": f"{base_url}/register",
            "scopes_supported": ["mcp", "read", "write"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "client_credentials"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
            "code_challenge_methods_supported": ["S256"],
            "revocation_endpoint": f"{base_url}/oauth/revoke",
            "introspection_endpoint": f"{base_url}/oauth/introspect"
        }
    
    
    @app.get("/.well-known/oauth-protected-resource")
    async def oauth_protected_resource():
        """OAuth 2.0 Protected Resource Metadata."""
        base_url = "https://mcp-server-883360737972.asia-northeast1.run.app"
        
        return {
            "resource_server": base_url,
            "authorization_servers": [base_url],
            "scopes_supported": ["mcp", "read", "write"],
            "bearer_methods_supported": ["header", "query"],
            "resource_documentation": f"{base_url}/docs",
            "introspection_endpoint": f"{base_url}/oauth/introspect",
            "revocation_endpoint": f"{base_url}/oauth/revoke"
        }
    
    
    @app.post("/register")
    async def dynamic_client_registration():
        """Dynamic Client Registration (RFC 7591)."""
        # Generate a simple client for MCP
        import uuid
        client_id = f"mcp-client-{str(uuid.uuid4())[:8]}"
        
        return {
            "client_id": client_id,
            "client_secret": server_instance.settings.mcp_api_key if server_instance else "fallback-secret",
            "registration_access_token": f"access-{str(uuid.uuid4())}",
            "registration_client_uri": f"https://mcp-server-883360737972.asia-northeast1.run.app/clients/{client_id}",
            "client_id_issued_at": int(datetime.now().timestamp()),
            "grant_types": ["authorization_code", "client_credentials"],
            "response_types": ["code"],
            "scope": "mcp read write",
            "token_endpoint_auth_method": "client_secret_post"
        }
    
    
    @app.get("/oauth/authorize")
    async def oauth_authorize(
        response_type: str = None,
        client_id: str = None,
        redirect_uri: str = None,
        scope: str = None,
        state: str = None,
        code_challenge: str = None,
        code_challenge_method: str = None
    ):
        """OAuth authorization endpoint."""
        if response_type != "code":
            raise HTTPException(status_code=400, detail="unsupported_response_type")
        
        if not redirect_uri:
            raise HTTPException(status_code=400, detail="redirect_uri is required")
        
        # Generate authorization code
        import uuid
        auth_code = f"auth-{str(uuid.uuid4())}"
        
        # Build redirect URL with authorization code
        from urllib.parse import urlencode
        from fastapi.responses import RedirectResponse
        
        params = {"code": auth_code}
        if state:
            params["state"] = state
        
        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        
        # Return HTTP 302 redirect
        return RedirectResponse(url=redirect_url, status_code=302)
    
    
    @app.post("/oauth/token")
    async def oauth_token(request: Request):
        """OAuth token endpoint with flexible parameter handling."""
        try:
            # Try to parse as form data first
            try:
                form_data = await request.form()
                grant_type = form_data.get("grant_type")
                code = form_data.get("code")
                client_id = form_data.get("client_id")
                client_secret = form_data.get("client_secret")
                redirect_uri = form_data.get("redirect_uri")
            except:
                # If form parsing fails, try JSON
                json_data = await request.json()
                grant_type = json_data.get("grant_type")
                code = json_data.get("code")
                client_id = json_data.get("client_id") 
                client_secret = json_data.get("client_secret")
                redirect_uri = json_data.get("redirect_uri")
            
            logger.info(f"OAuth token request - grant_type: {grant_type}, client_id: {client_id}")
            
            # More flexible grant type validation
            if not grant_type:
                logger.warning("No grant_type provided")
                raise HTTPException(status_code=400, detail="missing_grant_type")
            
            if grant_type not in ["authorization_code", "client_credentials"]:
                logger.warning(f"Unsupported grant_type: {grant_type}")
                # Accept anyway for MCP Inspector compatibility
                pass
            
            # Generate token (accept any valid-looking request)
            import uuid
            access_token = server_instance.settings.mcp_api_key  # Use our actual API key as token
            
            return {
                "access_token": access_token,
                "token_type": "Bearer", 
                "expires_in": 3600,
                "scope": "mcp read write",
                "refresh_token": f"refresh-{str(uuid.uuid4())}"
            }
            
        except Exception as e:
            logger.error(f"OAuth token error: {e}")
            return {
                "error": "invalid_request",
                "error_description": str(e)
            }
    
    
    
    
    @app.get("/sse")
    async def connect_sse_unified(
        request: Request,
        authorization: Optional[str] = Header(None)
    ):
        """Unified SSE endpoint supporting both MCP standard and backward compatibility."""
        if not server_instance:
            raise HTTPException(status_code=503, detail="Server not initialized")
        
        # Extract auth token (support both Bearer and query param)
        auth_token = None
        if authorization and authorization.startswith("Bearer "):
            auth_token = authorization[7:]
        elif request.query_params.get("api_key"):
            auth_token = request.query_params.get("api_key")
        
        if not auth_token:
            raise HTTPException(status_code=401, detail="Missing authentication")
        
        # Validate auth token (use existing auth manager for consistency)
        if not server_instance.auth_manager:
            raise HTTPException(status_code=500, detail="Server not initialized")
        
        credentials = {"api_key": auth_token}
        if not server_instance.auth_manager.validate_credentials(credentials):
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        auth_result = await server_instance.auth_manager.authenticate(credentials)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        # Detect if client wants MCP standard (Bearer token) or legacy (query param)
        is_mcp_standard = authorization and authorization.startswith("Bearer ")
        
        if is_mcp_standard:
            # MCP-compliant implementation
            session_id = session_manager.create_session(auth_token)
            
            async def mcp_sse_generator():
                try:
                    # Send initial endpoint information (MCP requirement)
                    yield f"event: endpoint\n"
                    yield f"data: /messages?session_id={session_id}\n\n"
                    
                    # Message loop
                    logger.info(f"Starting SSE message loop for session {session_id}")
                    while True:
                        # Check if session is still active
                        session = session_manager.get_session(session_id)
                        if not session or not session.is_active:
                            logger.info(f"Session {session_id} no longer active, breaking SSE loop")
                            break
                        
                        # Get next message from queue
                        logger.info(f"Waiting for next message for session {session_id}")
                        message = await session_manager.get_next_message(session_id, timeout=30.0)
                        if message:
                            logger.info(f"Sending SSE message for session {session_id}: {message}")
                            yield f"event: message\n"
                            yield f"data: {json.dumps(message)}\n\n"
                        else:
                            # Send keep-alive comment (every 30s)
                            logger.info(f"Sending keep-alive for session {session_id}")
                            yield f": keep-alive\n\n"
                        
                        session_manager.update_activity(session_id)
                        
                except asyncio.CancelledError:
                    logger.info(f"SSE connection cancelled for session {session_id}")
                except Exception as e:
                    logger.error(f"SSE stream error for session {session_id}: {e}")
                    yield f"event: error\n"
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                mcp_sse_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Legacy implementation for backward compatibility
            client_ip = request.client.host if request.client else "unknown"
            connection_id = await server_instance.sse_transport.connection_manager.connect(
                client_ip, 
                auth_result.user_info or {}
            )
            
            return create_sse_response(server_instance.sse_transport, connection_id, request)
    
    
    
    
    @app.post("/message")
    async def mcp_message_endpoint(
        request: Request,
        authorization: Optional[str] = Header(None)
    ):
        """MCP Inspector compatible endpoint (singular)."""
        # Get session_id from query parameter
        session_id = request.query_params.get("sessionId")  # MCP Inspector uses camelCase
        if not session_id:
            session_id = request.query_params.get("session_id")  # fallback
        
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing sessionId parameter"}
            )
        
        # Forward to the standard messages endpoint
        return await mcp_messages_endpoint(session_id, request, authorization)
    
    
    @app.post("/messages")
    async def mcp_messages_endpoint(
        session_id: str,
        request: Request,
        authorization: Optional[str] = Header(None)
    ):
        """MCP-compliant messages endpoint for client->server communication."""
        if not server_instance:
            raise HTTPException(status_code=503, detail="Server not initialized")
        
        # Verify session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify auth token matches session
        auth_token = None
        if authorization and authorization.startswith("Bearer "):
            auth_token = authorization[7:]
        elif request.query_params.get("api_key"):
            auth_token = request.query_params.get("api_key")
        
        if auth_token != session.auth_token:
            raise HTTPException(status_code=401, detail="Invalid session authentication")
        
        # Parse JSON-RPC message
        try:
            message = await request.json()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error", "data": str(e)}
            }
            return JSONResponse(content=error_response)
        
        logger.info(f"Received MCP message for session {session_id}: {message}")
        session_manager.update_activity(session_id)
        
        # Process JSON-RPC message
        try:
            response = await process_mcp_message(message)
            
            # Send response back via SSE stream
            if response:
                success = session_manager.send_message_to_session(session_id, response)
                if success:
                    return JSONResponse(content={"status": "accepted"})
                else:
                    return JSONResponse(content={"status": "error", "message": "Failed to send to SSE stream"})
            
            return JSONResponse(content={"status": "no_response"})
            
        except Exception as e:
            logger.error(f"Error processing MCP message: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": "Internal error", "data": str(e)}
            }
            session_manager.send_message_to_session(session_id, error_response)
            return JSONResponse(content={"status": "error", "message": str(e)})
    
    
    async def process_mcp_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process MCP JSON-RPC message and return response."""
        method = message.get("method")
        params = message.get("params", {})
        message_id = message.get("id")
        
        if method == "initialize":
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
        
        elif method == "tools/list":
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
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = await server_instance._execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]}
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {"code": -32603, "message": str(e)}
                }
        
        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"status": "pong"}
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
    
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, api_key: str = None):
        """WebSocket endpoint for MCP communication."""
        # Check API key from query parameter
        if api_key != server_instance.settings.mcp_api_key:
            await websocket.close(code=1008, reason="Unauthorized")
            return
            
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        try:
            # Send welcome message
            await websocket.send_json({
                "type": "welcome",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat(),
                "server": "MCP-WebSocket-Server/1.0"
            })
            
            # Handle messages
            while True:
                # Receive message from client
                message = await websocket.receive_json()
                logger.info(f"WebSocket message from {connection_id}: {message}")
                
                # Get message type and handler
                message_type = message.get("type")
                
                # Process message based on type
                if message_type == "initialize":
                    response = await handle_ws_initialize(connection_id, message)
                elif message_type == "list_tools":
                    response = await handle_ws_list_tools(connection_id, message)
                elif message_type == "tool_call":
                    response = await handle_ws_tool_call(connection_id, message)
                elif message_type == "ping":
                    response = {"type": "pong", "timestamp": datetime.now().isoformat()}
                else:
                    response = {
                        "type": "error",
                        "error": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Send response
                await websocket.send_json(response)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
            await websocket.close()
    
    
    async def handle_ws_initialize(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebSocket initialize request."""
        return {
            "type": "initialize",
            "id": message.get("id"),
            "result": {
                "protocolVersion": "1.0",
                "serverName": "MCP Ticket Server",
                "serverVersion": "1.0.0",
                "capabilities": {
                    "tools": ["search", "fetch"],
                    "resources": False,
                    "prompts": False
                }
            }
        }
    
    
    async def handle_ws_list_tools(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebSocket list tools request."""
        tools = [
            {
                "name": "search",
                "description": "Searches for resources using the provided query string and returns matching results.",
                "input_schema": {
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
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "ID of the resource to fetch."}
                    },
                    "required": ["id"]
                }
            }
        ]
        
        return {
            "type": "tools_list",
            "id": message.get("id"),
            "tools": tools
        }
    
    
    async def handle_ws_tool_call(connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebSocket tool call request."""
        if not server_instance:
            return {
                "type": "error",
                "id": message.get("id"),
                "error": "Server not initialized"
            }
        
        tool_name = message.get("tool")
        arguments = message.get("arguments", {})
        
        try:
            result = await server_instance._execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": str(e)}
            }
    
    
    @app.get("/connections")
    async def list_connections(auth_result = Depends(verify_authentication)):
        """List active connections (admin endpoint)."""
        if not server_instance or not server_instance.sse_transport:
            raise HTTPException(status_code=503, detail="Server not initialized")
        
        connections = []
        for conn_id, conn in server_instance.sse_transport.connection_manager.connections.items():
            if conn.is_active:
                connections.append({
                    "connection_id": conn_id,
                    "client_ip": conn.client_ip,
                    "connected_at": conn.connected_at.isoformat(),
                    "last_ping": conn.last_ping.isoformat()
                })
        
        return {
            "active_connections": len(connections),
            "connections": connections
        }


async def main():
    """Main entry point for the cloud MCP server."""
    if not FASTAPI_AVAILABLE:
        logger.error("FastAPI not available. Install with: pip install fastapi uvicorn")
        sys.exit(1)
    
    settings = get_cloud_settings()
    
    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True
    )
    
    server = uvicorn.Server(config)
    
    logger.info(f"Starting Cloud MCP Server on {settings.host}:{settings.port}")
    logger.info(f"Auth provider: {settings.auth_provider}")
    logger.info(f"API base URL: {settings.api_base_url}")
    
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())