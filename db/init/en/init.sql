-- PostgreSQL database initialization script

-- Create schema
CREATE SCHEMA IF NOT EXISTS mcp_ux;

-- All following tables will be created in mcp_ux schema
SET search_path TO mcp_ux;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  role VARCHAR(50) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Category details table
CREATE TABLE IF NOT EXISTS category_details (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category_id VARCHAR(50) NOT NULL REFERENCES categories(id),
  category_name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Status table
CREATE TABLE IF NOT EXISTS statuses (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Request channels table
CREATE TABLE IF NOT EXISTS request_channels (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Response categories table
CREATE TABLE IF NOT EXISTS response_categories (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  parent_category VARCHAR(100),
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sequence for ticket numbering
CREATE SEQUENCE IF NOT EXISTS ticket_id_seq START 1;

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
  id VARCHAR(50) PRIMARY KEY,  -- Format is "TCK-XXXX"
  reception_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
  requestor_id VARCHAR(50) NOT NULL REFERENCES users(id),
  requestor_name VARCHAR(100) NOT NULL,  -- Denormalized
  account_id VARCHAR(50) NOT NULL REFERENCES accounts(id),
  account_name VARCHAR(100) NOT NULL,  -- Denormalized
  category_id VARCHAR(50) NOT NULL REFERENCES categories(id),
  category_name VARCHAR(100) NOT NULL,  -- Denormalized
  category_detail_id VARCHAR(50) NOT NULL REFERENCES category_details(id),
  category_detail_name VARCHAR(200) NOT NULL,  -- Denormalized
  request_channel_id VARCHAR(50) NOT NULL REFERENCES request_channels(id),
  request_channel_name VARCHAR(50) NOT NULL,  -- Denormalized
  summary VARCHAR(200) NOT NULL,
  description TEXT,
  person_in_charge_id VARCHAR(50) NOT NULL REFERENCES users(id),
  person_in_charge_name VARCHAR(100) NOT NULL,  -- Denormalized
  status_id VARCHAR(50) NOT NULL REFERENCES statuses(id),
  status_name VARCHAR(50) NOT NULL,  -- Denormalized
  scheduled_completion_date DATE,
  completion_date DATE,
  actual_effort_hours NUMERIC(5,1),
  response_category_id VARCHAR(50) REFERENCES response_categories(id),
  response_category_name VARCHAR(100),  -- Denormalized
  response_details TEXT,
  has_defect BOOLEAN DEFAULT FALSE,
  external_ticket_id VARCHAR(50),
  remarks TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Attachments table
CREATE TABLE IF NOT EXISTS attachments (
  id SERIAL PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL REFERENCES tickets(id),
  file_name VARCHAR(255) NOT NULL,
  file_url VARCHAR(1000) NOT NULL,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ticket history table (change history of tickets)
CREATE TABLE IF NOT EXISTS ticket_history (
  id SERIAL PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL REFERENCES tickets(id),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  user_id VARCHAR(50) REFERENCES users(id),
  user_name VARCHAR(100) NOT NULL,  -- Denormalized
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Changed fields history table (child table of ticket history)
CREATE TABLE IF NOT EXISTS history_changed_fields (
  id SERIAL PRIMARY KEY,
  history_id INTEGER NOT NULL REFERENCES ticket_history(id),
  field_name VARCHAR(100) NOT NULL,
  old_value TEXT,
  new_value TEXT
);

-- Sample data - Users
INSERT INTO users (id, name, email, role) VALUES
  ('user1', 'John Smith', 'john.smith@example.com', 'Agent'),
  ('user2', 'Emily Johnson', 'emily.johnson@example.com', 'Agent'),
  ('user3', 'Michael Brown', 'michael.brown@example.com', 'Requester'),
  ('user4', 'Sarah Wilson', 'sarah.wilson@example.com', 'Requester'),
  ('user5', 'David Thompson', 'david.thompson@example.com', 'Manager'),
  ('user6', 'Jennifer Davis', 'jennifer.davis@example.com', 'Agent'),
  ('user7', 'Robert Garcia', 'robert.garcia@example.com', 'Requester'),
  ('user8', 'Maria Martinez', 'maria.martinez@example.com', 'Requester');

-- Sample data - Accounts
INSERT INTO accounts (id, name, order_no) VALUES
  ('acc1', 'ABC Corporation', 1),
  ('acc2', 'XYZ Corporation', 2),
  ('acc3', '123 Corporation', 3),
  ('acc4', 'Global Tech Inc', 4),
  ('acc5', 'Innovation Labs', 5);

-- Sample data - Categories
INSERT INTO categories (id, name, order_no) VALUES
  ('cat1', 'Inquiry', 1),
  ('cat2', 'Data Correction Request', 2),
  ('cat3', 'Incident Report', 3),
  ('cat4', 'UX Improvement Request', 4),
  ('cat5', 'Feature Request', 5);

-- Sample data - Category details
INSERT INTO category_details (id, name, category_id, category_name, order_no) VALUES
  ('catd1', 'Portal, Article, and Search Function Inquiries', 'cat1', 'Inquiry', 1),
  ('catd2', 'Support Management Inquiries', 'cat1', 'Inquiry', 2),
  ('catd3', 'Master Data Correction Request', 'cat2', 'Data Correction Request', 1),
  ('catd4', 'System Incident', 'cat3', 'Incident Report', 1),
  ('catd5', 'UI/UX Improvement Proposal', 'cat4', 'UX Improvement Request', 1),
  ('catd6', 'Search Function Enhancement Proposal', 'cat4', 'UX Improvement Request', 2),
  ('catd7', 'New Feature Development', 'cat5', 'Feature Request', 1),
  ('catd8', 'Integration Request', 'cat5', 'Feature Request', 2);

-- Sample data - Statuses
INSERT INTO statuses (id, name, order_no) VALUES
  ('stat1', 'Received', 1),
  ('stat2', 'In Progress', 2),
  ('stat3', 'Verifying', 3),
  ('stat4', 'Completed', 4);

-- Sample data - Request channels
INSERT INTO request_channels (id, name, order_no) VALUES
  ('ch1', 'Email', 1),
  ('ch2', 'Phone', 2),
  ('ch3', 'Teams', 3),
  ('ch4', 'Chat/LLM', 4),
  ('ch5', 'Web Form', 5);

-- Sample data - Response categories
INSERT INTO response_categories (id, name, parent_category, order_no) VALUES
  ('resp1', 'Can be answered from Japan', 'Inquiry', 1),
  ('resp2', 'Free Support', 'Data Correction Request', 1),
  ('resp3', 'Development Modification', 'Incident Report', 1),
  ('resp4', 'Design Review Required', 'UX Improvement Request', 1),
  ('resp5', 'Implementation Scheduled', 'Feature Request', 1);

-- Sample data - Ticket 1
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id
) VALUES (
  'TCK-0001',
  NOW() - INTERVAL '5 days',
  'user3', 'Michael Brown',
  'acc1', 'ABC Corporation',
  'cat1', 'Inquiry',
  'catd1', 'Portal, Article, and Search Function Inquiries',
  'ch1', 'Email',
  'Search function not working properly',
  'When entering specific keywords in the search box, no results are displayed.Steps to reproduce:1. Enter search terms containing "special characters" in the search box on the top page2. Click the search button3. "No search results" is displayed',
  'user1', 'John Smith',
  'stat2', 'In Progress',
  CURRENT_DATE + INTERVAL '2 days',
  FALSE,
  'EXT-123'
);

-- Ticket 1 attachments
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0001', 'error_screenshot.png', 'https://example.com/storage/error_screenshot.png', NOW() - INTERVAL '5 days');

-- Ticket 1 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0001', NOW() - INTERVAL '5 days', 'user1', 'John Smith', 'New ticket created');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0001', NOW() - INTERVAL '3 days', 'user1', 'John Smith', 'Investigation started. There may be an issue with special character escaping.');

-- Ticket 1 history changed fields
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (2, 'status', 'Received', 'In Progress');

-- Sample data - Ticket 2
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details, has_defect
) VALUES (
  'TCK-0002',
  NOW() - INTERVAL '10 days',
  'user4', 'Sarah Wilson',
  'acc2', 'XYZ Corporation',
  'cat2', 'Data Correction Request',
  'catd3', 'Master Data Correction Request',
  'ch2', 'Phone',
  'User master information update request',
  'Our company contact person has changed. Please update as follows:Old contact: Robert JohnsonNew contact: David ThompsonEmail: david.thompson@xyz.co.jpPhone: 03-1234-5678',
  'user2', 'Emily Johnson',
  'stat4', 'Completed',
  CURRENT_DATE - INTERVAL '8 days',
  CURRENT_DATE - INTERVAL '9 days',
  1.5,
  'resp2', 'Free Support',
  'Master data update has been completed.Please verify the changes.',
  FALSE
);

-- Ticket 2 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0002', NOW() - INTERVAL '10 days', 'user2', 'Emily Johnson', 'New ticket created');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0002', NOW() - INTERVAL '9 days', 'user2', 'Emily Johnson', 'Master data update completed. Confirmation email sent to customer.');

-- Ticket 2 history changed fields
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (4, 'status', 'Received', 'Completed');

-- Sample ticket 3
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id, remarks
) VALUES (
  'TCK-0003',
  NOW() - INTERVAL '1 day',
  'user3', 'Michael Brown',
  'acc1', 'ABC Corporation',
  'cat3', 'Incident Report',
  'catd4', 'System Incident',
  'ch3', 'Teams',
  'Dashboard not displaying',
  'Since this morning, an error is displayed when accessing the dashboard.Error message: "Failed to load data"Multiple users are experiencing the same issue.',
  'user1', 'John Smith',
  'stat1', 'Received',
  CURRENT_DATE + INTERVAL '1 day',
  TRUE,
  'INC-456',
  'Urgent attention required.'
);

-- Ticket 3 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0003', NOW() - INTERVAL '1 day', 'user1', 'John Smith', 'New ticket created');

-- Sample data - Ticket 4 (Search related issue)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id
) VALUES (
  'TCK-0004',
  NOW() - INTERVAL '2 days',
  'user7', 'Robert Garcia',
  'acc4', 'Global Tech Inc',
  'cat1', 'Inquiry',
  'catd1', 'Portal, Article, and Search Function Inquiries',
  'ch4', 'Chat/LLM',
  'Full-text search not returning some results',
  'When using the full-text search function, articles that should contain specific keywords are not appearing in results.Reproduction steps:1. Enter "operation manual" in the search box2. Click the search button3. Articles containing "operation manual" are not displayed in the search results',
  'user6', 'Jennifer Davis',
  'stat2', 'In Progress',
  CURRENT_DATE + INTERVAL '5 days',
  TRUE,
  'BUG-789'
);

