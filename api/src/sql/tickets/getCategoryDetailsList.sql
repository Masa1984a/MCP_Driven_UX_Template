/* @name GetCategoryDetailsList */
/* Query to get category details, optionally filtered by category ID */
/* @param categoryId - (optional) Filter by category ID */
SELECT id, name, category_id, category_name, order_no
FROM mcp_ux.category_details
WHERE (:categoryId::varchar IS NULL OR category_id = :categoryId)
ORDER BY order_no ASC, name ASC;