import { Request, Response } from 'express';
import { logger } from '../utils/logger';
import { TicketQueryParams } from '../types';

/**
 * Get ticket list with filtering and pagination
 */
export const getTicketList = async (req: Request, res: Response) => {
  try {
    // Get query parameters
    const queryParams: TicketQueryParams = {
      personInChargeId: req.query.personInChargeId as string,
      accountId: req.query.accountId as string,
      statusId: req.query.statusId as string,
      scheduledCompletionDateFrom: req.query.scheduledCompletionDateFrom as string,
      scheduledCompletionDateTo: req.query.scheduledCompletionDateTo as string,
      showCompleted: req.query.showCompleted === 'true',
      searchQuery: req.query.searchQuery as string,
      sortBy: req.query.sortBy as string || 'reception_date_time',
      sortOrder: (req.query.sortOrder as 'asc' | 'desc') || 'desc',
      limit: parseInt(req.query.limit as string) || 20,
      offset: parseInt(req.query.offset as string) || 0
    };

    // Field mapping (camelCase query params to snake_case DB fields)
    const fieldMapping: Record<string, string> = {
      'receptionDateTime': 'reception_date_time',
      'scheduledCompletionDate': 'scheduled_completion_date',
      'completionDate': 'completion_date'
    };
    
    // Convert sortBy if needed
    const sortBy = fieldMapping[queryParams.sortBy as string] || queryParams.sortBy;

    // Build the base query
    let query = `
      SELECT t.id as ticket_id, t.reception_date_time, t.requestor_name, 
             t.account_name, t.category_name, t.category_detail_name,
             t.summary, t.person_in_charge_name, t.status_name,
             t.scheduled_completion_date, t.external_ticket_id
      FROM mcp_ux.tickets t
      WHERE 1=1
    `;
    
    const params: any[] = [];
    
    // Add filters
    if (queryParams.personInChargeId) {
      query += " AND t.person_in_charge_id = $" + (params.length + 1);
      params.push(queryParams.personInChargeId);
    }
      
    if (queryParams.accountId) {
      query += " AND t.account_id = $" + (params.length + 1);
      params.push(queryParams.accountId);
    }
      
    if (queryParams.statusId) {
      query += " AND t.status_id = $" + (params.length + 1);
      params.push(queryParams.statusId);
    }
      
    if (queryParams.scheduledCompletionDateFrom) {
      query += " AND t.scheduled_completion_date >= $" + (params.length + 1);
      params.push(queryParams.scheduledCompletionDateFrom);
    }
      
    if (queryParams.scheduledCompletionDateTo) {
      query += " AND t.scheduled_completion_date <= $" + (params.length + 1);
      params.push(queryParams.scheduledCompletionDateTo);
    }
      
    if (!queryParams.showCompleted) {
      query += " AND t.status_id != 'stat4'";  // Assuming 'stat4' is the ID for completed status
    }
    
    // Add search query filter
    if (queryParams.searchQuery) {
      query += " AND (t.summary ILIKE $" + (params.length + 1) + 
               " OR t.account_name ILIKE $" + (params.length + 1) + 
               " OR t.requestor_name ILIKE $" + (params.length + 1) + ")";
      params.push(`%${queryParams.searchQuery}%`);
    }
    
    // Add sorting
    query += ` ORDER BY ${sortBy} ${queryParams.sortOrder}`;
    
    // Add pagination
    query += " LIMIT $" + (params.length + 1) + " OFFSET $" + (params.length + 2);
    params.push(queryParams.limit, queryParams.offset);
    
    // Execute the query
    const client = await req.db.connect();
    try {
      const result = await client.query(query, params);
      
      // Process results to match expected format
      const tickets = result.rows.map(row => {
        // Calculate remaining days for scheduled completion
        let remainingDays = null;
        if (row.scheduled_completion_date) {
          const scheduledDate = new Date(row.scheduled_completion_date);
          const today = new Date();
          remainingDays = Math.floor((scheduledDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
        }
        
        // Format dates
        const receptionDate = row.reception_date_time ? new Date(row.reception_date_time) : null;
        const receptionDateStr = receptionDate ? 
          `${receptionDate.getFullYear()}-${String(receptionDate.getMonth() + 1).padStart(2, '0')}-${String(receptionDate.getDate()).padStart(2, '0')} ` +
          `${String(receptionDate.getHours()).padStart(2, '0')}:${String(receptionDate.getMinutes()).padStart(2, '0')}` : null;
        
        const scheduledDate = row.scheduled_completion_date ? new Date(row.scheduled_completion_date) : null;
        const scheduledDateStr = scheduledDate ? 
          `${scheduledDate.getFullYear()}-${String(scheduledDate.getMonth() + 1).padStart(2, '0')}-${String(scheduledDate.getDate()).padStart(2, '0')}` : null;
        
        return {
          ticketId: row.ticket_id,
          receptionDateTime: receptionDateStr,
          requestorName: row.requestor_name,
          accountName: row.account_name,
          categoryName: row.category_name,
          categoryDetailName: row.category_detail_name,
          summary: row.summary,
          personInChargeName: row.person_in_charge_name,
          statusName: row.status_name,
          scheduledCompletionDate: scheduledDateStr,
          remainingDays,
          externalTicketId: row.external_ticket_id
        };
      });
      
      res.json(tickets);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting ticket list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving tickets' });
  }
};