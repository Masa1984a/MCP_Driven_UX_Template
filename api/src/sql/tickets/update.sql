/* @name findTicketById */
SELECT * FROM mcp_ux.tickets WHERE id = :id;

/* @name getNamesForUpdate */
SELECT 
  (SELECT name FROM mcp_ux.users WHERE id = :requestorId) as requestor_name,
  (SELECT name FROM mcp_ux.accounts WHERE id = :accountId) as account_name,
  (SELECT name FROM mcp_ux.categories WHERE id = :categoryId) as category_name,
  (SELECT name FROM mcp_ux.category_details WHERE id = :categoryDetailId) as category_detail_name,
  (SELECT name FROM mcp_ux.request_channels WHERE id = :requestChannelId) as request_channel_name,
  (SELECT name FROM mcp_ux.users WHERE id = :personInChargeId) as person_in_charge_name,
  (SELECT name FROM mcp_ux.statuses WHERE id = :statusId) as status_name,
  (SELECT name FROM mcp_ux.response_categories WHERE id = :responseCategoryId) as response_category_name,
  (SELECT name FROM mcp_ux.users WHERE id = :updatedById) as updated_by_name;

/* @name updateTicket */
UPDATE mcp_ux.tickets SET
  requestor_id = COALESCE(:requestorId, requestor_id),
  requestor_name = COALESCE(:requestorName, requestor_name),
  account_id = COALESCE(:accountId, account_id),
  account_name = COALESCE(:accountName, account_name),
  category_id = COALESCE(:categoryId, category_id),
  category_name = COALESCE(:categoryName, category_name),
  category_detail_id = COALESCE(:categoryDetailId, category_detail_id),
  category_detail_name = COALESCE(:categoryDetailName, category_detail_name),
  request_channel_id = COALESCE(:requestChannelId, request_channel_id),
  request_channel_name = COALESCE(:requestChannelName, request_channel_name),
  summary = COALESCE(:summary, summary),
  description = COALESCE(:description, description),
  person_in_charge_id = COALESCE(:personInChargeId, person_in_charge_id),
  person_in_charge_name = COALESCE(:personInChargeName, person_in_charge_name),
  status_id = COALESCE(:statusId, status_id),
  status_name = COALESCE(:statusName, status_name),
  scheduled_completion_date = COALESCE(:scheduledCompletionDate, scheduled_completion_date),
  completion_date = COALESCE(:completionDate, completion_date),
  actual_effort_hours = COALESCE(:actualEffortHours, actual_effort_hours),
  response_category_id = COALESCE(:responseCategoryId, response_category_id),
  response_category_name = COALESCE(:responseCategoryName, response_category_name),
  response_details = COALESCE(:responseDetails, response_details),
  has_defect = COALESCE(:hasDefect, has_defect),
  external_ticket_id = COALESCE(:externalTicketId, external_ticket_id),
  remarks = COALESCE(:remarks, remarks),
  updated_at = CURRENT_TIMESTAMP
WHERE id = :id
RETURNING id;