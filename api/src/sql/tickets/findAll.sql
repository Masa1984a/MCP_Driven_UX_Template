/* @name findAll */
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
WHERE 
  (CASE WHEN :personInChargeId::VARCHAR IS NOT NULL THEN t.person_in_charge_id = :personInChargeId ELSE TRUE END)
  AND (CASE WHEN :accountId::VARCHAR IS NOT NULL THEN t.account_id = :accountId ELSE TRUE END)
  AND (CASE WHEN :statusId::VARCHAR IS NOT NULL THEN t.status_id = :statusId ELSE TRUE END)
  AND (CASE WHEN :scheduledCompletionDateFrom::DATE IS NOT NULL THEN t.scheduled_completion_date >= :scheduledCompletionDateFrom ELSE TRUE END)
  AND (CASE WHEN :scheduledCompletionDateTo::DATE IS NOT NULL THEN t.scheduled_completion_date <= :scheduledCompletionDateTo ELSE TRUE END)
  AND (CASE WHEN :showCompleted::BOOLEAN = FALSE THEN t.status_id != 'stat4' ELSE TRUE END)
  AND (CASE WHEN :searchQuery::VARCHAR IS NOT NULL THEN 
        (t.summary ILIKE '%' || :searchQuery || '%' 
        OR t.account_name ILIKE '%' || :searchQuery || '%' 
        OR t.requestor_name ILIKE '%' || :searchQuery || '%') 
      ELSE TRUE END)
ORDER BY
  CASE WHEN :sortOrder::VARCHAR = 'asc' THEN
    CASE :sortBy::VARCHAR
      WHEN 'receptionDateTime' THEN t.reception_date_time::TEXT
      WHEN 'scheduledCompletionDate' THEN t.scheduled_completion_date::TEXT
      WHEN 'completionDate' THEN t.completion_date::TEXT
      ELSE COALESCE(nullif(:sortBy, '')::TEXT, 'reception_date_time')
    END
  END ASC,
  CASE WHEN :sortOrder::VARCHAR = 'desc' OR :sortOrder IS NULL THEN
    CASE :sortBy::VARCHAR
      WHEN 'receptionDateTime' THEN t.reception_date_time::TEXT
      WHEN 'scheduledCompletionDate' THEN t.scheduled_completion_date::TEXT
      WHEN 'completionDate' THEN t.completion_date::TEXT
      ELSE COALESCE(nullif(:sortBy, '')::TEXT, 'reception_date_time')
    END
  END DESC
LIMIT :limit OFFSET :offset;