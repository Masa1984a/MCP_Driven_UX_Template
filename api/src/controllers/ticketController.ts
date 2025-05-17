import { Request, Response } from 'express';
import { logger } from '../utils/logger';
import { TicketQueryParams, ChangedField } from '../types';

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

/**
 * Get ticket detail by ID
 */
export const getTicketDetail = async (req: Request, res: Response) => {
  try {
    const ticketId = req.params.id;

    // Execute the query
    const client = await req.db.connect();
    try {
      const query = `
        SELECT t.*
        FROM mcp_ux.tickets t
        WHERE t.id = $1
      `;
      
      const result = await client.query(query, [ticketId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Ticket not found' });
      }
      
      // Format the ticket data
      const row = result.rows[0];
      
      // Format dates
      const receptionDate = row.reception_date_time ? new Date(row.reception_date_time) : null;
      const receptionDateStr = receptionDate ? 
        `${receptionDate.getFullYear()}-${String(receptionDate.getMonth() + 1).padStart(2, '0')}-${String(receptionDate.getDate()).padStart(2, '0')} ` +
        `${String(receptionDate.getHours()).padStart(2, '0')}:${String(receptionDate.getMinutes()).padStart(2, '0')}` : null;
      
      const scheduledDate = row.scheduled_completion_date ? new Date(row.scheduled_completion_date) : null;
      const scheduledDateStr = scheduledDate ? 
        `${scheduledDate.getFullYear()}-${String(scheduledDate.getMonth() + 1).padStart(2, '0')}-${String(scheduledDate.getDate()).padStart(2, '0')}` : null;
      
      const completionDate = row.completion_date ? new Date(row.completion_date) : null;
      const completionDateStr = completionDate ? 
        `${completionDate.getFullYear()}-${String(completionDate.getMonth() + 1).padStart(2, '0')}-${String(completionDate.getDate()).padStart(2, '0')}` : null;
      
      // Get attachments
      const attachmentsQuery = `
        SELECT id, file_name, file_url, uploaded_at
        FROM mcp_ux.attachments
        WHERE ticket_id = $1
        ORDER BY uploaded_at DESC
      `;
      
      const attachmentsResult = await client.query(attachmentsQuery, [ticketId]);
      
      const attachments = attachmentsResult.rows.map(attachment => ({
        id: attachment.id,
        fileName: attachment.file_name,
        fileUrl: attachment.file_url,
        uploadedAt: attachment.uploaded_at
      }));
      
      const ticket = {
        id: row.id,
        receptionDateTime: receptionDateStr,
        requestorId: row.requestor_id,
        requestorName: row.requestor_name,
        accountId: row.account_id,
        accountName: row.account_name,
        categoryId: row.category_id,
        categoryName: row.category_name,
        categoryDetailId: row.category_detail_id,
        categoryDetailName: row.category_detail_name,
        requestChannelId: row.request_channel_id,
        requestChannelName: row.request_channel_name,
        summary: row.summary,
        description: row.description,
        personInChargeId: row.person_in_charge_id,
        personInChargeName: row.person_in_charge_name,
        statusId: row.status_id,
        statusName: row.status_name,
        scheduledCompletionDate: scheduledDateStr,
        completionDate: completionDateStr,
        actualEffortHours: row.actual_effort_hours,
        responseCategoryId: row.response_category_id,
        responseCategoryName: row.response_category_name,
        responseDetails: row.response_details,
        hasDefect: row.has_defect,
        externalTicketId: row.external_ticket_id,
        remarks: row.remarks,
        attachments
      };
      
      res.json(ticket);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting ticket detail', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving ticket details' });
  }
};

/**
 * Create a new ticket
 */
