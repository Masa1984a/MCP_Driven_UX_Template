import { Pool } from 'pg';
import { ChangedField, TicketHistoryEntry } from '../types';
import { executeTransaction } from './baseRepo';
// Import generated types - these will be generated when pgtyped runs
import { findHistoryByTicketId } from '../sql/ticket_history/findByTicketId.types';
import { createHistory } from '../sql/ticket_history/create.types';
import { findChangedFieldsByHistoryId } from '../sql/ticket_history/findChangedFields.types';
import { addChangedField } from '../sql/ticket_history/addChangedField.types';

/**
 * Get all history entries for a ticket
 */
export const getTicketHistory = async (ticketId: string, pool: Pool): Promise<TicketHistoryEntry[]> => {
  const client = await pool.connect();
  try {
    const historyResult = await findHistoryByTicketId.run({ ticketId }, client);
    
    const history = await Promise.all(historyResult.map(async (entry) => {
      const changedFieldsResult = await findChangedFieldsByHistoryId.run({ historyId: entry.id }, client);
      
      return {
        id: entry.id,
        timestamp: entry.timestamp,
        userId: entry.userId,
        userName: entry.userName,
        comment: entry.comment,
        changedFields: changedFieldsResult.map(field => ({
          fieldName: field.fieldName,
          oldValue: field.oldValue,
          newValue: field.newValue
        }))
      };
    }));
    
    return history;
  } finally {
    client.release();
  }
};

/**
 * Add a history entry to a ticket
 */
export const addHistoryEntry = async (
  ticketId: string,
  userId: string,
  userName: string,
  comment: string,
  changedFields: ChangedField[],
  pool: Pool
): Promise<number> => {
  return executeTransaction(pool, async (client) => {
    // Create the history entry
    const historyResult = await createHistory.run({
      ticketId,
      userId,
      userName,
      comment
    }, client);
    
    const historyId = historyResult[0].id;
    
    // Add changed fields
    for (const field of changedFields) {
      await addChangedField.run({
        historyId,
        fieldName: field.fieldName,
        oldValue: field.oldValue,
        newValue: field.newValue
      }, client);
    }
    
    return historyId;
  });
};