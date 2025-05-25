import { Request, Response } from 'express';
import { logger } from '../utils/logger';
import { TicketQueryParams, ChangedField } from '../types';
import { getTicketById } from '../sql/tickets/getTicketById.queries';
import { getTicketAttachments, IGetTicketAttachmentsResult } from '../sql/tickets/getTicketAttachments.queries';
import { getTicketList as getTicketListQuery } from '../sql/tickets/getTicketList.queries';
import { getNextTicketSequence } from '../sql/tickets/getNextTicketSequence.queries';
import { getNamesForIds } from '../sql/tickets/getNamesForIds.queries';
import { createTicket as createTicketQuery } from '../sql/tickets/createTicket.queries';
import { createTicketHistory } from '../sql/tickets/createTicketHistory.queries';
import { checkTicketExists } from '../sql/tickets/checkTicketExists.queries';
import { getNamesForUpdate } from '../sql/tickets/getNamesForUpdate.queries';
import { updateTicket as updateTicketQuery } from '../sql/tickets/updateTicket.queries';
import { createHistoryChangedFields } from '../sql/tickets/createHistoryChangedFields.queries';
import { getHistoryChangedFields } from '../sql/tickets/getHistoryChangedFields.queries';
import { getTicketHistory as getTicketHistoryQuery, IGetTicketHistoryResult } from '../sql/tickets/getTicketHistory.queries';
import { getUserById } from '../sql/tickets/getUserById.queries';
import { getUsersList as getUsersListQuery } from '../sql/tickets/getUsersList.queries';
import { getAccountsList as getAccountsListQuery } from '../sql/tickets/getAccountsList.queries';
import { getCategoriesList as getCategoriesListQuery } from '../sql/tickets/getCategoriesList.queries';
import { getCategoryDetailsList as getCategoryDetailsListQuery } from '../sql/tickets/getCategoryDetailsList.queries';
import { getStatusesList as getStatusesListQuery } from '../sql/tickets/getStatusesList.queries';
import { getRequestChannelsList as getRequestChannelsListQuery } from '../sql/tickets/getRequestChannelsList.queries';
import { getResponseCategoriesList as getResponseCategoriesListQuery } from '../sql/tickets/getResponseCategoriesList.queries';

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

    // Execute the query using PgTyped
    const client = await req.db.connect();
    try {
      const result = await getTicketListQuery.run({
        personInChargeId: queryParams.personInChargeId || null,
        accountId: queryParams.accountId || null,
        statusId: queryParams.statusId || null,
        scheduledCompletionDateFrom: queryParams.scheduledCompletionDateFrom || null,
        scheduledCompletionDateTo: queryParams.scheduledCompletionDateTo || null,
        showCompleted: queryParams.showCompleted,
        searchQuery: queryParams.searchQuery || null,
        sortBy: sortBy,
        limit: queryParams.limit ? queryParams.limit.toString() : '20',
        offset: queryParams.offset ? queryParams.offset.toString() : '0'
      }, client);
      
      // Process results to match expected format
      const tickets = result.map(row => {
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
      // PgTyped implementation
      const ticketResult = await getTicketById.run({ ticketId }, client);
      
      if (ticketResult.length === 0) {
        return res.status(404).json({ error: 'Ticket not found' });
      }
      
      const row = ticketResult[0];
      
      // Get attachments using PgTyped
      const attachmentsResult = await getTicketAttachments.run({ ticketId }, client);
      
      // Format dates (common for both implementations)
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
      
      const attachments = attachmentsResult.map((attachment: IGetTicketAttachmentsResult) => ({
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
    const seqResult = await getNextTicketSequence.run(undefined, client);
    const seqValue = seqResult[0].seq_value;
    
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
    const namesResult = await getNamesForIds.run({
      requestorId,
      accountId,
      categoryId,
      categoryDetailId,
      requestChannelId,
      personInChargeId,
      statusId,
      responseCategoryId: responseCategoryId || null
    }, client);
    
    if (!namesResult[0].requestor_name || 
        !namesResult[0].account_name || 
        !namesResult[0].category_name || 
        !namesResult[0].category_detail_name || 
        !namesResult[0].request_channel_name || 
        !namesResult[0].person_in_charge_name || 
        !namesResult[0].status_name) {
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
    } = namesResult[0];
    
    // Insert new ticket
    await createTicketQuery.run({
      ticketId,
      receptionDateTime: receptionDateTime || new Date(),
      requestorId,
      requestorName: requestor_name,
      accountId,
      accountName: account_name,
      categoryId,
      categoryName: category_name,
      categoryDetailId,
      categoryDetailName: category_detail_name,
      requestChannelId,
      requestChannelName: request_channel_name,
      summary,
      description,
      personInChargeId,
      personInChargeName: person_in_charge_name,
      statusId,
      statusName: status_name,
      scheduledCompletionDate,
      completionDate,
      actualEffortHours,
      responseCategoryId,
      responseCategoryName: response_category_name,
      responseDetails,
      hasDefect: hasDefect || false,
      externalTicketId,
      remarks
    }, client);
    
    // Add initial history entry
    await createTicketHistory.run({
      ticketId,
      userId: personInChargeId,
      userName: person_in_charge_name,
      comment: 'Create New Ticket.'
    }, client);
    
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
    const checkResult = await checkTicketExists.run({ ticketId }, client);
    
    if (checkResult.length === 0) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    const oldTicket = checkResult[0];
    
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
    const namesResult = await getNamesForUpdate.run({
      requestorId: requestorId || oldTicket.requestor_id,
      accountId: accountId || oldTicket.account_id,
      categoryId: categoryId || oldTicket.category_id,
      categoryDetailId: categoryDetailId || oldTicket.category_detail_id,
      requestChannelId: requestChannelId || oldTicket.request_channel_id,
      personInChargeId: personInChargeId || oldTicket.person_in_charge_id,
      statusId: statusId || oldTicket.status_id,
      responseCategoryId: responseCategoryId || oldTicket.response_category_id,
      updatedById
    }, client);
    
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
    } = namesResult[0];
    
    // Update ticket
    await updateTicketQuery.run({
      requestorId,
      requestorName: requestorId ? requestor_name : null,
      accountId,
      accountName: accountId ? account_name : null,
      categoryId,
      categoryName: categoryId ? category_name : null,
      categoryDetailId,
      categoryDetailName: categoryDetailId ? category_detail_name : null,
      requestChannelId,
      requestChannelName: requestChannelId ? request_channel_name : null,
      summary,
      description,
      personInChargeId,
      personInChargeName: personInChargeId ? person_in_charge_name : null,
      statusId,
      statusName: statusId ? status_name : null,
      scheduledCompletionDate,
      completionDate,
      actualEffortHours,
      responseCategoryId,
      responseCategoryName: responseCategoryId ? response_category_name : null,
      responseDetails,
      hasDefect,
      externalTicketId,
      remarks,
      ticketId
    }, client);
    
    // Add history entry
    const historyResult = await createTicketHistory.run({
      ticketId,
      userId: updatedById,
      userName: updated_by_name || 'Unknown User',
      comment: comment || 'Ticket was updated.'
    }, client);
    
    const historyId = historyResult[0].id;
    
    // Track changed fields
    const changedFields: ChangedField[] = [];
    
    // Helper function to check for changes
    const checkAndAddChange = (fieldName: string, oldValue: unknown, newValue: unknown, displayFieldName?: string) => {
      if (newValue !== undefined && newValue !== null && oldValue !== newValue) {
        changedFields.push({
          fieldName: displayFieldName || fieldName,
          oldValue: String(oldValue ?? ''),
          newValue: String(newValue)
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
      for (const field of changedFields) {
        await createHistoryChangedFields.run({
          historyId,
          fieldName: field.fieldName,
          oldValue: field.oldValue === null ? null : String(field.oldValue),
          newValue: field.newValue === null ? null : String(field.newValue)
        }, client);
      }
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
    const checkResult = await checkTicketExists.run({ ticketId }, client);
    
    if (checkResult.length === 0) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    const { userId, comment } = req.body;
    
    if (!userId || !comment) {
      return res.status(400).json({ error: 'User ID and comment are required' });
    }
    
    // Get user name
    const userResult = await getUserById.run({ userId }, client);
    
    if (userResult.length === 0) {
      return res.status(400).json({ error: 'User not found' });
    }
    
    const userName = userResult[0].name;
    
    // Add history entry
    const historyResult = await createTicketHistory.run({
      ticketId,
      userId,
      userName,
      comment
    }, client);
    
    res.status(201).json({ 
      id: historyResult[0].id,
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
      const historyResult = await getTicketHistoryQuery.run({ ticketId }, client);
      
      // Get changed fields for each history entry
      const history = await Promise.all(historyResult.map(async (entry: IGetTicketHistoryResult) => {
        const changedFieldsResult = await getHistoryChangedFields.run({ historyId: entry.id }, client);
        
        return {
          id: entry.id,
          timestamp: entry.timestamp,
          userId: entry.user_id,
          userName: entry.user_name,
          comment: entry.comment,
          changedFields: changedFieldsResult.map(field => ({
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
      const result = await getUsersListQuery.run(undefined, client);
      
      const users = result.map(row => ({
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
      const result = await getAccountsListQuery.run(undefined, client);
      
      const accounts = result.map(row => ({
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
      const result = await getCategoriesListQuery.run(undefined, client);
      
      const categories = result.map(row => ({
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
      const result = await getCategoryDetailsListQuery.run({
        categoryId: categoryId || null
      }, client);
      
      const categoryDetails = result.map(row => ({
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
      const result = await getStatusesListQuery.run(undefined, client);
      
      const statuses = result.map(row => ({
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
      const result = await getRequestChannelsListQuery.run(undefined, client);
      
      const channels = result.map(row => ({
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
      const result = await getResponseCategoriesListQuery.run(undefined, client);
      
      const responseCategories = result.map(row => ({
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