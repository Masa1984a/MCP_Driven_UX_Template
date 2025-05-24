/* @name GetResponseCategoriesList */
/* Query to get all response categories */
SELECT id, name, parent_category, order_no
FROM mcp_ux.response_categories
ORDER BY order_no ASC, name ASC;