/* @name getNextTicketId */
SELECT nextval('mcp_ux.ticket_id_seq');

/* @name getNamesForIds */
SELECT 
  (SELECT name FROM mcp_ux.users WHERE id = :requestorId) as requestor_name,
  (SELECT name FROM mcp_ux.accounts WHERE id = :accountId) as account_name,
  (SELECT name FROM mcp_ux.categories WHERE id = :categoryId) as category_name,
  (SELECT name FROM mcp_ux.category_details WHERE id = :categoryDetailId) as category_detail_name,
  (SELECT name FROM mcp_ux.request_channels WHERE id = :requestChannelId) as request_channel_name,
  (SELECT name FROM mcp_ux.users WHERE id = :personInChargeId) as person_in_charge_name,
  (SELECT name FROM mcp_ux.statuses WHERE id = :statusId) as status_name,
  (SELECT name FROM mcp_ux.response_categories WHERE id = :responseCategoryId) as response_category_name;

/* @name insertTicket */
INSERT INTO mcp_ux.tickets(
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details,
  has_defect, external_ticket_id, remarks
) VALUES (
  :id, 
  :receptionDateTime, 
  :requestorId, 
  :requestorName, 
  :accountId, 
  :accountName,
  :categoryId, 
  :categoryName, 
  :categoryDetailId, 
  :categoryDetailName,
  :requestChannelId, 
  :requestChannelName, 
  :summary, 
  :description,
  :personInChargeId, 
  :personInChargeName, 
  :statusId, 
  :statusName,
  :scheduledCompletionDate, 
  :completionDate, 
  :actualEffortHours,
  :responseCategoryId, 
  :responseCategoryName, 
  :responseDetails,
  :hasDefect, 
  :externalTicketId, 
  :remarks
) RETURNING id;