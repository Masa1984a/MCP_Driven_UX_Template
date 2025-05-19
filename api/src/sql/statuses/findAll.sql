/* @name findAllStatuses */
SELECT id, name, order_no
FROM mcp_ux.statuses
ORDER BY order_no ASC, name ASC;