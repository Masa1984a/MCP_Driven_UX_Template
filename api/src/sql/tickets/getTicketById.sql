-- @name GetTicketById
-- @param ticketId - The ID of the ticket to retrieve
SELECT 
  t.id,
  t.reception_date_time,
  t.requestor_id,
  t.requestor_name,
  t.account_id,
  t.account_name,
  t.category_id,
  t.category_name,
  t.category_detail_id,
  t.category_detail_name,
  t.request_channel_id,
  t.request_channel_name,
  t.summary,
  t.description,
  t.person_in_charge_id,
  t.person_in_charge_name,
  t.status_id,
  t.status_name,
  t.scheduled_completion_date,
  t.completion_date,
  t.actual_effort_hours,
  t.response_category_id,
  t.response_category_name,
  t.response_details,
  t.has_defect,
  t.external_ticket_id,
  t.remarks
FROM mcp_ux.tickets t
WHERE t.id = :ticketId!