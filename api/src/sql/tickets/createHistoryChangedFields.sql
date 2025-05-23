/* @name CreateHistoryChangedFields */
/* @param historyId - History entry ID */
/* @param fieldName - Field name that was changed */
/* @param oldValue - Old value (as string) */
/* @param newValue - New value (as string) */
INSERT INTO mcp_ux.history_changed_fields(
  history_id, field_name, old_value, new_value
) VALUES (
  :historyId!, :fieldName!, :oldValue, :newValue
);