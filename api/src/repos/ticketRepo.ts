import { Pool, PoolClient } from 'pg';
import { Ticket, TicketDetail, TicketQueryParams } from '../types';
import { calculateRemainingDays, executeTransaction, formatDate, formatDateTime } from './baseRepo';
// Import generated types - these will be generated when pgtyped runs
import { 
  findById, 
  findAll, 
  getNextTicketId, 
  getNamesForIds, 
  insertTicket,
  findTicketById,
  getNamesForUpdate,
  updateTicket
} from '../sql/tickets/findById.types';
import '../sql/tickets/findAll.types';
import '../sql/tickets/create.types';
import '../sql/tickets/update.types';

/**
 * Get a list of tickets with pagination and filtering
 */
export const getTickets = async (params: TicketQueryParams, pool: Pool): Promise<Ticket[]> => {
  const client = await pool.connect();
  try {
    const result = await findAll.run({
      personInChargeId: params.personInChargeId || null,
      accountId: params.accountId || null,
      statusId: params.statusId || null,
      scheduledCompletionDateFrom: params.scheduledCompletionDateFrom || null,
      scheduledCompletionDateTo: params.scheduledCompletionDateTo || null,
      showCompleted: params.showCompleted || false,
      searchQuery: params.searchQuery || null,
      sortBy: params.sortBy || 'reception_date_time',
      sortOrder: params.sortOrder || 'desc',
      limit: params.limit || 20,
      offset: params.offset || 0
    }, client);
    
    return result.map(row => {
      const remainingDays = calculateRemainingDays(row.scheduledCompletionDate);
      
      return {
        ticketId: row.ticketId,
        receptionDateTime: formatDateTime(row.receptionDateTime),
        requestorName: row.requestorName,
        accountName: row.accountName,
        categoryName: row.categoryName,
        categoryDetailName: row.categoryDetailName,
        summary: row.summary,
        personInChargeName: row.personInChargeName,
        statusName: row.statusName,
        scheduledCompletionDate: formatDate(row.scheduledCompletionDate),
        remainingDays,
        externalTicketId: row.externalTicketId
      };
    });
  } finally {
    client.release();
  }
};

/**
 * Get ticket detail by ID
 */
export const getTicketById = async (ticketId: string, pool: Pool): Promise<TicketDetail | null> => {
  const client = await pool.connect();
  try {
    const result = await findById.run({ id: ticketId }, client);
    
    if (result.length === 0) {
      return null;
    }
    
    const ticket = result[0];
    
    return {
      id: ticket.id,
      receptionDateTime: formatDateTime(ticket.receptionDateTime),
      requestorId: ticket.requestorId,
      requestorName: ticket.requestorName,
      accountId: ticket.accountId,
      accountName: ticket.accountName,
      categoryId: ticket.categoryId,
      categoryName: ticket.categoryName,
      categoryDetailId: ticket.categoryDetailId,
      categoryDetailName: ticket.categoryDetailName,
      requestChannelId: ticket.requestChannelId,
      requestChannelName: ticket.requestChannelName,
      summary: ticket.summary,
      description: ticket.description,
      personInChargeId: ticket.personInChargeId,
      personInChargeName: ticket.personInChargeName,
      statusId: ticket.statusId,
      statusName: ticket.statusName,
      scheduledCompletionDate: formatDate(ticket.scheduledCompletionDate),
      completionDate: formatDate(ticket.completionDate),
      actualEffortHours: ticket.actualEffortHours,
      responseCategoryId: ticket.responseCategoryId,
      responseCategoryName: ticket.responseCategoryName,
      responseDetails: ticket.responseDetails,
      hasDefect: ticket.hasDefect,
      externalTicketId: ticket.externalTicketId,
      remarks: ticket.remarks,
      attachments: [] // Will be populated by the controller
    };
  } finally {
    client.release();
  }
};

/**
 * Create a new ticket
 */
