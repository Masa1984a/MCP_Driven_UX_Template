/* @name CreateTicket */
/* @param ticketId - The ticket ID (e.g., TCK-0001) */
/* @param receptionDateTime - Reception date and time */
/* @param requestorId - Requestor user ID */
/* @param requestorName - Requestor name */
/* @param accountId - Account ID */
/* @param accountName - Account name */
/* @param categoryId - Category ID */
/* @param categoryName - Category name */
/* @param categoryDetailId - Category detail ID */
/* @param categoryDetailName - Category detail name */
/* @param requestChannelId - Request channel ID */
/* @param requestChannelName - Request channel name */
/* @param summary - Ticket summary */
/* @param description - Ticket description */
/* @param personInChargeId - Person in charge user ID */
/* @param personInChargeName - Person in charge name */
/* @param statusId - Status ID */
/* @param statusName - Status name */
/* @param scheduledCompletionDate - (optional) Scheduled completion date */
/* @param completionDate - (optional) Completion date */
/* @param actualEffortHours - (optional) Actual effort hours */
/* @param responseCategoryId - (optional) Response category ID */
/* @param responseCategoryName - (optional) Response category name */
/* @param responseDetails - (optional) Response details */
/* @param hasDefect - Has defect flag (default: false) */
/* @param externalTicketId - (optional) External ticket ID */
/* @param remarks - (optional) Remarks */
INSERT INTO mcp_ux.tickets(
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details,
  has_defect, external_ticket_id, remarks
) VALUES (
  :ticketId!, :receptionDateTime!, :requestorId!, :requestorName!, :accountId!, :accountName!,
  :categoryId!, :categoryName!, :categoryDetailId!, :categoryDetailName!,
  :requestChannelId!, :requestChannelName!, :summary!, :description!,
  :personInChargeId!, :personInChargeName!, :statusId!, :statusName!,
  :scheduledCompletionDate, :completionDate, :actualEffortHours,
  :responseCategoryId, :responseCategoryName, :responseDetails,
  :hasDefect!, :externalTicketId, :remarks
) RETURNING id;