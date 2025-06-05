"""
MCP Server for Ticket Management System
This server connects Claude for desktop to the Ticket API service
for ticket management operations.

MCP Server for Ticket Management System
This server connects Claude desktop to the Ticket API service
and performs ticket management operations.
"""
import sys
import os
import datetime
import requests
import json
import logging
from mcp.server.fastmcp import FastMCP, Context, Image
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp_ticket_server')

# API configuration
@dataclass
class AppContext:
    api_base_url: str
    api_key: Optional[str] = None

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage API connection lifecycle"""
    # Get API base URL from environment or use default
    api_base_url = os.environ.get('API_BASE_URL', 'http://localhost:8080')
    api_key = os.environ.get('API_KEY')
    
    logger.info(f"Using API base URL: {api_base_url}")
    if api_key:
        logger.info("API key configured for authentication")
    else:
        logger.warning("API_KEY not configured - requests may fail if API requires authentication")
    
    # Test API connection
    try:
        headers = {'x-api-key': api_key} if api_key else {}
        response = requests.get(f"{api_base_url}/health", headers=headers)
        response.raise_for_status()  # Raise exception for non-200 status codes
        logger.info(f"Successfully connected to API at {api_base_url}")
    except Exception as e:
        logger.warning(f"Failed to connect to API at {api_base_url}: {str(e)}")
        logger.warning("API operations may fail if the connection is not available")
    
    try:
        yield AppContext(api_base_url=api_base_url, api_key=api_key)
    finally:
        logger.info("Shutting down API connection")

# Configure MCP server with lifespan
# Explicitly specify log level in uppercase
mcp = FastMCP(
    name="Ticket Management System",
    lifespan=app_lifespan,
    description="Ticket Management System - MCP server for executing various ticket operations",
    log_level="INFO"  # Directly specified with uppercase literal
)

# Helper function to get API headers
def get_api_headers(ctx: Context) -> Dict[str, str]:
    """Get headers for API requests including authentication"""
    headers = {'Content-Type': 'application/json'}
    
    # Only add API key in production environment
    node_env = os.environ.get('NODE_ENV', 'development')
    if node_env == 'production' and hasattr(ctx.request_context.lifespan_context, 'api_key') and ctx.request_context.lifespan_context.api_key:
        headers['x-api-key'] = ctx.request_context.lifespan_context.api_key
    elif node_env == 'development':
        logger.info("Development mode: API key authentication skipped")
    
    return headers

# === Tools ===

@mcp.tool(description="Get ticket list - Display list of tickets according to search criteria")
def get_ticket_list(
    personInChargeId: Optional[str] = None,
    accountId: Optional[str] = None,
    statusId: Optional[str] = None,
    scheduledCompletionDateFrom: Optional[str] = None,
    scheduledCompletionDateTo: Optional[str] = None,
    showCompleted: Optional[bool] = True,
    searchQuery: Optional[str] = None,
    sortBy: str = "receptionDateTime",
    sortOrder: str = "desc",
    limit: int = 20,
    offset: int = 0,
    ctx: Context = None
) -> str:
    """
    Retrieve a list of tickets based on search criteria and display in tabular format

    Parameters:
    - personInChargeId: Filter by person in charge ID (all persons if not specified)
    - accountId: Filter by account ID (all accounts if not specified)
    - statusId: Filter by status ID (all statuses if not specified)
    - scheduledCompletionDateFrom: Scheduled completion date start (YYYY-MM-DD format)
    - scheduledCompletionDateTo: Scheduled completion date end (YYYY-MM-DD format)
    - showCompleted: Whether to show completed tickets (default: True)
    - searchQuery: Search keyword (searches in summary, account name, requestor name)
    - sortBy: Field to sort by (default: "receptionDateTime")
    - sortOrder: Sort order ("asc" or "desc", default: "desc")
    - limit: Maximum number of results to return (default: 20)
    - offset: Starting position (for pagination, default: 0)

    Returns:
    - Ticket list in Markdown table format

    Usage examples:
    1. Display all tickets: get_ticket_list()
    2. Tickets for a specific person in charge: get_ticket_list(personInChargeId="user1")
    3. Keyword search: get_ticket_list(searchQuery="error")
    4. Date range specification: get_ticket_list(scheduledCompletionDateFrom="2023-01-01", scheduledCompletionDateTo="2023-12-31")
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare query parameters
    params = {
        'personInChargeId': personInChargeId,
        'accountId': accountId,
        'statusId': statusId,
        'scheduledCompletionDateFrom': scheduledCompletionDateFrom,
        'scheduledCompletionDateTo': scheduledCompletionDateTo,
        'showCompleted': 'true' if showCompleted else 'false',
        'searchQuery': searchQuery,
        'sortBy': sortBy,
        'sortOrder': sortOrder,
        'limit': limit,
        'offset': offset
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        # Make API request with authentication headers
        headers = get_api_headers(ctx)
        response = requests.get(f"{api_base_url}/tickets", params=params, headers=headers)
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        # Parse response
        tickets = response.json()
        
        # Format as a table
        if not tickets:
            return "No tickets found matching the criteria."
        
        output = "# Ticket List\n\n"
        output += "| ID | Reception Date | Account/Requestor | Category/Detail | Summary | Person in Charge | Status | Scheduled Date/Remaining |\n"
        output += "|---|---|---|---|---|---|---|---|\n"
        
        for t in tickets:
            remaining = f"{t.get('remainingDays')} days left" if t.get('remainingDays') is not None else ""
            scheduled = f"{t.get('scheduledCompletionDate')} {remaining}" if t.get('scheduledCompletionDate') else ""
            
            output += f"| {t.get('ticketId')} | {t.get('receptionDateTime')} | {t.get('accountName')}/{t.get('requestorName')} | "
            output += f"{t.get('categoryName')}/{t.get('categoryDetailName')} | {t.get('summary')} | "
            output += f"{t.get('personInChargeName')} | {t.get('statusName')} | {scheduled} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Get ticket details - Display detailed information for a specific ticket ID")
