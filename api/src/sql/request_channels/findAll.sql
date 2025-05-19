/* @name findAllRequestChannels */
SELECT id, name, order_no
FROM mcp_ux.request_channels
ORDER BY order_no ASC, name ASC;