import { Request, Response } from 'express';
import { logger } from '../utils/logger';
import { ChangedField, TicketQueryParams } from '../types';
import { 
  getTickets, 
  getTicketById,
  createTicket,
  updateTicketById 
} from '../repos/ticketRepo';
import {
  getAttachmentsByTicketId,
  addAttachment
} from '../repos/attachmentRepo';
import {
  getTicketHistory as getTicketHistoryRepo,
  addHistoryEntry
} from '../repos/historyRepo';
import {
  getUsers,
  getAccounts,
  getCategories,
  getCategoryDetails,
  getStatuses,
  getRequestChannels,
  getResponseCategories
} from '../repos/masterDataRepo';

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

    const tickets = await getTickets(queryParams, req.db);
    res.json(tickets);
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
    
    // Get ticket details
    const ticket = await getTicketById(ticketId, req.db);
    
    if (!ticket) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    // Get attachments
    const attachments = await getAttachmentsByTicketId(ticketId, req.db);
    ticket.attachments = attachments;
    
    res.json(ticket);
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
  try {
    // Extract data from request body
    const ticketData = req.body;
    
    // Create the ticket
    const ticketId = await createTicket(ticketData, req.db);
    
    // Add initial history entry
    await addHistoryEntry(
      ticketId,
      ticketData.personInChargeId,
      ticketData.personInChargeName || '', // This will be populated by the repo
      'Create New Ticket.',
      [],
      req.db
    );
    
    res.status(201).json({ 
      id: ticketId,
      message: 'Ticket created successfully' 
    });
  } catch (error) {
    logger.error('Error creating ticket', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while creating the ticket' });
  }
};

/**
 * Update an existing ticket
 */
export const updateTicket = async (req: Request, res: Response) => {
  try {
    const ticketId = req.params.id;
    
    // Extract data from request body
    const updates = req.body;
    const { updatedById, comment } = updates;
    
    // Verify ticket exists by getting the original values
    const originalTicket = await getTicketById(ticketId, req.db);
    
    if (!originalTicket) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    // Update the ticket
    await updateTicketById(ticketId, updates, req.db);
    
    // Check for changed fields
    const changedFields: ChangedField[] = [];
    
    // Helper function to check for changes
    const checkAndAddChange = (fieldName: string, oldValue: any, newValue: any, displayFieldName?: string) => {
      if (newValue !== undefined && newValue !== null && oldValue !== newValue) {
        changedFields.push({
          fieldName: displayFieldName || fieldName,
          oldValue: oldValue === null ? null : String(oldValue),
          newValue: newValue === null ? null : String(newValue)
        });
      }
    };
    
    // Get updated ticket to compare changes
    const updatedTicket = await getTicketById(ticketId, req.db);
    
    if (updatedTicket) {
      // Check each field for changes
      checkAndAddChange('requestor', originalTicket.requestorName, updatedTicket.requestorName);
      checkAndAddChange('account', originalTicket.accountName, updatedTicket.accountName);
      checkAndAddChange('category', originalTicket.categoryName, updatedTicket.categoryName);
      checkAndAddChange('category_detail', originalTicket.categoryDetailName, updatedTicket.categoryDetailName);
      checkAndAddChange('request_channel', originalTicket.requestChannelName, updatedTicket.requestChannelName);
      checkAndAddChange('summary', originalTicket.summary, updatedTicket.summary);
      checkAndAddChange('description', originalTicket.description, updatedTicket.description);
      checkAndAddChange('person_in_charge', originalTicket.personInChargeName, updatedTicket.personInChargeName);
      checkAndAddChange('status', originalTicket.statusName, updatedTicket.statusName);
      checkAndAddChange('scheduled_completion_date', originalTicket.scheduledCompletionDate, updatedTicket.scheduledCompletionDate);
      checkAndAddChange('completion_date', originalTicket.completionDate, updatedTicket.completionDate);
      checkAndAddChange('actual_effort_hours', originalTicket.actualEffortHours, updatedTicket.actualEffortHours);
      checkAndAddChange('response_category', originalTicket.responseCategoryName, updatedTicket.responseCategoryName);
      checkAndAddChange('response_details', originalTicket.responseDetails, updatedTicket.responseDetails);
      checkAndAddChange('has_defect', originalTicket.hasDefect, updatedTicket.hasDefect);
      checkAndAddChange('external_ticket_id', originalTicket.externalTicketId, updatedTicket.externalTicketId);
      checkAndAddChange('remarks', originalTicket.remarks, updatedTicket.remarks);
    }
    
    // Add history entry with changed fields
    if (updatedById) {
      await addHistoryEntry(
        ticketId,
        updatedById,
        '', // Will be populated by repo
        comment || 'Ticket was updated.',
        changedFields,
        req.db
      );
    }
    
    res.json({ 
      id: ticketId,
      message: 'Ticket updated successfully' 
    });
  } catch (error) {
    logger.error('Error updating ticket', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while updating the ticket' });
  }
};

/**
 * Add history entry to a ticket
 */
export const addTicketHistory = async (req: Request, res: Response) => {
  try {
    const ticketId = req.params.id;
    
    // Check if ticket exists
    const ticket = await getTicketById(ticketId, req.db);
    
    if (!ticket) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    const { userId, comment } = req.body;
    
    if (!userId || !comment) {
      return res.status(400).json({ error: 'User ID and comment are required' });
    }
    
    // Add history entry
    const historyId = await addHistoryEntry(
      ticketId,
      userId,
      '', // Will be populated by repo
      comment,
      [], // No changed fields
      req.db
    );
    
    res.status(201).json({ 
      id: historyId,
      message: 'History entry added successfully' 
    });
  } catch (error) {
    logger.error('Error adding ticket history', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while adding history entry' });
  }
};

/**
 * Get ticket history
 */
export const getTicketHistory = async (req: Request, res: Response) => {
  try {
    const ticketId = req.params.id;
    
    const history = await getTicketHistoryRepo(ticketId, req.db);
    res.json(history);
  } catch (error) {
    logger.error('Error getting ticket history', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving ticket history' });
  }
};

/**
 * Get users list
 * Note: User table is handled by existing implementation per requirements
 */
export const getUsersList = async (req: Request, res: Response) => {
  try {
    const users = await getUsers(req.db);
    res.json(users);
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
    const accounts = await getAccounts(req.db);
    res.json(accounts);
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
    const categories = await getCategories(req.db);
    res.json(categories);
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
    const categoryId = req.query.categoryId as string || null;
    
    const categoryDetails = await getCategoryDetails(categoryId, req.db);
    res.json(categoryDetails);
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
    const statuses = await getStatuses(req.db);
    res.json(statuses);
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
    const channels = await getRequestChannels(req.db);
    res.json(channels);
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
    const responseCategories = await getResponseCategories(req.db);
    res.json(responseCategories);
  } catch (error) {
    logger.error('Error getting response categories list', { 
      error: error instanceof Error ? error.message : String(error) 
    });
    res.status(500).json({ error: 'An error occurred while retrieving response categories' });
  }
};