def get_ticket_detail(
    ticketId: str,
    ctx: Context = None
) -> str:
    """
    Retrieve and display detailed information for a specific ticket based on its ID

    Parameters:
    - ticketId: ID of the ticket to display (e.g., "TCK-0001")

    Returns:
    - Ticket details in Markdown format report
      - Reception information (date/time, account, requestor, category, summary, description, attachments)
      - Response information (person in charge, scheduled completion date, status, completion date, actual effort hours, response category, response details)
      - History (chronological comment history)

    Usage examples:
    1. Display ticket details: get_ticket_detail(ticketId="TCK-0001")

    Notes:
    - Returns an error message if the specified ticket ID doesn't exist
    - History is displayed in newest first order
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Get headers for API requests
        headers = get_api_headers(ctx)
        
        # Get ticket details
        detail_response = requests.get(f"{api_base_url}/tickets/{ticketId}", headers=headers)
        detail_response.raise_for_status()
        
        # Parse ticket data
        ticket = detail_response.json()
        
        # Get ticket history
        history_response = requests.get(f"{api_base_url}/tickets/{ticketId}/history", headers=headers)
        history_response.raise_for_status()
        
        # Parse history data
        history_entries = history_response.json()
        
        # Format as markdown
        output = f"# Ticket Details: {ticket.get('id')}\n\n"
        
        output += "## Reception Information\n\n"
        output += f"- **Reception Date/Time**: {ticket.get('receptionDateTime', 'Not set')}\n"
        output += f"- **Account**: {ticket.get('accountName', 'Not set')}\n"
        output += f"- **Requestor**: {ticket.get('requestorName', 'Not set')}\n"
        output += f"- **Category**: {ticket.get('categoryName', 'Not set')}\n"
        output += f"- **Category Detail**: {ticket.get('categoryDetailName', 'Not set')}\n"
        output += f"- **Request Channel**: {ticket.get('requestChannelName', 'Not set')}\n"
        output += f"- **Summary**: {ticket.get('summary', 'Not set')}\n"
        output += f"- **Description**:\n\n{ticket.get('description', 'Not set')}\n\n"
        
        # Add attachments if any
        attachments = ticket.get('attachments', [])
        if attachments:
            output += "- **Attachments**:\n"
            for attachment in attachments:
                file_name = attachment.get('fileName', 'Unknown file')
                file_url = attachment.get('fileUrl', '#')
                output += f"  - [{file_name}]({file_url})\n"
        else:
            output += "- **Attachments**: None\n"
        
        output += "\n## Response Information\n\n"
        output += f"- **Person in Charge**: {ticket.get('personInChargeName', 'Not set')}\n"
        output += f"- **Scheduled Completion Date**: {ticket.get('scheduledCompletionDate', 'Not set')}\n"
        output += f"- **Status**: {ticket.get('statusName', 'Not set')}\n"
        output += f"- **Completion Date**: {ticket.get('completionDate', 'Not completed')}\n"
        output += f"- **Actual Effort Hours**: {ticket.get('actualEffortHours', 'Not set')} hours\n"
        output += f"- **Response Category**: {ticket.get('responseCategoryName', 'Not set')}\n"
        
        response_details = ticket.get('responseDetails', '')
        output += "- **Response Details**:\n\n"
        output += f"{response_details if response_details else 'Not set'}\n\n"
        
        output += f"- **Has Defect**: {'Yes' if ticket.get('hasDefect') else 'No'}\n"
        output += f"- **External Ticket**: {ticket.get('externalTicketId', 'Not set')}\n"
        output += f"- **Remarks**: {ticket.get('remarks', 'Not set')}\n\n"
        
        # Add history
        output += "## Response History\n\n"
        if history_entries:
            for entry in history_entries:
                output += f"### {entry.get('timestamp')} - {entry.get('userName', 'Unknown')}\n\n"
                output += f"{entry.get('comment', '')}\n\n"
                
                # Add changed fields if any
                changed_fields = entry.get('changedFields', [])
                if changed_fields:
                    output += "Changed fields:\n"
                    for field in changed_fields:
                        field_name = field.get('fieldName', 'Unknown')
                        old_value = field.get('oldValue', '')
                        new_value = field.get('newValue', '')
                        output += f"- {field_name}: {old_value} → {new_value}\n"
                    output += "\n"
        else:
            output += "No history available.\n"
        
        return output
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Ticket {ticketId} not found."
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Create a new ticket - Register a new ticket with the required information")
def create_ticket(
    receptionDateTime: str,
    requestorId: str,
    accountId: str,
    categoryId: str,
    categoryDetailId: str,
    requestChannelId: str,
    summary: str,
    description: str,
    personInChargeId: str,
    statusId: str,
    scheduledCompletionDate: Optional[str] = None,
    completionDate: Optional[str] = None,
    actualEffortHours: Optional[float] = None,
    responseCategoryId: Optional[str] = None,
    responseDetails: Optional[str] = None,
    hasDefect: Optional[bool] = False,
    externalTicketId: Optional[str] = None,
    remarks: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
    ctx: Context = None
) -> Dict[str, str]:
    """
    Register a new ticket in the system

    Parameters:
    - receptionDateTime: Reception date/time (ISO 8601 format: YYYY-MM-DDThh:mm:ss)
    - requestorId: Requestor ID (reference users collection, can be checked with get_users)
    - accountId: Account ID (reference accounts collection, can be checked with get_accounts)
    - categoryId: Category ID (reference categories collection, can be checked with get_categories)
    - categoryDetailId: Category detail ID (reference categoryDetails collection, can be checked with get_category_details)
    - requestChannelId: Request channel ID (e.g., "ch1"=Email, "ch2"=Phone, "ch3"=Teams)
    - summary: Ticket summary (title)
    - description: Ticket detailed content
    - personInChargeId: Person in charge ID (reference users collection, can be checked with get_users)
    - statusId: Status ID (reference statuses collection, can be checked with get_statuses)
    - scheduledCompletionDate: Scheduled completion date (ISO 8601 format: YYYY-MM-DD, optional)
    - completionDate: Completion date (ISO 8601 format: YYYY-MM-DD, optional)
    - actualEffortHours: Actual effort hours (in hours, optional)
    - responseCategoryId: Response category ID (optional)
    - responseDetails: Response details (optional)
    - hasDefect: Whether there is a defect (default: False, optional)
    - externalTicketId: External ticket number (e.g., EEP number, optional)
    - remarks: Remarks (optional)
    - attachments: Attachment information (optional), in the following format:
      [
        {"fileName": "sample.png", "fileUrl": "https://example.com/files/sample.png"}
      ]

    Returns:
    - Dictionary containing the result:
      - Success: {"id": "new ticket ID", "message": "Ticket created. (ID: ticketID)"}
      - Failure: {"error": "Error message"}

    Usage examples:
    1. Basic ticket creation:
       create_ticket(
           receptionDateTime="2023-04-01T09:00:00",
           requestorId="user3",
           accountId="acc1",
           categoryId="cat1",
           categoryDetailId="catd1",
           requestChannelId="ch1",
           summary="Error on login screen",
           description="Authentication error appears on the login screen.\nReproduction steps: ...",
           personInChargeId="user1",
           statusId="stat1",
           scheduledCompletionDate="2023-04-10"
       )

    Notes:
    - Ticket number (ticketId) is automatically assigned ("TCK-XXXX" format)
    - A comment "New ticket created" is automatically added to the history when created
    - An error is returned if any required fields are missing
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare request data
    ticket_data = {
        'receptionDateTime': receptionDateTime,
        'requestorId': requestorId,
        'accountId': accountId,
        'categoryId': categoryId,
        'categoryDetailId': categoryDetailId,
        'requestChannelId': requestChannelId,
        'summary': summary,
        'description': description,
        'personInChargeId': personInChargeId,
        'statusId': statusId,
        'scheduledCompletionDate': scheduledCompletionDate,
        'completionDate': completionDate,
        'actualEffortHours': actualEffortHours,
        'responseCategoryId': responseCategoryId,
        'responseDetails': responseDetails,
        'hasDefect': hasDefect,
        'externalTicketId': externalTicketId,
        'remarks': remarks
    }
    
    # Remove None values
    ticket_data = {k: v for k, v in ticket_data.items() if v is not None}
    
    # Add attachments if provided
    if attachments:
        ticket_data['attachments'] = attachments
    
    try:
        # Make API request
        headers = get_api_headers(ctx)
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f"{api_base_url}/tickets",
            json=ticket_data,
            headers=headers
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        return {
            'id': result.get('id', 'unknown'),
            'message': f"Ticket created. (ID: {result.get('id', 'unknown')})"
        }
    
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        error_msg = str(e)
        try:
            error_json = e.response.json()
            if 'error' in error_json:
                error_msg = error_json['error']
        except:
            pass
        
        return {"error": f"API error: {error_msg}"}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@mcp.tool(description="Update existing ticket - Update ticket information by specifying ticket ID and updated content")
