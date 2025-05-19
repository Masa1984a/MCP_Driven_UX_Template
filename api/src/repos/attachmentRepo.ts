import { Pool } from 'pg';
import { Attachment } from '../types';
// Import generated types - these will be generated when pgtyped runs
import { findByTicketId } from '../sql/attachments/findByTicketId.types';
import { createAttachment } from '../sql/attachments/create.types';

/**
 * Get all attachments for a ticket
 */
export const getAttachmentsByTicketId = async (ticketId: string, pool: Pool): Promise<Attachment[]> => {
  const client = await pool.connect();
  try {
    const result = await findByTicketId.run({ ticketId }, client);
    
    return result.map(row => ({
      id: row.id,
      fileName: row.fileName,
      fileUrl: row.fileUrl,
      uploadedAt: row.uploadedAt
    }));
  } finally {
    client.release();
  }
};

/**
 * Add a new attachment to a ticket
 */
export const addAttachment = async (
  ticketId: string,
  fileName: string,
  fileUrl: string,
  uploadedById: string,
  uploadedByName: string,
  pool: Pool
): Promise<number> => {
  const client = await pool.connect();
  try {
    const result = await createAttachment.run({
      ticketId,
      fileName,
      fileUrl,
      uploadedById,
      uploadedByName
    }, client);
    
    return result[0].id;
  } finally {
    client.release();
  }
};