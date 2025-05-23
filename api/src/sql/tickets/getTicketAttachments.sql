/* @name GetTicketAttachments */
/* @param ticketId - The ID of the ticket to get attachments for */
SELECT 
  id,
  file_name,
  file_url,
  uploaded_at
FROM mcp_ux.attachments
WHERE ticket_id = :ticketId!
ORDER BY uploaded_at DESC;