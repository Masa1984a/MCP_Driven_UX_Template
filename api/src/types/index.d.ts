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

export interface TicketDetail {
  id: string;
  receptionDateTime: string | null;
  requestorId: string;
  requestorName: string;
  accountId: string;
  accountName: string;
  categoryId: string;
  categoryName: string;
  categoryDetailId: string;
  categoryDetailName: string;
  requestChannelId: string;
  requestChannelName: string;
  summary: string;
  description: string | null;
  personInChargeId: string;
  personInChargeName: string;
  statusId: string;
  statusName: string;
  scheduledCompletionDate: string | null;
  completionDate: string | null;
  actualEffortHours: number | null;
  responseCategoryId: string | null;
  responseCategoryName: string | null;
  responseDetails: string | null;
  hasDefect: boolean;
  externalTicketId: string | null;
  remarks: string | null;
  attachments: Attachment[];
}

export interface Attachment {
  id: number;
  fileName: string;
  fileUrl: string;
  uploadedAt: string;
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

export interface TicketHistoryEntry {
  id: number;
  timestamp: string;
  userId: string;
  userName: string;
  comment: string;
  changedFields: ChangedField[];
}

export interface ChangedField {
  fieldName: string;
  oldValue: string | null;
  newValue: string | null;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface Account {
  id: string;
  name: string;
  orderNo: number;
}

export interface Category {
  id: string;
  name: string;
  orderNo: number;
}

export interface CategoryDetail {
  id: string;
  name: string;
  categoryId: string;
  categoryName: string;
  orderNo: number;
}

export interface Status {
  id: string;
  name: string;
  orderNo: number;
}

export interface RequestChannel {
  id: string;
  name: string;
  orderNo: number;
}

export interface ResponseCategory {
  id: string;
  name: string;
  parentCategory: string | null;
  orderNo: number;
}