-- Ticket 4 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0004', NOW() - INTERVAL '2 days', 'user6', 'Jennifer Davis', 'New ticket created');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0004', NOW() - INTERVAL '1 day', 'user6', 'Jennifer Davis', 'Investigation started. Found indexing issue with special characters.');

-- Ticket 4 history changed fields
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (6, 'status', 'Received', 'In Progress');

-- Sample data - Ticket 5 (UX improvement)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0005',
  NOW() - INTERVAL '7 days',
  'user8', 'Maria Martinez',
  'acc5', 'Innovation Labs',
  'cat4', 'UX Improvement Request',
  'catd6', 'Search Function Enhancement Proposal',
  'ch1', 'Email',
  'Want to customize search result sorting',
  'Search results are currently displayed in date order, but we would like to be able to sort by relevance, category, etc.We have received feedback from users that "it is difficult to find what they are looking for".',
  'user1', 'John Smith',
  'stat3', 'Verifying',
  CURRENT_DATE + INTERVAL '14 days',
  FALSE
);

-- Ticket 5 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '7 days', 'user1', 'John Smith', 'New ticket created');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '5 days', 'user1', 'John Smith', 'Proposal reviewed. Preparing mockups for new sorting options.');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '2 days', 'user1', 'John Smith', 'Mockups sent to requester for review.');

