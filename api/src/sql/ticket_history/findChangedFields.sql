/* @name findChangedFieldsByHistoryId */
SELECT field_name, old_value, new_value
FROM mcp_ux.history_changed_fields
WHERE history_id = :historyId;