def update_ticket(
    ticketId: str,
    updatedById: str,
    comment: Optional[str] = "Ticket updated",
    requestorId: Optional[str] = None,
    accountId: Optional[str] = None,
    categoryId: Optional[str] = None,
    categoryDetailId: Optional[str] = None,
    requestChannelId: Optional[str] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    personInChargeId: Optional[str] = None,
    statusId: Optional[str] = None,
    scheduledCompletionDate: Optional[str] = None,
    completionDate: Optional[str] = None,
    actualEffortHours: Optional[float] = None,
    responseCategoryId: Optional[str] = None,
    responseDetails: Optional[str] = None,
    hasDefect: Optional[bool] = None,
    externalTicketId: Optional[str] = None,
    remarks: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, str]:
    """
    Update existing ticket information

    Parameters:
    - ticketId: ID of the ticket to update (e.g., "TCK-0001")
    - updatedById: User ID of the person making the update (reference users collection)
    - comment: Update comment (optional, default: "Ticket updated")
    
    Updatable fields (all optional, specify None for fields that shouldn't be updated):
    - requestorId: Requestor ID
    - accountId: Account ID
    - categoryId: Category ID
    - categoryDetailId: Category detail ID
    - requestChannelId: Request channel ID
    - summary: Summary
    - description: Description
    - personInChargeId: Person in charge ID
    - statusId: Status ID
    - scheduledCompletionDate: Scheduled completion date (YYYY-MM-DD format)
    - completionDate: Completion date (YYYY-MM-DD format)
    - actualEffortHours: Actual effort hours (in hours)
    - responseCategoryId: Response category ID
    - responseDetails: Response details
    - hasDefect: Whether there is a defect
    - externalTicketId: External ticket number
    - remarks: Remarks

    Returns:
    - Dictionary containing the result:
      - Success: {"id": "updated ticket ID", "message": "Ticket updated. (ID: ticketID)"}
      - Failure: {"error": "Error message"}

    Usage examples:
    1. Update status and person in charge:
       update_ticket(
           ticketId="TCK-0001",
           updatedById="user1",
           statusId="stat2",
           personInChargeId="user2",
           comment="Transferred to new person in charge"
       )

    2. Complete ticket processing:
       update_ticket(
           ticketId="TCK-0001",
           updatedById="user2",
           statusId="stat4",
           completionDate="2023-05-10",
           actualEffortHours=3.5,
           responseCategoryId="resp1",
           responseDetails="Identified and fixed the issue",
           comment="Response completed"
       )

    Notes:
    - Error if non-existent ticket ID is specified
    - Only the fields specified will be changed; unspecified fields remain unchanged
    - Update history is automatically recorded, and values before and after changes are saved
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare request data - only include fields that need to be updated
    update_data = {
        'updatedById': updatedById,
        'comment': comment
    }
    
    # Add all update fields (excluding None values)
    for field_name in [
        'requestorId', 'accountId', 'categoryId', 'categoryDetailId', 'requestChannelId',
        'summary', 'description', 'personInChargeId', 'statusId', 'scheduledCompletionDate',
        'completionDate', 'actualEffortHours', 'responseCategoryId', 'responseDetails',
        'hasDefect', 'externalTicketId', 'remarks'
    ]:
        value = locals()[field_name]
        if value is not None:
            update_data[field_name] = value
    
    try:
        # Make API request
        headers = get_api_headers(ctx)
        headers['Content-Type'] = 'application/json'
        response = requests.put(
            f"{api_base_url}/tickets/{ticketId}",
            json=update_data,
            headers=headers
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        return {
            'id': result.get('id', 'unknown'),
            'message': f"Ticket updated. (ID: {ticketId})"
        }
    
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        error_msg = str(e)
        try:
            error_json = e.response.json()
            if 'error' in error_json:
                error_msg = error_json['error']
        except:
            pass
        
        if e.response.status_code == 404:
            return {"error": f"Ticket {ticketId} not found."}
        
        return {"error": f"API error: {error_msg}"}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@mcp.tool(description="Add comment or history to a ticket - Record ticket response history")
def add_ticket_history(
    ticketId: str,
    userId: str,
    comment: str,
    ctx: Context = None
) -> Dict[str, str]:
    """
    Add a comment or change history to a ticket

    Parameters:
    - ticketId: Target ticket ID (e.g., "TCK-0001")
    - userId: User ID of the commenter (reference users collection)
    - comment: Comment content

    Returns:
    - Dictionary containing the result:
      - Success: {"id": "history entry ID", "message": "Comment added. (Ticket ID: ticketID)"}
      - Failure: {"error": "Error message"}

    Usage examples:
    1. Simple comment addition:
       add_ticket_history(
           ticketId="TCK-0001",
           userId="user2",
           comment="Reported status to customer via email."
       )

    Notes:
    - It is recommended to use the update_ticket function when changing the ticket status
    - This tool is primarily intended for adding comments and recording history
    - The timestamp for the history is automatically set to the current time
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare request data
    history_data = {
        'userId': userId,
        'comment': comment
    }
    
    try:
        # Make API request
        headers = get_api_headers(ctx)
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f"{api_base_url}/tickets/{ticketId}/history",
            json=history_data,
            headers=headers
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        return {
            'id': result.get('id', 'unknown'),
            'message': f"Comment added. (Ticket ID: {ticketId})"
        }
    
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        error_msg = str(e)
        try:
            error_json = e.response.json()
            if 'error' in error_json:
                error_msg = error_json['error']
        except:
            pass
        
        if e.response.status_code == 404:
            return {"error": f"Ticket {ticketId} not found."}
        
        return {"error": f"API error: {error_msg}"}
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Master data reference tools
@mcp.tool(description="Get user list - Reference user information needed for ticket creation")
def get_users(
    role: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    Retrieve and display a list of users (persons in charge, requestors, etc.) registered in the system

    Parameters:
    - role: Filter by specific role (e.g., "Person in Charge", "Requestor") (optional)

    Returns:
    - User list in Markdown table format

    Usage examples:
    1. Display all users: get_users()
    2. Display only persons in charge: get_users(role="Person in Charge")
    3. Display only requestors: get_users(role="Requestor")

    Notes:
    - User IDs are needed as requestorId or personInChargeId when creating tickets
    - Displayed information: ID, name, email address, role
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare query parameters
    params = {}
    if role:
        params['role'] = role
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/users", params=params, headers=get_api_headers(ctx))
        response.raise_for_status()
        
        # Parse response
        users = response.json()
        
        # Format as markdown
        if not users:
            return "No users registered."
        
        output = "# User List\n\n"
        output += "| ID | Name | Email Address | Role |\n"
        output += "|---|---|---|---|\n"
        
        for user in users:
            output += f"| {user.get('id', '')} | {user.get('name', '')} | {user.get('email', '')} | {user.get('role', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Get account list - Reference account information needed for ticket creation")
