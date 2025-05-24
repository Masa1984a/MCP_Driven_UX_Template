/* @name GetUsersList */
/* Query to get all users */
SELECT id, name, email, role
FROM mcp_ux.users
ORDER BY name ASC;