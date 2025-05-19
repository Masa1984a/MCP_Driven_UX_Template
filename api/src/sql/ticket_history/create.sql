/* @name createHistory */
INSERT INTO mcp_ux.ticket_history(
  ticket_id, user_id, user_name, comment
) VALUES (
  :ticketId, :userId, :userName, :comment
) RETURNING id;