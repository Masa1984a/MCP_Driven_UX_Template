/* @name GetNamesForIds */
/* @param requestorId - Requestor user ID */
/* @param accountId - Account ID */
/* @param categoryId - Category ID */
/* @param categoryDetailId - Category detail ID */
/* @param requestChannelId - Request channel ID */
/* @param personInChargeId - Person in charge user ID */
/* @param statusId - Status ID */
/* @param responseCategoryId - (optional) Response category ID */
SELECT 
  (SELECT name FROM mcp_ux.users WHERE id = :requestorId!) as requestor_name,
  (SELECT name FROM mcp_ux.accounts WHERE id = :accountId!) as account_name,
  (SELECT name FROM mcp_ux.categories WHERE id = :categoryId!) as category_name,
  (SELECT name FROM mcp_ux.category_details WHERE id = :categoryDetailId!) as category_detail_name,
  (SELECT name FROM mcp_ux.request_channels WHERE id = :requestChannelId!) as request_channel_name,
  (SELECT name FROM mcp_ux.users WHERE id = :personInChargeId!) as person_in_charge_name,
  (SELECT name FROM mcp_ux.statuses WHERE id = :statusId!) as status_name,
  (SELECT name FROM mcp_ux.response_categories WHERE id = :responseCategoryId) as response_category_name;