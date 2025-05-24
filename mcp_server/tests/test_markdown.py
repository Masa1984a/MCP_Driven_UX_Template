"""
Unit tests for markdown table generation utilities

Tests column order changes and data formatting for consistent GitHub table output.
"""

import unittest
from utils.markdown import (
    to_md_table, tickets_to_md_table, users_to_md_table, accounts_to_md_table,
    categories_to_md_table, category_details_to_md_table, statuses_to_md_table,
    request_channels_to_md_table
)


class TestMarkdownTableUtilities(unittest.TestCase):
    
    def test_to_md_table_basic(self):
        """Test basic table generation with simple data"""
        data = [
            {"id": "1", "name": "Test"},
            {"id": "2", "name": "Example"}
        ]
        result = to_md_table(data)
        
        # Should contain GitHub table format
        self.assertIn("|", result)
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertIn("Test", result)
        self.assertIn("Example", result)
    
    def test_to_md_table_with_title(self):
        """Test table generation with title"""
        data = [{"id": "1", "name": "Test"}]
        result = to_md_table(data, title="Test Table")
        
        self.assertIn("# Test Table", result)
    
    def test_to_md_table_custom_headers(self):
        """Test table generation with custom headers"""
        data = [{"id": "1", "name": "Test", "extra": "ignore"}]
        headers = ["id", "name"]
        result = to_md_table(data, headers=headers)
        
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertNotIn("extra", result)
    
    def test_to_md_table_empty_data(self):
        """Test table generation with empty data"""
        result = to_md_table([])
        self.assertEqual(result, "No data available.")
    
    def test_tickets_to_md_table(self):
        """Test ticket table generation"""
        tickets = [
            {
                "ticketId": "TCK-001",
                "receptionDateTime": "2023-01-01T10:00:00",
                "accountName": "Company A",
                "requestorName": "John Doe",
                "categoryName": "Bug",
                "categoryDetailName": "UI Issue",
                "summary": "Login problem",
                "personInChargeName": "Jane Smith",
                "statusName": "Open",
                "scheduledCompletionDate": "2023-01-10",
                "remainingDays": 5
            }
        ]
        
        result = tickets_to_md_table(tickets)
        
        # Check for presence of expected data
        self.assertIn("TCK-001", result)
        self.assertIn("Company A/John Doe", result)  # Combined field
        self.assertIn("Bug/UI Issue", result)  # Combined field
        self.assertIn("5 days left", result)  # Formatted remaining days
        self.assertIn("# Ticket List", result)  # Title
    
    def test_tickets_to_md_table_empty(self):
        """Test ticket table with empty data"""
        result = tickets_to_md_table([])
        self.assertEqual(result, "No tickets found matching the criteria.")
    
    def test_users_to_md_table(self):
        """Test user table generation"""
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com", "role": "Admin"}
        ]
        
        result = users_to_md_table(users)
        
        self.assertIn("user1", result)
        self.assertIn("John Doe", result)
        self.assertIn("john@example.com", result)
        self.assertIn("Admin", result)
        self.assertIn("# User List", result)
    
    def test_accounts_to_md_table(self):
        """Test account table generation"""
        accounts = [
            {"id": "acc1", "name": "Company A"}
        ]
        
        result = accounts_to_md_table(accounts)
        
        self.assertIn("acc1", result)
        self.assertIn("Company A", result)
        self.assertIn("# Account List", result)
    
    def test_categories_to_md_table(self):
        """Test category table generation"""
        categories = [
            {"id": "cat1", "name": "Bug Reports"}
        ]
        
        result = categories_to_md_table(categories)
        
        self.assertIn("cat1", result)
        self.assertIn("Bug Reports", result)
        self.assertIn("# Category List", result)
    
    def test_category_details_to_md_table(self):
        """Test category details table generation"""
        category_details = [
            {"id": "cd1", "name": "UI Issue", "categoryName": "Bug Reports"}
        ]
        
        result = category_details_to_md_table(category_details)
        
        self.assertIn("cd1", result)
        self.assertIn("UI Issue", result)
        self.assertIn("Bug Reports", result)
        self.assertIn("# Category Detail List", result)
    
    def test_statuses_to_md_table(self):
        """Test status table generation"""
        statuses = [
            {"id": "stat1", "name": "Open"}
        ]
        
        result = statuses_to_md_table(statuses)
        
        self.assertIn("stat1", result)
        self.assertIn("Open", result)
        self.assertIn("# Status List", result)
    
    def test_request_channels_to_md_table(self):
        """Test request channels table generation"""
        channels = [
            {"id": "ch1", "name": "Email"}
        ]
        
        result = request_channels_to_md_table(channels)
        
        self.assertIn("ch1", result)
        self.assertIn("Email", result)
        self.assertIn("# Request Channel List", result)
    
    def test_column_order_consistency(self):
        """Test that column order remains consistent across modifications"""
        # Test that tickets table always has the same column structure
        tickets1 = [
            {
                "ticketId": "TCK-001",
                "receptionDateTime": "2023-01-01T10:00:00",
                "accountName": "Company A",
                "requestorName": "John Doe",
                "categoryName": "Bug",
                "categoryDetailName": "UI Issue",
                "summary": "Login problem",
                "personInChargeName": "Jane Smith",
                "statusName": "Open"
            }
        ]
        
        tickets2 = [
            {
                "ticketId": "TCK-002",
                "receptionDateTime": "2023-01-02T10:00:00",
                "accountName": "Company B",
                "requestorName": "Alice Brown",
                "categoryName": "Feature",
                "categoryDetailName": "Enhancement",
                "summary": "New feature request",
                "personInChargeName": "Bob Wilson",
                "statusName": "In Progress",
                "scheduledCompletionDate": "2023-01-15",
                "remainingDays": 10
            }
        ]
        
        result1 = tickets_to_md_table(tickets1)
        result2 = tickets_to_md_table(tickets2)
        
        # Extract headers (second line contains the table headers)
        lines1 = result1.split('\n')
        lines2 = result2.split('\n')
        
        # Find the header line (should contain pipe symbols and headers)
        header1 = None
        header2 = None
        for line in lines1:
            if "ID" in line and "Reception Date" in line:
                header1 = line
                break
        for line in lines2:
            if "ID" in line and "Reception Date" in line:
                header2 = line
                break
        
        # Headers should be identical regardless of data content
        self.assertEqual(header1, header2, "Column headers should be consistent")
    
    def test_empty_table_responses(self):
        """Test all empty data handlers return appropriate messages"""
        self.assertEqual(tickets_to_md_table([]), "No tickets found matching the criteria.")
        self.assertEqual(users_to_md_table([]), "No users registered.")
        self.assertEqual(accounts_to_md_table([]), "No accounts registered.")
        self.assertEqual(categories_to_md_table([]), "No categories registered.")
        self.assertEqual(category_details_to_md_table([]), "No category details registered.")
        self.assertEqual(statuses_to_md_table([]), "No statuses registered.")
        self.assertEqual(request_channels_to_md_table([]), "No request channels registered.")


if __name__ == '__main__':
    unittest.main()