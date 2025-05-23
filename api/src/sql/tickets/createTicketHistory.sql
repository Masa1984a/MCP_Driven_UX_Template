/* @name CreateTicketHistory */
/* @param ticketId - The ticket ID */
/* @param userId - User ID who made the change */
/* @param userName - User name who made the change */
/* @param comment - History comment */
INSERT INTO mcp_ux.ticket_history(
  ticket_id, user_id, user_name, comment
) VALUES (
  :ticketId!, :userId!, :userName!, :comment!
) RETURNING id;