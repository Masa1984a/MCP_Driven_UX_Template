import { Pool, PoolClient } from 'pg';
import { logger } from '../utils/logger';

/**
 * Execute a transaction with automatic commit/rollback
 */
export const executeTransaction = async <T>(
  pool: Pool, 
  callback: (client: PoolClient) => Promise<T>
): Promise<T> => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    logger.error('Transaction error', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    throw error;
  } finally {
    client.release();
  }
};

/**
 * Format a date as YYYY-MM-DD
 */
export const formatDate = (date: Date | string | null): string | null => {
  if (!date) return null;
  
  const d = typeof date === 'string' ? new Date(date) : date;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

/**
 * Format a datetime as YYYY-MM-DD HH:MM
 */
export const formatDateTime = (date: Date | string | null): string | null => {
  if (!date) return null;
  
  const d = typeof date === 'string' ? new Date(date) : date;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ` +
    `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

/**
 * Calculate remaining days between a date and today
 */
export const calculateRemainingDays = (date: Date | string | null): number | null => {
  if (!date) return null;
  
  const scheduledDate = typeof date === 'string' ? new Date(date) : date;
  const today = new Date();
  return Math.floor((scheduledDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
};