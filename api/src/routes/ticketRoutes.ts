import { Router } from 'express';
import { getTicketList } from '../controllers/ticketController';

export const ticketRoutes = Router();

// Get ticket list
ticketRoutes.get('/', getTicketList);