-- Ticket 5 history changed fields
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (8, 'status', 'Received', 'In Progress');

INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (9, 'status', 'In Progress', 'Verifying');

-- Sample data - Ticket 6 (Performance issue)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id, remarks
) VALUES (
  'TCK-0006',
  NOW() - INTERVAL '3 days',
  'user3', 'Michael Brown',
  'acc1', 'ABC Corporation',
  'cat3', 'Incident Report',
  'catd4', 'System Incident',
  'ch3', 'Teams',
  'Search function performance degradation',
  'Since last week\'s update, the search function response time has significantly decreased.Especially when returning a large number of search results, it can take more than 10 seconds.APM tool logs are attached.',
  'user2', 'Emily Johnson',
  'stat2', 'In Progress',
  CURRENT_DATE + INTERVAL '1 day',
  TRUE,
  'PERF-456',
  'High priority - affecting multiple users'
);

-- Ticket 6 attachments
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0006', 'apm_logs.txt', 'https://example.com/storage/apm_logs.txt', NOW() - INTERVAL '3 days'),
  ('TCK-0006', 'performance_metrics.pdf', 'https://example.com/storage/performance_metrics.pdf', NOW() - INTERVAL '3 days');

-- Ticket 6 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0006', NOW() - INTERVAL '3 days', 'user2', 'Emily Johnson', 'New ticket created');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0006', NOW() - INTERVAL '2 days', 'user2', 'Emily Johnson', 'Performance analysis started. Identified database query optimization needed.');

