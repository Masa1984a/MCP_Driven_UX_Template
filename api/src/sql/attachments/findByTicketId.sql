/* @name findByTicketId */
SELECT id, file_name, file_url, uploaded_at
FROM mcp_ux.attachments
WHERE ticket_id = :ticketId
ORDER BY uploaded_at DESC;