export const createTicket = async (req: Request, res: Response) => {
  const client = await req.db.connect();
  try {
    await client.query('BEGIN');
    
    // Get the next ticket ID sequence
    const seqResult = await client.query('SELECT nextval(\'mcp_ux.ticket_id_seq\')');
    const seqValue = seqResult.rows[0].nextval;
    
    // Format the ticket ID as TCK-XXXX with leading zeros
    const ticketId = `TCK-${String(seqValue).padStart(4, '0')}`;
    
    // Extract data from request body
    const {
      receptionDateTime,
      requestorId,
      accountId,
      categoryId,
      categoryDetailId,
      requestChannelId,
      summary,
      description,
      personInChargeId,
      statusId,
      scheduledCompletionDate,
      completionDate,
      actualEffortHours,
      responseCategoryId,
      responseDetails,
      hasDefect,
      externalTicketId,
      remarks
    } = req.body;
    
    // Get the names for the IDs from their respective tables
    const namesQuery = `
      SELECT 
        (SELECT name FROM mcp_ux.users WHERE id = $1) as requestor_name,
        (SELECT name FROM mcp_ux.accounts WHERE id = $2) as account_name,
        (SELECT name FROM mcp_ux.categories WHERE id = $3) as category_name,
        (SELECT name FROM mcp_ux.category_details WHERE id = $4) as category_detail_name,
        (SELECT name FROM mcp_ux.request_channels WHERE id = $5) as request_channel_name,
        (SELECT name FROM mcp_ux.users WHERE id = $6) as person_in_charge_name,
        (SELECT name FROM mcp_ux.statuses WHERE id = $7) as status_name,
        (SELECT name FROM mcp_ux.response_categories WHERE id = $8) as response_category_name
    `;
    
    const namesResult = await client.query(namesQuery, [
      requestorId, 
      accountId, 
      categoryId, 
      categoryDetailId, 
      requestChannelId, 
      personInChargeId, 
      statusId,
      responseCategoryId || null
    ]);
    
    if (!namesResult.rows[0].requestor_name || 
        !namesResult.rows[0].account_name || 
        !namesResult.rows[0].category_name || 
        !namesResult.rows[0].category_detail_name || 
        !namesResult.rows[0].request_channel_name || 
        !namesResult.rows[0].person_in_charge_name || 
        !namesResult.rows[0].status_name) {
      throw new Error('One or more referenced entities do not exist');
    }
    
    const {
      requestor_name,
      account_name,
      category_name,
      category_detail_name,
      request_channel_name,
      person_in_charge_name,
      status_name,
      response_category_name
    } = namesResult.rows[0];
    
    // Insert new ticket
    const insertQuery = `
      INSERT INTO mcp_ux.tickets(
        id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
        category_id, category_name, category_detail_id, category_detail_name,
        request_channel_id, request_channel_name, summary, description,
        person_in_charge_id, person_in_charge_name, status_id, status_name,
        scheduled_completion_date, completion_date, actual_effort_hours,
        response_category_id, response_category_name, response_details,
        has_defect, external_ticket_id, remarks
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 
        $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
      ) RETURNING id
    `;
    
    const insertResult = await client.query(insertQuery, [
      ticketId,
      receptionDateTime || new Date(),
      requestorId,
      requestor_name,
      accountId,
      account_name,
      categoryId,
      category_name,
      categoryDetailId,
      category_detail_name,
      requestChannelId,
      request_channel_name,
      summary,
      description,
      personInChargeId,
      person_in_charge_name,
      statusId,
      status_name,
      scheduledCompletionDate,
      completionDate,
      actualEffortHours,
      responseCategoryId,
      response_category_name,
      responseDetails,
      hasDefect || false,
      externalTicketId,
      remarks
    ]);
    
    // Add initial history entry
    const historyQuery = `
      INSERT INTO mcp_ux.ticket_history(
        ticket_id, user_id, user_name, comment
      ) VALUES (
        $1, $2, $3, $4
      )
    `;
    
    await client.query(historyQuery, [
      ticketId, 
      personInChargeId, 
      person_in_charge_name, 
      '新規チケット作成'
    ]);
    
    await client.query('COMMIT');
    
    res.status(201).json({ 
      id: ticketId,
      message: 'Ticket created successfully' 
    });
  } catch (error) {
    await client.query('ROLLBACK');
    logger.error('Error creating ticket', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while creating the ticket' });
  } finally {
    client.release();
  }
};

/**
 * Update an existing ticket
 */
export const updateTicket = async (req: Request, res: Response) => {
  const client = await req.db.connect();
  try {
    await client.query('BEGIN');
    
    const ticketId = req.params.id;
    
    // Check if ticket exists
    const checkQuery = 'SELECT * FROM mcp_ux.tickets WHERE id = $1';
    const checkResult = await client.query(checkQuery, [ticketId]);
    
    if (checkResult.rows.length === 0) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    const oldTicket = checkResult.rows[0];
    
    // Extract data from request body
    const {
      requestorId,
      accountId,
      categoryId,
      categoryDetailId,
      requestChannelId,
      summary,
      description,
      personInChargeId,
      statusId,
      scheduledCompletionDate,
      completionDate,
      actualEffortHours,
      responseCategoryId,
      responseDetails,
      hasDefect,
      externalTicketId,
      remarks,
      updatedById, // ID of the user making the update
      comment // Comment for the history entry
    } = req.body;
    
    // Get the names for the IDs from their respective tables
    const namesQuery = `
      SELECT 
        (SELECT name FROM mcp_ux.users WHERE id = $1) as requestor_name,
        (SELECT name FROM mcp_ux.accounts WHERE id = $2) as account_name,
        (SELECT name FROM mcp_ux.categories WHERE id = $3) as category_name,
        (SELECT name FROM mcp_ux.category_details WHERE id = $4) as category_detail_name,
        (SELECT name FROM mcp_ux.request_channels WHERE id = $5) as request_channel_name,
        (SELECT name FROM mcp_ux.users WHERE id = $6) as person_in_charge_name,
        (SELECT name FROM mcp_ux.statuses WHERE id = $7) as status_name,
        (SELECT name FROM mcp_ux.response_categories WHERE id = $8) as response_category_name,
        (SELECT name FROM mcp_ux.users WHERE id = $9) as updated_by_name
    `;
    
    const namesResult = await client.query(namesQuery, [
      requestorId || oldTicket.requestor_id, 
      accountId || oldTicket.account_id, 
      categoryId || oldTicket.category_id, 
      categoryDetailId || oldTicket.category_detail_id, 
      requestChannelId || oldTicket.request_channel_id, 
      personInChargeId || oldTicket.person_in_charge_id, 
      statusId || oldTicket.status_id,
      responseCategoryId || oldTicket.response_category_id,
      updatedById
    ]);
    
    const {
      requestor_name,
      account_name,
      category_name,
      category_detail_name,
      request_channel_name,
      person_in_charge_name,
      status_name,
      response_category_name,
      updated_by_name
    } = namesResult.rows[0];
    
    // Update ticket
    const updateQuery = `
      UPDATE mcp_ux.tickets SET
        requestor_id = COALESCE($1, requestor_id),
        requestor_name = COALESCE($2, requestor_name),
        account_id = COALESCE($3, account_id),
        account_name = COALESCE($4, account_name),
        category_id = COALESCE($5, category_id),
        category_name = COALESCE($6, category_name),
        category_detail_id = COALESCE($7, category_detail_id),
        category_detail_name = COALESCE($8, category_detail_name),
        request_channel_id = COALESCE($9, request_channel_id),
        request_channel_name = COALESCE($10, request_channel_name),
        summary = COALESCE($11, summary),
        description = COALESCE($12, description),
        person_in_charge_id = COALESCE($13, person_in_charge_id),
        person_in_charge_name = COALESCE($14, person_in_charge_name),
        status_id = COALESCE($15, status_id),
        status_name = COALESCE($16, status_name),
        scheduled_completion_date = COALESCE($17, scheduled_completion_date),
        completion_date = COALESCE($18, completion_date),
        actual_effort_hours = COALESCE($19, actual_effort_hours),
        response_category_id = COALESCE($20, response_category_id),
        response_category_name = COALESCE($21, response_category_name),
        response_details = COALESCE($22, response_details),
        has_defect = COALESCE($23, has_defect),
        external_ticket_id = COALESCE($24, external_ticket_id),
        remarks = COALESCE($25, remarks),
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $26
      RETURNING id
    `;
    
    await client.query(updateQuery, [
      requestorId,
      requestorId ? requestor_name : null,
      accountId,
      accountId ? account_name : null,
      categoryId,
      categoryId ? category_name : null,
      categoryDetailId,
      categoryDetailId ? category_detail_name : null,
      requestChannelId,
      requestChannelId ? request_channel_name : null,
      summary,
      description,
      personInChargeId,
      personInChargeId ? person_in_charge_name : null,
      statusId,
      statusId ? status_name : null,
      scheduledCompletionDate,
      completionDate,
      actualEffortHours,
      responseCategoryId,
      responseCategoryId ? response_category_name : null,
      responseDetails,
      hasDefect,
      externalTicketId,
      remarks,
      ticketId
    ]);
    
    // Add history entry
    const historyQuery = `
      INSERT INTO mcp_ux.ticket_history(
        ticket_id, user_id, user_name, comment
      ) VALUES (
        $1, $2, $3, $4
      ) RETURNING id
    `;
    
    const historyResult = await client.query(historyQuery, [
      ticketId, 
      updatedById, 
      updated_by_name, 
      comment || 'チケットを更新しました'
    ]);
    
    const historyId = historyResult.rows[0].id;
    
    // Track changed fields
    const changedFields: ChangedField[] = [];
    
    // Helper function to check for changes
    const checkAndAddChange = (fieldName: string, oldValue: any, newValue: any, displayFieldName?: string) => {
      if (newValue !== undefined && newValue !== null && oldValue !== newValue) {
        changedFields.push({
          fieldName: displayFieldName || fieldName,
          oldValue: oldValue,
          newValue: newValue
        });
      }
    };
    
    // Check each field for changes
    checkAndAddChange('requestor_id', oldTicket.requestor_name, requestorId ? requestor_name : null, 'requestor');
    checkAndAddChange('account_id', oldTicket.account_name, accountId ? account_name : null, 'account');
    checkAndAddChange('category_id', oldTicket.category_name, categoryId ? category_name : null, 'category');
    checkAndAddChange('category_detail_id', oldTicket.category_detail_name, categoryDetailId ? category_detail_name : null, 'category_detail');
    checkAndAddChange('request_channel_id', oldTicket.request_channel_name, requestChannelId ? request_channel_name : null, 'request_channel');
    checkAndAddChange('summary', oldTicket.summary, summary);
    checkAndAddChange('description', oldTicket.description, description);
    checkAndAddChange('person_in_charge_id', oldTicket.person_in_charge_name, personInChargeId ? person_in_charge_name : null, 'person_in_charge');
    checkAndAddChange('status_id', oldTicket.status_name, statusId ? status_name : null, 'status');
    checkAndAddChange('scheduled_completion_date', oldTicket.scheduled_completion_date, scheduledCompletionDate);
    checkAndAddChange('completion_date', oldTicket.completion_date, completionDate);
    checkAndAddChange('actual_effort_hours', oldTicket.actual_effort_hours, actualEffortHours);
    checkAndAddChange('response_category_id', oldTicket.response_category_name, responseCategoryId ? response_category_name : null, 'response_category');
    checkAndAddChange('response_details', oldTicket.response_details, responseDetails);
    checkAndAddChange('has_defect', oldTicket.has_defect, hasDefect);
    checkAndAddChange('external_ticket_id', oldTicket.external_ticket_id, externalTicketId);
    checkAndAddChange('remarks', oldTicket.remarks, remarks);
    
    // Record changed fields
    if (changedFields.length > 0) {
      // Generate SQL for inserting changed fields
      const fieldsValues = changedFields.map((field, index) => {
        return `($1, $${index * 3 + 2}, $${index * 3 + 3}, $${index * 3 + 4})`;
      }).join(', ');
      
      const fieldsParams = changedFields.flatMap(field => [
        field.fieldName,
        field.oldValue === null ? null : String(field.oldValue),
        field.newValue === null ? null : String(field.newValue)
      ]);
      
      const changedFieldsQuery = `
        INSERT INTO mcp_ux.history_changed_fields(
          history_id, field_name, old_value, new_value
        ) VALUES ${fieldsValues}
      `;
      
      await client.query(changedFieldsQuery, [historyId, ...fieldsParams]);
    }
    
    await client.query('COMMIT');
    
    res.json({ 
      id: ticketId,
      message: 'Ticket updated successfully' 
    });
  } catch (error) {
    await client.query('ROLLBACK');
    logger.error('Error updating ticket', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while updating the ticket' });
  } finally {
    client.release();
  }
};

/**
 * Add history entry to a ticket
 */
export const addTicketHistory = async (req: Request, res: Response) => {
  const client = await req.db.connect();
  try {
    const ticketId = req.params.id;
    
    // Check if ticket exists
    const checkQuery = 'SELECT id FROM mcp_ux.tickets WHERE id = $1';
    const checkResult = await client.query(checkQuery, [ticketId]);
    
    if (checkResult.rows.length === 0) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    const { userId, comment } = req.body;
    
    if (!userId || !comment) {
      return res.status(400).json({ error: 'User ID and comment are required' });
    }
    
    // Get user name
    const userQuery = 'SELECT name FROM mcp_ux.users WHERE id = $1';
    const userResult = await client.query(userQuery, [userId]);
    
    if (userResult.rows.length === 0) {
      return res.status(400).json({ error: 'User not found' });
    }
    
    const userName = userResult.rows[0].name;
    
    // Add history entry
    const historyQuery = `
      INSERT INTO mcp_ux.ticket_history(
        ticket_id, user_id, user_name, comment
      ) VALUES (
        $1, $2, $3, $4
      ) RETURNING id
    `;
    
    const historyResult = await client.query(historyQuery, [
      ticketId, 
      userId, 
      userName, 
      comment
    ]);
    
    res.status(201).json({ 
      id: historyResult.rows[0].id,
      message: 'History entry added successfully' 
    });
  } catch (error) {
    logger.error('Error adding ticket history', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while adding history entry' });
  } finally {
    client.release();
  }
};

/**
 * Get ticket history
 */
export const getTicketHistory = async (req: Request, res: Response) => {
  try {
    const ticketId = req.params.id;
    
    const client = await req.db.connect();
    try {
      // Get history entries
      const historyQuery = `
        SELECT h.id, h.timestamp, h.user_id, h.user_name, h.comment
        FROM mcp_ux.ticket_history h
        WHERE h.ticket_id = $1
        ORDER BY h.timestamp DESC
      `;
      
      const historyResult = await client.query(historyQuery, [ticketId]);
      
      // Get changed fields for each history entry
      const history = await Promise.all(historyResult.rows.map(async (entry) => {
        const changedFieldsQuery = `
          SELECT field_name, old_value, new_value
          FROM mcp_ux.history_changed_fields
          WHERE history_id = $1
        `;
        
        const changedFieldsResult = await client.query(changedFieldsQuery, [entry.id]);
        
        return {
          id: entry.id,
          timestamp: entry.timestamp,
          userId: entry.user_id,
          userName: entry.user_name,
          comment: entry.comment,
          changedFields: changedFieldsResult.rows.map(field => ({
            fieldName: field.field_name,
            oldValue: field.old_value,
            newValue: field.new_value
          }))
        };
      }));
      
      res.json(history);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting ticket history', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving ticket history' });
  }
};

/**
 * Get users list
 */
export const getUsersList = async (req: Request, res: Response) => {
  try {
    const client = await req.db.connect();
    try {
      const query = `
        SELECT id, name, email, role
        FROM mcp_ux.users
        ORDER BY name ASC
      `;
      
      const result = await client.query(query);
      
      const users = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        email: row.email,
        role: row.role
      }));
      
      res.json(users);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting users list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving users' });
  }
};