export const createTicket = async (ticketData: Omit<TicketDetail, 'id' | 'attachments'>, pool: Pool): Promise<string> => {
  return executeTransaction(pool, async (client) => {
    // Get the next ticket ID
    const seqResult = await getNextTicketId.run({}, client);
    const seqValue = seqResult[0].nextval;
    const ticketId = `TCK-${String(seqValue).padStart(4, '0')}`;
    
    // Get the names for all the IDs
    const namesResult = await getNamesForIds.run({
      requestorId: ticketData.requestorId,
      accountId: ticketData.accountId,
      categoryId: ticketData.categoryId,
      categoryDetailId: ticketData.categoryDetailId,
      requestChannelId: ticketData.requestChannelId,
      personInChargeId: ticketData.personInChargeId,
      statusId: ticketData.statusId,
      responseCategoryId: ticketData.responseCategoryId || null
    }, client);
    
    if (namesResult.length === 0) {
      throw new Error('One or more referenced entities do not exist');
    }
    
    const names = namesResult[0];
    
    if (!names.requestorName || 
        !names.accountName || 
        !names.categoryName || 
        !names.categoryDetailName || 
        !names.requestChannelName || 
        !names.personInChargeName || 
        !names.statusName) {
      throw new Error('One or more referenced entities do not exist');
    }
    
    // Insert new ticket
    const insertResult = await insertTicket.run({
      id: ticketId,
      receptionDateTime: ticketData.receptionDateTime ? new Date(ticketData.receptionDateTime) : new Date(),
      requestorId: ticketData.requestorId,
      requestorName: names.requestorName,
      accountId: ticketData.accountId,
      accountName: names.accountName,
      categoryId: ticketData.categoryId,
      categoryName: names.categoryName,
      categoryDetailId: ticketData.categoryDetailId,
      categoryDetailName: names.categoryDetailName,
      requestChannelId: ticketData.requestChannelId,
      requestChannelName: names.requestChannelName,
      summary: ticketData.summary,
      description: ticketData.description,
      personInChargeId: ticketData.personInChargeId,
      personInChargeName: names.personInChargeName,
      statusId: ticketData.statusId,
      statusName: names.statusName,
      scheduledCompletionDate: ticketData.scheduledCompletionDate ? new Date(ticketData.scheduledCompletionDate) : null,
      completionDate: ticketData.completionDate ? new Date(ticketData.completionDate) : null,
      actualEffortHours: ticketData.actualEffortHours,
      responseCategoryId: ticketData.responseCategoryId,
      responseCategoryName: names.responseCategoryName,
      responseDetails: ticketData.responseDetails,
      hasDefect: ticketData.hasDefect || false,
      externalTicketId: ticketData.externalTicketId,
      remarks: ticketData.remarks
    }, client);
    
    // Return the new ticket ID
    return insertResult[0].id;
  });
};

/**
 * Update an existing ticket
 */
export const updateTicketById = async (
  ticketId: string, 
  updates: Partial<Omit<TicketDetail, 'id' | 'attachments'>>, 
  pool: Pool
): Promise<string> => {
  return executeTransaction(pool, async (client) => {
    // Check if ticket exists
    const existingTicket = await findTicketById.run({ id: ticketId }, client);
    
    if (existingTicket.length === 0) {
      throw new Error('Ticket not found');
    }
    
    // Get the names for the updated IDs
    const namesResult = await getNamesForUpdate.run({
      requestorId: updates.requestorId || null,
      accountId: updates.accountId || null,
      categoryId: updates.categoryId || null,
      categoryDetailId: updates.categoryDetailId || null,
      requestChannelId: updates.requestChannelId || null,
      personInChargeId: updates.personInChargeId || null,
      statusId: updates.statusId || null,
      responseCategoryId: updates.responseCategoryId || null,
      updatedById: updates.updatedById || null
    }, client);
    
    if (namesResult.length === 0) {
      throw new Error('One or more referenced entities do not exist');
    }
    
    const names = namesResult[0];
    
    // Update the ticket
    const updateResult = await updateTicket.run({
      id: ticketId,
      requestorId: updates.requestorId || null,
      requestorName: updates.requestorId ? names.requestorName : null,
      accountId: updates.accountId || null,
      accountName: updates.accountId ? names.accountName : null,
      categoryId: updates.categoryId || null,
      categoryName: updates.categoryId ? names.categoryName : null,
      categoryDetailId: updates.categoryDetailId || null,
      categoryDetailName: updates.categoryDetailId ? names.categoryDetailName : null,
      requestChannelId: updates.requestChannelId || null,
      requestChannelName: updates.requestChannelId ? names.requestChannelName : null,
      summary: updates.summary || null,
      description: updates.description || null,
      personInChargeId: updates.personInChargeId || null,
      personInChargeName: updates.personInChargeId ? names.personInChargeName : null,
      statusId: updates.statusId || null,
      statusName: updates.statusId ? names.statusName : null,
      scheduledCompletionDate: updates.scheduledCompletionDate ? new Date(updates.scheduledCompletionDate) : null,
      completionDate: updates.completionDate ? new Date(updates.completionDate) : null,
      actualEffortHours: updates.actualEffortHours || null,
      responseCategoryId: updates.responseCategoryId || null,
      responseCategoryName: updates.responseCategoryId ? names.responseCategoryName : null,
      responseDetails: updates.responseDetails || null,
      hasDefect: updates.hasDefect !== undefined ? updates.hasDefect : null,
      externalTicketId: updates.externalTicketId || null,
      remarks: updates.remarks || null
    }, client);
    
    return updateResult[0].id;
  });
};