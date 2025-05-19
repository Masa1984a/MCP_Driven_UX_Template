/* @name createAttachment */
INSERT INTO mcp_ux.attachments(
  ticket_id, file_name, file_url, uploaded_by_id, uploaded_by_name
)
VALUES (
  :ticketId, :fileName, :fileUrl, :uploadedById, :uploadedByName
)
RETURNING id;