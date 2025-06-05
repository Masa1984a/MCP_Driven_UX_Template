"""
Shared ticket management tools for MCP server implementations.

Provides common tool functionality for both STDIO and cloud versions
with consistent API communication and data formatting.
"""

import datetime
import json
from typing import Dict, List, Optional, Any, Union
from .api_client import APIClient, APIClientError


class TicketTools:
    """
    Shared ticket management tools for MCP server implementations.
    
    Provides consistent tool functionality with proper error handling
    and data formatting for both sync and async contexts.
    """
    
    def __init__(self, api_client: APIClient):
        """
        Initialize ticket tools with API client.
        
        Args:
            api_client: Configured API client instance
        """
        self.api_client = api_client
    
    def _remove_none_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove None values from dictionary."""
        return {k: v for k, v in data.items() if v is not None}
    
    def _format_markdown_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Format data as markdown table."""
        if not rows:
            return "No data found."
        
        # Create header row
        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        # Create data rows
        data_rows = []
        for row in rows:
            # Escape markdown characters and handle None values
            escaped_row = [str(cell).replace("|", "\\|") if cell is not None else "" for cell in row]
            data_rows.append("| " + " | ".join(escaped_row) + " |")
        
        return "\n".join([header_row, separator_row] + data_rows)
    
    def _handle_api_error(self, error: Exception, operation: str) -> Dict[str, str]:
        """Standard error handling for API operations."""
        if isinstance(error, APIClientError):
            return {"error": f"{operation} failed: {str(error)}"}
        else:
            return {"error": f"Unexpected error during {operation}: {str(error)}"}
    
    # Sync versions (for STDIO compatibility)
    
    def get_ticket_list_sync(self, **kwargs) -> str:
        """
        Get ticket list with filtering and pagination (sync version).
        
        Args:
            personInChargeId: Filter by person in charge
            accountId: Filter by account
            statusId: Filter by status
            scheduledCompletionDateFrom: Start date filter (YYYY-MM-DD)
            scheduledCompletionDateTo: End date filter (YYYY-MM-DD)
            showCompleted: Include completed tickets
            searchQuery: Text search query
            sortBy: Sort field
            sortOrder: Sort order (asc/desc)
            limit: Maximum results
            offset: Results offset
            
        Returns:
            Markdown formatted ticket list or error message
        """
        try:
            # Build query parameters, removing None values
            params = self._remove_none_values(kwargs)
            
            response = self.api_client.get_sync("tickets", params=params)
            tickets = response.get('tickets', [])
            
            if not tickets:
                return "No tickets found matching the criteria."
            
            # Format as markdown table
            headers = ["ID", "Title", "Status", "Person in Charge", "Account", "Priority", "Due Date"]
            rows = []
            
            for ticket in tickets:
                due_date = ticket.get('scheduledCompletionDate', '')
                if due_date:
                    try:
                        # Format date if it's a valid ISO string
                        parsed_date = datetime.datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        due_date = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass  # Keep original format if parsing fails
                
                rows.append([
                    str(ticket.get('id', '')),
                    ticket.get('title', ''),
                    ticket.get('statusName', ''),
                    ticket.get('personInChargeName', ''),
                    ticket.get('accountName', ''),
                    ticket.get('priority', ''),
                    due_date
                ])
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving ticket list: {str(e)}"
    
    def get_ticket_detail_sync(self, ticket_id: str) -> str:
        """
        Get detailed ticket information including history (sync version).
        
        Args:
            ticket_id: Ticket ID to retrieve
            
        Returns:
            Detailed markdown report or error message
        """
        try:
            # Get ticket details
            ticket_response = self.api_client.get_sync(f"tickets/{ticket_id}")
            ticket = ticket_response.get('ticket')
            
            if not ticket:
                return f"Ticket {ticket_id} not found."
            
            # Get ticket history
            try:
                history_response = self.api_client.get_sync(f"tickets/{ticket_id}/history")
                history = history_response.get('history', [])
            except:
                history = []
            
            # Format detailed report
            report = f"# Ticket Details - {ticket.get('title', 'Untitled')}\n\n"
            report += f"**ID**: {ticket.get('id', '')}\n"
            report += f"**Status**: {ticket.get('statusName', '')}\n"
            report += f"**Priority**: {ticket.get('priority', '')}\n"
            report += f"**Person in Charge**: {ticket.get('personInChargeName', '')}\n"
            report += f"**Account**: {ticket.get('accountName', '')}\n"
            report += f"**Category**: {ticket.get('categoryName', '')}\n"
            report += f"**Category Detail**: {ticket.get('categoryDetailName', '')}\n"
            report += f"**Request Channel**: {ticket.get('requestChannelName', '')}\n"
            
            # Format dates
            created_date = ticket.get('createdAt', '')
            updated_date = ticket.get('updatedAt', '')
            due_date = ticket.get('scheduledCompletionDate', '')
            
            if created_date:
                try:
                    parsed_date = datetime.datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    created_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            if updated_date:
                try:
                    parsed_date = datetime.datetime.fromisoformat(updated_date.replace('Z', '+00:00'))
                    updated_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            if due_date:
                try:
                    parsed_date = datetime.datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    due_date = parsed_date.strftime('%Y-%m-%d')
                except:
                    pass
            
            report += f"**Created**: {created_date}\n"
            report += f"**Updated**: {updated_date}\n"
            report += f"**Due Date**: {due_date}\n\n"
            
            # Description
            if ticket.get('description'):
                report += f"## Description\n{ticket['description']}\n\n"
            
            # Attachments
            attachments = ticket.get('attachments', [])
            if attachments:
                report += "## Attachments\n"
                for attachment in attachments:
                    name = attachment.get('fileName', 'Unnamed')
                    url = attachment.get('url', '#')
                    report += f"- [{name}]({url})\n"
                report += "\n"
            
            # History
            if history:
                report += "## History\n"
                for entry in history:
                    timestamp = entry.get('createdAt', '')
                    if timestamp:
                        try:
                            parsed_date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    
                    user_name = entry.get('userName', 'Unknown User')
                    comment = entry.get('comment', '')
                    changed_fields = entry.get('changedFields', [])
                    
                    report += f"### {timestamp} - {user_name}\n"
                    
                    if comment:
                        report += f"**Comment**: {comment}\n"
                    
                    if changed_fields:
                        report += "**Changed Fields**:\n"
                        for field in changed_fields:
                            field_name = field.get('fieldName', '')
                            old_value = field.get('oldValue', '')
                            new_value = field.get('newValue', '')
                            report += f"- {field_name}: {old_value} → {new_value}\n"
                    
                    report += "\n"
            
            return report
            
        except Exception as e:
            return f"Error retrieving ticket details: {str(e)}"
    
    def create_ticket_sync(self, **kwargs) -> Dict[str, Any]:
        """
        Create a new ticket (sync version).
        
        Args:
            title: Ticket title (required)
            description: Ticket description (required)
            personInChargeId: Person in charge ID (required)
            accountId: Account ID (required)
            categoryId: Category ID (required)
            categoryDetailId: Category detail ID (required)
            statusId: Status ID (required)
            requestChannelId: Request channel ID (required)
            priority: Priority level
            scheduledCompletionDate: Due date (YYYY-MM-DD)
            attachments: List of attachments
            ... (other optional fields)
            
        Returns:
            Dict with 'id' and 'message' on success, 'error' on failure
        """
        try:
            # Remove None values from request data
            ticket_data = self._remove_none_values(kwargs)
            
            response = self.api_client.post_sync("tickets", data=ticket_data)
            
            if response.get('success'):
                ticket_id = response.get('ticketId') or response.get('id')
                return {
                    "id": ticket_id,
                    "message": f"Ticket created successfully with ID: {ticket_id}"
                }
            else:
                return {"error": f"Failed to create ticket: {response.get('message', 'Unknown error')}"}
                
        except Exception as e:
            return self._handle_api_error(e, "Ticket creation")
    
    def update_ticket_sync(self, ticket_id: str, updated_by_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing ticket (sync version).
        
        Args:
            ticket_id: Ticket ID to update
            updated_by_id: ID of user making the update
            **kwargs: Fields to update
            
        Returns:
            Dict with 'id' and 'message' on success, 'error' on failure
        """
        try:
            # Build update data
            update_data = {"updatedById": updated_by_id}
            update_data.update(self._remove_none_values(kwargs))
            
            response = self.api_client.put_sync(f"tickets/{ticket_id}", data=update_data)
            
            if response.get('success'):
                return {
                    "id": ticket_id,
                    "message": f"Ticket {ticket_id} updated successfully"
                }
            else:
                return {"error": f"Failed to update ticket: {response.get('message', 'Unknown error')}"}
                
        except Exception as e:
            return self._handle_api_error(e, "Ticket update")
    
    def add_ticket_history_sync(self, ticket_id: str, user_id: str, comment: str) -> Dict[str, Any]:
        """
        Add history entry to ticket (sync version).
        
        Args:
            ticket_id: Ticket ID
            user_id: User ID adding the comment
            comment: Comment text
            
        Returns:
            Dict with 'id' and 'message' on success, 'error' on failure
        """
        try:
            history_data = {
                "userId": user_id,
                "comment": comment
            }
            
            response = self.api_client.post_sync(f"tickets/{ticket_id}/history", data=history_data)
            
            if response.get('success'):
                history_id = response.get('historyId') or response.get('id')
                return {
                    "id": history_id,
                    "message": f"History entry added to ticket {ticket_id}"
                }
            else:
                return {"error": f"Failed to add history: {response.get('message', 'Unknown error')}"}
                
        except Exception as e:
            return self._handle_api_error(e, "History addition")
    
    # Master data retrieval methods
    
    def get_users_sync(self, role: Optional[str] = None) -> str:
        """Get users list (sync version)."""
        try:
            params = {"role": role} if role else {}
            response = self.api_client.get_sync("tickets/master/users", params=params)
            users = response.get('users', [])
            
            if not users:
                return "No users found."
            
            headers = ["ID", "Name", "Email", "Role"]
            rows = [[str(user.get('id', '')), user.get('name', ''), 
                    user.get('email', ''), user.get('role', '')] for user in users]
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving users: {str(e)}"
    
    def get_accounts_sync(self) -> str:
        """Get accounts list (sync version)."""
        try:
            response = self.api_client.get_sync("tickets/master/accounts")
            accounts = response.get('accounts', [])
            
            if not accounts:
                return "No accounts found."
            
            headers = ["ID", "Account Name"]
            rows = [[str(account.get('id', '')), account.get('name', '')] for account in accounts]
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving accounts: {str(e)}"
    
    def get_categories_sync(self) -> str:
        """Get categories list (sync version)."""
        try:
            response = self.api_client.get_sync("tickets/master/categories")
            categories = response.get('categories', [])
            
            if not categories:
                return "No categories found."
            
            headers = ["ID", "Category Name"]
            rows = [[str(cat.get('id', '')), cat.get('name', '')] for cat in categories]
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving categories: {str(e)}"
    
    def get_category_details_sync(self, category_id: Optional[str] = None) -> str:
        """Get category details list (sync version)."""
        try:
            params = {"categoryId": category_id} if category_id else {}
            response = self.api_client.get_sync("tickets/master/category-details", params=params)
            details = response.get('categoryDetails', [])
            
            if not details:
                return "No category details found."
            
            headers = ["ID", "Detail Name", "Category"]
            rows = [[str(detail.get('id', '')), detail.get('name', ''), 
                    detail.get('categoryName', '')] for detail in details]
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving category details: {str(e)}"
    
    def get_statuses_sync(self) -> str:
        """Get statuses list (sync version)."""
        try:
            response = self.api_client.get_sync("tickets/master/statuses")
            statuses = response.get('statuses', [])
            
            if not statuses:
                return "No statuses found."
            
            headers = ["ID", "Status Name"]
            rows = [[str(status.get('id', '')), status.get('name', '')] for status in statuses]
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving statuses: {str(e)}"
    
    def get_request_channels_sync(self) -> str:
        """Get request channels list (sync version)."""
        try:
            response = self.api_client.get_sync("tickets/master/request-channels")
            channels = response.get('requestChannels', [])
            
            if not channels:
                return "No request channels found."
            
            headers = ["ID", "Channel Name"]
            rows = [[str(channel.get('id', '')), channel.get('name', '')] for channel in channels]
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving request channels: {str(e)}"
    
    # Async versions (for cloud compatibility)
    
    async def get_ticket_list(self, **kwargs) -> str:
        """Get ticket list with filtering and pagination (async version)."""
        try:
            params = self._remove_none_values(kwargs)
            response = await self.api_client.get("tickets", params=params)
            tickets = response.get('tickets', [])
            
            if not tickets:
                return "No tickets found matching the criteria."
            
            headers = ["ID", "Title", "Status", "Person in Charge", "Account", "Priority", "Due Date"]
            rows = []
            
            for ticket in tickets:
                due_date = ticket.get('scheduledCompletionDate', '')
                if due_date:
                    try:
                        parsed_date = datetime.datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        due_date = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
                
                rows.append([
                    str(ticket.get('id', '')),
                    ticket.get('title', ''),
                    ticket.get('statusName', ''),
                    ticket.get('personInChargeName', ''),
                    ticket.get('accountName', ''),
                    ticket.get('priority', ''),
                    due_date
                ])
            
            return self._format_markdown_table(headers, rows)
            
        except Exception as e:
            return f"Error retrieving ticket list: {str(e)}"
    
    async def get_ticket_detail(self, ticket_id: str) -> str:
        """Get detailed ticket information including history (async version)."""
        try:
            ticket_response = await self.api_client.get(f"tickets/{ticket_id}")
            ticket = ticket_response.get('ticket')
            
            if not ticket:
                return f"Ticket {ticket_id} not found."
            
            try:
                history_response = await self.api_client.get(f"tickets/{ticket_id}/history")
                history = history_response.get('history', [])
            except:
                history = []
            
            # Use same formatting logic as sync version
            return self._format_ticket_detail_report(ticket, history)
            
        except Exception as e:
            return f"Error retrieving ticket details: {str(e)}"
    
    def _format_ticket_detail_report(self, ticket: Dict[str, Any], history: List[Dict[str, Any]]) -> str:
        """Format ticket details and history into markdown report."""
        report = f"# Ticket Details - {ticket.get('title', 'Untitled')}\n\n"
        report += f"**ID**: {ticket.get('id', '')}\n"
        report += f"**Status**: {ticket.get('statusName', '')}\n"
        report += f"**Priority**: {ticket.get('priority', '')}\n"
        report += f"**Person in Charge**: {ticket.get('personInChargeName', '')}\n"
        report += f"**Account**: {ticket.get('accountName', '')}\n"
        report += f"**Category**: {ticket.get('categoryName', '')}\n"
        report += f"**Category Detail**: {ticket.get('categoryDetailName', '')}\n"
        report += f"**Request Channel**: {ticket.get('requestChannelName', '')}\n"
        
        # Format dates
        created_date = self._format_datetime(ticket.get('createdAt', ''))
        updated_date = self._format_datetime(ticket.get('updatedAt', ''))
        due_date = self._format_date(ticket.get('scheduledCompletionDate', ''))
        
        report += f"**Created**: {created_date}\n"
        report += f"**Updated**: {updated_date}\n"
        report += f"**Due Date**: {due_date}\n\n"
        
        # Description
        if ticket.get('description'):
            report += f"## Description\n{ticket['description']}\n\n"
        
        # Attachments
        attachments = ticket.get('attachments', [])
        if attachments:
            report += "## Attachments\n"
            for attachment in attachments:
                name = attachment.get('fileName', 'Unnamed')
                url = attachment.get('url', '#')
                report += f"- [{name}]({url})\n"
            report += "\n"
        
        # History
        if history:
            report += "## History\n"
            for entry in history:
                timestamp = self._format_datetime(entry.get('createdAt', ''))
                user_name = entry.get('userName', 'Unknown User')
                comment = entry.get('comment', '')
                changed_fields = entry.get('changedFields', [])
                
                report += f"### {timestamp} - {user_name}\n"
                
                if comment:
                    report += f"**Comment**: {comment}\n"
                
                if changed_fields:
                    report += "**Changed Fields**:\n"
                    for field in changed_fields:
                        field_name = field.get('fieldName', '')
                        old_value = field.get('oldValue', '')
                        new_value = field.get('newValue', '')
                        report += f"- {field_name}: {old_value} → {new_value}\n"
                
                report += "\n"
        
        return report
    
    def _format_datetime(self, timestamp: str) -> str:
        """Format ISO timestamp to readable datetime."""
        if not timestamp:
            return ""
        try:
            parsed_date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    
    def _format_date(self, timestamp: str) -> str:
        """Format ISO timestamp to readable date."""
        if not timestamp:
            return ""
        try:
            parsed_date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return timestamp