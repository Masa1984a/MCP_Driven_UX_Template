"""
MCP Server for Ticket Management System
This server connects Claude for desktop to the Ticket API service
for ticket management operations.

Updated version using shared components for consistency with cloud version.
"""
import sys
import os
import logging
from mcp.server.fastmcp import FastMCP, Context, Image
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Dict, List, Optional, Any, Union

# Import shared components
from shared.config import get_base_settings, MCPBaseSettings
from shared.api_client import APIClient
from shared.tools import TicketTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp_ticket_server')


class STDIOContext:
    """Context for STDIO MCP server with shared components."""
    
    def __init__(self, settings: MCPBaseSettings):
        self.settings = settings
        self.api_client = APIClient(
            base_url=settings.api_base_url,
            api_key=settings.api_key,
            timeout=30
        )
        self.ticket_tools = TicketTools(self.api_client)
        
        logger.info(f"Using API base URL: {settings.api_base_url}")
        if settings.api_key:
            logger.info("API key configured for authentication")
        else:
            logger.warning("API_KEY not configured - requests may fail if API requires authentication")


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[STDIOContext]:
    """Manage API connection lifecycle with shared components"""
    # Get settings from shared configuration
    settings = get_base_settings()
    
    # Initialize context with shared components
    context = STDIOContext(settings)
    
    # Test API connection
    try:
        # Simple connectivity test
        test_response = context.api_client.get_sync("tickets/master/statuses")
        logger.info("API connection test successful")
    except Exception as e:
        logger.warning(f"API connection test failed: {e}")
        logger.info("Server will start anyway - API calls may fail")
    
    yield context


# Create FastMCP server with shared components
mcp = FastMCP(
    name="Ticket Management System",
    lifespan=app_lifespan,
    log_level="INFO"
)


