/* @name CheckTicketExists */
/* @param ticketId - The ticket ID to check */
SELECT * FROM mcp_ux.tickets WHERE id = :ticketId!;