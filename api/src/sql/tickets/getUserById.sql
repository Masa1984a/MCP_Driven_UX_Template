/* @name GetUserById */
/* Query to get user by ID */
/* @param userId - User ID */
SELECT name 
FROM mcp_ux.users 
WHERE id = :userId!;