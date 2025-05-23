/* @name GetHistoryChangedFields */
/* @param historyId - History entry ID */
SELECT field_name, old_value, new_value
FROM mcp_ux.history_changed_fields
WHERE history_id = :historyId!;