def get_accounts(ctx: Context = None) -> str:
    """
    Retrieve and display a list of accounts (customer companies, etc.) registered in the system

    Returns:
    - Account list in Markdown table format

    Usage examples:
    1. Display account list: get_accounts()

    Notes:
    - Account IDs are needed as accountId when creating tickets
    - Displayed information: ID, account name
    - Accounts are displayed sorted by account name
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/accounts", headers=get_api_headers(ctx))
        response.raise_for_status()
        
        # Parse response
        accounts = response.json()
        
        # Format as markdown
        if not accounts:
            return "No accounts registered."
        
        output = "# Account List\n\n"
        output += "| ID | Account Name |\n"
        output += "|---|---|\n"
        
        for account in accounts:
            output += f"| {account.get('id', '')} | {account.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Get category list - Reference category information needed for ticket creation")
def get_categories(ctx: Context = None) -> str:
    """
    Retrieve and display a list of ticket categories used in the system

    Returns:
    - Category list in Markdown table format

    Usage examples:
    1. Display category list: get_categories()

    Notes:
    - Category IDs are needed as categoryId when creating tickets
    - After selecting a category, retrieve related category details with get_category_details(categoryId="...")
    - Displayed information: ID, category name
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/categories", headers=get_api_headers(ctx))
        response.raise_for_status()
        
        # Parse response
        categories = response.json()
        
        # Format as markdown
        if not categories:
            return "No categories registered."
        
        output = "# Category List\n\n"
        output += "| ID | Category Name |\n"
        output += "|---|---|\n"
        
        for category in categories:
            output += f"| {category.get('id', '')} | {category.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Get category detail list - Reference category detail information needed for ticket creation")
