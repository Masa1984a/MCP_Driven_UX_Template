/* @name findAllCategoryDetails */
SELECT id, name, category_id, category_name, order_no
FROM mcp_ux.category_details
WHERE 
  CASE WHEN :categoryId::VARCHAR IS NOT NULL 
    THEN category_id = :categoryId 
    ELSE TRUE 
  END
ORDER BY order_no ASC, name ASC;