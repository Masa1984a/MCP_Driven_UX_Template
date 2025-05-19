/* @name findHistoryByTicketId */
SELECT h.id, h.timestamp, h.user_id, h.user_name, h.comment
FROM mcp_ux.ticket_history h
WHERE h.ticket_id = :ticketId
ORDER BY h.timestamp DESC;