@mcp.tool()
def get_ticket_list(
    ctx: Context = None,
    personInChargeId: Optional[str] = None,
    accountId: Optional[str] = None,  
    statusId: Optional[str] = None,
    scheduledCompletionDateFrom: Optional[str] = None,
    scheduledCompletionDateTo: Optional[str] = None,
    showCompleted: Optional[bool] = None,
    searchQuery: Optional[str] = None,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> str:
    """
    Get a list of tickets with optional filtering and pagination.
    
    Args:
        personInChargeId: Filter by person in charge ID
        accountId: Filter by account ID
        statusId: Filter by status ID
        scheduledCompletionDateFrom: Filter by scheduled completion date from (YYYY-MM-DD)
        scheduledCompletionDateTo: Filter by scheduled completion date to (YYYY-MM-DD)
        showCompleted: Include completed tickets (true/false)
        searchQuery: Search query for ticket content
        sortBy: Sort field (id, title, createdAt, updatedAt, scheduledCompletionDate)
        sortOrder: Sort order (asc, desc)
        limit: Maximum number of results to return
        offset: Number of results to skip
        
    Returns:
        Formatted list of tickets as markdown table
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        
        # Build parameters
        params = {}
        if personInChargeId is not None:
            params['personInChargeId'] = personInChargeId
        if accountId is not None:
            params['accountId'] = accountId
        if statusId is not None:
            params['statusId'] = statusId
        if scheduledCompletionDateFrom is not None:
            params['scheduledCompletionDateFrom'] = scheduledCompletionDateFrom
        if scheduledCompletionDateTo is not None:
            params['scheduledCompletionDateTo'] = scheduledCompletionDateTo
        if showCompleted is not None:
            params['showCompleted'] = showCompleted
        if searchQuery is not None:
            params['searchQuery'] = searchQuery
        if sortBy is not None:
            params['sortBy'] = sortBy
        if sortOrder is not None:
            params['sortOrder'] = sortOrder
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        
        # Use shared tools
        return context.ticket_tools.get_ticket_list_sync(**params)
        
    except Exception as e:
        logger.error(f"Error in get_ticket_list: {e}")
        return f"Error retrieving ticket list: {str(e)}"


@mcp.tool()
def get_ticket_detail(ticketId: str, ctx: Context = None) -> str:
    """
    Get detailed information about a specific ticket including its history.
    
    Args:
        ticketId: The ID of the ticket to retrieve
        
    Returns:
        Detailed ticket information formatted as markdown
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.get_ticket_detail_sync(ticketId)
        
    except Exception as e:
        logger.error(f"Error in get_ticket_detail: {e}")
        return f"Error retrieving ticket details: {str(e)}"


@mcp.tool()
def create_ticket(
    title: str,
    description: str,
    personInChargeId: str,
    accountId: str,
    categoryId: str,
    categoryDetailId: str,
    statusId: str,
    requestChannelId: str,
    ctx: Context = None,
    priority: Optional[str] = None,
    scheduledCompletionDate: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    requestedById: Optional[str] = None,
    managerNote: Optional[str] = None,
    customerNote: Optional[str] = None,
    internalNote: Optional[str] = None,
    resolution: Optional[str] = None,
    actualCompletionDate: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new ticket in the system.
    
    Args:
        title: Ticket title (required)
        description: Ticket description (required)
        personInChargeId: ID of the person in charge (required)
        accountId: ID of the account (required)
        categoryId: ID of the category (required)
        categoryDetailId: ID of the category detail (required)
        statusId: ID of the status (required)
        requestChannelId: ID of the request channel (required)
        priority: Priority level (optional)
        scheduledCompletionDate: Scheduled completion date in YYYY-MM-DD format (optional)
        attachments: List of attachment objects (optional)
        requestedById: ID of the person who requested the ticket (optional)
        managerNote: Manager's note (optional)
        customerNote: Customer's note (optional)
        internalNote: Internal note (optional)
        resolution: Resolution description (optional)
        actualCompletionDate: Actual completion date in YYYY-MM-DD format (optional)
        
    Returns:
        Dictionary containing the created ticket ID and success message, or error details
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        
        # Build ticket data
        ticket_data = {
            'title': title,
            'description': description,
            'personInChargeId': personInChargeId,
            'accountId': accountId,
            'categoryId': categoryId,
            'categoryDetailId': categoryDetailId,
            'statusId': statusId,
            'requestChannelId': requestChannelId
        }
        
        # Add optional fields
        if priority is not None:
            ticket_data['priority'] = priority
        if scheduledCompletionDate is not None:
            ticket_data['scheduledCompletionDate'] = scheduledCompletionDate
        if attachments is not None:
            ticket_data['attachments'] = attachments
        if requestedById is not None:
            ticket_data['requestedById'] = requestedById
        if managerNote is not None:
            ticket_data['managerNote'] = managerNote
        if customerNote is not None:
            ticket_data['customerNote'] = customerNote
        if internalNote is not None:
            ticket_data['internalNote'] = internalNote
        if resolution is not None:
            ticket_data['resolution'] = resolution
        if actualCompletionDate is not None:
            ticket_data['actualCompletionDate'] = actualCompletionDate
        
        return context.ticket_tools.create_ticket_sync(**ticket_data)
        
    except Exception as e:
        logger.error(f"Error in create_ticket: {e}")
        return {"error": f"Error creating ticket: {str(e)}"}


@mcp.tool()
def update_ticket(
    ticketId: str,
    updatedById: str,
    ctx: Context = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    personInChargeId: Optional[str] = None,
    accountId: Optional[str] = None,
    categoryId: Optional[str] = None,
    categoryDetailId: Optional[str] = None,
    statusId: Optional[str] = None,
    requestChannelId: Optional[str] = None,
    priority: Optional[str] = None,
    scheduledCompletionDate: Optional[str] = None,
    requestedById: Optional[str] = None,
    managerNote: Optional[str] = None,
    customerNote: Optional[str] = None,
    internalNote: Optional[str] = None,
    resolution: Optional[str] = None,
    actualCompletionDate: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing ticket with new information.
    
    Args:
        ticketId: ID of the ticket to update (required)
        updatedById: ID of the user making the update (required)
        title: New ticket title (optional)
        description: New ticket description (optional)
        personInChargeId: New person in charge ID (optional)
        accountId: New account ID (optional)
        categoryId: New category ID (optional)
        categoryDetailId: New category detail ID (optional)
        statusId: New status ID (optional)
        requestChannelId: New request channel ID (optional)
        priority: New priority level (optional)
        scheduledCompletionDate: New scheduled completion date (optional)
        requestedById: New requested by ID (optional)
        managerNote: New manager's note (optional)
        customerNote: New customer's note (optional)
        internalNote: New internal note (optional)
        resolution: New resolution description (optional)
        actualCompletionDate: New actual completion date (optional)
        
    Returns:
        Dictionary containing success message or error details
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        
        # Build update data
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if personInChargeId is not None:
            update_data['personInChargeId'] = personInChargeId
        if accountId is not None:
            update_data['accountId'] = accountId
        if categoryId is not None:
            update_data['categoryId'] = categoryId
        if categoryDetailId is not None:
            update_data['categoryDetailId'] = categoryDetailId
        if statusId is not None:
            update_data['statusId'] = statusId
        if requestChannelId is not None:
            update_data['requestChannelId'] = requestChannelId
        if priority is not None:
            update_data['priority'] = priority
        if scheduledCompletionDate is not None:
            update_data['scheduledCompletionDate'] = scheduledCompletionDate
        if requestedById is not None:
            update_data['requestedById'] = requestedById
        if managerNote is not None:
            update_data['managerNote'] = managerNote
        if customerNote is not None:
            update_data['customerNote'] = customerNote
        if internalNote is not None:
            update_data['internalNote'] = internalNote
        if resolution is not None:
            update_data['resolution'] = resolution
        if actualCompletionDate is not None:
            update_data['actualCompletionDate'] = actualCompletionDate
        
        return context.ticket_tools.update_ticket_sync(ticketId, updatedById, **update_data)
        
    except Exception as e:
        logger.error(f"Error in update_ticket: {e}")
        return {"error": f"Error updating ticket: {str(e)}"}


@mcp.tool()
def add_ticket_history(ticketId: str, userId: str, comment: str, ctx: Context = None) -> Dict[str, Any]:
    """
    Add a history entry (comment) to a ticket.
    
    Args:
        ticketId: ID of the ticket to add history to
        userId: ID of the user adding the comment
        comment: The comment text to add
        
    Returns:
        Dictionary containing success message or error details
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.add_ticket_history_sync(ticketId, userId, comment)
        
    except Exception as e:
        logger.error(f"Error in add_ticket_history: {e}")
        return {"error": f"Error adding ticket history: {str(e)}"}


@mcp.tool()
def get_users(ctx: Context = None, role: Optional[str] = None) -> str:
    """
    Get a list of users in the system.
    
    Args:
        role: Filter users by role (optional)
        
    Returns:
        Formatted list of users as markdown table
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.get_users_sync(role)
        
    except Exception as e:
        logger.error(f"Error in get_users: {e}")
        return f"Error retrieving users: {str(e)}"


@mcp.tool()
def get_accounts(ctx: Context = None) -> str:
    """
    Get a list of accounts in the system.
    
    Returns:
        Formatted list of accounts as markdown table
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.get_accounts_sync()
        
    except Exception as e:
        logger.error(f"Error in get_accounts: {e}")
        return f"Error retrieving accounts: {str(e)}"


@mcp.tool()
def get_categories(ctx: Context = None) -> str:
    """
    Get a list of ticket categories in the system.
    
    Returns:
        Formatted list of categories as markdown table
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.get_categories_sync()
        
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        return f"Error retrieving categories: {str(e)}"


@mcp.tool()
def get_category_details(ctx: Context = None, categoryId: Optional[str] = None) -> str:
    """
    Get a list of category details in the system.
    
    Args:
        categoryId: Filter by category ID (optional)
        
    Returns:
        Formatted list of category details as markdown table
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.get_category_details_sync(categoryId)
        
    except Exception as e:
        logger.error(f"Error in get_category_details: {e}")
        return f"Error retrieving category details: {str(e)}"


@mcp.tool()
def get_statuses(ctx: Context = None) -> str:
    """
    Get a list of ticket statuses in the system.
    
    Returns:
        Formatted list of statuses as markdown table
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.get_statuses_sync()
        
    except Exception as e:
        logger.error(f"Error in get_statuses: {e}")
        return f"Error retrieving statuses: {str(e)}"


@mcp.tool()
def get_request_channels(ctx: Context = None) -> str:
    """
    Get a list of request channels in the system.
    
    Returns:
        Formatted list of request channels as markdown table
    """
    try:
        context: STDIOContext = ctx.request_context.lifespan_context
        return context.ticket_tools.get_request_channels_sync()
        
    except Exception as e:
        logger.error(f"Error in get_request_channels: {e}")
        return f"Error retrieving request channels: {str(e)}"


@mcp.resource("docs://overview")
def get_overview() -> str:
    """Get an overview of the ticket management system capabilities."""
    return """
# Ticket Management System MCP Server

This server provides access to a comprehensive ticket management system with the following capabilities:

## Available Tools

### Ticket Operations
- **get_ticket_list**: Retrieve tickets with filtering and pagination options
- **get_ticket_detail**: Get detailed information about a specific ticket including history
- **create_ticket**: Create new tickets with all required and optional fields
- **update_ticket**: Update existing tickets with new information
- **add_ticket_history**: Add comments and notes to ticket history

### Master Data Reference
- **get_users**: List system users with optional role filtering
- **get_accounts**: List available accounts
- **get_categories**: List ticket categories
- **get_category_details**: List category details with optional filtering
- **get_statuses**: List available ticket statuses
- **get_request_channels**: List available request channels

## Usage Examples

### List tickets for a specific account:
```
get_ticket_list(accountId="123")
```

### Create a new ticket:
```
create_ticket(
    title="System Issue",
    description="Server is down",
    personInChargeId="1",
    accountId="1",
    categoryId="1", 
    categoryDetailId="1",
    statusId="1",
    requestChannelId="1",
    priority="High"
)
```

### Get available statuses for reference:
```
get_statuses()
```

All tools provide comprehensive error handling and return formatted results for easy reading.
"""


if __name__ == "__main__":
    try:
        logger.info("Starting Ticket Management MCP Server (STDIO version with shared components)")
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)