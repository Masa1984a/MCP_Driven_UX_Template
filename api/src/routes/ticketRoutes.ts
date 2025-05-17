import { Router } from 'express';
import {
  getTicketList,
  getTicketDetail,
  createTicket,
  updateTicket,
  addTicketHistory,
  getTicketHistory,
  getUsersList,
  getAccountsList,
  getCategoriesList,
  getCategoryDetailsList,
  getStatusesList,
  getRequestChannelsList,
  getResponseCategoriesList
} from '../controllers/ticketController';

export const ticketRoutes = Router();

// Ticket endpoints
ticketRoutes.get('/', getTicketList);
ticketRoutes.get('/:id', getTicketDetail);
ticketRoutes.post('/', createTicket);
ticketRoutes.put('/:id', updateTicket);
ticketRoutes.post('/:id/history', addTicketHistory);
ticketRoutes.get('/:id/history', getTicketHistory);

// Master data endpoints
ticketRoutes.get('/master/users', getUsersList);
ticketRoutes.get('/master/accounts', getAccountsList);
ticketRoutes.get('/master/categories', getCategoriesList);
ticketRoutes.get('/master/category-details', getCategoryDetailsList);
ticketRoutes.get('/master/statuses', getStatusesList);
ticketRoutes.get('/master/request-channels', getRequestChannelsList);
ticketRoutes.get('/master/response-categories', getResponseCategoriesList);