/**
 * Get accounts list
 */
export const getAccountsList = async (req: Request, res: Response) => {
  try {
    const client = await req.db.connect();
    try {
      const query = `
        SELECT id, name, order_no
        FROM mcp_ux.accounts
        ORDER BY order_no ASC, name ASC
      `;
      
      const result = await client.query(query);
      
      const accounts = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        orderNo: row.order_no
      }));
      
      res.json(accounts);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting accounts list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving accounts' });
  }
};

/**
 * Get categories list
 */
export const getCategoriesList = async (req: Request, res: Response) => {
  try {
    const client = await req.db.connect();
    try {
      const query = `
        SELECT id, name, order_no
        FROM mcp_ux.categories
        ORDER BY order_no ASC, name ASC
      `;
      
      const result = await client.query(query);
      
      const categories = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        orderNo: row.order_no
      }));
      
      res.json(categories);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting categories list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving categories' });
  }
};

/**
 * Get category details list
 */
export const getCategoryDetailsList = async (req: Request, res: Response) => {
  try {
    const categoryId = req.query.categoryId as string;
    
    const client = await req.db.connect();
    try {
      let query = `
        SELECT id, name, category_id, category_name, order_no
        FROM mcp_ux.category_details
      `;
      
      const params: any[] = [];
      
      if (categoryId) {
        query += ' WHERE category_id = $1';
        params.push(categoryId);
      }
      
      query += ' ORDER BY order_no ASC, name ASC';
      
      const result = await client.query(query, params);
      
      const categoryDetails = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        categoryId: row.category_id,
        categoryName: row.category_name,
        orderNo: row.order_no
      }));
      
      res.json(categoryDetails);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting category details list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving category details' });
  }
};