def get_category_details(
    categoryId: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    Retrieve and display a list of ticket category details used in the system

    Parameters:
    - categoryId: Filter by specific parent category ID (optional)

    Returns:
    - Category detail list in Markdown table format

    Usage examples:
    1. Display all category details: get_category_details()
    2. Display only details belonging to a specific category: get_category_details(categoryId="cat1")

    Notes:
    - Category detail IDs are needed as categoryDetailId when creating tickets
    - Category IDs can be checked with get_categories()
    - Displayed information: ID, detail name, parent category
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare query parameters
    params = {}
    if categoryId:
        params['categoryId'] = categoryId
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/category-details", params=params, headers=get_api_headers(ctx))
        response.raise_for_status()
        
        # Parse response
        category_details = response.json()
        
        # Format as markdown
        if not category_details:
            return "No category details registered."
        
        output = "# Category Detail List\n\n"
        output += "| ID | Detail Name | Parent Category |\n"
        output += "|---|---|---|\n"
        
        for detail in category_details:
            output += f"| {detail.get('id', '')} | {detail.get('name', '')} | {detail.get('categoryName', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Get status list - Reference status information needed for ticket creation/update")
def get_statuses(ctx: Context = None) -> str:
    """
    Retrieve and display a list of ticket statuses used in the system

    Returns:
    - Status list in Markdown table format

    Usage examples:
    1. Display status list: get_statuses()

    Notes:
    - Status IDs are needed as statusId when creating or updating tickets
    - Displayed information: ID, status name
    - Statuses are displayed in typical workflow order
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/statuses", headers=get_api_headers(ctx))
        response.raise_for_status()
        
        # Parse response
        statuses = response.json()
        
        # Format as markdown
        if not statuses:
            return "No statuses registered."
        
        output = "# Status List\n\n"
        output += "| ID | Status Name |\n"
        output += "|---|---|\n"
        
        for status in statuses:
            output += f"| {status.get('id', '')} | {status.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool(description="Get request channel list - Reference channel information needed for ticket creation")
def get_request_channels(ctx: Context = None) -> str:
    """
    Retrieve and display a list of request channels used in the system
    
    Returns:
    - Request channel list in Markdown table format

    Usage examples:
    1. Display request channel list: get_request_channels()

    Notes:
    - Request channel IDs are needed as requestChannelId when creating tickets
    - Displayed information: ID, channel name
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/request-channels", headers=get_api_headers(ctx))
        response.raise_for_status()
        
        # Parse response
        channels = response.json()
        
        # Format as markdown
        if not channels:
            return "No request channels registered."
        
        output = "# Request Channel List\n\n"
        output += "| ID | Channel Name |\n"
        output += "|---|---|\n"
        
        for channel in channels:
            output += f"| {channel.get('id', '')} | {channel.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

