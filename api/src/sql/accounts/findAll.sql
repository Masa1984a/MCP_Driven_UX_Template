/* @name findAllAccounts */
SELECT id, name, order_no
FROM mcp_ux.accounts
ORDER BY order_no ASC, name ASC;