-- Ticket 6 history changed fields
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (12, 'status', 'Received', 'In Progress');

-- Sample data - Ticket 7 (Feature request)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details, has_defect
) VALUES (
  'TCK-0007',
  NOW() - INTERVAL '15 days',
  'user4', 'Sarah Wilson',
  'acc2', 'XYZ Corporation',
  'cat5', 'Feature Request',
  'catd7', 'New Feature Development',
  'ch5', 'Web Form',
  'Advanced search filters implementation',
  'We would like to have advanced search capabilities with filters for:- Date ranges- Document types- Tags/Categories- Author- Status This would greatly improve our ability to find specific documents quickly.',
  'user1', 'John Smith',
  'stat4', 'Completed',
  CURRENT_DATE - INTERVAL '10 days',
  CURRENT_DATE - INTERVAL '2 days',
  24.5,
  'resp5', 'Implementation Scheduled',
  'Advanced search filters have been implemented and deployed to production. Users can now filter search results by multiple criteria.',
  FALSE
);

-- Ticket 7 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '15 days', 'user1', 'John Smith', 'New ticket created');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '12 days', 'user1', 'John Smith', 'Development started. Created UI mockups and backend API design.');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '2 days', 'user1', 'John Smith', 'Feature completed and deployed to production.');

-- Ticket 7 history changed fields
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (14, 'status', 'Received', 'In Progress');

INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (15, 'status', 'In Progress', 'Completed');

-- Sample data - Ticket 8 (Integration request)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0008',
  NOW() - INTERVAL '4 days',
  'user7', 'Robert Garcia',
  'acc4', 'Global Tech Inc',
  'cat5', 'Feature Request',
  'catd8', 'Integration Request',
  'ch2', 'Phone',
  'API integration with Slack for notifications',
  'We would like to integrate the ticket system with Slack to receive real-time notifications when:- New tickets are created- Tickets are assigned to team members- Status changes occur- Comments are added This would improve our response time significantly.',
  'user6', 'Jennifer Davis',
  'stat1', 'Received',
  CURRENT_DATE + INTERVAL '21 days',
  FALSE
);

-- Ticket 8 history
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0008', NOW() - INTERVAL '4 days', 'user6', 'Jennifer Davis', 'New ticket created');

-- Update sequence value for next ticket ID
SELECT setval('ticket_id_seq', 8, true);