# === Resources ===

# Add a basic resource for documentation
@mcp.resource("docs://overview")
def get_overview_docs() -> str:
    """Get overview documentation for the ticket system"""
    return """
    # Ticket Management System MCP Server

    This server provides various ticket operations through the Ticket Management System API.

    ## Available Features

    ### Ticket Operations
    
    - **Get Ticket List**: Retrieve a list of tickets based on conditions (`get_ticket_list`)
    - **Get Ticket Details**: Retrieve detailed information for a specific ticket (`get_ticket_detail`)
    - **Create Ticket**: Create a new ticket (`create_ticket`)
    - **Update Ticket**: Update existing ticket information (`update_ticket`)
    - **Add History**: Add comments or history to a ticket (`add_ticket_history`)

    ### Master Data Reference
    
    - **User List**: Retrieve user information registered in the system (`get_users`)
    - **Account List**: Retrieve account information registered in the system (`get_accounts`)
    - **Category List**: Retrieve category information registered in the system (`get_categories`)
    - **Category Detail List**: Retrieve category detail information registered in the system (`get_category_details`)
    - **Status List**: Retrieve status information registered in the system (`get_statuses`)
    - **Request Channel List**: Retrieve request channel information registered in the system (`get_request_channels`)

    ## Notes

    - For detailed usage of each feature, refer to the docstring following the tool name
    - The API connection destination can be configured with the environment variable `API_BASE_URL` (default: http://localhost:8080)
    """

# Run the server
if __name__ == "__main__":
    logger.info("MCP server starting...")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        logger.info("MCP server stopped.")