/**
 * Get statuses list
 */
export const getStatusesList = async (req: Request, res: Response) => {
  try {
    const client = await req.db.connect();
    try {
      const query = `
        SELECT id, name, order_no
        FROM mcp_ux.statuses
        ORDER BY order_no ASC, name ASC
      `;
      
      const result = await client.query(query);
      
      const statuses = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        orderNo: row.order_no
      }));
      
      res.json(statuses);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting statuses list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving statuses' });
  }
};

/**
 * Get request channels list
 */
export const getRequestChannelsList = async (req: Request, res: Response) => {
  try {
    const client = await req.db.connect();
    try {
      const query = `
        SELECT id, name, order_no
        FROM mcp_ux.request_channels
        ORDER BY order_no ASC, name ASC
      `;
      
      const result = await client.query(query);
      
      const channels = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        orderNo: row.order_no
      }));
      
      res.json(channels);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting request channels list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving request channels' });
  }
};

/**
 * Get response categories list
 */
export const getResponseCategoriesList = async (req: Request, res: Response) => {
  try {
    const client = await req.db.connect();
    try {
      const query = `
        SELECT id, name, parent_category, order_no
        FROM mcp_ux.response_categories
        ORDER BY order_no ASC, name ASC
      `;
      
      const result = await client.query(query);
      
      const responseCategories = result.rows.map(row => ({
        id: row.id,
        name: row.name,
        parentCategory: row.parent_category,
        orderNo: row.order_no
      }));
      
      res.json(responseCategories);
    } finally {
      client.release();
    }
  } catch (error) {
    logger.error('Error getting response categories list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving response categories' });
  }
};