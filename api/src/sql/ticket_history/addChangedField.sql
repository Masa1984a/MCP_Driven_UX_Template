/* @name addChangedField */
INSERT INTO mcp_ux.history_changed_fields(
  history_id, field_name, old_value, new_value
) VALUES (
  :historyId, :fieldName, :oldValue, :newValue
);