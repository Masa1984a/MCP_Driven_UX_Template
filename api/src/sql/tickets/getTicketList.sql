/* @name GetTicketList */
/* Query to get ticket list with filters */
/* @param personInChargeId - (optional) Filter by person in charge ID */
/* @param accountId - (optional) Filter by account ID */
/* @param statusId - (optional) Filter by status ID */
/* @param scheduledCompletionDateFrom - (optional) Filter by scheduled completion date from */
/* @param scheduledCompletionDateTo - (optional) Filter by scheduled completion date to */
/* @param showCompleted - (optional) Show completed tickets (default: false) */
/* @param searchQuery - (optional) Search in summary, account name, or requestor name */
/* @param sortBy - Sort field (default: reception_date_time) */
/* @param limit - Number of records to return (default: 20) */
/* @param offset - Number of records to skip (default: 0) */
SELECT 
  t.id as ticket_id, 
  t.reception_date_time, 
  t.requestor_name, 
  t.account_name, 
  t.category_name, 
  t.category_detail_name,
  t.summary, 
  t.person_in_charge_name, 
  t.status_name,
  t.scheduled_completion_date, 
  t.external_ticket_id
FROM mcp_ux.tickets t
WHERE 1=1
  AND (:personInChargeId::text IS NULL OR t.person_in_charge_id = :personInChargeId)
  AND (:accountId::text IS NULL OR t.account_id = :accountId)
  AND (:statusId::text IS NULL OR t.status_id = :statusId)
  AND (:scheduledCompletionDateFrom::date IS NULL OR t.scheduled_completion_date >= :scheduledCompletionDateFrom)
  AND (:scheduledCompletionDateTo::date IS NULL OR t.scheduled_completion_date <= :scheduledCompletionDateTo)
  AND (:showCompleted::boolean IS TRUE OR t.status_id != 'stat4')
  AND (:searchQuery::text IS NULL OR (
    t.summary ILIKE '%' || :searchQuery || '%' 
    OR t.account_name ILIKE '%' || :searchQuery || '%' 
    OR t.requestor_name ILIKE '%' || :searchQuery || '%'
  ))
ORDER BY 
  CASE 
    WHEN :sortBy = 'reception_date_time' THEN t.reception_date_time
    WHEN :sortBy = 'scheduled_completion_date' THEN t.scheduled_completion_date
    WHEN :sortBy = 'completion_date' THEN t.completion_date
    ELSE t.reception_date_time
  END DESC
LIMIT :limit!
OFFSET :offset!;