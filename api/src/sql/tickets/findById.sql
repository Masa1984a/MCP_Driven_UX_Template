/* @name findById */
SELECT t.*
FROM mcp_ux.tickets t
WHERE t.id = :id;