/* @name findAllCategories */
SELECT id, name, order_no
FROM mcp_ux.categories
ORDER BY order_no ASC, name ASC;