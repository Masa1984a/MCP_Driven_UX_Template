import { Pool } from 'pg';

declare global {
  namespace Express {
    interface Request {
      db: Pool;
    }
  }
}

export interface Ticket {
  ticketId: string;
  receptionDateTime: string | null;
  requestorName: string;
  accountName: string;
  categoryName: string;
  categoryDetailName: string;
  summary: string;
  personInChargeName: string;
  statusName: string;
  scheduledCompletionDate: string | null;
  remainingDays: number | null;
  externalTicketId: string | null;
}

export interface TicketQueryParams {
  personInChargeId?: string;
  accountId?: string;
  statusId?: string;
  scheduledCompletionDateFrom?: string;
  scheduledCompletionDateTo?: string;
  showCompleted?: boolean;
  searchQuery?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}