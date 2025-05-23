/* @name UpdateTicket */
/* @param ticketId - The ticket ID to update */
/* @param requestorId - (optional) Requestor user ID */
/* @param requestorName - (optional) Requestor name */
/* @param accountId - (optional) Account ID */
/* @param accountName - (optional) Account name */
/* @param categoryId - (optional) Category ID */
/* @param categoryName - (optional) Category name */
/* @param categoryDetailId - (optional) Category detail ID */
/* @param categoryDetailName - (optional) Category detail name */
/* @param requestChannelId - (optional) Request channel ID */
/* @param requestChannelName - (optional) Request channel name */
/* @param summary - (optional) Ticket summary */
/* @param description - (optional) Ticket description */
/* @param personInChargeId - (optional) Person in charge user ID */
/* @param personInChargeName - (optional) Person in charge name */
/* @param statusId - (optional) Status ID */
/* @param statusName - (optional) Status name */
/* @param scheduledCompletionDate - (optional) Scheduled completion date */
/* @param completionDate - (optional) Completion date */
/* @param actualEffortHours - (optional) Actual effort hours */
/* @param responseCategoryId - (optional) Response category ID */
/* @param responseCategoryName - (optional) Response category name */
/* @param responseDetails - (optional) Response details */
/* @param hasDefect - (optional) Has defect flag */
/* @param externalTicketId - (optional) External ticket ID */
/* @param remarks - (optional) Remarks */
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
WHERE id = :ticketId!
RETURNING id;