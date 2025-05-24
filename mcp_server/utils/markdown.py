"""
Markdown Table Generation Utilities

This module provides unified table generation functions for consistent
GitHub-style markdown table formatting across all MCP server tools.
"""

from typing import List, Dict, Any, Optional
from tabulate import tabulate


def to_md_table(
    data: List[Dict[str, Any]], 
    headers: Optional[List[str]] = None,
    title: Optional[str] = None
) -> str:
    """
    Convert list of dictionaries to GitHub-style markdown table
    
    Args:
        data: List of dictionaries containing table data
        headers: Optional list of column headers. If None, uses keys from first data item
        title: Optional table title to include above the table
        
    Returns:
        Formatted markdown table string
    """
    if not data:
        return "No data available."
    
    # Use provided headers or extract from first item
    if headers is None:
        headers = list(data[0].keys())
    
    # Extract table rows based on specified headers
    table_data = []
    for row in data:
        table_row = [row.get(header, '') for header in headers]
        table_data.append(table_row)
    
    # Generate table using tabulate with GitHub style
    table = tabulate(table_data, headers=headers, tablefmt="github")
    
    # Add title if provided
    if title:
        return f"# {title}\n\n{table}"
    
    return table


def tickets_to_md_table(tickets: List[Dict[str, Any]]) -> str:
    """
    Convert ticket data to markdown table with standardized columns
    
    Args:
        tickets: List of ticket dictionaries from API
        
    Returns:
        Formatted markdown table for tickets
    """
    if not tickets:
        return "No tickets found matching the criteria."
    
    # Define standard ticket table structure
    headers = [
        "ID", "Reception Date", "Account/Requestor", "Category/Detail", 
        "Summary", "Person in Charge", "Status", "Scheduled Date/Remaining"
    ]
    
    # Transform ticket data to match headers
    table_data = []
    for ticket in tickets:
        # Format complex fields
        account_requestor = f"{ticket.get('accountName', '')}/{ticket.get('requestorName', '')}"
        category_detail = f"{ticket.get('categoryName', '')}/{ticket.get('categoryDetailName', '')}"
        
        # Handle scheduled date and remaining days
        remaining = f"{ticket.get('remainingDays')} days left" if ticket.get('remainingDays') is not None else ""
        scheduled = f"{ticket.get('scheduledCompletionDate')} {remaining}" if ticket.get('scheduledCompletionDate') else ""
        
        row_data = {
            "ID": ticket.get('ticketId', ''),
            "Reception Date": ticket.get('receptionDateTime', ''),
            "Account/Requestor": account_requestor,
            "Category/Detail": category_detail,
            "Summary": ticket.get('summary', ''),
            "Person in Charge": ticket.get('personInChargeName', ''),
            "Status": ticket.get('statusName', ''),
            "Scheduled Date/Remaining": scheduled
        }
        
        table_data.append(row_data)
    
    return to_md_table(table_data, headers=headers, title="Ticket List")


def users_to_md_table(users: List[Dict[str, Any]]) -> str:
    """
    Convert user data to markdown table with standardized columns
    
    Args:
        users: List of user dictionaries from API
        
    Returns:
        Formatted markdown table for users
    """
    if not users:
        return "No users registered."
    
    headers = ["ID", "Name", "Email Address", "Role"]
    return to_md_table(users, headers=headers, title="User List")


def accounts_to_md_table(accounts: List[Dict[str, Any]]) -> str:
    """
    Convert account data to markdown table with standardized columns
    
    Args:
        accounts: List of account dictionaries from API
        
    Returns:
        Formatted markdown table for accounts
    """
    if not accounts:
        return "No accounts registered."
    
    headers = ["ID", "Account Name"]
    # Map 'name' to 'Account Name' for consistency
    normalized_data = []
    for account in accounts:
        normalized_data.append({
            "ID": account.get('id', ''),
            "Account Name": account.get('name', '')
        })
    
    return to_md_table(normalized_data, headers=headers, title="Account List")


def categories_to_md_table(categories: List[Dict[str, Any]]) -> str:
    """
    Convert category data to markdown table with standardized columns
    
    Args:
        categories: List of category dictionaries from API
        
    Returns:
        Formatted markdown table for categories
    """
    if not categories:
        return "No categories registered."
    
    headers = ["ID", "Category Name"]
    # Map 'name' to 'Category Name' for consistency
    normalized_data = []
    for category in categories:
        normalized_data.append({
            "ID": category.get('id', ''),
            "Category Name": category.get('name', '')
        })
    
    return to_md_table(normalized_data, headers=headers, title="Category List")


def category_details_to_md_table(category_details: List[Dict[str, Any]]) -> str:
    """
    Convert category detail data to markdown table with standardized columns
    
    Args:
        category_details: List of category detail dictionaries from API
        
    Returns:
        Formatted markdown table for category details
    """
    if not category_details:
        return "No category details registered."
    
    headers = ["ID", "Detail Name", "Parent Category"]
    # Map 'name' to 'Detail Name' for consistency
    normalized_data = []
    for detail in category_details:
        normalized_data.append({
            "ID": detail.get('id', ''),
            "Detail Name": detail.get('name', ''),
            "Parent Category": detail.get('categoryName', '')
        })
    
    return to_md_table(normalized_data, headers=headers, title="Category Detail List")


def statuses_to_md_table(statuses: List[Dict[str, Any]]) -> str:
    """
    Convert status data to markdown table with standardized columns
    
    Args:
        statuses: List of status dictionaries from API
        
    Returns:
        Formatted markdown table for statuses
    """
    if not statuses:
        return "No statuses registered."
    
    headers = ["ID", "Status Name"]
    # Map 'name' to 'Status Name' for consistency
    normalized_data = []
    for status in statuses:
        normalized_data.append({
            "ID": status.get('id', ''),
            "Status Name": status.get('name', '')
        })
    
    return to_md_table(normalized_data, headers=headers, title="Status List")


def request_channels_to_md_table(channels: List[Dict[str, Any]]) -> str:
    """
    Convert request channel data to markdown table with standardized columns
    
    Args:
        channels: List of request channel dictionaries from API
        
    Returns:
        Formatted markdown table for request channels
    """
    if not channels:
        return "No request channels registered."
    
    headers = ["ID", "Channel Name"]
    # Map 'name' to 'Channel Name' for consistency
    normalized_data = []
    for channel in channels:
        normalized_data.append({
            "ID": channel.get('id', ''),
            "Channel Name": channel.get('name', '')
        })
    
    return to_md_table(normalized_data, headers=headers, title="Request Channel List")