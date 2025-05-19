import { Pool } from 'pg';
import { 
  Account, 
  Category, 
  CategoryDetail, 
  RequestChannel,
  ResponseCategory,
  Status, 
  User 
} from '../types';
// Import generated types - these will be generated when pgtyped runs
import { findAllAccounts } from '../sql/accounts/findAll.types';
import { findAllCategories } from '../sql/categories/findAll.types';
import { findAllCategoryDetails } from '../sql/category_details/findAll.types';
import { findAllStatuses } from '../sql/statuses/findAll.types';
import { findAllRequestChannels } from '../sql/request_channels/findAll.types';
import { findAllResponseCategories } from '../sql/response_categories/findAll.types';

/**
 * Get all users
 * Note: Users table is handled by existing implementation per requirements
 */
export const getUsers = async (pool: Pool): Promise<User[]> => {
  const client = await pool.connect();
  try {
    const query = `
      SELECT id, name, email, role
      FROM mcp_ux.users
      ORDER BY name ASC
    `;
    
    const result = await client.query(query);
    
    return result.rows.map(row => ({
      id: row.id,
      name: row.name,
      email: row.email,
      role: row.role
    }));
  } finally {
    client.release();
  }
};

/**
 * Get all accounts
 */
export const getAccounts = async (pool: Pool): Promise<Account[]> => {
  const client = await pool.connect();
  try {
    const result = await findAllAccounts.run({}, client);
    
    return result.map(row => ({
      id: row.id,
      name: row.name,
      orderNo: row.orderNo
    }));
  } finally {
    client.release();
  }
};

/**
 * Get all categories
 */
export const getCategories = async (pool: Pool): Promise<Category[]> => {
  const client = await pool.connect();
  try {
    const result = await findAllCategories.run({}, client);
    
    return result.map(row => ({
      id: row.id,
      name: row.name,
      orderNo: row.orderNo
    }));
  } finally {
    client.release();
  }
};

/**
 * Get category details, optionally filtered by category ID
 */
export const getCategoryDetails = async (categoryId: string | null, pool: Pool): Promise<CategoryDetail[]> => {
  const client = await pool.connect();
  try {
    const result = await findAllCategoryDetails.run({ categoryId }, client);
    
    return result.map(row => ({
      id: row.id,
      name: row.name,
      categoryId: row.categoryId,
      categoryName: row.categoryName,
      orderNo: row.orderNo
    }));
  } finally {
    client.release();
  }
};

/**
 * Get all statuses
 */
export const getStatuses = async (pool: Pool): Promise<Status[]> => {
  const client = await pool.connect();
  try {
    const result = await findAllStatuses.run({}, client);
    
    return result.map(row => ({
      id: row.id,
      name: row.name,
      orderNo: row.orderNo
    }));
  } finally {
    client.release();
  }
};

/**
 * Get all request channels
 */
export const getRequestChannels = async (pool: Pool): Promise<RequestChannel[]> => {
  const client = await pool.connect();
  try {
    const result = await findAllRequestChannels.run({}, client);
    
    return result.map(row => ({
      id: row.id,
      name: row.name,
      orderNo: row.orderNo
    }));
  } finally {
    client.release();
  }
};

/**
 * Get all response categories
 */
export const getResponseCategories = async (pool: Pool): Promise<ResponseCategory[]> => {
  const client = await pool.connect();
  try {
    const result = await findAllResponseCategories.run({}, client);
    
    return result.map(row => ({
      id: row.id,
      name: row.name,
      parentCategory: row.parentCategory,
      orderNo: row.orderNo
    }));
  } finally {
    client.release();
  }
};